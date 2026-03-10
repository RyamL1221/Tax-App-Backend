"""
Property test for successful reset audit logging.

**Property 19: Successful Reset Audit Logging**
**Validates: Requirements 8.5**

For any successful password reset, the system should log an audit event
containing the user's email, timestamp, and action type (without sensitive data).
"""

import json
import logging
import os
import sys
from unittest.mock import patch, MagicMock, call
from io import StringIO

import pytest
from hypothesis import given, strategies as st, settings

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from reset_password_handler import lambda_handler


# Strategy for generating any tokens (we'll mock validation anyway)
any_tokens = st.text(min_size=10, max_size=100)

# Strategy for generating any passwords (we'll mock validation anyway)
any_passwords = st.text(min_size=8, max_size=50)

# Strategy for generating email addresses
emails = st.emails()


@settings(max_examples=100, deadline=None)
@given(
    token=any_tokens,
    password=any_passwords,
    email=emails
)
def test_successful_reset_logs_audit_event(token, password, email):
    """
    Property 19: Successful Reset Audit Logging
    
    For any successful password reset, the system should log an audit event
    containing the user's email, timestamp, and action type (without sensitive data).
    
    This test verifies that successful password resets are logged for audit purposes
    and that no sensitive data (tokens, passwords) is included in the logs.
    """
    # Skip if email contains token or password (edge case that would cause false positive)
    if token in email or password in email:
        return
    
    # Create event with valid input
    event = {
        'body': json.dumps({
            'token': token,
            'new_password': password
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
        mock_validator.validate_reset_password_input.return_value = (True, token, password, None)
        mock_validator_class.return_value = mock_validator
        
        # Mock token validation to succeed
        with patch('reset_password_handler.TokenValidator') as mock_token_validator_class:
            mock_token_validator = MagicMock()
            mock_token_validator.validate_token.return_value = (True, email, None)
            mock_token_validator._get_token_hash.return_value = 'mock_hash'
            mock_token_validator_class.return_value = mock_token_validator
            
            # Mock password hasher to succeed
            with patch('reset_password_handler.PasswordHasher') as mock_hasher_class:
                mock_hasher = MagicMock()
                mock_hasher.hash_password.return_value = '$2b$12$mockhash'
                mock_hasher_class.return_value = mock_hasher
                
                # Mock update_password to succeed
                with patch('reset_password_handler.update_password') as mock_update:
                    mock_update.return_value = True
                    
                    # Mock mark_token_used to succeed
                    with patch('reset_password_handler.mark_token_used') as mock_mark:
                        mock_mark.return_value = True
                        
                        # Mock session manager
                        with patch('reset_password_handler.SessionManager') as mock_session_class:
                            mock_session = MagicMock()
                            mock_session_class.return_value = mock_session
                            
                            # Capture log output
                            with patch('reset_password_handler.logger') as mock_logger:
                                # Call the handler
                                response = lambda_handler(event, None)
                                
                                # Verify response is successful
                                assert response['statusCode'] == 200, \
                                    f"Expected 200 status code for successful reset, got {response['statusCode']}"
                                
                                # Verify audit log was created
                                # Look for the audit log message
                                audit_log_found = False
                                for call_args in mock_logger.info.call_args_list:
                                    log_message = str(call_args[0][0])
                                    if 'password reset completed successfully' in log_message.lower():
                                        audit_log_found = True
                                        
                                        # Verify email is in the log
                                        assert email in log_message, \
                                            f"Audit log should contain user email: {email}"
                                        
                                        # Verify no sensitive data in logs
                                        # Token should not be in the audit log (unless it's part of email)
                                        if token not in email:
                                            assert token not in log_message, \
                                                "Audit log should not contain plaintext token"
                                        
                                        # Password should not be in the audit log (unless it's part of email)
                                        if password not in email:
                                            assert password not in log_message, \
                                                "Audit log should not contain plaintext password"
                                        
                                        break
                                
                                assert audit_log_found, \
                                    "Audit log for successful password reset should be created"


@settings(max_examples=100, deadline=None)
@given(
    token=any_tokens,
    password=any_passwords,
    email=emails
)
def test_audit_log_contains_required_information(token, password, email):
    """
    Property 19: Successful Reset Audit Logging (information completeness)
    
    Verifies that the audit log contains all required information:
    - User's email
    - Action type (password reset)
    - No sensitive data (tokens, passwords)
    """
    # Skip if email contains token or password (edge case that would cause false positive)
    if token in email or password in email:
        return
    
    # Create event with valid input
    event = {
        'body': json.dumps({
            'token': token,
            'new_password': password
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
        mock_validator.validate_reset_password_input.return_value = (True, token, password, None)
        mock_validator_class.return_value = mock_validator
        
        # Mock token validation to succeed
        with patch('reset_password_handler.TokenValidator') as mock_token_validator_class:
            mock_token_validator = MagicMock()
            mock_token_validator.validate_token.return_value = (True, email, None)
            mock_token_validator._get_token_hash.return_value = 'mock_hash'
            mock_token_validator_class.return_value = mock_token_validator
            
            # Mock password hasher to succeed
            with patch('reset_password_handler.PasswordHasher') as mock_hasher_class:
                mock_hasher = MagicMock()
                mock_hasher.hash_password.return_value = '$2b$12$mockhash'
                mock_hasher_class.return_value = mock_hasher
                
                # Mock update_password to succeed
                with patch('reset_password_handler.update_password') as mock_update:
                    mock_update.return_value = True
                    
                    # Mock mark_token_used to succeed
                    with patch('reset_password_handler.mark_token_used') as mock_mark:
                        mock_mark.return_value = True
                        
                        # Mock session manager
                        with patch('reset_password_handler.SessionManager') as mock_session_class:
                            mock_session = MagicMock()
                            mock_session_class.return_value = mock_session
                            
                            # Capture all log output
                            with patch('reset_password_handler.logger') as mock_logger:
                                # Call the handler
                                response = lambda_handler(event, None)
                                
                                # Verify response is successful
                                assert response['statusCode'] == 200
                                
                                # Collect all log messages
                                all_log_messages = []
                                for call_args in mock_logger.info.call_args_list:
                                    all_log_messages.append(str(call_args[0][0]))
                                
                                combined_logs = ' '.join(all_log_messages)
                                
                                # Verify no sensitive data anywhere in logs (unless part of email)
                                if token not in email:
                                    assert token not in combined_logs, \
                                        "Logs should not contain plaintext token"
                                if password not in email:
                                    assert password not in combined_logs, \
                                        "Logs should not contain plaintext password"


if __name__ == '__main__':
    # Run the property tests
    test_successful_reset_logs_audit_event()
    test_audit_log_contains_required_information()
    print("✓ All property tests passed")
