"""
Integration tests for reset password Lambda handler.

These tests verify the complete reset password flow including:
- Successful password reset
- Expired token handling
- Used token handling
- Invalid token handling
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from reset_password_handler import lambda_handler


class TestResetPasswordIntegration:
    """Integration tests for reset password endpoint."""
    
    def test_successful_password_reset(self):
        """
        Test successful password reset flow.
        
        Verifies that a valid token and password result in:
        - Password being updated
        - Token being marked as used
        - Sessions being invalidated
        - Success response returned
        """
        # Create event with valid input
        event = {
            'body': json.dumps({
                'token': 'valid_token_12345',
                'new_password': 'NewSecurePass123!'
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
            mock_validator.validate_reset_password_input.return_value = (
                True, 'valid_token_12345', 'NewSecurePass123!', None
            )
            mock_validator_class.return_value = mock_validator
            
            # Mock token validation to succeed
            with patch('reset_password_handler.TokenValidator') as mock_token_validator_class:
                mock_token_validator = MagicMock()
                mock_token_validator.validate_token.return_value = (True, 'user@example.com', None)
                mock_token_validator._get_token_hash.return_value = 'token_hash_123'
                mock_token_validator_class.return_value = mock_token_validator
                
                # Mock password hasher
                with patch('reset_password_handler.PasswordHasher') as mock_hasher_class:
                    mock_hasher = MagicMock()
                    mock_hasher.hash_password.return_value = '$2b$12$hashedpassword'
                    mock_hasher_class.return_value = mock_hasher
                    
                    # Mock database operations
                    with patch('reset_password_handler.update_password') as mock_update:
                        mock_update.return_value = True
                        
                        with patch('reset_password_handler.mark_token_used') as mock_mark:
                            mock_mark.return_value = True
                            
                            # Mock session manager
                            with patch('reset_password_handler.SessionManager') as mock_session_class:
                                mock_session = MagicMock()
                                mock_session_class.return_value = mock_session
                                
                                # Call the handler
                                response = lambda_handler(event, None)
                                
                                # Verify response
                                assert response['statusCode'] == 200
                                body = json.loads(response['body'])
                                assert 'message' in body
                                assert 'successfully reset' in body['message'].lower()
                                
                                # Verify CORS headers
                                assert 'Access-Control-Allow-Origin' in response['headers']
                                
                                # Verify all operations were called
                                mock_hasher.hash_password.assert_called_once_with('NewSecurePass123!')
                                mock_update.assert_called_once_with('user@example.com', '$2b$12$hashedpassword')
                                mock_mark.assert_called_once_with('token_hash_123')
                                mock_session.invalidate_all_sessions.assert_called_once_with('user@example.com')
    
    def test_expired_token(self):
        """
        Test reset password with expired token.
        
        Verifies that an expired token is rejected with 401 status.
        """
        # Create event with valid input
        event = {
            'body': json.dumps({
                'token': 'expired_token_12345',
                'new_password': 'NewSecurePass123!'
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
            mock_validator.validate_reset_password_input.return_value = (
                True, 'expired_token_12345', 'NewSecurePass123!', None
            )
            mock_validator_class.return_value = mock_validator
            
            # Mock token validation to fail (expired)
            with patch('reset_password_handler.TokenValidator') as mock_token_validator_class:
                mock_token_validator = MagicMock()
                mock_token_validator.validate_token.return_value = (
                    False, None, 'The reset token has expired'
                )
                mock_token_validator_class.return_value = mock_token_validator
                
                # Call the handler
                response = lambda_handler(event, None)
                
                # Verify response
                assert response['statusCode'] == 401
                body = json.loads(response['body'])
                assert body['error'] == 'InvalidToken'
                assert 'invalid, expired, or has already been used' in body['message'].lower()
    
    def test_used_token(self):
        """
        Test reset password with already-used token.
        
        Verifies that a used token is rejected with 401 status.
        """
        # Create event with valid input
        event = {
            'body': json.dumps({
                'token': 'used_token_12345',
                'new_password': 'NewSecurePass123!'
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
            mock_validator.validate_reset_password_input.return_value = (
                True, 'used_token_12345', 'NewSecurePass123!', None
            )
            mock_validator_class.return_value = mock_validator
            
            # Mock token validation to fail (already used)
            with patch('reset_password_handler.TokenValidator') as mock_token_validator_class:
                mock_token_validator = MagicMock()
                mock_token_validator.validate_token.return_value = (
                    False, None, 'This reset token has already been used'
                )
                mock_token_validator_class.return_value = mock_token_validator
                
                # Call the handler
                response = lambda_handler(event, None)
                
                # Verify response
                assert response['statusCode'] == 401
                body = json.loads(response['body'])
                assert body['error'] == 'InvalidToken'
    
    def test_invalid_token(self):
        """
        Test reset password with invalid token.
        
        Verifies that an invalid token is rejected with 401 status.
        """
        # Create event with valid input
        event = {
            'body': json.dumps({
                'token': 'invalid_token_12345',
                'new_password': 'NewSecurePass123!'
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
            mock_validator.validate_reset_password_input.return_value = (
                True, 'invalid_token_12345', 'NewSecurePass123!', None
            )
            mock_validator_class.return_value = mock_validator
            
            # Mock token validation to fail (invalid)
            with patch('reset_password_handler.TokenValidator') as mock_token_validator_class:
                mock_token_validator = MagicMock()
                mock_token_validator.validate_token.return_value = (
                    False, None, 'Invalid or expired reset token'
                )
                mock_token_validator_class.return_value = mock_token_validator
                
                # Call the handler
                response = lambda_handler(event, None)
                
                # Verify response
                assert response['statusCode'] == 401
                body = json.loads(response['body'])
                assert body['error'] == 'InvalidToken'
    
    def test_missing_token_field(self):
        """
        Test reset password with missing token field.
        
        Verifies that missing token field is rejected with 400 status.
        """
        # Create event with missing token
        event = {
            'body': json.dumps({
                'new_password': 'NewSecurePass123!'
            }),
            'requestContext': {
                'identity': {
                    'sourceIp': '192.168.1.1'
                }
            }
        }
        
        # Mock input validator to fail
        with patch('reset_password_handler.InputValidator') as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator.validate_reset_password_input.return_value = (
                False, None, None, 'Reset token is required'
            )
            mock_validator_class.return_value = mock_validator
            
            # Call the handler
            response = lambda_handler(event, None)
            
            # Verify response
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['error'] == 'ValidationError'
            assert 'token is required' in body['message'].lower()
    
    def test_missing_password_field(self):
        """
        Test reset password with missing password field.
        
        Verifies that missing password field is rejected with 400 status.
        """
        # Create event with missing password
        event = {
            'body': json.dumps({
                'token': 'valid_token_12345'
            }),
            'requestContext': {
                'identity': {
                    'sourceIp': '192.168.1.1'
                }
            }
        }
        
        # Mock input validator to fail
        with patch('reset_password_handler.InputValidator') as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator.validate_reset_password_input.return_value = (
                False, None, None, 'New password is required'
            )
            mock_validator_class.return_value = mock_validator
            
            # Call the handler
            response = lambda_handler(event, None)
            
            # Verify response
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['error'] == 'ValidationError'
            assert 'password is required' in body['message'].lower()
    
    def test_weak_password(self):
        """
        Test reset password with weak password.
        
        Verifies that weak password is rejected with 400 status.
        """
        # Create event with weak password
        event = {
            'body': json.dumps({
                'token': 'valid_token_12345',
                'new_password': 'weak'
            }),
            'requestContext': {
                'identity': {
                    'sourceIp': '192.168.1.1'
                }
            }
        }
        
        # Mock input validator to fail
        with patch('reset_password_handler.InputValidator') as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator.validate_reset_password_input.return_value = (
                False, None, None, 'Password must be at least 8 characters'
            )
            mock_validator_class.return_value = mock_validator
            
            # Call the handler
            response = lambda_handler(event, None)
            
            # Verify response
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['error'] == 'ValidationError'
    
    def test_token_race_condition(self):
        """
        Test reset password with token race condition.
        
        Verifies that if token is marked as used by another request (race condition),
        the request is rejected with 401 status.
        """
        # Create event with valid input
        event = {
            'body': json.dumps({
                'token': 'valid_token_12345',
                'new_password': 'NewSecurePass123!'
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
            mock_validator.validate_reset_password_input.return_value = (
                True, 'valid_token_12345', 'NewSecurePass123!', None
            )
            mock_validator_class.return_value = mock_validator
            
            # Mock token validation to succeed
            with patch('reset_password_handler.TokenValidator') as mock_token_validator_class:
                mock_token_validator = MagicMock()
                mock_token_validator.validate_token.return_value = (True, 'user@example.com', None)
                mock_token_validator._get_token_hash.return_value = 'token_hash_123'
                mock_token_validator_class.return_value = mock_token_validator
                
                # Mock password hasher
                with patch('reset_password_handler.PasswordHasher') as mock_hasher_class:
                    mock_hasher = MagicMock()
                    mock_hasher.hash_password.return_value = '$2b$12$hashedpassword'
                    mock_hasher_class.return_value = mock_hasher
                    
                    # Mock database operations
                    with patch('reset_password_handler.update_password') as mock_update:
                        mock_update.return_value = True
                        
                        # Mock mark_token_used to return False (race condition)
                        with patch('reset_password_handler.mark_token_used') as mock_mark:
                            mock_mark.return_value = False
                            
                            # Call the handler
                            response = lambda_handler(event, None)
                            
                            # Verify response
                            assert response['statusCode'] == 401
                            body = json.loads(response['body'])
                            assert body['error'] == 'InvalidToken'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
