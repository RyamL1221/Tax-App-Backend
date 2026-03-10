"""
Integration tests for forgot password flow.

These tests verify the end-to-end forgot password flow including:
- Successful flow with registered user
- Flow with non-existent user
- Rate limiting
- Error handling
"""

import pytest
import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from password_recovery.forgot_password_handler import lambda_handler


class TestForgotPasswordIntegration:
    """Integration tests for forgot password flow."""
    
    def test_successful_flow_with_registered_user(self):
        """
        Test successful forgot password flow with a registered user.
        
        Verifies:
        - User lookup succeeds
        - Token is generated
        - Token hash is stored
        - Email is sent
        - Generic success response is returned
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.store_reset_token') as mock_store, \
             patch('password_recovery.forgot_password_handler.EmailService') as mock_email_class:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # User exists
            mock_user_exists.return_value = True
            
            # Setup token generator
            mock_token_gen = Mock()
            expiration = datetime.now(timezone.utc) + timedelta(hours=1)
            mock_token_gen.generate_reset_token.return_value = ('plaintext_token', 'token_hash', expiration)
            mock_token_gen_class.return_value = mock_token_gen
            
            # Setup email service
            mock_email = Mock()
            mock_email.send_reset_email.return_value = True
            mock_email_class.return_value = mock_email
            
            # Create event
            event = {
                'body': json.dumps({'email': 'user@example.com'}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            # Call handler
            response = lambda_handler(event, None)
            
            # Verify response
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'If an account exists' in body['message']
            
            # Verify rate limiter was checked
            mock_rate_limiter.check_rate_limit.assert_called_once_with('192.168.1.1')
            mock_rate_limiter.record_request.assert_called_once_with('192.168.1.1')
            
            # Verify user lookup
            mock_user_exists.assert_called_once_with('user@example.com')
            
            # Verify token generation
            mock_token_gen.generate_reset_token.assert_called_once_with('user@example.com')
            
            # Verify token storage
            mock_store.assert_called_once_with('user@example.com', 'token_hash', expiration)
            
            # Verify email was sent
            mock_email.send_reset_email.assert_called_once_with('user@example.com', 'plaintext_token', expiration)
    
    def test_flow_with_non_existent_user(self):
        """
        Test forgot password flow with a non-existent user.
        
        Verifies:
        - User lookup returns False
        - Token is NOT generated
        - Email is NOT sent
        - Same generic success response is returned (non-enumeration)
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.store_reset_token') as mock_store, \
             patch('password_recovery.forgot_password_handler.EmailService') as mock_email_class:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # User does NOT exist
            mock_user_exists.return_value = False
            
            # Setup token generator (should not be called)
            mock_token_gen = Mock()
            mock_token_gen_class.return_value = mock_token_gen
            
            # Setup email service (should not be called)
            mock_email = Mock()
            mock_email_class.return_value = mock_email
            
            # Create event
            event = {
                'body': json.dumps({'email': 'nonexistent@example.com'}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            # Call handler
            response = lambda_handler(event, None)
            
            # Verify response (same as registered user)
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'If an account exists' in body['message']
            
            # Verify rate limiter was checked
            mock_rate_limiter.check_rate_limit.assert_called_once_with('192.168.1.1')
            mock_rate_limiter.record_request.assert_called_once_with('192.168.1.1')
            
            # Verify user lookup
            mock_user_exists.assert_called_once_with('nonexistent@example.com')
            
            # Verify token generation was NOT called
            mock_token_gen.generate_reset_token.assert_not_called()
            
            # Verify token storage was NOT called
            mock_store.assert_not_called()
            
            # Verify email was NOT sent
            mock_email.send_reset_email.assert_not_called()
    
    def test_rate_limiting(self):
        """
        Test rate limiting functionality.
        
        Verifies:
        - Rate limiter blocks request when limit exceeded
        - 429 response is returned
        - Retry-After header is included
        - No further processing occurs
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists:
            
            # Setup rate limiter to block requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (False, 300)  # Blocked, retry after 300s
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # Create event
            event = {
                'body': json.dumps({'email': 'user@example.com'}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            # Call handler
            response = lambda_handler(event, None)
            
            # Verify response
            assert response['statusCode'] == 429
            assert 'Retry-After' in response['headers']
            assert response['headers']['Retry-After'] == '300'
            
            body = json.loads(response['body'])
            assert 'RateLimitExceeded' in body['error']
            assert 'Too many requests' in body['message']
            
            # Verify rate limiter was checked
            mock_rate_limiter.check_rate_limit.assert_called_once_with('192.168.1.1')
            
            # Verify no further processing occurred
            mock_user_exists.assert_not_called()
    
    def test_validation_error_missing_email(self):
        """
        Test validation error when email is missing.
        
        Verifies:
        - 400 response is returned
        - Error message indicates missing email
        - No further processing occurs
        """
        # Create event with missing email
        event = {
            'body': json.dumps({}),
            'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'email' in body['message'].lower() or 'required' in body['message'].lower()
    
    def test_validation_error_invalid_email_format(self):
        """
        Test validation error when email format is invalid.
        
        Verifies:
        - 400 response is returned
        - Error message indicates invalid email
        - No further processing occurs
        """
        # Create event with invalid email
        event = {
            'body': json.dumps({'email': 'not-an-email'}),
            'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'email' in body['message'].lower() or 'valid' in body['message'].lower()
    
    def test_invalid_json_in_body(self):
        """
        Test error handling when request body contains invalid JSON.
        
        Verifies:
        - 400 response is returned
        - Error message indicates invalid JSON
        """
        # Create event with invalid JSON
        event = {
            'body': 'invalid json{',
            'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'json' in body['message'].lower() or 'format' in body['message'].lower()
    
    def test_database_error_during_user_lookup(self):
        """
        Test error handling when database error occurs during user lookup.
        
        Verifies:
        - 500 response is returned
        - Generic error message is returned
        - No further processing occurs
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # Simulate database error
            from password_recovery.user_repository import DatabaseError
            mock_user_exists.side_effect = DatabaseError("Database connection failed")
            
            # Create event
            event = {
                'body': json.dumps({'email': 'user@example.com'}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            # Call handler
            response = lambda_handler(event, None)
            
            # Verify response
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'InternalError' in body['error']
    
    def test_database_error_during_token_storage(self):
        """
        Test error handling when database error occurs during token storage.
        
        Verifies:
        - 500 response is returned
        - Generic error message is returned
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.store_reset_token') as mock_store:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # User exists
            mock_user_exists.return_value = True
            
            # Setup token generator
            mock_token_gen = Mock()
            expiration = datetime.now(timezone.utc) + timedelta(hours=1)
            mock_token_gen.generate_reset_token.return_value = ('plaintext_token', 'token_hash', expiration)
            mock_token_gen_class.return_value = mock_token_gen
            
            # Simulate database error during token storage
            from password_recovery.user_repository import DatabaseError
            mock_store.side_effect = DatabaseError("Failed to store token")
            
            # Create event
            event = {
                'body': json.dumps({'email': 'user@example.com'}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            # Call handler
            response = lambda_handler(event, None)
            
            # Verify response
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'InternalError' in body['error']
    
    def test_email_delivery_failure_returns_success(self):
        """
        Test that email delivery failure still returns success (non-enumeration).
        
        Verifies:
        - Email service returns False
        - 200 response is still returned
        - Generic success message is returned
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.store_reset_token') as mock_store, \
             patch('password_recovery.forgot_password_handler.EmailService') as mock_email_class:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # User exists
            mock_user_exists.return_value = True
            
            # Setup token generator
            mock_token_gen = Mock()
            expiration = datetime.now(timezone.utc) + timedelta(hours=1)
            mock_token_gen.generate_reset_token.return_value = ('plaintext_token', 'token_hash', expiration)
            mock_token_gen_class.return_value = mock_token_gen
            
            # Setup email service to fail
            mock_email = Mock()
            mock_email.send_reset_email.return_value = False
            mock_email_class.return_value = mock_email
            
            # Create event
            event = {
                'body': json.dumps({'email': 'user@example.com'}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            # Call handler
            response = lambda_handler(event, None)
            
            # Verify response (still success for non-enumeration)
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'If an account exists' in body['message']
            
            # Verify email was attempted
            mock_email.send_reset_email.assert_called_once()
    
    def test_cors_headers_present_in_all_responses(self):
        """
        Test that CORS headers are present in all response types.
        
        Verifies:
        - Success response has CORS headers
        - Error response has CORS headers
        """
        # Test success response
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.store_reset_token') as mock_store, \
             patch('password_recovery.forgot_password_handler.EmailService') as mock_email_class:
            
            # Setup mocks
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            mock_user_exists.return_value = True
            
            mock_token_gen = Mock()
            expiration = datetime.now(timezone.utc) + timedelta(hours=1)
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', expiration)
            mock_token_gen_class.return_value = mock_token_gen
            
            mock_email = Mock()
            mock_email.send_reset_email.return_value = True
            mock_email_class.return_value = mock_email
            
            event_success = {
                'body': json.dumps({'email': 'user@example.com'}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response_success = lambda_handler(event_success, None)
            
            # Verify CORS headers
            assert 'Access-Control-Allow-Origin' in response_success['headers']
            assert 'Access-Control-Allow-Headers' in response_success['headers']
            assert 'Access-Control-Allow-Methods' in response_success['headers']
            assert 'Content-Type' in response_success['headers']
        
        # Test error response
        event_error = {
            'body': json.dumps({'email': ''}),
            'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
        }
        
        response_error = lambda_handler(event_error, None)
        
        # Verify CORS headers
        assert 'Access-Control-Allow-Origin' in response_error['headers']
        assert 'Access-Control-Allow-Headers' in response_error['headers']
        assert 'Access-Control-Allow-Methods' in response_error['headers']
        assert 'Content-Type' in response_error['headers']
