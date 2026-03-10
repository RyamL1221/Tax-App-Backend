"""
Unit tests for dependency validation.

Tests the dependency validator functions with specific examples and edge cases.
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from validate_dependencies import (
    parse_requirements_file,
    validate_package_names,
    validate_version_syntax,
    check_version_conflicts,
    Requirement
)


class TestParseRequirementsFile:
    """Test requirements.txt parsing."""
    
    def test_parse_simple_requirements(self):
        """Test parsing simple package names without versions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("boto3\n")
            f.write("requests\n")
            f.write("PyYAML\n")
            f.flush()
            
            try:
                requirements = parse_requirements_file(f.name)
                
                assert len(requirements) == 3
                assert requirements[0].package_name == "boto3"
                assert requirements[0].version_spec == ""
                assert requirements[1].package_name == "requests"
                assert requirements[2].package_name == "PyYAML"
            finally:
                os.unlink(f.name)
    
    def test_parse_versioned_requirements(self):
        """Test parsing packages with version specifications."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("boto3==1.26.0\n")
            f.write("requests>=2.28.0\n")
            f.write("PyYAML~=6.0\n")
            f.flush()
            
            try:
                requirements = parse_requirements_file(f.name)
                
                assert len(requirements) == 3
                assert requirements[0].package_name == "boto3"
                assert requirements[0].version_spec == "==1.26.0"
                assert requirements[1].package_name == "requests"
                assert requirements[1].version_spec == ">=2.28.0"
                assert requirements[2].package_name == "PyYAML"
                assert requirements[2].version_spec == "~=6.0"
            finally:
                os.unlink(f.name)
    
    def test_parse_with_comments(self):
        """Test parsing with comments and empty lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("# This is a comment\n")
            f.write("boto3==1.26.0  # AWS SDK\n")
            f.write("\n")
            f.write("requests>=2.28.0\n")
            f.write("# Another comment\n")
            f.flush()
            
            try:
                requirements = parse_requirements_file(f.name)
                
                assert len(requirements) == 2
                assert requirements[0].package_name == "boto3"
                assert requirements[0].version_spec == "==1.26.0"
                assert requirements[1].package_name == "requests"
            finally:
                os.unlink(f.name)
    
    def test_parse_compound_version_specs(self):
        """Test parsing compound version specifications."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("boto3>=1.26.0,<2.0.0\n")
            f.write("requests>=2.28.0,!=2.29.0\n")
            f.flush()
            
            try:
                requirements = parse_requirements_file(f.name)
                
                assert len(requirements) == 2
                assert requirements[0].version_spec == ">=1.26.0,<2.0.0"
                assert requirements[1].version_spec == ">=2.28.0,!=2.29.0"
            finally:
                os.unlink(f.name)
    
    def test_parse_preserves_line_numbers(self):
        """Test that line numbers are preserved for error reporting."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("# Comment\n")
            f.write("boto3\n")
            f.write("\n")
            f.write("requests\n")
            f.flush()
            
            try:
                requirements = parse_requirements_file(f.name)
                
                assert requirements[0].line_number == 2
                assert requirements[1].line_number == 4
            finally:
                os.unlink(f.name)


class TestValidatePackageNames:
    """Test package name validation."""
    
    def test_valid_package_names(self):
        """Test that valid package names pass validation."""
        requirements = [
            Requirement("boto3", "", "boto3", 1),
            Requirement("PyYAML", "", "PyYAML", 2),
            Requirement("python-dateutil", "", "python-dateutil", 3),
            Requirement("requests_oauthlib", "", "requests_oauthlib", 4),
            Requirement("Flask-CORS", "", "Flask-CORS", 5),
        ]
        
        invalid = validate_package_names(requirements)
        assert len(invalid) == 0
    
    def test_invalid_package_names_special_chars(self):
        """Test that package names with invalid characters are rejected."""
        requirements = [
            Requirement("boto3!", "", "boto3!", 1),
            Requirement("@package", "", "@package", 2),
            Requirement("package$name", "", "package$name", 3),
        ]
        
        invalid = validate_package_names(requirements)
        assert len(invalid) == 3
        assert any("boto3!" in name for name, _ in invalid)
        assert any("@package" in name for name, _ in invalid)
        assert any("package$name" in name for name, _ in invalid)
    
    def test_invalid_package_names_start_end(self):
        """Test that package names starting/ending with special chars are rejected."""
        requirements = [
            Requirement("-boto3", "", "-boto3", 1),
            Requirement("boto3-", "", "boto3-", 2),
            Requirement("_package", "", "_package", 3),
            Requirement(".package", "", ".package", 4),
        ]
        
        invalid = validate_package_names(requirements)
        assert len(invalid) == 4
        
        # Check error messages are specific
        errors = {name: error for name, error in invalid}
        assert "cannot start" in errors["-boto3"].lower()
        assert "cannot end" in errors["boto3-"].lower()
    
    def test_empty_package_name(self):
        """Test that empty package names are rejected."""
        requirements = [
            Requirement("", "", "", 1),
        ]
        
        invalid = validate_package_names(requirements)
        assert len(invalid) == 1
        assert "empty" in invalid[0][1].lower()


