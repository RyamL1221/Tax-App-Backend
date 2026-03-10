"""
Property-based tests for generic authentication error messages.

**Validates: Requirements 6.4, 6.5, 7.1**

Property 11: Generic authentication error messages
For any authentication failure (whether due to non-existent user or incorrect
password), the endpoint should return a 401 status code with an identical
generic error message that does not reveal whether the email exists or the
password was incorrect.
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from user_login.response_formatter import authentication_error_response


@settings(max_examples=20)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_authentication_error_response_status_code_property(iteration):
    """
    Property 11: Generic authentication error messages - Status Code
    
    For any authentication failure, the response should have status code 401.
    
    **Validates: Requirements 6.4, 6.5, 7.1**
    """
    response = authentication_error_response()
    
    assert response["statusCode"] == 401, \
        f"Authentication error response should have status code 401, got {response['statusCode']}"


@settings(max_examples=20)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_authentication_error_response_contains_error_property(iteration):
    """
    Property 11: Generic authentication error messages - Error Field
    
    For any authentication failure, the response should contain an error field.
    
    **Validates: Requirements 6.4, 6.5, 7.1**
    """
    response = authentication_error_response()
    body = json.loads(response["body"])
    
    assert "error" in body, "Authentication error response should contain error field"
    assert isinstance(body["error"], str), "Error field should be a string"
    assert len(body["error"]) > 0, "Error message should not be empty"


@settings(max_examples=20)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_authentication_error_response_is_generic_property(iteration):
    """
    Property 11: Generic authentication error messages - Generic Message
    
    For any authentication failure, the response should use a generic error
    message that does not reveal whether the email exists or the password
    was incorrect. This prevents user enumeration attacks.
    
    **Validates: Requirements 6.4, 6.5, 7.1**
    """
    response = authentication_error_response()
    body = json.loads(response["body"])
    
    # The error message should be generic
    assert body["error"] == "Invalid credentials", \
        f"Error message should be 'Invalid credentials', got '{body['error']}'"


@settings(max_examples=20)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_authentication_error_response_consistency_property(iteration):
    """
    Property 11: Generic authentication error messages - Consistency
    
    For any authentication failure, the response should be identical across
    multiple invocations. This ensures that the same generic message is
    returned regardless of the failure reason.
    
    **Validates: Requirements 6.4, 6.5, 7.1**
    """
    response1 = authentication_error_response()
    response2 = authentication_error_response()
    
    # Both responses should be identical
    assert response1 == response2, \
        "Authentication error responses should be identical"


@settings(max_examples=20)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_authentication_error_response_has_cors_headers_property(iteration):
    """
    Property 11: Generic authentication error messages - CORS Headers
    
    For any authentication failure, the response should include CORS headers.
    
    **Validates: Requirements 6.4, 6.5, 7.1**
    """
    response = authentication_error_response()
    
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
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_authentication_error_response_body_is_valid_json_property(iteration):
    """
    Property 11: Generic authentication error messages - Valid JSON
    
    For any authentication failure, the response body should be valid JSON.
    
    **Validates: Requirements 6.4, 6.5, 7.1**
    """
    response = authentication_error_response()
    
    # Should be able to parse body as JSON without error
    try:
        body = json.loads(response["body"])
        assert isinstance(body, dict), "Parsed body should be a dictionary"
    except json.JSONDecodeError as e:
        pytest.fail(f"Response body should be valid JSON: {e}")


@settings(max_examples=20)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_authentication_error_response_does_not_reveal_details_property(iteration):
    """
    Property 11: Generic authentication error messages - No Details
    
    For any authentication failure, the response should not reveal specific
    details about why authentication failed (e.g., "user not found" or
    "incorrect password").
    
    **Validates: Requirements 6.4, 6.5, 7.1**
    """
    response = authentication_error_response()
    body = json.loads(response["body"])
    error_message = body["error"].lower()
    
    # Should not contain revealing phrases
    revealing_phrases = [
        "user not found",
        "email not found",
        "incorrect password",
        "wrong password",
        "password mismatch",
        "user does not exist",
        "email does not exist"
    ]
    
    for phrase in revealing_phrases:
        assert phrase not in error_message, \
            f"Error message should not contain revealing phrase '{phrase}'"
