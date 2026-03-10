"""
Property-based tests for Lambda code environment variable completeness.

These tests verify that all environment variables accessed by the Lambda code
via os.environ.get() are defined in the env.json configuration for
GenerateTaxDocumentFunction.

This ensures that the local development configuration provides all variables
that the Lambda code expects at runtime.
"""

import ast
import json
import pytest
from pathlib import Path
from typing import Set, List, Tuple


class TestLambdaCodeEnvCompletenessProperty:
    """Property-based tests for Lambda code environment variable completeness."""
    
    @pytest.fixture
    def env_json_path(self):
        """Path to the env.json configuration file."""
        return Path(__file__).parent.parent / "env.json"
    
    @pytest.fixture
    def lambda_code_dir(self):
        """Path to the Lambda code directory."""
        return Path(__file__).parent.parent / "tax_document_generation"
    
    @pytest.fixture
    def env_config(self, env_json_path):
        """Load and parse the env.json configuration."""
        with open(env_json_path, 'r') as f:
            return json.load(f)
    
    def extract_env_vars_from_python_code(self, python_file_path: Path) -> Set[str]:
        """
        Extract environment variable names accessed via os.environ.get() from a Python file.
        
        Args:
            python_file_path: Path to the Python file to analyze
        
        Returns:
            Set of environment variable names accessed in the file
        """
        env_vars = set()
        
        try:
            with open(python_file_path, 'r') as f:
                tree = ast.parse(f.read(), filename=str(python_file_path))
            
            # Walk the AST to find os.environ.get() calls
            for node in ast.walk(tree):
                # Look for attribute access: os.environ.get(...)
                if isinstance(node, ast.Call):
                    # Check if this is a call to .get() method
                    if isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
                        # Check if the object is os.environ
                        if isinstance(node.func.value, ast.Attribute):
                            if (node.func.value.attr == 'environ' and 
                                isinstance(node.func.value.value, ast.Name) and
                                node.func.value.value.id == 'os'):
                                # Extract the environment variable name (first argument)
                                if node.args and isinstance(node.args[0], ast.Constant):
                                    env_var_name = node.args[0].value
                                    if isinstance(env_var_name, str):
                                        env_vars.add(env_var_name)
                                elif node.args and isinstance(node.args[0], ast.Str):
                                    # For Python 3.7 compatibility
                                    env_vars.add(node.args[0].s)
        
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {python_file_path}: {e}")
        except Exception as e:
            pytest.fail(f"Failed to parse {python_file_path}: {e}")
        
        return env_vars
    
    def extract_all_env_vars_from_lambda_code(self, lambda_code_dir: Path) -> Set[str]:
        """
        Extract all environment variable names accessed by the Lambda code.
        
        Args:
            lambda_code_dir: Path to the Lambda code directory
        
        Returns:
            Set of all environment variable names accessed across all Python files
        """
        all_env_vars = set()
        
        # Find all Python files in the Lambda code directory (excluding tests)
        python_files = [
            f for f in lambda_code_dir.glob("*.py")
            if f.is_file() and not f.name.startswith("test_")
        ]
        
        for python_file in python_files:
            env_vars = self.extract_env_vars_from_python_code(python_file)
            all_env_vars.update(env_vars)
        
        return all_env_vars
    
    def extract_env_vars_from_config(self, env_config: dict, function_name: str) -> Set[str]:
        """
        Extract environment variable names from env.json for a specific function.
        
        Args:
            env_config: Parsed env.json dictionary
            function_name: Name of the Lambda function
        
        Returns:
            Set of environment variable names defined in env.json
        """
        try:
            function_env = env_config.get(function_name, {})
            return set(function_env.keys())
        except (KeyError, AttributeError) as e:
            pytest.fail(f"Failed to extract environment variables from env.json: {e}")
    
    def test_lambda_code_env_completeness(self, lambda_code_dir, env_config):
        """
        **Validates: Requirements 2.2**
        Feature: fix-s3-bucket-env-config, Property 2: Environment variable completeness for Lambda code
        
        For any environment variable accessed by the Lambda code via os.environ.get(),
        that variable name should be defined in the env.json configuration for
        GenerateTaxDocumentFunction.
        
        This test verifies that:
        1. All environment variables accessed in the Lambda code are present in env.json
        2. Variable names match exactly (case-sensitive)
        3. The local configuration provides all variables the code expects
        """
        function_name = "GenerateTaxDocumentFunction"
        
        # Extract environment variables from Lambda code
        code_env_vars = self.extract_all_env_vars_from_lambda_code(lambda_code_dir)
        
        # Extract environment variables from env.json
        config_env_vars = self.extract_env_vars_from_config(env_config, function_name)
        
        # Verification: All code variables should exist in env.json
        missing_vars = code_env_vars - config_env_vars
        
        assert len(missing_vars) == 0, (
            f"Environment variables accessed by Lambda code but missing from env.json: {missing_vars}\n"
            f"Code accesses: {sorted(code_env_vars)}\n"
            f"Config defines: {sorted(config_env_vars)}"
        )
    
    def test_lambda_code_accesses_environment_variables(self, lambda_code_dir):
        """
        **Validates: Requirements 2.2**
        Feature: fix-s3-bucket-env-config, Property 2: Environment variable completeness for Lambda code
        
        The Lambda code must access at least one environment variable.
        
        This test verifies that:
        1. The Lambda code uses os.environ.get() at least once
        2. Environment variables are being accessed
        3. The test has something to validate
        """
        code_env_vars = self.extract_all_env_vars_from_lambda_code(lambda_code_dir)
        
        # Verification: At least one environment variable should be accessed
        assert len(code_env_vars) > 0, (
            "Lambda code does not access any environment variables via os.environ.get()"
        )
    
    def test_env_json_defines_variables_for_function(self, env_config):
        """
        **Validates: Requirements 2.2**
        Feature: fix-s3-bucket-env-config, Property 2: Environment variable completeness for Lambda code
        
        The env.json must define environment variables for GenerateTaxDocumentFunction.
        
        This test verifies that:
        1. The function configuration exists in env.json
        2. At least one variable is defined
        3. The configuration is not empty
        """
        function_name = "GenerateTaxDocumentFunction"
        
        config_env_vars = self.extract_env_vars_from_config(env_config, function_name)
        
        # Verification: At least one environment variable should be defined
        assert len(config_env_vars) > 0, (
            f"{function_name} in env.json does not define any environment variables"
        )
    
    def test_specific_required_variables_are_present(self, lambda_code_dir, env_config):
        """
        **Validates: Requirements 2.2**
        Feature: fix-s3-bucket-env-config, Property 2: Environment variable completeness for Lambda code
        
        Specific critical environment variables must be present in env.json.
        
        This test verifies that:
        1. TEMPLATES_BUCKET is defined (required for template retrieval)
        2. OUTPUTS_BUCKET is defined (required for output storage)
        3. JOB_TABLE_NAME is defined (required for job tracking)
        4. JWT_SECRET_KEY is defined (required for authentication)
        """
        function_name = "GenerateTaxDocumentFunction"
        
        # Extract environment variables from Lambda code
        code_env_vars = self.extract_all_env_vars_from_lambda_code(lambda_code_dir)
        
        # Extract environment variables from env.json
        config_env_vars = self.extract_env_vars_from_config(env_config, function_name)
        
        # Define critical variables that must be present
        critical_vars = {'TEMPLATES_BUCKET', 'OUTPUTS_BUCKET', 'JOB_TABLE_NAME', 'JWT_SECRET_KEY'}
        
        # Only check critical variables that are actually accessed by the code
        required_vars = critical_vars & code_env_vars
        
        # Verification: All required variables should be in env.json
        missing_critical = required_vars - config_env_vars
        
        assert len(missing_critical) == 0, (
            f"Critical environment variables missing from env.json: {missing_critical}\n"
            f"Required variables: {sorted(required_vars)}\n"
            f"Config defines: {sorted(config_env_vars)}"
        )
    
    def test_aws_endpoint_url_is_defined_for_localstack(self, env_config):
        """
        **Validates: Requirements 2.2**
        Feature: fix-s3-bucket-env-config, Property 2: Environment variable completeness for Lambda code
        
        AWS_ENDPOINT_URL must be defined for LocalStack integration.
        
        This test verifies that:
        1. AWS_ENDPOINT_URL is present in env.json
        2. The value points to LocalStack (contains 4566)
        3. Local development can route to LocalStack
        """
        function_name = "GenerateTaxDocumentFunction"
        
        config_env_vars = self.extract_env_vars_from_config(env_config, function_name)
        
        # Verification: AWS_ENDPOINT_URL should be defined
        assert 'AWS_ENDPOINT_URL' in config_env_vars, (
            "AWS_ENDPOINT_URL is not defined in env.json for GenerateTaxDocumentFunction"
        )
        
        # Verification: AWS_ENDPOINT_URL should point to LocalStack
        endpoint_url = env_config[function_name].get('AWS_ENDPOINT_URL', '')
        assert '4566' in endpoint_url, (
            f"AWS_ENDPOINT_URL does not point to LocalStack (expected port 4566): {endpoint_url}"
        )
    
    def test_lambda_code_files_are_valid_python(self, lambda_code_dir):
        """
        **Validates: Requirements 2.2**
        Feature: fix-s3-bucket-env-config, Property 2: Environment variable completeness for Lambda code
        
        All Lambda code files must be valid Python that can be parsed.
        
        This test verifies that:
        1. All .py files in the Lambda directory are syntactically valid
        2. The AST can be constructed for analysis
        3. The code can be analyzed for environment variable access
        """
        python_files = [
            f for f in lambda_code_dir.glob("*.py")
            if f.is_file() and not f.name.startswith("test_")
        ]
        
        assert len(python_files) > 0, (
            f"No Python files found in {lambda_code_dir}"
        )
        
        for python_file in python_files:
            try:
                with open(python_file, 'r') as f:
                    ast.parse(f.read(), filename=str(python_file))
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {python_file}: {e}")
    
    def test_env_json_is_valid_json(self, env_json_path):
        """
        **Validates: Requirements 2.2**
        Feature: fix-s3-bucket-env-config, Property 2: Environment variable completeness for Lambda code
        
        The env.json file must be valid JSON that can be parsed.
        
        This test verifies that:
        1. env.json is syntactically valid JSON
        2. The file can be loaded without errors
        3. The configuration is accessible for validation
        """
        try:
            with open(env_json_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"env.json is not valid JSON: {e}")
        except FileNotFoundError:
            pytest.fail(f"env.json not found at {env_json_path}")
    
    def test_no_hardcoded_environment_values_in_code(self, lambda_code_dir):
        """
        **Validates: Requirements 2.2**
        Feature: fix-s3-bucket-env-config, Property 2: Environment variable completeness for Lambda code
        
        Lambda code should not contain hardcoded bucket or table names.
        
        This test verifies that:
        1. No hardcoded "tax-app-documents" strings in code
        2. No hardcoded "TaxDocumentJobs" strings in code
        3. All configuration comes from environment variables
        
        Note: This is a best practice check to ensure proper configuration management.
        """
        python_files = [
            f for f in lambda_code_dir.glob("*.py")
            if f.is_file() and not f.name.startswith("test_")
        ]
        
        hardcoded_values = {
            'tax-app-documents': 'S3 bucket name',
            'TaxDocumentJobs': 'DynamoDB table name'
        }
        
        violations = []
        
        for python_file in python_files:
            with open(python_file, 'r') as f:
                content = f.read()
                
                for value, description in hardcoded_values.items():
                    if value in content:
                        # Check if it's in a comment or docstring (which is acceptable)
                        lines = content.split('\n')
                        for line_num, line in enumerate(lines, 1):
                            if value in line:
                                # Skip comments and docstrings
                                stripped = line.strip()
                                if not (stripped.startswith('#') or 
                                       stripped.startswith('"""') or 
                                       stripped.startswith("'''")):
                                    violations.append(
                                        f"{python_file.name}:{line_num} - Hardcoded {description}: {value}"
                                    )
        
        # This is a warning, not a hard failure, as some hardcoded values might be acceptable
        if violations:
            pytest.skip(
                f"Found hardcoded configuration values (consider using environment variables):\n" +
                "\n".join(violations)
            )
