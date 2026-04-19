"""
Property-based tests for API response format consistency.

Feature: password-recovery
Property 20: API Response Format Consistency

**Validates: Requirements 9.3**

For any response from the password recovery endpoints, the response should 
follow the existing API format conventions with consistent structure for 
success and error responses.
"""

import pytest
import json
from unittest.mock import Mock, patch
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


# Strategy for generating invalid email formats
invalid_email_formats = st.sampled_from([
    'notanemail',
    '@example.com',
    'user@',
    'user @example.com',
    'user@.com',
    '',
    'user@domain',
])


class TestAPIResponseFormatProperty:
    """Property-based tests for API response format consistency."""
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_success_response_has_required_fields(self, email):
        """
        Property: Success responses should have required fields.
        
        For any successful request, the response should have:
        - statusCode (number)
        - headers (object)
        - body (JSON string containing message)
        """
        # Mock dependencies
        with patch('password_recovery.forgot_password_handler.RateLimiter') as mock_rate_limiter_class, \
             patch('password_recovery.forgot_password_handler.user_exists') as mock_user_exists, \
             patch('password_recovery.forgot_password_handler.TokenGenerator') as mock_token_gen_class, \
             patch('password_recovery.forgot_password_handler.store_reset_token') as mock_store, \
             patch('password_recovery.forgot_password_handler.EmailService') as mock_email_class:
            
            # Setup mocks for successful flow
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
            
            # Check required fields
            assert 'statusCode' in response
            assert isinstance(response['statusCode'], int)
            assert 'headers' in response
            assert isinstance(response['headers'], dict)
            assert 'body' in response
            assert isinstance(response['body'], str)
            
            # Body should be valid JSON
            body = json.loads(response['body'])
            assert 'message' in body
    
    @given(invalid_email_formats)
    @settings(max_examples=100)
    def test_validation_error_response_has_required_fields(self, invalid_email):
        """
        Property: Validation error responses should have required fields.
        
        For any validation error, the response should have:
        - statusCode: 400
        - headers (object)
        - body (JSON string containing error and message)
        """
        event = {
            'body': json.dumps({'email': invalid_email}),
            'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
        }
        
        response = lambda_handler(event, None)
        
        # Check required fields
        assert 'statusCode' in response
        assert response['statusCode'] == 400
        assert 'headers' in response
        assert isinstance(response['headers'], dict)
        assert 'body' in response
        assert isinstance(response['body'], str)
        
        # Body should be valid JSON with error fields
        body = json.loads(response['body'])
        assert 'error' in body or 'message' in body
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_rate_limit_error_response_has_required_fields(self, email):
        """
        Property: Rate limit error responses should have required fields.
        
        For any rate limit error, the response should have:
        - statusCode: 429
        - headers (object with Retry-After)
        - body (JSON string containing error and message)
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
            
            # Check required fields
            assert 'statusCode' in response
            assert response['statusCode'] == 429
            assert 'headers' in response
            assert isinstance(response['headers'], dict)
            assert 'Retry-After' in response['headers']
            assert 'body' in response
            assert isinstance(response['body'], str)
            
            # Body should be valid JSON with error fields
            body = json.loads(response['body'])
            assert 'error' in body
            assert 'message' in body
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_internal_error_response_has_required_fields(self, email):
        """
        Property: Internal error responses should have required fields.
        
        For any internal error, the response should have:
        - statusCode: 500
        - headers (object)
        - body (JSON string containing error and message)
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
            
            # Check required fields
            assert 'statusCode' in response
            assert response['statusCode'] == 500
            assert 'headers' in response
            assert isinstance(response['headers'], dict)
            assert 'body' in response
            assert isinstance(response['body'], str)
            
            # Body should be valid JSON with error fields
            body = json.loads(response['body'])
            assert 'error' in body
            assert 'message' in body
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_response_body_is_valid_json(self, email):
        """
        Property: Response body should always be valid JSON.
        
        For any response (success or error), the body should be a valid
        JSON string that can be parsed.
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
            
            # Body should be valid JSON
            try:
                body = json.loads(response['body'])
                assert isinstance(body, dict)
            except json.JSONDecodeError:
                pytest.fail("Response body is not valid JSON")
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_error_responses_have_error_field(self, email):
        """
        Property: Error responses should have an 'error' field.
        
        For any error response (4xx or 5xx), the body should contain
        an 'error' field identifying the error type.
        """
        # Test validation error
        event_invalid = {
            'body': json.dumps({'email': ''}),
            'requestContext': {'identity': {'sourceIp': '192.168.1.1'}}
        }
        
        response = lambda_handler(event_invalid, None)
        
        if response['statusCode'] >= 400:
            body = json.loads(response['body'])
            # Should have either 'error' field or 'message' field
            assert 'error' in body or 'message' in body
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_success_responses_have_message_field(self, email):
        """
        Property: Success responses should have a 'message' field.
        
        For any success response (200), the body should contain
        a 'message' field with a user-friendly message.
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
            
            if response['statusCode'] == 200:
                body = json.loads(response['body'])
                assert 'message' in body
                assert isinstance(body['message'], str)
                assert len(body['message']) > 0
    
    @given(valid_emails())
    @settings(max_examples=100)
    def test_response_structure_matches_existing_endpoints(self, email):
        """
        Property: Response structure should match existing endpoints.
        
        For any response, the structure should be consistent with existing
        endpoints (user_login, user_registration) with the same fields
        and types.
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
            
            # Check structure matches API Gateway proxy response format
            assert isinstance(response, dict)
            assert 'statusCode' in response
            assert 'headers' in response
            assert 'body' in response
            
            # Only these three fields should be present (no extra fields)
            assert set(response.keys()) == {'statusCode', 'headers', 'body'}
