"""
Property-based tests for SAM template and env.json consistency.

These tests verify that environment variable names defined in the SAM template
(template.yaml) for GenerateTaxDocumentFunction are consistently defined in the
local development configuration (env.json).

This ensures that local testing with SAM CLI accurately reflects production behavior.
"""

import json
import yaml
import pytest
from pathlib import Path


# Custom YAML loader to handle CloudFormation intrinsic functions
class CloudFormationLoader(yaml.SafeLoader):
    """Custom YAML loader that handles CloudFormation intrinsic functions."""
    pass


# Define constructors for CloudFormation intrinsic functions
def cf_constructor(loader, node):
    """Generic constructor for CloudFormation intrinsic functions."""
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


# Register CloudFormation intrinsic functions
cf_tags = ['!Ref', '!GetAtt', '!Sub', '!Join', '!Select', '!Split', 
           '!Equals', '!If', '!Not', '!And', '!Or', '!FindInMap',
           '!GetAZs', '!ImportValue', '!Base64', '!Cidr']

for tag in cf_tags:
    CloudFormationLoader.add_constructor(tag, cf_constructor)


class TestSAMTemplateEnvConsistencyProperty:
    """Property-based tests for SAM template environment variable consistency."""
    
    @pytest.fixture
    def template_yaml_path(self):
        """Path to the SAM template file."""
        return Path(__file__).parent.parent / "template.yaml"
    
    @pytest.fixture
    def env_json_path(self):
        """Path to the env.json configuration file."""
        return Path(__file__).parent.parent / "env.json"
    
    @pytest.fixture
    def sam_template(self, template_yaml_path):
        """Load and parse the SAM template."""
        with open(template_yaml_path, 'r') as f:
            return yaml.load(f, Loader=CloudFormationLoader)
    
    @pytest.fixture
    def env_config(self, env_json_path):
        """Load and parse the env.json configuration."""
        with open(env_json_path, 'r') as f:
            return json.load(f)
    
    def extract_env_vars_from_template(self, sam_template, function_name):
        """
        Extract environment variable names from SAM template for a specific function.
        
        Args:
            sam_template: Parsed SAM template dictionary
            function_name: Name of the Lambda function (e.g., "GenerateTaxDocumentFunction")
        
        Returns:
            Set of environment variable names defined in the template
        """
        try:
            resources = sam_template.get('Resources', {})
            function_resource = resources.get(function_name, {})
            properties = function_resource.get('Properties', {})
            environment = properties.get('Environment', {})
            variables = environment.get('Variables', {})
            return set(variables.keys())
        except (KeyError, AttributeError) as e:
            pytest.fail(f"Failed to extract environment variables from template: {e}")
    
    def extract_env_vars_from_config(self, env_config, function_name):
        """
        Extract environment variable names from env.json for a specific function.
        
        Args:
            env_config: Parsed env.json dictionary
            function_name: Name of the Lambda function (e.g., "GenerateTaxDocumentFunction")
        
        Returns:
            Set of environment variable names defined in env.json
        """
        try:
            function_env = env_config.get(function_name, {})
            return set(function_env.keys())
        except (KeyError, AttributeError) as e:
            pytest.fail(f"Failed to extract environment variables from env.json: {e}")
    
    def test_generate_tax_document_function_env_consistency(self, sam_template, env_config):
        """
        **Validates: Requirements 2.1**
        Feature: fix-s3-bucket-env-config, Property 1: Environment variable name consistency with SAM template
        
        For any environment variable defined in the SAM template for GenerateTaxDocumentFunction,
        that variable name should also exist in the env.json configuration for GenerateTaxDocumentFunction.
        
        This test verifies that:
        1. All environment variables from template.yaml are present in env.json
        2. Variable names are identical (case-sensitive match)
        3. Local development configuration matches production configuration
        """
        function_name = "GenerateTaxDocumentFunction"
        
        # Extract environment variables from both sources
        template_vars = self.extract_env_vars_from_template(sam_template, function_name)
        config_vars = self.extract_env_vars_from_config(env_config, function_name)
        
        # Verification: All template variables should exist in env.json
        missing_vars = template_vars - config_vars
        
        assert len(missing_vars) == 0, (
            f"Environment variables defined in template.yaml but missing from env.json: {missing_vars}\n"
            f"Template variables: {sorted(template_vars)}\n"
            f"Config variables: {sorted(config_vars)}"
        )
    
    def test_all_lambda_functions_env_consistency(self, sam_template, env_config):
        """
        **Validates: Requirements 2.1**
        Feature: fix-s3-bucket-env-config, Property 1: Environment variable name consistency with SAM template
        
        For any Lambda function defined in the SAM template, all environment variables
        defined in the template should exist in the corresponding env.json configuration.
        
        This test verifies consistency across all Lambda functions, not just
        GenerateTaxDocumentFunction, to prevent similar configuration issues.
        """
        resources = sam_template.get('Resources', {})
        
        # Find all Lambda functions in the template
        lambda_functions = [
            name for name, resource in resources.items()
            if resource.get('Type') == 'AWS::Serverless::Function'
        ]
        
        inconsistencies = {}
        
        for function_name in lambda_functions:
            # Skip if function is not in env.json (some functions may not need local config)
            if function_name not in env_config:
                continue
            
            template_vars = self.extract_env_vars_from_template(sam_template, function_name)
            config_vars = self.extract_env_vars_from_config(env_config, function_name)
            
            missing_vars = template_vars - config_vars
            
            if missing_vars:
                inconsistencies[function_name] = missing_vars
        
        # Verification: No function should have missing variables
        assert len(inconsistencies) == 0, (
            f"Environment variable inconsistencies found:\n" +
            "\n".join([
                f"  {func}: missing {sorted(vars)}"
                for func, vars in inconsistencies.items()
            ])
        )
    
    def test_env_var_names_are_case_sensitive_match(self, sam_template, env_config):
        """
        **Validates: Requirements 2.1**
        Feature: fix-s3-bucket-env-config, Property 1: Environment variable name consistency with SAM template
        
        Environment variable names must match exactly (case-sensitive) between
        template.yaml and env.json.
        
        This test verifies that:
        1. Variable names are not just similar but identical
        2. Case differences are detected as inconsistencies
        3. No case-insensitive matching is used
        """
        function_name = "GenerateTaxDocumentFunction"
        
        template_vars = self.extract_env_vars_from_template(sam_template, function_name)
        config_vars = self.extract_env_vars_from_config(env_config, function_name)
        
        # Check for case-insensitive matches that are not exact matches
        template_vars_lower = {var.lower(): var for var in template_vars}
        config_vars_lower = {var.lower(): var for var in config_vars}
        
        case_mismatches = []
        for var_lower, template_var in template_vars_lower.items():
            if var_lower in config_vars_lower:
                config_var = config_vars_lower[var_lower]
                if template_var != config_var:
                    case_mismatches.append((template_var, config_var))
        
        # Verification: No case mismatches should exist
        assert len(case_mismatches) == 0, (
            f"Case mismatches found between template.yaml and env.json:\n" +
            "\n".join([
                f"  Template: '{template_var}' vs Config: '{config_var}'"
                for template_var, config_var in case_mismatches
            ])
        )
    
    def test_template_yaml_is_valid_yaml(self, template_yaml_path):
        """
        **Validates: Requirements 2.1**
        Feature: fix-s3-bucket-env-config, Property 1: Environment variable name consistency with SAM template
        
        The template.yaml file must be valid YAML that can be parsed successfully.
        
        This test verifies that:
        1. template.yaml is syntactically valid YAML
        2. The file can be loaded without errors
        3. The structure is accessible for validation
        """
        try:
            with open(template_yaml_path, 'r') as f:
                yaml.load(f, Loader=CloudFormationLoader)
        except yaml.YAMLError as e:
            pytest.fail(f"template.yaml is not valid YAML: {e}")
        except FileNotFoundError:
            pytest.fail(f"template.yaml not found at {template_yaml_path}")
    
    def test_env_json_is_valid_json(self, env_json_path):
        """
        **Validates: Requirements 2.1**
        Feature: fix-s3-bucket-env-config, Property 1: Environment variable name consistency with SAM template
        
        The env.json file must be valid JSON that can be parsed successfully.
        
        This test verifies that:
        1. env.json is syntactically valid JSON
        2. The file can be loaded without errors
        3. The structure is accessible for validation
        """
        try:
            with open(env_json_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"env.json is not valid JSON: {e}")
        except FileNotFoundError:
            pytest.fail(f"env.json not found at {env_json_path}")
    
    def test_generate_tax_document_function_exists_in_both_files(self, sam_template, env_config):
        """
        **Validates: Requirements 2.1**
        Feature: fix-s3-bucket-env-config, Property 1: Environment variable name consistency with SAM template
        
        GenerateTaxDocumentFunction must be defined in both template.yaml and env.json.
        
        This test verifies that:
        1. The function exists in the SAM template
        2. The function has a corresponding entry in env.json
        3. Both configurations are present for validation
        """
        function_name = "GenerateTaxDocumentFunction"
        
        # Verification 1: Function exists in template.yaml
        resources = sam_template.get('Resources', {})
        assert function_name in resources, (
            f"{function_name} not found in template.yaml Resources"
        )
        
        # Verification 2: Function exists in env.json
        assert function_name in env_config, (
            f"{function_name} not found in env.json"
        )
    
    def test_template_defines_environment_variables(self, sam_template):
        """
        **Validates: Requirements 2.1**
        Feature: fix-s3-bucket-env-config, Property 1: Environment variable name consistency with SAM template
        
        GenerateTaxDocumentFunction in template.yaml must define environment variables.
        
        This test verifies that:
        1. The function has an Environment section
        2. The Environment section contains Variables
        3. At least one variable is defined
        """
        function_name = "GenerateTaxDocumentFunction"
        
        template_vars = self.extract_env_vars_from_template(sam_template, function_name)
        
        # Verification: At least one environment variable should be defined
        assert len(template_vars) > 0, (
            f"{function_name} in template.yaml does not define any environment variables"
        )
    
    def test_env_json_defines_environment_variables(self, env_config):
        """
        **Validates: Requirements 2.1**
        Feature: fix-s3-bucket-env-config, Property 1: Environment variable name consistency with SAM template
        
        GenerateTaxDocumentFunction in env.json must define environment variables.
        
        This test verifies that:
        1. The function configuration exists
        2. At least one variable is defined
        3. The configuration is not empty
        """
        function_name = "GenerateTaxDocumentFunction"
        
        config_vars = self.extract_env_vars_from_config(env_config, function_name)
        
        # Verification: At least one environment variable should be defined
        assert len(config_vars) > 0, (
            f"{function_name} in env.json does not define any environment variables"
        )