class TestValidateVersionSyntax:
    """Test version syntax validation."""
    
    def test_valid_version_specs(self):
        """Test that valid version specifications pass validation."""
        requirements = [
            Requirement("boto3", "==1.26.0", "boto3==1.26.0", 1),
            Requirement("requests", ">=2.28.0", "requests>=2.28.0", 2),
            Requirement("PyYAML", "~=6.0", "PyYAML~=6.0", 3),
            Requirement("flask", "<2.0", "flask<2.0", 4),
            Requirement("django", "<=4.0.0", "django<=4.0.0", 5),
            Requirement("pytest", "!=7.0.0", "pytest!=7.0.0", 6),
            Requirement("numpy", "", "numpy", 7),  # No version is valid
        ]
        
        invalid = validate_version_syntax(requirements)
        assert len(invalid) == 0
    
    def test_valid_compound_version_specs(self):
        """Test that compound version specifications pass validation."""
        requirements = [
            Requirement("boto3", ">=1.26.0,<2.0.0", "boto3>=1.26.0,<2.0.0", 1),
            Requirement("requests", ">=2.28.0,!=2.29.0", "requests>=2.28.0,!=2.29.0", 2),
        ]
        
        invalid = validate_version_syntax(requirements)
        assert len(invalid) == 0
    
    def test_invalid_version_missing_operator(self):
        """Test that version specs without operators are rejected."""
        requirements = [
            Requirement("boto3", "1.26.0", "boto3 1.26.0", 1),
        ]
        
        invalid = validate_version_syntax(requirements)
        assert len(invalid) == 1
        assert "operator" in invalid[0][2].lower()
    
    def test_invalid_version_wrong_operator(self):
        """Test that version specs with wrong operators are rejected."""
        requirements = [
            Requirement("boto3", "=1.26.0", "boto3=1.26.0", 1),  # Should be ==
            Requirement("requests", ">>2.28.0", "requests>>2.28.0", 2),  # Should be >
        ]
        
        invalid = validate_version_syntax(requirements)
        assert len(invalid) == 2
        
        # Check for specific error messages
        errors = {pkg: error for pkg, _, error in invalid}
        assert "==" in errors["boto3"]
        assert "operator" in errors["requests"].lower()
    
    def test_version_with_prerelease(self):
        """Test that versions with pre-release suffixes are valid."""
        requirements = [
            Requirement("package", "==1.0.0a1", "package==1.0.0a1", 1),
            Requirement("package2", ">=1.0.0rc1", "package2>=1.0.0rc1", 2),
            Requirement("package3", "~=1.0.0.post1", "package3~=1.0.0.post1", 3),
        ]
        
        invalid = validate_version_syntax(requirements)
        assert len(invalid) == 0


