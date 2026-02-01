"""
Integration tests for Lambda handler.

These tests verify the end-to-end flow of the login endpoint with mocked
DynamoDB and all components integrated.
"""

import json
import bcrypt
import pytest
from unittest.mock import patch, MagicMock
from user_login.app import lambda_handler
from user_registration.user_repository import UserNotFoundError, DatabaseError


class TestLambdaHandlerIntegration:
    """Integration tests for the Lambda handler."""
    
    def test_successful_login_end_to_end(self):
        """
        Test successful login with all components integrated.
        
        Validates: Requirements 1.1, 1.2, 1.4, 4.1, 4.3, 5.1, 6.1
        """
        email = "user@example.com"
        password = "SecurePass123!"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'email': email,
                'password': password
            })
        }
        context = {}
        
        # Mock database to return user
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            mock_get_user.return_value = {
                'email': email,
                'name': 'Test User',
                'password_hash': password_hash,
                'created_at': '2024-01-01T00:00:00Z'
            }
            
            # Call lambda handler
            response = lambda_handler(event, context)
            
            # Verify response
            assert response['statusCode'] == 200
            assert 'headers' in response
            assert 'body' in response
            
            body = json.loads(response['body'])
            assert body['message'] == 'Login successful'
            assert body['email'] == email
            assert 'token' in body
            assert len(body['token']) == 64  # 32 bytes in hex
            assert 'password' not in body
            assert 'password_hash' not in body
    
    def test_login_with_non_existent_user(self):
        """
        Test login with non-existent user returns 401 with generic message.
        
        Validates: Requirements 3.2, 6.4, 6.5, 7.1
        """
        email = "nonexistent@example.com"
        password = "SomePassword123!"
        
        event = {
            'body': json.dumps({
                'email': email,
                'password': password
            })
        }
        context = {}
        
        # Mock database to raise UserNotFoundError
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            mock_get_user.side_effect = UserNotFoundError("User not found")
            
            # Call lambda handler
            response = lambda_handler(event, context)
            
            # Verify response
            assert response['statusCode'] == 401
            body = json.loads(response['body'])
            assert body['error'] == 'Invalid credentials'
            # Should not reveal that user doesn't exist
            assert 'not found' not in body['error'].lower()
            assert 'does not exist' not in body['error'].lower()
    
    def test_login_with_incorrect_password(self):
        """
        Test login with incorrect password returns 401 with generic message.
        
        Validates: Requirements 4.2, 6.4, 6.5, 7.1
        """
        email = "user@example.com"
        correct_password = "CorrectPass123!"
        wrong_password = "WrongPass456!"
        password_hash = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'email': email,
                'password': wrong_password
            })
        }
        context = {}
        
        # Mock database to return user
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            mock_get_user.return_value = {
                'email': email,
                'name': 'Test User',
                'password_hash': password_hash,
                'created_at': '2024-01-01T00:00:00Z'
            }
            
            # Call lambda handler
            response = lambda_handler(event, context)
            
            # Verify response
            assert response['statusCode'] == 401
            body = json.loads(response['body'])
            assert body['error'] == 'Invalid credentials'
            # Should not reveal that password was incorrect
            assert 'password' not in body['error'].lower()
            assert 'incorrect' not in body['error'].lower()
    
    def test_login_with_invalid_email_format(self):
        """
        Test login with invalid email format returns 400.
        
        Validates: Requirements 2.1, 2.2, 6.3
        """
        event = {
            'body': json.dumps({
                'email': 'invalid-email',
                'password': 'SomePassword123!'
            })
        }
        context = {}
        
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Validation failed' in body['error']
        assert 'email' in body['error'].lower()
    
    def test_login_with_missing_email(self):
        """
        Test login with missing email returns 400.
        
        Validates: Requirements 1.3, 6.3
        """
        event = {
            'body': json.dumps({
                'password': 'SomePassword123!'
            })
        }
        context = {}
        
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Validation failed' in body['error']
        assert 'email' in body['error'].lower()
    
    def test_login_with_missing_password(self):
        """
        Test login with missing password returns 400.
        
        Validates: Requirements 1.3, 6.3
        """
        event = {
            'body': json.dumps({
                'email': 'user@example.com'
            })
        }
        context = {}
        
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Validation failed' in body['error']
        assert 'password' in body['error'].lower()
    
    def test_login_with_missing_both_fields(self):
        """
        Test login with both fields missing returns 400.
        
        Validates: Requirements 1.3, 6.3
        """
        event = {
            'body': json.dumps({})
        }
        context = {}
        
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Validation failed' in body['error']
    
    def test_login_with_empty_password(self):
        """
        Test login with empty password returns 400.
        
        Validates: Requirements 2.3, 2.4, 6.3
        """
        event = {
            'body': json.dumps({
                'email': 'user@example.com',
                'password': ''
            })
        }
        context = {}
        
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Validation failed' in body['error']
        assert 'password' in body['error'].lower()
    
    def test_database_failure_handling(self):
        """
        Test that database failures return 500.
        
        Validates: Requirements 3.3, 6.6, 9.3
        """
        email = "user@example.com"
        password = "SecurePass123!"
        
        event = {
            'body': json.dumps({
                'email': email,
                'password': password
            })
        }
        context = {}
        
        # Mock database to raise DatabaseError
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            mock_get_user.side_effect = DatabaseError("Connection failed")
            
            # Call lambda handler
            response = lambda_handler(event, context)
            
            # Verify response
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['error'] == 'Internal server error'
            # Should not reveal internal details
            assert 'Connection' not in body['error']
            assert 'Database' not in body['error']
    
    def test_generic_error_messages_are_identical(self):
        """
        Test that non-existent user and incorrect password return identical messages.
        
        This prevents user enumeration attacks.
        
        Validates: Requirements 6.4, 6.5, 7.1
        """
        email = "user@example.com"
        password = "SomePassword123!"
        
        # Test 1: Non-existent user
        event1 = {
            'body': json.dumps({
                'email': email,
                'password': password
            })
        }
        
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            mock_get_user.side_effect = UserNotFoundError("User not found")
            response1 = lambda_handler(event1, {})
        
        # Test 2: Incorrect password
        correct_password = "CorrectPass123!"
        password_hash = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
        
        event2 = {
            'body': json.dumps({
                'email': email,
                'password': password
            })
        }
        
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            mock_get_user.return_value = {
                'email': email,
                'name': 'Test User',
                'password_hash': password_hash,
                'created_at': '2024-01-01T00:00:00Z'
            }
            response2 = lambda_handler(event2, {})
        
        # Both should return 401 with identical error message
        assert response1['statusCode'] == 401
        assert response2['statusCode'] == 401
        
        body1 = json.loads(response1['body'])
        body2 = json.loads(response2['body'])
        
        assert body1['error'] == body2['error'] == 'Invalid credentials'
    
    def test_cors_headers_in_all_responses(self):
        """
        Test that CORS headers are present in all responses.
        
        Validates: Requirements 6.7
        """
        email = "user@example.com"
        password = "SecurePass123!"
        
        # Test success response
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
        event = {
            'body': json.dumps({
                'email': email,
                'password': password
            })
        }
        
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            mock_get_user.return_value = {
                'email': email,
                'name': 'Test User',
                'password_hash': password_hash,
                'created_at': '2024-01-01T00:00:00Z'
            }
            success_response = lambda_handler(event, {})
        
        # Test error response
        event_error = {
            'body': json.dumps({
                'email': 'invalid-email',
                'password': password
            })
        }
        error_response = lambda_handler(event_error, {})
        
        # Verify CORS headers in both responses
        for response in [success_response, error_response]:
            assert 'headers' in response
            headers = response['headers']
            assert 'Access-Control-Allow-Origin' in headers
            assert 'Access-Control-Allow-Headers' in headers
            assert 'Access-Control-Allow-Methods' in headers
            assert 'Content-Type' in headers
    
    def test_invalid_json_in_request_body(self):
        """
        Test that invalid JSON returns 400.
        
        Validates: Requirements 1.1, 1.2, 6.3
        """
        event = {
            'body': 'invalid json {'
        }
        context = {}
        
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'JSON' in body['error'] or 'json' in body['error']
