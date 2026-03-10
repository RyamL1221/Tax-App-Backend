"""
Property-based tests for error logging with context.

**Validates: Requirements 9.1**

Property 16: Error logging with context
For any error that occurs, the endpoint should log error details including
timestamp, error type, and relevant context.
"""

import json
from unittest.mock import patch
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails
from user_login.app import lambda_handler


@settings(max_examples=10)
@given(
    email=emails(),
    password=st.text(min_size=1, max_size=50)
)
def test_database_error_logged_with_context_property(email, password):
    """
    Property 16: Error logging with context - Database Error
    
    For any database error, the endpoint should log the error with context
    including the error type and relevant details.
    
    **Validates: Requirements 9.1**
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
        # Mock database to raise DatabaseError
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            from user_registration.user_repository import DatabaseError
            mock_get_user.side_effect = DatabaseError("Connection failed")
            
            # Call lambda handler
            response = lambda_handler(event, context)
            
            # Verify 500 response
            assert response['statusCode'] == 500
            
            # Verify that error was logged with context
            error_calls = [call for call in mock_logger.error.call_args_list]
            assert len(error_calls) > 0, "Error should be logged"
            
            # Check that error log contains context (email and error details)
            error_log_str = str(error_calls)
            assert email in error_log_str, "Error log should contain email for context"
            assert "Database error" in error_log_str or "database" in error_log_str.lower(), \
                "Error log should indicate database error"


@settings(max_examples=10)
@given(email=st.text(min_size=1, max_size=100))
def test_validation_error_logged_with_context_property(email):
    """
    Property 16: Error logging with context - Validation Error
    
    For any validation error, the endpoint should log the error with context.
    
    **Validates: Requirements 9.1**
    """
    # Create event with invalid data (missing password)
    event = {
        'body': json.dumps({
            'email': email,
            'password': ''
        })
    }
    context = {}
    
    # Mock logger to capture log calls
    with patch('user_login.app.logger') as mock_logger:
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Verify 400 response
        assert response['statusCode'] == 400
        
        # Verify that validation error was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list]
        assert len(warning_calls) > 0, "Validation error should be logged"


@settings(max_examples=10)
@given(
    email=emails(),
    password=st.text(min_size=1, max_size=50)
)
def test_unexpected_error_logged_with_context_property(email, password):
    """
    Property 16: Error logging with context - Unexpected Error
    
    For any unexpected error, the endpoint should log the error with full
    context including error type and traceback.
    
    **Validates: Requirements 9.1**
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
        # Mock get_user_by_email to raise an unexpected exception
        with patch('user_login.app.get_user_by_email') as mock_get_user:
            mock_get_user.side_effect = RuntimeError("Unexpected error")
            
            # Call lambda handler
            response = lambda_handler(event, context)
            
            # Verify 500 response
            assert response['statusCode'] == 500
            
            # Verify that unexpected error was logged
            error_calls = [call for call in mock_logger.error.call_args_list]
            assert len(error_calls) > 0, "Unexpected error should be logged"
            
            # Check that error log contains error type
            error_log_str = str(error_calls)
            assert "RuntimeError" in error_log_str or "Unexpected" in error_log_str, \
                "Error log should contain error type"
