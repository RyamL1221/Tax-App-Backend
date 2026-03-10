"""
Property-based tests for CORS headers.

**Validates: Requirements 6.7**

Property 12: CORS headers present
For any response (success or error), the endpoint should include appropriate
CORS headers (Access-Control-Allow-Origin, Access-Control-Allow-Headers,
Access-Control-Allow-Methods).
"""

import json
import os
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails
from user_login.response_formatter import (
    success_response,
    validation_error_response,
    authentication_error_response,
    internal_error_response,
    error_response
)


def get_expected_cors_origin():
    """Get the expected CORS origin from environment or default."""
    return os.environ.get('CORS_ALLOWED_ORIGIN', '*')


@settings(max_examples=20)
@given(
    email=emails(),
    token=st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')
)
def test_success_response_has_cors_headers_property(email, token):
    """
    Property 12: CORS headers present - Success Response
    
    For any success response, CORS headers should be present.
    
    **Validates: Requirements 6.7**
    """
    response = success_response(email, token)
    
    _assert_cors_headers_present(response)


@settings(max_examples=20)
@given(message=st.text(min_size=1, max_size=200))
def test_validation_error_response_has_cors_headers_property(message):
    """
    Property 12: CORS headers present - Validation Error Response
    
    For any validation error response, CORS headers should be present.
    
    **Validates: Requirements 6.7**
    """
    response = validation_error_response(message)
    
    _assert_cors_headers_present(response)


@settings(max_examples=20)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_authentication_error_response_has_cors_headers_property(iteration):
    """
    Property 12: CORS headers present - Authentication Error Response
    
    For any authentication error response, CORS headers should be present.
    
    **Validates: Requirements 6.7**
    """
    response = authentication_error_response()
    
    _assert_cors_headers_present(response)


@settings(max_examples=20)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_internal_error_response_has_cors_headers_property(iteration):
    """
    Property 12: CORS headers present - Internal Error Response
    
    For any internal error response, CORS headers should be present.
    
    **Validates: Requirements 6.7**
    """
    response = internal_error_response()
    
    _assert_cors_headers_present(response)


@settings(max_examples=20)
@given(
    status_code=st.integers(min_value=400, max_value=599),
    message=st.text(min_size=1, max_size=200)
)
def test_generic_error_response_has_cors_headers_property(status_code, message):
    """
    Property 12: CORS headers present - Generic Error Response
    
    For any generic error response, CORS headers should be present.
    
    **Validates: Requirements 6.7**
    """
    response = error_response(status_code, message)
    
    _assert_cors_headers_present(response)


def _assert_cors_headers_present(response):
    """
    Helper function to assert that CORS headers are present in a response.
    
    Args:
        response: API Gateway proxy response dictionary
    """
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
    
    # Verify header values are appropriate
    expected_origin = get_expected_cors_origin()
    assert headers["Access-Control-Allow-Origin"] == expected_origin, \
        f"Access-Control-Allow-Origin should be '{expected_origin}'"
    
    assert "Content-Type" in headers["Access-Control-Allow-Headers"], \
        "Access-Control-Allow-Headers should include Content-Type"
    
    assert "POST" in headers["Access-Control-Allow-Methods"], \
        "Access-Control-Allow-Methods should include POST"
    
    assert headers["Content-Type"] == "application/json", \
        "Content-Type should be application/json"


@settings(max_examples=20)
@given(
    email=emails(),
    token=st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')
)
def test_cors_headers_values_are_consistent_property(email, token):
    """
    Property 12: CORS headers present - Consistency
    
    For any response, CORS headers should have consistent values across
    different response types.
    
    **Validates: Requirements 6.7**
    """
    success_resp = success_response(email, token)
    auth_error_resp = authentication_error_response()
    internal_error_resp = internal_error_response()
    
    # All responses should have the same CORS headers
    assert success_resp["headers"]["Access-Control-Allow-Origin"] == \
           auth_error_resp["headers"]["Access-Control-Allow-Origin"] == \
           internal_error_resp["headers"]["Access-Control-Allow-Origin"], \
        "Access-Control-Allow-Origin should be consistent across all responses"
    
    assert success_resp["headers"]["Access-Control-Allow-Methods"] == \
           auth_error_resp["headers"]["Access-Control-Allow-Methods"] == \
           internal_error_resp["headers"]["Access-Control-Allow-Methods"], \
        "Access-Control-Allow-Methods should be consistent across all responses"
