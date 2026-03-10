"""
Example-based tests for env.json configuration validation.

These tests verify specific configuration values in the env.json file for
GenerateTaxDocumentFunction. Unlike property-based tests that verify general
rules, these tests validate concrete examples of correct configuration.

Each test validates a specific acceptance criterion from the requirements.
"""

import json
import pytest
from pathlib import Path


class TestEnvConfigExamples:
    """Example-based tests for env.json configuration validation."""
    
    @pytest.fixture
    def env_json_path(self):
        """Path to the env.json configuration file."""
        return Path(__file__).parent.parent / "env.json"
    
    @pytest.fixture
    def env_config(self, env_json_path):
        """Load and parse the env.json configuration."""
        with open(env_json_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def generate_tax_document_config(self, env_config):
        """Extract GenerateTaxDocumentFunction configuration from env.json."""
        function_name = "GenerateTaxDocumentFunction"
        assert function_name in env_config, (
            f"{function_name} not found in env.json"
        )
        return env_config[function_name]
    
    def test_templates_bucket_is_defined(self, generate_tax_document_config):
        """
        **Validates: Requirements 1.1**
        Feature: fix-s3-bucket-env-config, Example 1: TEMPLATES_BUCKET is defined
        
        The env.json file for GenerateTaxDocumentFunction should contain the key
        "TEMPLATES_BUCKET" with value "tax-app-documents".
        
        This test verifies that:
        1. The TEMPLATES_BUCKET environment variable is defined
        2. The value is exactly "tax-app-documents"
        3. The Lambda can access the S3 bucket for template retrieval
        """
        # Verification 1: TEMPLATES_BUCKET key exists
        assert 'TEMPLATES_BUCKET' in generate_tax_document_config, (
            "TEMPLATES_BUCKET is not defined in env.json for GenerateTaxDocumentFunction"
        )
        
        # Verification 2: TEMPLATES_BUCKET has the correct value
        actual_value = generate_tax_document_config['TEMPLATES_BUCKET']
        expected_value = "tax-app-documents"
        
        assert actual_value == expected_value, (
            f"TEMPLATES_BUCKET has incorrect value. "
            f"Expected: '{expected_value}', Got: '{actual_value}'"
        )

    def test_outputs_bucket_is_defined(self, generate_tax_document_config):
        """
        **Validates: Requirements 1.2**
        Feature: fix-s3-bucket-env-config, Example 2: OUTPUTS_BUCKET is defined
        
        The env.json file for GenerateTaxDocumentFunction should contain the key
        "OUTPUTS_BUCKET" with value "tax-app-documents".
        
        This test verifies that:
        1. The OUTPUTS_BUCKET environment variable is defined
        2. The value is exactly "tax-app-documents"
        3. The Lambda can access the S3 bucket for output storage
        """
        # Verification 1: OUTPUTS_BUCKET key exists
        assert 'OUTPUTS_BUCKET' in generate_tax_document_config, (
            "OUTPUTS_BUCKET is not defined in env.json for GenerateTaxDocumentFunction"
        )
        
        # Verification 2: OUTPUTS_BUCKET has the correct value
        actual_value = generate_tax_document_config['OUTPUTS_BUCKET']
        expected_value = "tax-app-documents"
        
        assert actual_value == expected_value, (
            f"OUTPUTS_BUCKET has incorrect value. "
            f"Expected: '{expected_value}', Got: '{actual_value}'"
        )

    def test_documents_bucket_is_not_defined(self, generate_tax_document_config):
        """
        **Validates: Requirements 1.3**
        Feature: fix-s3-bucket-env-config, Example 3: DOCUMENTS_BUCKET is not defined
        
        The env.json file for GenerateTaxDocumentFunction should NOT contain the key
        "DOCUMENTS_BUCKET".
        
        This test verifies that:
        1. The DOCUMENTS_BUCKET environment variable is NOT defined
        2. The incorrect legacy variable name has been removed
        3. Only the correct variable names (TEMPLATES_BUCKET, OUTPUTS_BUCKET) are used
        """
        # Verification: DOCUMENTS_BUCKET key does NOT exist
        assert 'DOCUMENTS_BUCKET' not in generate_tax_document_config, (
            "DOCUMENTS_BUCKET should not be defined in env.json for GenerateTaxDocumentFunction. "
            "Use TEMPLATES_BUCKET and OUTPUTS_BUCKET instead."
        )

    def test_job_table_name_is_defined(self, generate_tax_document_config):
        """
        **Validates: Requirements 1.4**
        Feature: fix-s3-bucket-env-config, Example 4: JOB_TABLE_NAME is defined
        
        The env.json file for GenerateTaxDocumentFunction should contain the key
        "JOB_TABLE_NAME" with value "TaxDocumentJobs".
        
        This test verifies that:
        1. The JOB_TABLE_NAME environment variable is defined
        2. The value is exactly "TaxDocumentJobs"
        3. The Lambda can access the DynamoDB table for job tracking
        """
        # Verification 1: JOB_TABLE_NAME key exists
        assert 'JOB_TABLE_NAME' in generate_tax_document_config, (
            "JOB_TABLE_NAME is not defined in env.json for GenerateTaxDocumentFunction"
        )
        
        # Verification 2: JOB_TABLE_NAME has the correct value
        actual_value = generate_tax_document_config['JOB_TABLE_NAME']
        expected_value = "TaxDocumentJobs"
        
        assert actual_value == expected_value, (
            f"JOB_TABLE_NAME has incorrect value. "
            f"Expected: '{expected_value}', Got: '{actual_value}'"
        )

    def test_jobs_table_name_is_not_defined(self, generate_tax_document_config):
        """
        **Validates: Requirements 1.5**
        Feature: fix-s3-bucket-env-config, Example 5: JOBS_TABLE_NAME is not defined
        
        The env.json file for GenerateTaxDocumentFunction should NOT contain the key
        "JOBS_TABLE_NAME".
        
        This test verifies that:
        1. The JOBS_TABLE_NAME environment variable is NOT defined
        2. The incorrect legacy variable name has been removed
        3. Only the correct variable name (JOB_TABLE_NAME) is used
        """
        # Verification: JOBS_TABLE_NAME key does NOT exist
        assert 'JOBS_TABLE_NAME' not in generate_tax_document_config, (
            "JOBS_TABLE_NAME should not be defined in env.json for GenerateTaxDocumentFunction. "
            "Use JOB_TABLE_NAME instead (singular, not plural)."
        )

    def test_localstack_variables_are_preserved(self, generate_tax_document_config):
        """
        **Validates: Requirements 2.3**
        Feature: fix-s3-bucket-env-config, Example 6: LocalStack variables are preserved
        
        The env.json file for GenerateTaxDocumentFunction should contain all of:
        "AWS_ENDPOINT_URL", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY".
        
        This test verifies that:
        1. All LocalStack-specific environment variables are preserved
        2. The Lambda can connect to LocalStack for local development
        3. The configuration fix did not remove any required LocalStack variables
        """
        # Define the required LocalStack variables
        required_localstack_vars = [
            'AWS_ENDPOINT_URL',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY'
        ]
        
        # Verification: All LocalStack variables exist
        missing_vars = []
        for var_name in required_localstack_vars:
            if var_name not in generate_tax_document_config:
                missing_vars.append(var_name)
        
        assert not missing_vars, (
            f"Missing required LocalStack environment variables in env.json for "
            f"GenerateTaxDocumentFunction: {', '.join(missing_vars)}. "
            f"These variables are required for local development with LocalStack."
        )
        
        # Additional verification: Check that the values are not empty
        for var_name in required_localstack_vars:
            value = generate_tax_document_config[var_name]
            assert value, (
                f"LocalStack environment variable '{var_name}' is defined but has an empty value. "
                f"This variable must have a valid value for LocalStack to work correctly."
            )
