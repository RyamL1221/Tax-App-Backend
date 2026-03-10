"""
Property-based tests for success response format.

**Validates: Requirements 6.1, 6.2, 5.4**

Property 9: Success response format
For any successful authentication, the endpoint should return a 200 status code
with a JSON body containing a success message, the user's email, and an
authentication token, but never the password or password hash.
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails
from user_login.response_formatter import success_response


@settings(max_examples=20)
@given(
    email=emails(),
    token=st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')
)
def test_success_response_status_code_property(email, token):
    """
    Property 9: Success response format - Status Code
    
    For any successful authentication, the response should have status code 200.
    
    **Validates: Requirements 6.1, 5.4**
    """
    response = success_response(email, token)
    
    assert response["statusCode"] == 200, \
        f"Success response should have status code 200, got {response['statusCode']}"


@settings(max_examples=20)
@given(
    email=emails(),
    token=st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')
)
def test_success_response_contains_email_property(email, token):
    """
    Property 9: Success response format - Email
    
    For any successful authentication, the response should contain the user's email.
    
    **Validates: Requirements 6.1, 5.4**
    """
    response = success_response(email, token)
    body = json.loads(response["body"])
    
    assert "email" in body, "Success response should contain email"
    assert body["email"] == email, \
        f"Response email should match input email: {body['email']} != {email}"


@settings(max_examples=20)
@given(
    email=emails(),
    token=st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')
)
def test_success_response_contains_token_property(email, token):
    """
    Property 9: Success response format - Token
    
    For any successful authentication, the response should contain the authentication token.
    
    **Validates: Requirements 6.1, 5.4**
    """
    response = success_response(email, token)
    body = json.loads(response["body"])
    
    assert "token" in body, "Success response should contain token"
    assert body["token"] == token, \
        f"Response token should match input token: {body['token']} != {token}"


@settings(max_examples=20)
@given(
    email=emails(),
    token=st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')
)
def test_success_response_contains_message_property(email, token):
    """
    Property 9: Success response format - Message
    
    For any successful authentication, the response should contain a success message.
    
    **Validates: Requirements 6.1, 5.4**
    """
    response = success_response(email, token)
    body = json.loads(response["body"])
    
    assert "message" in body, "Success response should contain message"
    assert isinstance(body["message"], str), "Message should be a string"
    assert len(body["message"]) > 0, "Message should not be empty"


@settings(max_examples=20)
@given(
    email=emails(),
    token=st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')
)
def test_success_response_does_not_contain_password_property(email, token):
    """
    Property 9: Success response format - No Password
    
    For any successful authentication, the response should never contain
    password or password_hash fields.
    
    **Validates: Requirements 6.2**
    """
    response = success_response(email, token)
    body = json.loads(response["body"])
    
    assert "password" not in body, \
        "Success response should not contain password field"
    assert "password_hash" not in body, \
        "Success response should not contain password_hash field"


@settings(max_examples=20)
@given(
    email=emails(),
    token=st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')
)
def test_success_response_has_cors_headers_property(email, token):
    """
    Property 9: Success response format - CORS Headers
    
    For any successful authentication, the response should include CORS headers.
    
    **Validates: Requirements 6.1, 5.4**
    """
    response = success_response(email, token)
    
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
@given(
    email=emails(),
    token=st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')
)
def test_success_response_body_is_valid_json_property(email, token):
    """
    Property 9: Success response format - Valid JSON
    
    For any successful authentication, the response body should be valid JSON.
    
    **Validates: Requirements 6.1, 5.4**
    """
    response = success_response(email, token)
    
    # Should be able to parse body as JSON without error
    try:
        body = json.loads(response["body"])
        assert isinstance(body, dict), "Parsed body should be a dictionary"
    except json.JSONDecodeError as e:
        pytest.fail(f"Response body should be valid JSON: {e}")
