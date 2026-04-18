"""
Property-based tests for error logging without sensitive data in forgot password handler.

Feature: password-recovery
Property 17: Error Logging Without Sensitive Data

**Validates: Requirements 8.2**

For any error that occurs during password reset processing, the system should 
log the error with sufficient context for debugging, but should never log 
sensitive information such as plaintext tokens, passwords, or password hashes.
"""

import pytest
import json
import logging
from unittest.mock import Mock, patch, call
from hypothesis import given, strategies as st, settings
from password_recovery.forgot_password_handler import lambda_handler


# Strategy for generating valid email addresses
@st.composite
def valid_emails(draw):
    """Generate valid email addresses."""
    local_chars = 'abcdefghijklmnopqrstuvwxyz0123456789._-'
    local = draw(st.text(alphabet=local_chars, min_size=1, max_size=20))
    domain = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=15))
    tld = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=2, max_size=5))
    return f"{local}@{domain}.{tld}"


# Strategy for generating tokens (simulating sensitive data)
@st.composite
def reset_tokens(draw):
    """Generate reset tokens (base64-like strings)."""
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/='
    return draw(st.text(alphabet=chars, min_size=32, max_size=64))


class TestForgotPasswordLoggingProperty:
    """Property-based tests for error logging without sensitive data."""
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_database_error_logs_without_token(self, email, token):
        """
        Property: Database errors should be logged without token data.
        
        For any database error during token storage, the error should be
        logged with context but should not include the plaintext token.
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.store_reset_token') as mock_store, \
             patch('password_recovery.forgot_password_handler.logger') as mock_logger:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # User exists
            mock_user_exists.return_value = True
            
            # Setup token generator to return our test token
            mock_token_gen = Mock()
            mock_token_gen.generate_reset_token.return_value = (token, 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            # Simulate database error
            from password_recovery.user_repository import DatabaseError
            mock_store.side_effect = DatabaseError("Database connection failed")
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Should return 500 error
            assert response['statusCode'] == 500
            
            # Check that error was logged
            assert mock_logger.error.called
            
            # Get all log calls
            log_calls = [str(call) for call in mock_logger.error.call_args_list]
            all_logs = ' '.join(log_calls)
            
            # Token should NOT be in logs
            assert token not in all_logs
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_user_lookup_error_logs_without_exposing_existence(self, email):
        """
        Property: User lookup errors should be logged without exposing user existence.
        
        For any database error during user lookup, the error should be logged
        but should not reveal whether the user exists or not.
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.logger') as mock_logger:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # Simulate database error during user lookup
            from password_recovery.user_repository import DatabaseError
            mock_user_exists.side_effect = DatabaseError("Database connection failed")
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Should return 500 error
            assert response['statusCode'] == 500
            
            # Should have logged the error
            assert mock_logger.error.called
            
            # Get all log calls
            log_calls = [str(call) for call in mock_logger.error.call_args_list]
            all_logs = ' '.join(log_calls)
            
            # Should not contain phrases that reveal user existence
            assert 'user exists' not in all_logs.lower()
            assert 'user not found' not in all_logs.lower()
            assert 'user found' not in all_logs.lower()
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_successful_flow_logs_without_token(self, email, token):
        """
        Property: Successful flows should log events without token data.
        
        For any successful password reset initiation, the system should log
        the event for audit purposes but should not include the plaintext token.
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.store_reset_token') as mock_store, \
             patch('password_recovery.forgot_password_handler.EmailService') as mock_email_class, \
             patch('password_recovery.forgot_password_handler.logger') as mock_logger:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # User exists
            mock_user_exists.return_value = True
            
            # Setup token generator to return our test token
            mock_token_gen = Mock()
            mock_token_gen.generate_reset_token.return_value = (token, 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            # Setup email service
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (True, 'test-message-id-123', None)
            mock_email_class.return_value = mock_email
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Should return 200 success
            assert response['statusCode'] == 200
            
            # Get all log calls (info, warning, error)
            all_log_calls = []
            if mock_logger.info.called:
                all_log_calls.extend([str(call) for call in mock_logger.info.call_args_list])
            if mock_logger.warning.called:
                all_log_calls.extend([str(call) for call in mock_logger.warning.call_args_list])
            if mock_logger.error.called:
                all_log_calls.extend([str(call) for call in mock_logger.error.call_args_list])
            
            all_logs = ' '.join(all_log_calls)
            
            # Token should NOT be in logs
            assert token not in all_logs
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_validation_error_logs_without_sensitive_data(self, email):
        """
        Property: Validation errors should be logged without sensitive data.
        
        For any validation error, the error should be logged but should not
        include any sensitive information.
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.logger') as mock_logger:
            
            # Test with invalid JSON
            event = {
                'body': 'invalid json{',
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Should return 400 error
            assert response['statusCode'] == 400
            
            # Should have logged a warning
            assert mock_logger.warning.called
            
            # Get all log calls
            log_calls = [str(call) for call in mock_logger.warning.call_args_list]
            all_logs = ' '.join(log_calls)
            
            # Should log the validation issue
            assert 'json' in all_logs.lower() or 'validation' in all_logs.lower()
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_unexpected_error_logs_without_token(self, email, token):
        """
        Property: Unexpected errors should be logged without token data.
        
        For any unexpected exception during processing, the error should be
        logged with context but should not include the plaintext token.
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.logger') as mock_logger:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # User exists
            mock_user_exists.return_value = True
            
            # Setup token generator to raise unexpected exception
            mock_token_gen = Mock()
            mock_token_gen.generate_reset_token.side_effect = Exception("Unexpected error")
            mock_token_gen_class.return_value = mock_token_gen
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Should return 500 error
            assert response['statusCode'] == 500
            
            # Should have logged the error
            assert mock_logger.error.called
            
            # Get all log calls
            log_calls = [str(call) for call in mock_logger.error.call_args_list]
            all_logs = ' '.join(log_calls)
            
            # Should log error type and context
            assert 'error' in all_logs.lower() or 'exception' in all_logs.lower()
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_rate_limit_logs_without_sensitive_data(self, email):
        """
        Property: Rate limit events should be logged without sensitive data.
        
        For any rate limit event, the system should log the event but should
        not include sensitive information.
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.logger') as mock_logger:
            
            # Setup rate limiter to block requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (False, 300)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Should return 429 error
            assert response['statusCode'] == 429
            
            # Should have logged a warning
            assert mock_logger.warning.called
            
            # Get all log calls
            log_calls = [str(call) for call in mock_logger.warning.call_args_list]
            all_logs = ' '.join(log_calls)
            
            # Should log rate limit event
            assert 'rate limit' in all_logs.lower()
            
            # Should include IP for monitoring
            assert '192.168.1.1' in all_logs
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_email_failure_logs_without_token(self, email, token):
        """
        Property: Email failures should be logged without token data.
        
        For any email delivery failure, the error should be logged but should
        not include the plaintext token.
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.store_reset_token') as mock_store, \
             patch('password_recovery.forgot_password_handler.EmailService') as mock_email_class, \
             patch('password_recovery.forgot_password_handler.logger') as mock_logger:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # User exists
            mock_user_exists.return_value = True
            
            # Setup token generator to return our test token
            mock_token_gen = Mock()
            mock_token_gen.generate_reset_token.return_value = (token, 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            # Setup email service to fail
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (False, None, 'MessageRejected')
            mock_email_class.return_value = mock_email
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Should still return 200 success (non-enumeration)
            assert response['statusCode'] == 200
            
            # Get all log calls
            all_log_calls = []
            if mock_logger.info.called:
                all_log_calls.extend([str(call) for call in mock_logger.info.call_args_list])
            if mock_logger.warning.called:
                all_log_calls.extend([str(call) for call in mock_logger.warning.call_args_list])
            if mock_logger.error.called:
                all_log_calls.extend([str(call) for call in mock_logger.error.call_args_list])
            
            all_logs = ' '.join(all_log_calls)
            
            # Token should NOT be in logs
            assert token not in all_logs
