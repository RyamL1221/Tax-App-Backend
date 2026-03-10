"""
Property-based tests for validation error response format.

**Validates: Requirements 6.3**

Property 10: Validation error response format
For any validation error, the endpoint should return a 400 status code with
a JSON body containing an error message describing the validation failure.
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from user_login.response_formatter import validation_error_response


@settings(max_examples=20)
@given(message=st.text(min_size=1, max_size=200))
def test_validation_error_response_status_code_property(message):
    """
    Property 10: Validation error response format - Status Code
    
    For any validation error message, the response should have status code 400.
    
    **Validates: Requirements 6.3**
    """
    response = validation_error_response(message)
    
    assert response["statusCode"] == 400, \
        f"Validation error response should have status code 400, got {response['statusCode']}"


@settings(max_examples=20)
@given(message=st.text(min_size=1, max_size=200))
def test_validation_error_response_contains_error_property(message):
    """
    Property 10: Validation error response format - Error Message
    
    For any validation error message, the response should contain an error field
    with a descriptive message.
    
    **Validates: Requirements 6.3**
    """
    response = validation_error_response(message)
    body = json.loads(response["body"])
    
    assert "error" in body, "Validation error response should contain error field"
    assert isinstance(body["error"], str), "Error field should be a string"
    assert len(body["error"]) > 0, "Error message should not be empty"


@settings(max_examples=20)
@given(message=st.text(min_size=1, max_size=200))
def test_validation_error_response_includes_message_property(message):
    """
    Property 10: Validation error response format - Message Inclusion
    
    For any validation error message, the response should include the provided
    message in the error field.
    
    **Validates: Requirements 6.3**
    """
    response = validation_error_response(message)
    body = json.loads(response["body"])
    
    # The error message should contain the provided message
    assert message in body["error"], \
        f"Error message should contain '{message}', got '{body['error']}'"


@settings(max_examples=20)
@given(message=st.text(min_size=1, max_size=200))
def test_validation_error_response_has_cors_headers_property(message):
    """
    Property 10: Validation error response format - CORS Headers
    
    For any validation error, the response should include CORS headers.
    
    **Validates: Requirements 6.3**
    """
    response = validation_error_response(message)
    
    assert "headers" in response, "Response should contain headers"
    headers = response["headers"]
    
    # Check for required CORS headers
    assert "Access-Control-Allow-Origin" in headers, \
        "Response should contain Access-Control-Allow-Origin header"
    assert "Access-Control-Allow-Headers" in headers, \
        "Response should contain Access-Control-Allow-Headers header"
    assert "Access-Control-Allow-Methods" in headers, \
        "Response should contain Access-Control-Allow-Methods header"
    assert "Content-Type" in headers, \
        "Response should contain Content-Type header"


@settings(max_examples=20)
@given(message=st.text(min_size=1, max_size=200))
def test_validation_error_response_body_is_valid_json_property(message):
    """
    Property 10: Validation error response format - Valid JSON
    
    For any validation error, the response body should be valid JSON.
    
    **Validates: Requirements 6.3**
    """
    response = validation_error_response(message)
    
    # Should be able to parse body as JSON without error
    try:
        body = json.loads(response["body"])
        assert isinstance(body, dict), "Parsed body should be a dictionary"
    except json.JSONDecodeError as e:
        pytest.fail(f"Response body should be valid JSON: {e}")


@settings(max_examples=20)
@given(message=st.text(min_size=1, max_size=200))
def test_validation_error_response_format_property(message):
    """
    Property 10: Validation error response format - Format
    
    For any validation error, the error message should be prefixed with
    "Validation failed: " to clearly indicate the error type.
    
    **Validates: Requirements 6.3**
    """
    response = validation_error_response(message)
    body = json.loads(response["body"])
    
    assert body["error"].startswith("Validation failed: "), \
        f"Error message should start with 'Validation failed: ', got '{body['error']}'"
