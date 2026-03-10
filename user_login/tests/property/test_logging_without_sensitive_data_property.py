"""
Property-based tests for logging without sensitive data.

**Validates: Requirements 7.3, 9.2**

Property 13: Logging without sensitive data
For any request processed or error that occurs, the endpoint should log
relevant details (email, outcome, error type, context) but never log
sensitive information such as passwords or password hashes.
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
    password=st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=10, max_size=30)
)
def test_password_not_logged_on_success_property(email, password):
    """
    Property 13: Logging without sensitive data - Success Case
    
    For any successful login, the password should never be logged.
    
    **Validates: Requirements 7.3, 9.2**
    """
    # Skip if password is a substring of email (would cause false positive)
    if password in email:
        return
    
    # Generate password hash (ASCII only, no truncation needed)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
    
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
            
            # Collect all log calls
            all_log_calls = []
            all_log_calls.extend(mock_logger.info.call_args_list)
            all_log_calls.extend(mock_logger.warning.call_args_list)
            all_log_calls.extend(mock_logger.error.call_args_list)
            
            # Verify password is not in any log
            all_logs_str = str(all_log_calls)
            assert password not in all_logs_str, \
                "Password should never be logged"
            assert password_hash not in all_logs_str, \
                "Password hash should never be logged"


@settings(max_examples=10)
@given(
    email=emails(),
    password=st.text(min_size=1, max_size=50)
)
def test_password_not_logged_on_failure_property(email, password):
    """
    Property 13: Logging without sensitive data - Failure Case
    
    For any failed login, the password should never be logged.
    
    **Validates: Requirements 7.3, 9.2**
    """
    # Skip if password is a substring of email (would cause false positive)
    if password in email:
        return
    
    # Skip if password is too short or is a common substring (like "emai" in "email")
    if len(password) <= 4:
        return
    
    # Skip if password is a substring of common log words
    common_log_words = ['email', 'login', 'failed', 'attempt', 'user', 'found', 'call', 'info', 'warning', 'error']
    if any(password.lower() in word for word in common_log_words):
        return
    
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
            
            # Collect all log calls
            all_log_calls = []
            all_log_calls.extend(mock_logger.info.call_args_list)
            all_log_calls.extend(mock_logger.warning.call_args_list)
            all_log_calls.extend(mock_logger.error.call_args_list)
            
            # Verify password is not in any log
            all_logs_str = str(all_log_calls)
            assert password not in all_logs_str, \
                "Password should never be logged"


@settings(max_examples=10)
@given(
    email=emails(),
    password=st.text(min_size=8, max_size=50)
)
def test_email_is_logged_but_not_password_property(email, password):
    """
    Property 13: Logging without sensitive data - Email vs Password
    
    For any login attempt, the email should be logged (for security monitoring)
    but the password should never be logged.
    
    **Validates: Requirements 7.3, 9.2**
    """
    # Skip if password is a substring of email (would cause false positive)
    if password in email:
        return
    
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
            
            # Collect all log calls
            all_log_calls = []
            all_log_calls.extend(mock_logger.info.call_args_list)
            all_log_calls.extend(mock_logger.warning.call_args_list)
            all_log_calls.extend(mock_logger.error.call_args_list)
            
            all_logs_str = str(all_log_calls)
            
            # Email should be logged (for security monitoring)
            assert email in all_logs_str, \
                "Email should be logged for security monitoring"
            
            # Password should NOT be logged
            if len(password) > 3:
                assert password not in all_logs_str, \
                    "Password should never be logged"


@settings(max_examples=10)
@given(
    email=emails(),
    password=st.text(min_size=8, max_size=50)
)
def test_password_hash_not_logged_property(email, password):
    """
    Property 13: Logging without sensitive data - Password Hash
    
    For any login attempt, password hashes should never be logged.
    
    **Validates: Requirements 7.3, 9.2**
    """
    # Truncate password to 72 bytes for bcrypt
    password_bytes = password.encode('utf-8')[:72]
    truncated_password = password_bytes.decode('utf-8', errors='ignore')
    
    # Generate password hash
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=4)).decode('utf-8')
    
    # Create event
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
            lambda_handler(event, context)
            
            # Collect all log calls
            all_log_calls = []
            all_log_calls.extend(mock_logger.info.call_args_list)
            all_log_calls.extend(mock_logger.warning.call_args_list)
            all_log_calls.extend(mock_logger.error.call_args_list)
            
            # Verify password hash is not in any log
            all_logs_str = str(all_log_calls)
            assert password_hash not in all_logs_str, \
                "Password hash should never be logged"
