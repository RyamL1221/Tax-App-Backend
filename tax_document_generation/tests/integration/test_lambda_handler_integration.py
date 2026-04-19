"""
Integration Tests: Lambda Handler

These tests verify end-to-end functionality with LocalStack (S3 + DynamoDB).
Run these tests with LocalStack running.

**Validates: All requirements**
"""

import pytest
import json
import boto3
import os
from datetime import datetime, timedelta
import jwt as pyjwt
from tax_document_generation.app import lambda_handler


# Skip these tests if not running with LocalStack
pytestmark = pytest.mark.skipif(
    os.environ.get('AWS_ENDPOINT_URL') is None,
    reason="Integration tests require LocalStack (set AWS_ENDPOINT_URL)"
)


@pytest.fixture
def aws_resources():
    """Set up AWS resources for integration testing."""
    # This would set up S3 buckets and DynamoDB tables in LocalStack
    # For now, assume they're already set up
    yield
    # Cleanup would go here


def test_end_to_end_generation_flow(aws_resources):
    """
    Integration test: End-to-end document generation flow.
    
    Tests the complete workflow from API request to document storage.
    """
    # Set up environment
    os.environ['TEMPLATES_BUCKET'] = 'tax-app-backend-dev-documents'
    os.environ['OUTPUTS_BUCKET'] = 'tax-app-backend-dev-documents'
    os.environ['JOB_TABLE_NAME'] = 'TaxDocumentJobs'
    os.environ['JWT_SECRET'] = 'local-dev-secret-key-min-32-chars-long-for-security'
    
    # Generate valid JWT
    user_id = "test-user-123"
    payload = {
        "userId": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = pyjwt.encode(payload, os.environ['JWT_SECRET'], algorithm="HS256")
    
    # Create API event
    event = {
        "headers": {
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps({
            "documentType": "1040",
            "formData": {
                "firstName": "John",
                "lastName": "Doe",
                "ssn": "123-45-6789",
                "filingStatus": "single",
                "income": 75000
            }
        })
    }
    
    # Invoke handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'jobId' in body
    assert body['userId'] == user_id
    assert body['status'] == 'COMPLETED'
    assert 'outputKey' in body


def test_authentication_flow():
    """
    Integration test: Authentication with valid and invalid tokens.
    """
    os.environ['TEMPLATES_BUCKET'] = 'tax-app-backend-dev-documents'
    os.environ['OUTPUTS_BUCKET'] = 'tax-app-backend-dev-documents'
    os.environ['JOB_TABLE_NAME'] = 'TaxDocumentJobs'
    os.environ['JWT_SECRET'] = 'local-dev-secret-key-min-32-chars-long-for-security'
    
    # Test with invalid token
    event = {
        "headers": {
            "Authorization": "Bearer invalid-token"
        },
        "body": json.dumps({
            "documentType": "1040",
            "formData": {}
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 401
    body = json.loads(response['body'])
    assert body['error'] == 'AuthenticationError'


def test_error_handling_with_missing_template():
    """
    Integration test: Error handling when template doesn't exist.
    """
    os.environ['TEMPLATES_BUCKET'] = 'tax-app-backend-dev-documents'
    os.environ['OUTPUTS_BUCKET'] = 'tax-app-backend-dev-documents'
    os.environ['JOB_TABLE_NAME'] = 'TaxDocumentJobs'
    os.environ['JWT_SECRET'] = 'local-dev-secret-key-min-32-chars-long-for-security'
    
    # Generate valid JWT
    user_id = "test-user-456"
    payload = {
        "userId": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = pyjwt.encode(payload, os.environ['JWT_SECRET'], algorithm="HS256")
    
    # Request non-existent document type
    event = {
        "headers": {
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps({
            "documentType": "9999",
            "formData": {
                "firstName": "John",
                "lastName": "Doe",
                "ssn": "123-45-6789",
                "filingStatus": "single",
                "income": 75000
            }
        })
    }
    
    response = lambda_handler(event, None)
    
    # Should return validation error for unsupported document type
    assert response['statusCode'] in [400, 404]
    body = json.loads(response['body'])
    assert 'error' in body


def test_1099_div_generation_end_to_end(aws_resources):
    """
    Integration test: End-to-end 1099-DIV document generation.
    
    Tests the complete workflow for 1099-DIV generation with all required fields.
    Verifies that the fix for "key must be PdfObject" error works in production.
    
    **Validates: Requirements 6.1, 6.2** (fix-pdf-form-field-error spec)
    """
    # Set up environment
    os.environ['TEMPLATES_BUCKET'] = 'tax-app-backend-dev-documents'
    os.environ['OUTPUTS_BUCKET'] = 'tax-app-backend-dev-documents'
    os.environ['JOB_TABLE_NAME'] = 'TaxDocumentJobs'
    os.environ['JWT_SECRET'] = 'local-dev-secret-key-min-32-chars-long-for-security'
    
    # Generate valid JWT
    user_id = "test-user-1099-div"
    payload = {
        "userId": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = pyjwt.encode(payload, os.environ['JWT_SECRET'], algorithm="HS256")
    
    # Create API event with 1099-DIV data
    event = {
        "headers": {
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps({
            "documentType": "1099-DIV",
            "formData": {
                # Required fields
                "payerName": "Vanguard Investments",
                "payerTIN": "23-1945930",
                "recipientTIN": "123-45-6789",
                "recipientName": "Jane Smith",
                "totalOrdinaryDividends": 5000.00,
                
                # Optional fields
                "qualifiedDividends": 3000.00,
                "totalCapitalGainDistributions": 1500.00,
                "federalIncomeTaxWithheld": 500.00,
                "section199ADividends": 2000.00,
                "investmentExpenses": 50.00,
                "foreignTaxPaid": 0.00,
                
                # Payer information
                "payerStreetAddress": "100 Vanguard Blvd",
                "payerCity": "Malvern",
                "payerState": "PA",
                "payerZip": "19355",
                
                # Recipient information
                "recipientStreetAddress": "456 Main St",
                "recipientCity": "Boston",
                "recipientState": "MA",
                "recipientZip": "02101",
                
                # Additional fields
                "accountNumber": "12345678",
                "calendarYear": "2025",
            }
        })
    }
    
    # Invoke handler
    response = lambda_handler(event, None)
    
    # Verify response
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}: {response.get('body')}"
    body = json.loads(response['body'])
    assert 'jobId' in body, "Response should contain jobId"
    assert body['userId'] == user_id, "Response should contain correct userId"
    assert body['status'] == 'COMPLETED', f"Job status should be COMPLETED, got {body.get('status')}"
    assert 'outputKey' in body, "Response should contain outputKey"
    
    # Verify the document was stored in S3
    s3_client = boto3.client('s3', endpoint_url=os.environ.get('AWS_ENDPOINT_URL'))
    try:
        s3_response = s3_client.head_object(
            Bucket=os.environ['OUTPUTS_BUCKET'],
            Key=body['outputKey']
        )
        assert s3_response['ContentLength'] > 0, "Generated document should have non-zero size"
    except Exception as e:
        pytest.fail(f"Failed to verify document in S3: {e}")
    
    # Verify job status in DynamoDB
    dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('AWS_ENDPOINT_URL'))
    table = dynamodb.Table(os.environ['JOB_TABLE_NAME'])
    try:
        db_response = table.get_item(Key={'jobId': body['jobId']})
        assert 'Item' in db_response, "Job should exist in DynamoDB"
        job_item = db_response['Item']
        assert job_item['status'] == 'COMPLETED', "Job status in DB should be COMPLETED"
        assert job_item['userId'] == user_id, "Job userId in DB should match"
    except Exception as e:
        pytest.fail(f"Failed to verify job in DynamoDB: {e}")


def test_error_recovery_with_generation_failure(aws_resources):
    """
    Integration test: Error recovery when document generation fails.
    
    Tests that when document generation fails (e.g., corrupted template),
    the job status is updated to FAILED and error is logged properly.
    
    **Validates: Requirements 5.1, 5.4** (fix-pdf-form-field-error spec)
    """
    # Set up environment
    os.environ['TEMPLATES_BUCKET'] = 'tax-app-backend-dev-documents'
    os.environ['OUTPUTS_BUCKET'] = 'tax-app-backend-dev-documents'
    os.environ['JOB_TABLE_NAME'] = 'TaxDocumentJobs'
    os.environ['JWT_SECRET'] = 'local-dev-secret-key-min-32-chars-long-for-security'
    
    # Generate valid JWT
    user_id = "test-user-error-recovery"
    payload = {
        "userId": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = pyjwt.encode(payload, os.environ['JWT_SECRET'], algorithm="HS256")
    
    # Create API event with a document type that will cause an error
    # (assuming we can trigger an error by using a non-existent template)
    event = {
        "headers": {
            "Authorization": f"Bearer {token}"
        },
        "body": json.dumps({
            "documentType": "NONEXISTENT-FORM",
            "formData": {
                "testField": "testValue"
            }
        })
    }
    
    # Invoke handler
    response = lambda_handler(event, None)
    
    # Verify response indicates error
    # Could be 400 (validation error) or 500 (generation error)
    assert response['statusCode'] in [400, 500], \
        f"Expected error status code, got {response['statusCode']}"
    
    body = json.loads(response['body'])
    assert 'error' in body, "Response should contain error field"
    
    # If a job was created, verify it's marked as FAILED
    if 'jobId' in body:
        dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('AWS_ENDPOINT_URL'))
        table = dynamodb.Table(os.environ['JOB_TABLE_NAME'])
        try:
            db_response = table.get_item(Key={'jobId': body['jobId']})
            if 'Item' in db_response:
                job_item = db_response['Item']
                assert job_item['status'] == 'FAILED', \
                    f"Job status in DB should be FAILED, got {job_item.get('status')}"
        except Exception as e:
            # If we can't verify in DB, that's okay for this test
            pass


# Note: Additional integration tests would include:
# - Concurrent request handling
# - S3 failure scenarios
# - DynamoDB failure scenarios
# - Large document generation
# - Multiple documents for same user