class TestCheckVersionConflicts:
    """Test version conflict detection."""
    
    def test_no_conflicts(self):
        """Test that identical versions across functions don't conflict."""
        all_requirements = {
            "user_login": [
                Requirement("boto3", ">=1.34.0", "boto3>=1.34.0", 1),
                Requirement("bcrypt", ">=4.1.0", "bcrypt>=4.1.0", 2),
            ],
            "user_registration": [
                Requirement("boto3", ">=1.34.0", "boto3>=1.34.0", 1),
                Requirement("bcrypt", ">=4.1.0", "bcrypt>=4.1.0", 2),
            ],
        }
        
        conflicts = check_version_conflicts(all_requirements)
        assert len(conflicts) == 0
    
    def test_version_conflicts_detected(self):
        """Test that different versions are detected as conflicts."""
        all_requirements = {
            "user_login": [
                Requirement("boto3", ">=1.34.0", "boto3>=1.34.0", 1),
            ],
            "user_registration": [
                Requirement("boto3", ">=1.26.0", "boto3>=1.26.0", 1),
            ],
        }
        
        conflicts = check_version_conflicts(all_requirements)
        assert len(conflicts) == 1
        
        package_name, details = conflicts[0]
        assert package_name == "boto3"
        assert "user_login" in details['functions']
        assert "user_registration" in details['functions']
        assert ">=1.34.0" in details['versions']
        assert ">=1.26.0" in details['versions']
    
    def test_latest_vs_pinned_conflict(self):
        """Test that no version (latest) conflicts with pinned versions."""
        all_requirements = {
            "user_login": [
                Requirement("boto3", "", "boto3", 1),  # No version = latest
            ],
            "user_registration": [
                Requirement("boto3", ">=1.34.0", "boto3>=1.34.0", 1),
            ],
        }
        
        conflicts = check_version_conflicts(all_requirements)
        assert len(conflicts) == 1
        
        package_name, details = conflicts[0]
        assert package_name == "boto3"
        assert "<latest>" in details['versions']
        assert ">=1.34.0" in details['versions']
    
    def test_multiple_conflicts(self):
        """Test detection of multiple conflicting packages."""
        all_requirements = {
            "function1": [
                Requirement("boto3", ">=1.34.0", "boto3>=1.34.0", 1),
                Requirement("bcrypt", ">=4.1.0", "bcrypt>=4.1.0", 2),
            ],
            "function2": [
                Requirement("boto3", ">=1.26.0", "boto3>=1.26.0", 1),
                Requirement("bcrypt", ">=4.0.0", "bcrypt>=4.0.0", 2),
            ],
        }
        
        conflicts = check_version_conflicts(all_requirements)
        assert len(conflicts) == 2
        
        conflict_packages = {pkg for pkg, _ in conflicts}
        assert "boto3" in conflict_packages
        assert "bcrypt" in conflict_packages
    
    def test_three_way_conflict(self):
        """Test conflicts across three Lambda functions."""
        all_requirements = {
            "function1": [
                Requirement("boto3", ">=1.34.0", "boto3>=1.34.0", 1),
            ],
            "function2": [
                Requirement("boto3", ">=1.26.0", "boto3>=1.26.0", 1),
            ],
            "function3": [
                Requirement("boto3", "", "boto3", 1),
            ],
        }
        
        conflicts = check_version_conflicts(all_requirements)
        assert len(conflicts) == 1
        
        package_name, details = conflicts[0]
        assert len(details['functions']) == 3
        assert len(details['versions']) == 3


class TestErrorHandling:
    """Test error handling in validation functions."""
    
    def test_parse_nonexistent_file(self):
        """Test that parsing nonexistent file raises appropriate error."""
        with pytest.raises(ValueError, match="Could not read"):
            parse_requirements_file("/nonexistent/file.txt")
    
    def test_validate_empty_requirements_list(self):
        """Test that validating empty list returns no issues."""
        invalid_names = validate_package_names([])
        assert len(invalid_names) == 0
        
        invalid_versions = validate_version_syntax([])
        assert len(invalid_versions) == 0
    
    def test_check_conflicts_empty_dict(self):
        """Test that checking conflicts with empty dict returns no conflicts."""
        conflicts = check_version_conflicts({})
        assert len(conflicts) == 0
    
    def test_check_conflicts_single_function(self):
        """Test that single function has no conflicts."""
        all_requirements = {
            "function1": [
                Requirement("boto3", ">=1.34.0", "boto3>=1.34.0", 1),
                Requirement("bcrypt", ">=4.1.0", "bcrypt>=4.1.0", 2),
            ],
        }
        
        conflicts = check_version_conflicts(all_requirements)
        assert len(conflicts) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
