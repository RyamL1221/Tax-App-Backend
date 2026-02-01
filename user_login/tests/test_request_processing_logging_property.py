"""
Property-based tests for request processing logging.

**Validates: Requirements 9.4**

Property 15: Request processing logging
For any request processed, the endpoint should log the request initiation
and completion with appropriate log levels.
"""

import json
import logging
import bcrypt
from unittest.mock import patch, MagicMock
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails
from user_login.app import lambda_handler


@settings(max_examples=50)
@given(
    email=emails(),
    password=st.text(min_size=8, max_size=50)
)
def test_request_initiation_logged_property(email, password):
    """
    Property 15: Request processing logging - Initiation
    
    For any request, the endpoint should log request initiation.
    
    **Validates: Requirements 9.4**
    """
    # Create event
    event = {
        'body': json.dumps({
            'email': email,
            'password': password
        })
    }
    context = {}
    
    # Mock logger to capture log calls
    with patch('user_login.app.logger') as mock_logger:
        # Mock database to avoid actual DB calls
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            # Make it raise UserNotFoundError to avoid password verification
            from user_registration.user_repository import UserNotFoundError
            mock_get_user.side_effect = UserNotFoundError("User not found")
            
            # Call lambda handler
            lambda_handler(event, context)
            
            # Verify that request initiation was logged
            info_calls = [call for call in mock_logger.info.call_args_list]
            assert any("Login request initiated" in str(call) for call in info_calls), \
                "Request initiation should be logged"


@settings(max_examples=50)
@given(
    email=emails(),
    password=st.text(min_size=8, max_size=50)
)
def test_successful_login_completion_logged_property(email, password):
    """
    Property 15: Request processing logging - Successful Completion
    
    For any successful login, the endpoint should log the completion.
    
    **Validates: Requirements 9.4**
    """
    # Truncate password to 72 bytes for bcrypt
    password_bytes = password.encode('utf-8')[:72]
    # Decode back to ensure we use the same password for both hashing and verification
    truncated_password = password_bytes.decode('utf-8', errors='ignore')
    
    # Generate password hash using the truncated password
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=4)).decode('utf-8')
    
    # Create event with the truncated password (same as what was hashed)
    event = {
        'body': json.dumps({
            'email': email,
            'password': truncated_password
        })
    }
    context = {}
    
    # Mock logger to capture log calls
    with patch('user_login.app.logger') as mock_logger:
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
            
            # Verify successful response
            assert response['statusCode'] == 200, \
                f"Expected 200, got {response['statusCode']}: {response.get('body', '')}"
            
            # Verify that successful login was logged
            info_calls = [call for call in mock_logger.info.call_args_list]
            assert any("Login successful" in str(call) and email in str(call) for call in info_calls), \
                "Successful login should be logged with email"


@settings(max_examples=50)
@given(
    email=emails(),
    password=st.text(min_size=1, max_size=50)
)
def test_failed_login_logged_property(email, password):
    """
    Property 15: Request processing logging - Failed Login
    
    For any failed login attempt, the endpoint should log the failure.
    
    **Validates: Requirements 9.4**
    """
    # Create event
    event = {
        'body': json.dumps({
            'email': email,
            'password': password
        })
    }
    context = {}
    
    # Mock logger to capture log calls
    with patch('user_login.app.logger') as mock_logger:
        # Mock database to raise UserNotFoundError
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            from user_registration.user_repository import UserNotFoundError
            mock_get_user.side_effect = UserNotFoundError("User not found")
            
            # Call lambda handler
            response = lambda_handler(event, context)
            
            # Verify 401 response
            assert response['statusCode'] == 401
            
            # Verify that failed login was logged
            warning_calls = [call for call in mock_logger.warning.call_args_list]
            assert any("Failed login attempt" in str(call) and email in str(call) for call in warning_calls), \
                "Failed login attempt should be logged with email"
