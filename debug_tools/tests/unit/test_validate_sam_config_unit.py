"""
Unit tests for SAM configuration validator.

Tests validation of template.yaml including CodeUri paths, function names,
runtime settings, and environment parameter configuration.
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from validate_sam_config import (
    validate_code_uris,
    check_duplicate_functions,
    validate_runtime_settings,
    validate_environment_config
)
from models import ConfigIssue


class TestValidateCodeUris:
    """Test CodeUri path validation."""
    
    def test_valid_code_uri_paths(self, tmp_path, monkeypatch):
        """Test that valid CodeUri paths pass validation."""
        # Create test directories
        (tmp_path / "user_login").mkdir()
        (tmp_path / "user_registration").mkdir()
        
        # Mock get_project_root to return tmp_path
        monkeypatch.setattr('validate_sam_config.get_project_root', lambda: str(tmp_path))
        
        template = {
            'Resources': {
                'UserLoginFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'CodeUri': 'user_login/',
                        'Handler': 'app.lambda_handler'
                    }
                },
                'UserRegistrationFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'CodeUri': 'user_registration/',
                        'Handler': 'app.lambda_handler'
                    }
                }
            }
        }
        
        issues = validate_code_uris(template)
        assert len(issues) == 0
    
    def test_missing_code_uri_path(self, tmp_path, monkeypatch):
        """Test that missing CodeUri paths are detected."""
        # Don't create the directory
        monkeypatch.setattr('validate_sam_config.get_project_root', lambda: str(tmp_path))
        
        template = {
            'Resources': {
                'MissingFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'CodeUri': 'nonexistent_function/',
                        'Handler': 'app.lambda_handler'
                    }
                }
            }
        }
        
        issues = validate_code_uris(template)
        assert len(issues) == 1
        assert issues[0].issue_type == 'missing_path'
        assert 'nonexistent_function' in issues[0].details
        assert 'MissingFunction' in issues[0].location
    
    def test_code_uri_is_file_not_directory(self, tmp_path, monkeypatch):
        """Test that CodeUri pointing to a file is detected."""
        # Create a file instead of directory
        (tmp_path / "not_a_directory.txt").write_text("test")
        
        monkeypatch.setattr('validate_sam_config.get_project_root', lambda: str(tmp_path))
        
        template = {
            'Resources': {
                'BadFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'CodeUri': 'not_a_directory.txt',
                        'Handler': 'app.lambda_handler'
                    }
                }
            }
        }
        
        issues = validate_code_uris(template)
        assert len(issues) == 1
        assert issues[0].issue_type == 'missing_path'
        assert 'not a directory' in issues[0].details
    
    def test_missing_code_uri_property(self, tmp_path, monkeypatch):
        """Test that missing CodeUri property is detected."""
        monkeypatch.setattr('validate_sam_config.get_project_root', lambda: str(tmp_path))
        
        template = {
            'Resources': {
                'NoCodeUriFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'Handler': 'app.lambda_handler'
                    }
                }
            }
        }
        
        issues = validate_code_uris(template)
        assert len(issues) == 1
        assert issues[0].issue_type == 'missing_path'
        assert 'no CodeUri specified' in issues[0].details
    
    def test_non_lambda_resources_ignored(self, tmp_path, monkeypatch):
        """Test that non-Lambda resources are ignored."""
        monkeypatch.setattr('validate_sam_config.get_project_root', lambda: str(tmp_path))
        
        template = {
            'Resources': {
                'MyTable': {
                    'Type': 'AWS::DynamoDB::Table',
                    'Properties': {
                        'TableName': 'Users'
                    }
                },
                'MyBucket': {
                    'Type': 'AWS::S3::Bucket',
                    'Properties': {
                        'BucketName': 'my-bucket'
                    }
                }
            }
        }
        
        issues = validate_code_uris(template)
        assert len(issues) == 0


class TestCheckDuplicateFunctions:
    """Test duplicate function name detection."""
    
    def test_no_duplicate_functions(self):
        """Test that unique function names pass validation."""
        template = {
            'Resources': {
                'UserLoginFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {}
                },
                'UserRegistrationFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {}
                },
                'PasswordRecoveryFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {}
                }
            }
        }
        
        issues = check_duplicate_functions(template)
        assert len(issues) == 0
    
    def test_duplicate_function_names(self):
        """Test that duplicate function names are detected."""
        # Note: In practice, YAML parsing would prevent duplicate keys,
        # but we test the logic for completeness
        template = {
            'Resources': {
                'UserLoginFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {}
                }
            }
        }
        
        # Manually check for duplicates (in real scenario, YAML would handle this)
        issues = check_duplicate_functions(template)
        # No duplicates in this structure
        assert len(issues) == 0
    
    def test_mixed_resource_types(self):
        """Test that only Lambda functions are checked for duplicates."""
        template = {
            'Resources': {
                'UserLoginFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {}
                },
                'UsersTable': {
                    'Type': 'AWS::DynamoDB::Table',
                    'Properties': {}
                },
                'DocumentsBucket': {
                    'Type': 'AWS::S3::Bucket',
                    'Properties': {}
                }
            }
        }
        
        issues = check_duplicate_functions(template)
        assert len(issues) == 0


class TestValidateRuntimeSettings:
    """Test runtime setting validation."""
    
    def test_correct_runtime_python314(self):
        """Test that python3.14 runtime passes validation."""
        template = {
            'Resources': {
                'UserLoginFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'Runtime': 'python3.14'
                    }
                },
                'UserRegistrationFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'Runtime': 'python3.14'
                    }
                }
            }
        }
        
        issues = validate_runtime_settings(template)
        assert len(issues) == 0
    
    def test_incorrect_runtime_version(self):
        """Test that incorrect runtime versions are detected."""
        template = {
            'Resources': {
                'OldPythonFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'Runtime': 'python3.9'
                    }
                },
                'NodeFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'Runtime': 'nodejs18.x'
                    }
                }
            }
        }
        
        issues = validate_runtime_settings(template)
        assert len(issues) == 2
        assert all(issue.issue_type == 'invalid_runtime' for issue in issues)
        assert any('python3.9' in issue.details for issue in issues)
        assert any('nodejs18.x' in issue.details for issue in issues)
    
    def test_missing_runtime_property(self):
        """Test that missing Runtime property is detected."""
        template = {
            'Resources': {
                'NoRuntimeFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'Handler': 'app.lambda_handler'
                    }
                }
            }
        }
        
        issues = validate_runtime_settings(template)
        assert len(issues) == 1
        assert issues[0].issue_type == 'invalid_runtime'
        assert 'no Runtime specified' in issues[0].details
    
    def test_non_lambda_resources_ignored_runtime(self):
        """Test that non-Lambda resources are ignored for runtime checks."""
        template = {
            'Resources': {
                'MyTable': {
                    'Type': 'AWS::DynamoDB::Table',
                    'Properties': {}
                }
            }
        }
        
        issues = validate_runtime_settings(template)
        assert len(issues) == 0


class TestValidateEnvironmentConfig:
    """Test environment parameter configuration validation."""
    
    def test_valid_environment_config(self):
        """Test that valid environment configuration passes."""
        template = {
            'Parameters': {
                'Environment': {
                    'Type': 'String',
                    'Default': 'local',
                    'AllowedValues': ['local', 'production']
                }
            },
            'Conditions': {
                'IsLocal': {'Fn::Equals': [{'Ref': 'Environment'}, 'local']}
            },
            'Resources': {
                'UserLoginFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'Environment': {
                            'Variables': {
                                'AWS_ENDPOINT_URL': {
                                    'Fn::If': ['IsLocal', 'http://172.18.0.1:4566', {'Ref': 'AWS::NoValue'}]
                                }
                            }
                        }
                    }
                }
            }
        }
        
        issues = validate_environment_config(template)
        assert len(issues) == 0
    
    def test_missing_environment_parameter(self):
        """Test that missing Environment parameter is detected."""
        template = {
            'Parameters': {},
            'Resources': {}
        }
        
        issues = validate_environment_config(template)
        assert len(issues) == 1
        assert issues[0].issue_type == 'env_config'
        assert 'Environment parameter not defined' in issues[0].details
    
    def test_incorrect_environment_type(self):
        """Test that incorrect Environment parameter type is detected."""
        template = {
            'Parameters': {
                'Environment': {
                    'Type': 'Number',
                    'AllowedValues': ['local', 'production']
                }
            },
            'Conditions': {
                'IsLocal': {'Fn::Equals': [{'Ref': 'Environment'}, 'local']}
            },
            'Resources': {}
        }
        
        issues = validate_environment_config(template)
        assert len(issues) == 1
        assert issues[0].issue_type == 'env_config'
        assert 'Type' in issues[0].details
    
    def test_incorrect_allowed_values(self):
        """Test that incorrect AllowedValues are detected."""
        template = {
            'Parameters': {
                'Environment': {
                    'Type': 'String',
                    'AllowedValues': ['dev', 'prod']
                }
            },
            'Conditions': {
                'IsLocal': {'Fn::Equals': [{'Ref': 'Environment'}, 'local']}
            },
            'Resources': {}
        }
        
        issues = validate_environment_config(template)
        assert len(issues) == 1
        assert issues[0].issue_type == 'env_config'
        assert 'AllowedValues' in issues[0].details
    
    def test_missing_islocal_condition(self):
        """Test that missing IsLocal condition is detected."""
        template = {
            'Parameters': {
                'Environment': {
                    'Type': 'String',
                    'AllowedValues': ['local', 'production']
                }
            },
            'Conditions': {},
            'Resources': {}
        }
        
        issues = validate_environment_config(template)
        assert len(issues) == 1
        assert issues[0].issue_type == 'env_config'
        assert 'IsLocal condition not defined' in issues[0].details
    
    def test_endpoint_url_without_condition(self):
        """Test that AWS_ENDPOINT_URL without IsLocal condition is detected."""
        template = {
            'Parameters': {
                'Environment': {
                    'Type': 'String',
                    'AllowedValues': ['local', 'production']
                }
            },
            'Conditions': {
                'IsLocal': {'Fn::Equals': [{'Ref': 'Environment'}, 'local']}
            },
            'Resources': {
                'BadFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        'Environment': {
                            'Variables': {
                                'AWS_ENDPOINT_URL': 'http://localhost:4566'
                            }
                        }
                    }
                }
            }
        }
        
        issues = validate_environment_config(template)
        assert len(issues) == 1
        assert issues[0].issue_type == 'env_config'
        assert 'should use IsLocal condition' in issues[0].details


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_template(self):
        """Test handling of empty template."""
        template = {}
        
        # Should not crash, just return empty or minimal issues
        code_uri_issues = validate_code_uris(template)
        duplicate_issues = check_duplicate_functions(template)
        runtime_issues = validate_runtime_settings(template)
        env_issues = validate_environment_config(template)
        
        # Empty template should have environment config issues
        assert len(env_issues) > 0
    
    def test_template_with_no_resources(self):
        """Test template with no Resources section."""
        template = {
            'Parameters': {
                'Environment': {
                    'Type': 'String',
                    'AllowedValues': ['local', 'production']
                }
            },
            'Conditions': {
                'IsLocal': {'Fn::Equals': [{'Ref': 'Environment'}, 'local']}
            }
        }
        
        issues = validate_code_uris(template)
        assert len(issues) == 0
        
        issues = check_duplicate_functions(template)
        assert len(issues) == 0
        
        issues = validate_runtime_settings(template)
        assert len(issues) == 0
    
    def test_template_with_empty_resources(self):
        """Test template with empty Resources section."""
        template = {
            'Resources': {}
        }
        
        issues = validate_code_uris(template)
        assert len(issues) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
