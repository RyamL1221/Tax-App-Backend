"""
Property-based tests for CORS headers presence.

Feature: password-recovery
Property 21: CORS Headers Presence

**Validates: Requirements 9.4**

For any response from the password recovery endpoints, the response should 
include CORS headers consistent with existing endpoints (Access-Control-Allow-Origin, 
Access-Control-Allow-Methods, Access-Control-Allow-Headers).
"""

import os
import pytest
import json
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings
from password_recovery.forgot_password_handler import lambda_handler


def get_expected_cors_origin():
    """Get the expected CORS origin from environment or default."""
    return os.environ.get('CORS_ALLOWED_ORIGIN', '*')


# Strategy for generating valid email addresses
@st.composite
def valid_emails(draw):
    """Generate valid email addresses."""
    local_chars = 'abcdefghijklmnopqrstuvwxyz0123456789._-'
    local = draw(st.text(alphabet=local_chars, min_size=1, max_size=20))
    domain = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=15))
    tld = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=2, max_size=5))
    return f"{local}@{domain}.{tld}"


# Strategy for generating invalid email formats
invalid_email_formats = st.sampled_from([
    'notanemail',
    '@example.com',
    'user@',
    '',
])


class TestCORSHeadersProperty:
    """Property-based tests for CORS headers presence."""
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_success_response_has_cors_headers(self, email):
        """
        Property: Success responses should have CORS headers.
        
        For any successful request, the response should include:
        - Access-Control-Allow-Origin
        - Access-Control-Allow-Headers
        - Access-Control-Allow-Methods
        - Content-Type
        """
        # Mock dependencies
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
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (True, 'test-message-id-123', None)
            mock_email_class.return_value = mock_email
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Check CORS headers are present
            assert 'headers' in response
            headers = response['headers']
            
            assert 'Access-Control-Allow-Origin' in headers
            assert 'Access-Control-Allow-Headers' in headers
            assert 'Access-Control-Allow-Methods' in headers
            assert 'Content-Type' in headers
    
    @given(invalid_email_formats)
    @settings(max_examples=100)
    def test_validation_error_response_has_cors_headers(self, invalid_email):
        """
        Property: Validation error responses should have CORS headers.
        
        For any validation error, the response should include CORS headers.
        """
        event = {
            'body': json.dumps({'email': invalid_email}),
            'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
        }
        
        response = lambda_handler(event, None)
        
        # Check CORS headers are present
        assert 'headers' in response
        headers = response['headers']
        
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Headers' in headers
        assert 'Access-Control-Allow-Methods' in headers
        assert 'Content-Type' in headers
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_rate_limit_error_response_has_cors_headers(self, email):
        """
        Property: Rate limit error responses should have CORS headers.
        
        For any rate limit error, the response should include CORS headers.
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class:
            
            # Setup rate limiter to block requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (False, 300)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Check CORS headers are present
            assert 'headers' in response
            headers = response['headers']
            
            assert 'Access-Control-Allow-Origin' in headers
            assert 'Access-Control-Allow-Headers' in headers
            assert 'Access-Control-Allow-Methods' in headers
            assert 'Content-Type' in headers
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_internal_error_response_has_cors_headers(self, email):
        """
        Property: Internal error responses should have CORS headers.
        
        For any internal error, the response should include CORS headers.
        """
        # Mock dependencies to cause internal error
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists:
            
            # Setup rate limiter to allow requests
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # Simulate database error
            from password_recovery.user_repository import DatabaseError
            mock_user_exists.side_effect = DatabaseError("Database error")
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Check CORS headers are present
            assert 'headers' in response
            headers = response['headers']
            
            assert 'Access-Control-Allow-Origin' in headers
            assert 'Access-Control-Allow-Headers' in headers
            assert 'Access-Control-Allow-Methods' in headers
            assert 'Content-Type' in headers
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_cors_origin_allows_all(self, email):
        """
        Property: CORS origin should allow all origins (*).
        
        For any response, the Access-Control-Allow-Origin header should
        be set to "*" to allow requests from any origin.
        """
        # Mock dependencies
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
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (True, 'test-message-id-123', None)
            mock_email_class.return_value = mock_email
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Check CORS origin matches expected value
            expected_origin = get_expected_cors_origin()
            assert response['headers']['Access-Control-Allow-Origin'] == expected_origin
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_cors_methods_includes_post(self, email):
        """
        Property: CORS methods should include POST.
        
        For any response, the Access-Control-Allow-Methods header should
        include POST since the endpoint accepts POST requests.
        """
        # Mock dependencies
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
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (True, 'test-message-id-123', None)
            mock_email_class.return_value = mock_email
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Check CORS methods includes POST
            methods = response['headers']['Access-Control-Allow-Methods']
            assert 'POST' in methods
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_content_type_is_json(self, email):
        """
        Property: Content-Type should be application/json.
        
        For any response, the Content-Type header should be set to
        application/json since all responses are JSON.
        """
        # Mock dependencies
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
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (True, 'test-message-id-123', None)
            mock_email_class.return_value = mock_email
            
            event = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            
            response = lambda_handler(event, None)
            
            # Check Content-Type is application/json
            assert response['headers']['Content-Type'] == 'application/json'
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_cors_headers_consistent_across_response_types(self, email):
        """
        Property: CORS headers should be consistent across all response types.
        
        For any response type (success, error), the CORS headers should be
        identical to ensure consistent behavior.
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.store_reset_token') as mock_store, \
             patch('password_recovery.forgot_password_handler.EmailService') as mock_email_class:
            
            # Setup mocks for success
            mock_rate_limiter = Mock()
            mock_rate_limiter.check_rate_limit.return_value = (True, None)
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            mock_user_exists.return_value = True
            
            mock_token_gen = Mock()
            mock_token_gen.generate_reset_token.return_value = ('token', 'hash', Mock())
            mock_token_gen_class.return_value = mock_token_gen
            
            mock_email = Mock()
            mock_email.send_reset_email.return_value = (True, 'test-message-id-123', None)
            mock_email_class.return_value = mock_email
            
            # Get success response
            event_success = {
                'body': json.dumps({'email': email}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
            }
            response_success = lambda_handler(event_success, None)
            
            # Get validation error response
            event_error = {
                'body': json.dumps({'email': ''}),
                'requestContext': {'identity': {'sourceIp': '192.168.1.2'}}
            }
            response_error = lambda_handler(event_error, None)
            
            # CORS headers should be the same (excluding Retry-After which is specific to 429)
            cors_headers_success = {
                k: v for k, v in response_success['headers'].items()
                if k.startswith('Access-Control') or k == 'Content-Type'
            }
            cors_headers_error = {
                k: v for k, v in response_error['headers'].items()
                if k.startswith('Access-Control') or k == 'Content-Type'
            }
            
            assert cors_headers_success == cors_headers_error
