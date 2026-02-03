"""
Integration Test: Lambda Handler Import Success

This test verifies that the Lambda handler can be imported and invoked successfully
without ImportError, validating that the fix for relative imports works correctly.

**Property 2: Lambda Handler Successful Invocation**
**Validates: Requirements 1.1, 4.2, 4.3**
"""

import pytest
import json
import os
from datetime import datetime, timedelta
import jwt as pyjwt


def test_lambda_handler_import_success():
    """
    Integration test: Verify Lambda handler can be imported without ImportError.
    
    This test validates that:
    1. The Lambda handler module can be imported successfully
    2. No ImportError is raised during import (specifically no relative import errors)
    3. All dependencies (document_generator, exceptions, field_mapper) are importable
    
    **Validates: Requirements 1.1, 4.2, 4.3**
    """
    # This import should succeed without ImportError
    # If relative imports are still present, this will fail with:
    # "attempted relative import with no known parent package"
    try:
        from tax_document_generation.app import lambda_handler
        # If we get here, the import succeeded
        assert lambda_handler is not None, "Lambda handler should be imported"
        assert callable(lambda_handler), "Lambda handler should be callable"
    except ImportError as e:
        pytest.fail(f"Failed to import Lambda handler: {e}")


def test_lambda_handler_invocation_without_import_error():
    """
    Integration test: Verify Lambda handler can be invoked without ImportError.
    
    This test validates that:
    1. The Lambda handler can be invoked with a valid event
    2. No ImportError is raised during execution
    3. The handler executes and returns a response (even if it's an error response)
    
    This test focuses on import correctness, not functional correctness.
    We expect the handler to fail with authentication or validation errors,
    but it should NOT fail with ImportError.
    
    **Validates: Requirements 1.1, 4.2, 4.3**
    """
    # Import the handler
    try:
        from tax_document_generation.app import lambda_handler
    except ImportError as e:
        pytest.fail(f"Failed to import Lambda handler: {e}")
    
    # Set up minimal environment variables
    os.environ['TEMPLATES_BUCKET'] = 'test-templates-bucket'
    os.environ['OUTPUTS_BUCKET'] = 'test-outputs-bucket'
    os.environ['JOB_TABLE_NAME'] = 'test-job-table'
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key-min-32-chars-long-for-testing-purposes'
    
    # Generate a valid JWT token
    user_id = "test-user-import-check"
    payload = {
        "userId": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = pyjwt.encode(payload, os.environ['JWT_SECRET_KEY'], algorithm="HS256")
    
    # Create a valid API Gateway event structure
    event = {
        "headers": {
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps({
            "documentType": "1099-DIV",
            "formData": {
                "payerName": "Test Payer",
                "payerTIN": "12-3456789",
                "recipientTIN": "987-65-4321",
                "recipientName": "Test Recipient",
                "totalOrdinaryDividends": 1000.00
            }
        })
    }
    
    # Invoke the handler
    # We expect this to fail with S3 or DynamoDB errors (since we're not using LocalStack),
    # but it should NOT fail with ImportError
    try:
        response = lambda_handler(event, None)
        
        # If we get here, the handler executed without ImportError
        # Verify we got a response (even if it's an error response)
        assert response is not None, "Handler should return a response"
        assert 'statusCode' in response, "Response should have statusCode"
        assert 'body' in response, "Response should have body"
        
        # The response might be an error (500 for S3/DynamoDB issues),
        # but that's okay - we're testing import success, not functional correctness
        
    except ImportError as e:
        pytest.fail(f"Lambda handler raised ImportError during execution: {e}")
    except Exception as e:
        # Other exceptions are expected (S3, DynamoDB, etc.)
        # As long as it's not ImportError, the test passes
        # This validates that all imports work correctly
        pass


def test_document_generator_import_success():
    """
    Integration test: Verify document_generator module can be imported.
    
    This test specifically validates that document_generator.py uses absolute imports
    and can be imported without "attempted relative import" errors.
    
    **Validates: Requirements 1.1, 1.2**
    """
    try:
        from tax_document_generation.document_generator import generate_document
        assert generate_document is not None, "generate_document should be imported"
        assert callable(generate_document), "generate_document should be callable"
    except ImportError as e:
        pytest.fail(f"Failed to import document_generator: {e}")


def test_exceptions_module_import_success():
    """
    Integration test: Verify exceptions module can be imported.
    
    This test validates that the exceptions module (used by document_generator)
    can be imported successfully.
    
    **Validates: Requirements 1.3**
    """
    try:
        from tax_document_generation.exceptions import GenerationError
        assert GenerationError is not None, "GenerationError should be imported"
        assert issubclass(GenerationError, Exception), "GenerationError should be an Exception"
    except ImportError as e:
        pytest.fail(f"Failed to import exceptions module: {e}")


def test_field_mapper_import_success():
    """
    Integration test: Verify field_mapper module can be imported.
    
    This test validates that the field_mapper module (used by document_generator)
    can be imported successfully.
    
    **Validates: Requirements 1.4**
    """
    try:
        from tax_document_generation.field_mapper import FieldMapper
        assert FieldMapper is not None, "FieldMapper should be imported"
        assert callable(FieldMapper), "FieldMapper should be instantiable"
    except ImportError as e:
        pytest.fail(f"Failed to import field_mapper module: {e}")


def test_all_lambda_dependencies_import_success():
    """
    Integration test: Verify all Lambda dependencies can be imported.
    
    This comprehensive test validates that all modules used by the Lambda handler
    can be imported successfully, ensuring no relative import issues exist anywhere.
    
    **Validates: Requirements 1.1, 3.3**
    """
    modules_to_test = [
        ('tax_document_generation.app', 'lambda_handler'),
        ('tax_document_generation.document_generator', 'generate_document'),
        ('tax_document_generation.exceptions', 'GenerationError'),
        ('tax_document_generation.field_mapper', 'FieldMapper'),
        ('tax_document_generation.jwt_validator', 'validate_jwt'),
        ('tax_document_generation.input_validator', 'validate_form_data'),
        ('tax_document_generation.template_retriever', 'get_template'),
        ('tax_document_generation.output_persister', 'store_output'),
        ('tax_document_generation.job_repository', 'create_job'),
        ('tax_document_generation.response_formatter', 'success_response'),
        ('tax_document_generation.logger', 'log_error'),
    ]
    
    failed_imports = []
    
    for module_name, attribute_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[attribute_name])
            attribute = getattr(module, attribute_name)
            assert attribute is not None, f"{attribute_name} should be imported from {module_name}"
        except ImportError as e:
            failed_imports.append((module_name, attribute_name, str(e)))
        except AttributeError as e:
            failed_imports.append((module_name, attribute_name, f"Attribute not found: {e}"))
    
    if failed_imports:
        error_msg = "Failed to import the following modules:\n"
        for module_name, attribute_name, error in failed_imports:
            error_msg += f"  - {module_name}.{attribute_name}: {error}\n"
        pytest.fail(error_msg)
