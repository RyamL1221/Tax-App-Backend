"""
Property Tests: Response Formatter

Feature: tax-document-generation
Property 2: Successful Response Completeness
Property 3: Error Response Format

Tests response formatting for success and error cases.
**Validates: Requirements 1.3, 1.4, 2.3, 5.3**
"""

import json
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from tax_document_generation.response_formatter import success_response, error_response


@st.composite
def completed_job_record(draw):
    """Generate a completed job record."""
    job_id = draw(st.uuids()).hex
    user_id = draw(st.uuids()).hex
    document_type = draw(st.sampled_from(["1040", "1099", "W2"]))
    now = datetime.utcnow().isoformat() + 'Z'
    
    return {
        'jobId': job_id,
        'userId': user_id,
        'documentType': document_type,
        'status': 'COMPLETED',
        'outputKey': f"outputs/{user_id}/{job_id}/form-{document_type}.pdf",
        'createdAt': now,
        'completedAt': now,
        'updatedAt': now,
        'templateKey': f"templates/irs/{document_type}.pdf"
    }


@settings(max_examples=100)
@given(job_record=completed_job_record())
def test_successful_response_completeness(job_record):
    """
    Property 2: For any successful generation request, the response should
    contain jobId, userId, status (COMPLETED), outputKey, documentType,
    createdAt, and completedAt fields.
    
    This ensures clients receive all necessary information about completed jobs.
    """
    response = success_response(job_record)
    
    # Verify response structure
    assert 'statusCode' in response
    assert 'headers' in response
    assert 'body' in response
    
    # Verify status code
    assert response['statusCode'] == 200
    
    # Verify CORS headers
    assert 'Access-Control-Allow-Origin' in response['headers']
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Verify all required fields are present
    required_fields = ['jobId', 'userId', 'status', 'outputKey', 'documentType', 'createdAt', 'completedAt']
    for field in required_fields:
        assert field in body, f"Required field '{field}' missing from response"
    
    # Verify field values match job record
    assert body['jobId'] == job_record['jobId']
    assert body['userId'] == job_record['userId']
    assert body['status'] == job_record['status']
    assert body['outputKey'] == job_record['outputKey']
    assert body['documentType'] == job_record['documentType']
    assert body['createdAt'] == job_record['createdAt']
    assert body['completedAt'] == job_record['completedAt']


@st.composite
def error_parameters(draw):
    """Generate random error parameters."""
    status_code = draw(st.sampled_from([400, 401, 404, 500]))
    error_type = draw(st.sampled_from([
        "ValidationError",
        "AuthenticationError",
        "TemplateNotFoundError",
        "GenerationError",
        "InternalError"
    ]))
    message = draw(st.text(min_size=1, max_size=200))
    return status_code, error_type, message


@settings(max_examples=100)
@given(params=error_parameters())
def test_error_response_format(params):
    """
    Property 3: For any failed generation request, the response should
    contain an "error" field with error type and a "message" field with
    a descriptive message.
    
    This ensures consistent error reporting to clients.
    """
    status_code, error_type, message = params
    
    response = error_response(status_code, error_type, message)
    
    # Verify response structure
    assert 'statusCode' in response
    assert 'headers' in response
    assert 'body' in response
    
    # Verify status code
    assert response['statusCode'] == status_code
    
    # Verify CORS headers
    assert 'Access-Control-Allow-Origin' in response['headers']
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Verify required error fields are present
    assert 'error' in body, "Error response must contain 'error' field"
    assert 'message' in body, "Error response must contain 'message' field"
    
    # Verify field values
    assert body['error'] == error_type
    assert body['message'] == message


def test_success_response_unit():
    """
    Unit test: Verify success response with specific values.
    """
    job_record = {
        'jobId': 'job-123',
        'userId': 'user-456',
        'documentType': '1040',
        'status': 'COMPLETED',
        'outputKey': 'outputs/user-456/job-123/form-1040.pdf',
        'createdAt': '2024-01-15T10:00:00Z',
        'completedAt': '2024-01-15T10:00:02Z'
    }
    
    response = success_response(job_record)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['jobId'] == 'job-123'
    assert body['status'] == 'COMPLETED'


def test_error_response_unit():
    """
    Unit test: Verify error response with specific values.
    """
    response = error_response(400, "ValidationError", "Missing required field: ssn")
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == "ValidationError"
    assert body['message'] == "Missing required field: ssn"


def test_cors_headers_in_success_response():
    """
    Unit test: Verify CORS headers are present in success response.
    """
    job_record = {
        'jobId': 'job-123',
        'userId': 'user-456',
        'documentType': '1040',
        'status': 'COMPLETED',
        'outputKey': 'outputs/user-456/job-123/form-1040.pdf',
        'createdAt': '2024-01-15T10:00:00Z',
        'completedAt': '2024-01-15T10:00:02Z'
    }
    
    response = success_response(job_record)
    
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert 'Access-Control-Allow-Headers' in response['headers']
    assert 'Access-Control-Allow-Methods' in response['headers']


def test_cors_headers_in_error_response():
    """
    Unit test: Verify CORS headers are present in error response.
    """
    response = error_response(500, "InternalError", "Something went wrong")
    
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert 'Access-Control-Allow-Headers' in response['headers']
    assert 'Access-Control-Allow-Methods' in response['headers']


def test_different_error_status_codes():
    """
    Unit test: Verify different error status codes are handled correctly.
    """
    test_cases = [
        (400, "ValidationError", "Invalid input"),
        (401, "AuthenticationError", "Invalid token"),
        (404, "TemplateNotFoundError", "Template not found"),
        (500, "InternalError", "Server error")
    ]
    
    for status_code, error_type, message in test_cases:
        response = error_response(status_code, error_type, message)
        assert response['statusCode'] == status_code
        body = json.loads(response['body'])
        assert body['error'] == error_type
        assert body['message'] == message
