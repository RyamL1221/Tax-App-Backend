"""
Property-based tests for response structure compatibility.

Feature: jwt-authentication-migration
Property 14: Response Structure Compatibility

**Validates: Requirements 1.6**

For any successful login, the response must maintain the same JSON structure 
as before: {"statusCode": 200, "body": {"message": "...", "email": "...", "token": "..."}}.
"""

import json
import bcrypt
import jwt
import pytest
import sys
import os
from hypothesis import given, strategies as st, settings
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import lambda_handler


# Strategy for generating valid email addresses
emails = st.emails()

# Strategy for generating valid passwords (8-128 chars with required complexity)
passwords = st.text(
    min_size=8,
    max_size=128,
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P'),
        min_codepoint=33,
        max_codepoint=126
    )
).filter(lambda p: any(c.isupper() for c in p) and 
                   any(c.islower() for c in p) and 
                   any(c.isdigit() for c in p))

# Strategy for generating JWT secret keys (>= 32 characters)
jwt_secrets = st.text(min_size=32, max_size=128)


@settings(max_examples=20)
@given(email=emails, password=passwords, jwt_secret=jwt_secrets)
def test_response_structure_compatibility(email, password, jwt_secret):
    """
    Property 14: Response Structure Compatibility
    
    For any successful login, the response must maintain the same JSON structure
    as before: {"statusCode": 200, "body": {"message": "...", "email": "...", "token": "..."}}.
    
    **Validates: Requirements 1.6**
    """
    # Generate password hash
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
    
    # Create login event
    event = {
        'body': json.dumps({
            'email': email,
            'password': password
        })
    }
    context = {}
    
    # Mock database and environment
    with patch('app.get_user_by_email') as mock_get_user, \
         patch('app.os.environ.get') as mock_env:
        
        mock_get_user.return_value = {
            'email': email,
            'name': 'Test User',
            'password_hash': password_hash,
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_env.return_value = jwt_secret
        
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Verify response structure
        assert isinstance(response, dict), "Response must be a dictionary"
        assert 'statusCode' in response, "Response must have statusCode"
        assert 'body' in response, "Response must have body"
        assert 'headers' in response, "Response must have headers"
        
        # Verify status code
        assert response['statusCode'] == 200, "Successful login must return 200"
        
        # Parse body
        body = json.loads(response['body'])
        
        # Verify body structure
        assert isinstance(body, dict), "Response body must be a dictionary"
        assert 'message' in body, "Response body must have message field"
        assert 'email' in body, "Response body must have email field"
        assert 'token' in body, "Response body must have token field"
        
        # Verify field values
        assert body['message'] == 'Login successful', "Message must be 'Login successful'"
        assert body['email'] == email, "Email in response must match login email"
        assert isinstance(body['token'], str), "Token must be a string"
        assert len(body['token']) > 0, "Token must not be empty"
        
        # Verify token is a valid JWT (three segments separated by periods)
        token_parts = body['token'].split('.')
        assert len(token_parts) == 3, "Token must be a valid JWT with three segments"
        
        # Verify token can be decoded with the secret
        try:
            payload = jwt.decode(body['token'], jwt_secret, algorithms=["HS256"])
            assert payload['email'] == email, "JWT payload must contain correct email"
        except jwt.InvalidTokenError:
            pytest.fail("Token must be a valid JWT that can be decoded")
        
        # Verify no sensitive data in response
        assert 'password' not in body, "Response must not contain password"
        assert 'password_hash' not in body, "Response must not contain password_hash"
        
        # Verify CORS headers are present
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
        assert 'Content-Type' in response['headers']


@settings(max_examples=10)
@given(email=emails, password=passwords, jwt_secret=jwt_secrets)
def test_response_body_is_valid_json(email, password, jwt_secret):
    """
    Property: Response body must be valid JSON string.
    
    For any successful login, the response body must be a valid JSON string
    that can be parsed.
    
    **Validates: Requirements 1.6**
    """
    # Generate password hash
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
    
    # Create login event
    event = {
        'body': json.dumps({
            'email': email,
            'password': password
        })
    }
    context = {}
    
    # Mock database and environment
    with patch('app.get_user_by_email') as mock_get_user, \
         patch('app.os.environ.get') as mock_env:
        
        mock_get_user.return_value = {
            'email': email,
            'name': 'Test User',
            'password_hash': password_hash,
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_env.return_value = jwt_secret
        
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Verify body is a valid JSON string
        assert isinstance(response['body'], str), "Response body must be a string"
        
        try:
            body = json.loads(response['body'])
            assert isinstance(body, dict), "Parsed body must be a dictionary"
        except json.JSONDecodeError:
            pytest.fail("Response body must be valid JSON")


@settings(max_examples=10)
@given(email=emails, password=passwords, jwt_secret=jwt_secrets)
def test_response_contains_only_expected_fields(email, password, jwt_secret):
    """
    Property: Response body must contain only expected fields.
    
    For any successful login, the response body must contain exactly the
    expected fields: message, email, and token (no extra fields).
    
    **Validates: Requirements 1.6**
    """
    # Generate password hash
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
    
    # Create login event
    event = {
        'body': json.dumps({
            'email': email,
            'password': password
        })
    }
    context = {}
    
    # Mock database and environment
    with patch('app.get_user_by_email') as mock_get_user, \
         patch('app.os.environ.get') as mock_env:
        
        mock_get_user.return_value = {
            'email': email,
            'name': 'Test User',
            'password_hash': password_hash,
            'created_at': '2024-01-01T00:00:00Z'
        }
        mock_env.return_value = jwt_secret
        
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Parse body
        body = json.loads(response['body'])
        
        # Verify only expected fields are present
        expected_fields = {'message', 'email', 'token'}
        actual_fields = set(body.keys())
        
        assert actual_fields == expected_fields, \
            f"Response body must contain exactly {expected_fields}, got {actual_fields}"
