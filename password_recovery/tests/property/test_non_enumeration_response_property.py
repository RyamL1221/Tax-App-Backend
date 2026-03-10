"""
Property-based tests for non-enumeration response consistency.

Feature: password-recovery
Property 1: Non-Enumeration Response Consistency

**Validates: Requirements 1.3**

For any email address (whether registered or not), when a password reset is 
requested via /forgot-password, the system should return the same generic 
success message and status code.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
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


class TestNonEnumerationResponseProperty:
    """Property-based tests for non-enumeration response consistency."""
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_registered_and_unregistered_emails_return_same_status_code(self, email):
        """
        Property: All emails should return the same status code (200).
        
        For any email address, whether registered or not, the response
        status code should always be 200 to prevent enumeration.
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
            
            # Setup token generator
            mock_token_gen = Mock()
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            # Setup email service
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (True, 'test-message-id-123')
            mock_email_class.return_value = mock_email
            
            # Test with registered user
            mock_user_exists.return_value = True
            event_registered = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            response_registered = lambda_handler(event_registered, None)
            
            # Test with unregistered user
            mock_user_exists.return_value = False
            event_unregistered = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.2'}}
            }
            response_unregistered = lambda_handler(event_unregistered, None)
            
            # Both should return 200
            assert response_registered['statusCode'] == 200
            assert response_unregistered['statusCode'] == 200
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_registered_and_unregistered_emails_return_same_message(self, email):
        """
        Property: All emails should return the same generic message.
        
        For any email address, whether registered or not, the response
        message should be identical to prevent enumeration.
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
            
            # Setup token generator
            mock_token_gen = Mock()
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            # Setup email service
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (True, 'test-message-id-123')
            mock_email_class.return_value = mock_email
            
            # Test with registered user
            mock_user_exists.return_value = True
            event_registered = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            response_registered = lambda_handler(event_registered, None)
            body_registered = json.loads(response_registered['body'])
            
            # Test with unregistered user
            mock_user_exists.return_value = False
            event_unregistered = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.2'}}
            }
            response_unregistered = lambda_handler(event_unregistered, None)
            body_unregistered = json.loads(response_unregistered['body'])
            
            # Both should return the same message
            assert body_registered['message'] == body_unregistered['message']
            assert 'If an account exists' in body_registered['message']
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_email_delivery_failure_returns_same_response(self, email):
        """
        Property: Email delivery failures should return the same success response.
        
        For any email address where email delivery fails, the response should
        still be the same generic success message to prevent enumeration.
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
            
            # Setup token generator
            mock_token_gen = Mock()
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            # User exists
            mock_user_exists.return_value = True
            
            # Test with successful email delivery
            mock_email_success = Mock()
            mock_email_success.send_reset_email.return_value = (True, 'test-message-id-123')
            mock_email_class.return_value = mock_email_success
            
            event_success = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            response_success = lambda_handler(event_success, None)
            
            # Test with failed email delivery
            mock_email_failure = Mock()
            mock_email_failure.send_reset_email.return_value = (False, None)
            mock_email_class.return_value = mock_email_failure
            
            event_failure = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.2'}}
            }
            response_failure = lambda_handler(event_failure, None)
            
            # Both should return 200 with same message
            assert response_success['statusCode'] == 200
            assert response_failure['statusCode'] == 200
            
            body_success = json.loads(response_success['body'])
            body_failure = json.loads(response_failure['body'])
            assert body_success['message'] == body_failure['message']
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_response_contains_no_user_existence_information(self, email):
        """
        Property: Response should not reveal whether user exists.
        
        For any email address, the response body should not contain any
        information that could be used to determine if the user exists.
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
            
            # Setup token generator
            mock_token_gen = Mock()
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            # Setup email service
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (True, 'test-message-id-123')
            mock_email_class.return_value = mock_email
            
            # Test with user exists
            mock_user_exists.return_value = True
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            response = lambda_handler(event, None)
            body = json.loads(response['body'])
            
            # Response should not contain words like "exists", "found", "registered"
            response_text = json.dumps(body).lower()
            assert 'found' not in response_text or 'not found' not in response_text
            assert 'registered' not in response_text or 'not registered' not in response_text
            # "exists" is okay in "If an account exists" context
            
            # Should use conditional language
            assert 'if' in response_text.lower()
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_response_headers_are_consistent(self, email):
        """
        Property: Response headers should be consistent regardless of user existence.
        
        For any email address, the response headers (including CORS headers)
        should be identical whether the user exists or not.
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
            
            # Setup token generator
            mock_token_gen = Mock()
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            # Setup email service
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (True, 'test-message-id-123')
            mock_email_class.return_value = mock_email
            
            # Test with registered user
            mock_user_exists.return_value = True
            event_registered = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            response_registered = lambda_handler(event_registered, None)
            
            # Test with unregistered user
            mock_user_exists.return_value = False
            event_unregistered = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.2'}}
            }
            response_unregistered = lambda_handler(event_unregistered, None)
            
            # Headers should be identical
            assert response_registered['headers'] == response_unregistered['headers']
            
            # Should include CORS headers
            assert 'Access-Control-Allow-Origin' in response_registered['headers']
            assert 'Content-Type' in response_registered['headers']
