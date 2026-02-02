"""
Property test for database error response.

**Property 18: Database Error Response**
**Validates: Requirements 8.3**

For any database operation failure during password reset processing,
the system should return a 500 status code with a generic error message.
"""

import json
import os
import sys
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from reset_password_handler import lambda_handler
from user_repository import DatabaseError


# Strategy for generating any tokens (we'll mock validation anyway)
any_tokens = st.text(min_size=10, max_size=100)

# Strategy for generating any passwords (we'll mock validation anyway)
any_passwords = st.text(min_size=8, max_size=50)


@settings(max_examples=100, deadline=None)
@given(
    token=any_tokens,
    password=any_passwords
)
def test_database_error_returns_500(token, password):
    """
    Property 18: Database Error Response
    
    For any database operation failure during password reset processing,
    the system should return a 500 status code with a generic error message.
    
    This test verifies that database errors are handled gracefully and
    return appropriate error responses without exposing internal details.
    """
    # Create event with valid input
    event = {
        'body': json.dumps({
            'token': token,
            'new_password': password
        }),
        'requestContext': {
            'identity': {
                'sourceIp': '192.168.1.1'
            }
        }
    }
    
    # Mock input validator to succeed
    with patch('reset_password_handler.InputValidator') as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate_reset_password_input.return_value = (True, token, password, None)
        mock_validator_class.return_value = mock_validator
        
        # Mock token validation to succeed
        with patch('reset_password_handler.TokenValidator') as mock_token_validator_class:
            mock_token_validator = MagicMock()
            mock_token_validator.validate_token.return_value = (True, 'user@example.com', None)
            mock_token_validator._get_token_hash.return_value = 'mock_hash'
            mock_token_validator_class.return_value = mock_token_validator
            
            # Mock password hasher to succeed
            with patch('reset_password_handler.PasswordHasher') as mock_hasher_class:
                mock_hasher = MagicMock()
                mock_hasher.hash_password.return_value = '$2b$12$mockhash'
                mock_hasher_class.return_value = mock_hasher
                
                # Mock update_password to raise DatabaseError
                with patch('reset_password_handler.update_password') as mock_update:
                    mock_update.side_effect = DatabaseError("Database connection failed")
                    
                    # Call the handler
                    response = lambda_handler(event, None)
                    
                    # Verify response
                    assert response['statusCode'] == 500, \
                        f"Expected 500 status code for database error, got {response['statusCode']}"
                    
                    # Parse response body
                    body = json.loads(response['body'])
                    
                    # Verify error structure
                    assert 'error' in body, "Response should contain 'error' field"
                    assert body['error'] == 'InternalError', \
                        f"Expected error type 'InternalError', got {body['error']}"
                    
                    # Verify generic error message (no internal details exposed)
                    assert 'message' in body, "Response should contain 'message' field"
                    assert 'unexpected error' in body['message'].lower() or \
                           'try again later' in body['message'].lower(), \
                        "Error message should be generic and user-friendly"
                    
                    # Verify no sensitive information is exposed
                    assert 'database' not in body['message'].lower(), \
                        "Error message should not expose database details"
                    assert 'connection' not in body['message'].lower(), \
                        "Error message should not expose connection details"


@settings(max_examples=100, deadline=None)
@given(
    token=any_tokens,
    password=any_passwords
)
def test_token_marking_database_error_returns_500(token, password):
    """
    Property 18: Database Error Response (token marking variant)
    
    Verifies that database errors during token marking also return 500.
    """
    # Create event with valid input
    event = {
        'body': json.dumps({
            'token': token,
            'new_password': password
        }),
        'requestContext': {
            'identity': {
                'sourceIp': '192.168.1.1'
            }
        }
    }
    
    # Mock input validator to succeed
    with patch('reset_password_handler.InputValidator') as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate_reset_password_input.return_value = (True, token, password, None)
        mock_validator_class.return_value = mock_validator
        
        # Mock token validation to succeed
        with patch('reset_password_handler.TokenValidator') as mock_token_validator_class:
            mock_token_validator = MagicMock()
            mock_token_validator.validate_token.return_value = (True, 'user@example.com', None)
            mock_token_validator._get_token_hash.return_value = 'mock_hash'
            mock_token_validator_class.return_value = mock_token_validator
            
            # Mock password hasher to succeed
            with patch('reset_password_handler.PasswordHasher') as mock_hasher_class:
                mock_hasher = MagicMock()
                mock_hasher.hash_password.return_value = '$2b$12$mockhash'
                mock_hasher_class.return_value = mock_hasher
                
                # Mock update_password to succeed
                with patch('reset_password_handler.update_password') as mock_update:
                    mock_update.return_value = True
                    
                    # Mock mark_token_used to raise DatabaseError
                    with patch('reset_password_handler.mark_token_used') as mock_mark:
                        mock_mark.side_effect = DatabaseError("Token table unavailable")
                        
                        # Call the handler
                        response = lambda_handler(event, None)
                        
                        # Verify response
                        assert response['statusCode'] == 500, \
                            f"Expected 500 status code for database error, got {response['statusCode']}"
                        
                        # Parse response body
                        body = json.loads(response['body'])
                        
                        # Verify error structure
                        assert body['error'] == 'InternalError'
                        assert 'message' in body


if __name__ == '__main__':
    # Run the property tests
    test_database_error_returns_500()
    test_token_marking_database_error_returns_500()
    print("✓ All property tests passed")
