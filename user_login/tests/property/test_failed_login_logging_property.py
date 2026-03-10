"""
Property-based tests for failed login attempt logging.

**Validates: Requirements 7.4, 9.5**

Property 14: Failed login attempt logging
For any failed authentication attempt, the endpoint should log the attempt
with the email address and outcome for security monitoring.
"""

import json
import bcrypt
from unittest.mock import patch
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails
from user_login.app import lambda_handler


@settings(max_examples=10)
@given(
    email=emails(),
    password=st.text(min_size=1, max_size=50)
)
def test_failed_login_user_not_found_logged_property(email, password):
    """
    Property 14: Failed login attempt logging - User Not Found
    
    For any failed login due to non-existent user, the attempt should be
    logged with the email address for security monitoring.
    
    **Validates: Requirements 7.4, 9.5**
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
            
            # Verify that failed login was logged with email
            warning_calls = [call for call in mock_logger.warning.call_args_list]
            assert len(warning_calls) > 0, "Failed login should be logged"
            
            # Check that email is in the log
            warning_log_str = str(warning_calls)
            assert email in warning_log_str, \
                "Failed login log should contain email for security monitoring"
            assert "Failed login attempt" in warning_log_str or "failed" in warning_log_str.lower(), \
                "Log should indicate failed login attempt"


@settings(max_examples=10)
@given(
    email=emails(),
    correct_password=st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=10, max_size=30),
    wrong_password=st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=10, max_size=30)
)
def test_failed_login_incorrect_password_logged_property(email, correct_password, wrong_password):
    """
    Property 14: Failed login attempt logging - Incorrect Password
    
    For any failed login due to incorrect password, the attempt should be
    logged with the email address for security monitoring.
    
    **Validates: Requirements 7.4, 9.5**
    """
    # Skip if passwords are the same
    if correct_password == wrong_password:
        return
    
    # Generate password hash for correct password
    password_hash = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
    
    # Create event with wrong password
    event = {
        'body': json.dumps({
            'email': email,
            'password': wrong_password
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
            
            # Verify 401 response
            assert response['statusCode'] == 401
            
            # Verify that failed login was logged with email
            warning_calls = [call for call in mock_logger.warning.call_args_list]
            assert len(warning_calls) > 0, "Failed login should be logged"
            
            # Check that email is in the log
            warning_log_str = str(warning_calls)
            assert email in warning_log_str, \
                "Failed login log should contain email for security monitoring"
            assert "Failed login attempt" in warning_log_str or "incorrect password" in warning_log_str.lower(), \
                "Log should indicate failed login attempt"


@settings(max_examples=10)
@given(
    email=emails(),
    password=st.text(min_size=1, max_size=50)
)
def test_failed_login_outcome_logged_property(email, password):
    """
    Property 14: Failed login attempt logging - Outcome
    
    For any failed login, the log should include the outcome (e.g., user not found,
    incorrect password) for security analysis.
    
    **Validates: Requirements 7.4, 9.5**
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
            lambda_handler(event, context)
            
            # Verify that outcome is logged
            warning_calls = [call for call in mock_logger.warning.call_args_list]
            warning_log_str = str(warning_calls)
            
            # Should indicate the reason for failure
            assert "user not found" in warning_log_str.lower() or "failed" in warning_log_str.lower(), \
                "Log should indicate the outcome/reason for failed login"


@settings(max_examples=10)
@given(
    email=emails(),
    password=st.text(min_size=1, max_size=50)
)
def test_multiple_failed_logins_all_logged_property(email, password):
    """
    Property 14: Failed login attempt logging - Multiple Attempts
    
    For multiple failed login attempts, each should be logged for future
    rate limiting implementation.
    
    **Validates: Requirements 7.4, 9.5**
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
            
            # Make 3 failed login attempts
            for _ in range(3):
                lambda_handler(event, context)
            
            # Verify that all 3 attempts were logged
            warning_calls = [call for call in mock_logger.warning.call_args_list]
            failed_login_logs = [call for call in warning_calls if "Failed login attempt" in str(call)]
            
            assert len(failed_login_logs) >= 3, \
                "All failed login attempts should be logged"
