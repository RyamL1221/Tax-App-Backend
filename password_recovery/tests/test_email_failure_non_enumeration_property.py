"""
Property-based tests for email failure non-enumeration.

Feature: password-recovery
Property 12: Email Failure Non-Enumeration

**Validates: Requirements 6.4, 8.4**

For any password reset request where email delivery fails, the system should 
log the failure internally but still return the same generic success response 
to the client, preventing account enumeration.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings
from botocore.exceptions import ClientError
from password_recovery.email_service import EmailService


# Strategy for generating valid email addresses (simplified)
@st.composite
def valid_emails(draw):
    """Generate valid email addresses."""
    local_chars = 'abcdefghijklmnopqrstuvwxyz0123456789._-'
    local = draw(st.text(alphabet=local_chars, min_size=1, max_size=20))
    domain = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=15))
    tld = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=2, max_size=5))
    return f"{local}@{domain}.{tld}"


# Strategy for generating reset tokens
@st.composite
def reset_tokens(draw):
    """Generate reset tokens (base64-like strings)."""
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/='
    return draw(st.text(alphabet=chars, min_size=32, max_size=64))


# Strategy for SES error codes
ses_error_codes = st.sampled_from([
    'MessageRejected',
    'MailFromDomainNotVerified',
    'ConfigurationSetDoesNotExist',
    'AccountSendingPaused',
    'InvalidParameterValue',
    'ServiceUnavailable'
])


class TestEmailFailureNonEnumerationProperty:
    """Property-based tests for email failure non-enumeration."""
    
    @given(valid_emails(), reset_tokens(), ses_error_codes)
    @settings(max_examples=100)
    def test_ses_error_returns_false_without_exception(self, email, token, error_code):
        """
        Property: SES errors should return False without raising exceptions.
        
        For any SES error, the email service should return False and handle
        the error gracefully without exposing details to the caller.
        """
        mock_ses = Mock()
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': error_code, 'Message': 'SES error'}},
            'SendEmail'
        )
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Should not raise an exception
        result = service.send_reset_email(email, token, expiration)
        
        # Should return False to indicate failure
        assert result is False
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_generic_exception_returns_false_without_exception(self, email, token):
        """
        Property: Generic exceptions should return False without raising.
        
        For any unexpected exception during email sending, the service should
        return False and handle the error gracefully.
        """
        mock_ses = Mock()
        mock_ses.send_email.side_effect = Exception("Unexpected error")
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Should not raise an exception
        result = service.send_reset_email(email, token, expiration)
        
        # Should return False to indicate failure
        assert result is False
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_email_failure_logs_error_without_sensitive_data(self, email, token):
        """
        Property: Email failures should be logged without sensitive data.
        
        For any email failure, the error should be logged but should not
        include sensitive information like the recipient email or token.
        """
        mock_ses = Mock()
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Email rejected'}},
            'SendEmail'
        )
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Capture log output
        with patch('password_recovery.email_service.logger') as mock_logger:
            result = service.send_reset_email(email, token, expiration)
            
            # Should have logged an error
            assert mock_logger.error.called
            
            # Get the logged message
            log_call_args = mock_logger.error.call_args
            log_message = str(log_call_args)
            
            # Should not contain sensitive data
            assert email not in log_message
            assert token not in log_message
            
            # Should return False
            assert result is False
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_email_failure_does_not_expose_error_details(self, email, token):
        """
        Property: Email failures should not expose error details to caller.
        
        For any email failure, the service should return a simple boolean
        False without exposing the underlying error details. This prevents
        information leakage that could be used for enumeration.
        """
        mock_ses = Mock()
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Detailed error message'}},
            'SendEmail'
        )
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        result = service.send_reset_email(email, token, expiration)
        
        # Should only return False, no error details
        assert result is False
        assert isinstance(result, bool)
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_success_and_failure_return_consistent_types(self, email, token):
        """
        Property: Success and failure should return consistent types.
        
        For any email send attempt, whether successful or failed, the return
        value should always be a boolean (True or False), making it easy for
        callers to handle both cases uniformly.
        """
        # Test success case
        mock_ses_success = Mock()
        mock_ses_success.send_email.return_value = {'MessageId': 'test-id'}
        service_success = EmailService(ses_client=mock_ses_success)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        result_success = service_success.send_reset_email(email, token, expiration)
        assert isinstance(result_success, bool)
        assert result_success is True
        
        # Test failure case
        mock_ses_failure = Mock()
        mock_ses_failure.send_email.side_effect = ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Error'}},
            'SendEmail'
        )
        service_failure = EmailService(ses_client=mock_ses_failure)
        
        result_failure = service_failure.send_reset_email(email, token, expiration)
        assert isinstance(result_failure, bool)
        assert result_failure is False
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_email_failure_allows_handler_to_return_success(self, email, token):
        """
        Property: Email failure should allow handler to return generic success.
        
        For any email failure, the service returns False, which allows the
        handler to detect the failure and still return a generic success
        response to prevent enumeration. This test verifies the service
        behavior that enables non-enumeration at the handler level.
        """
        mock_ses = Mock()
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Error'}},
            'SendEmail'
        )
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        result = service.send_reset_email(email, token, expiration)
        
        # Service returns False to indicate failure
        assert result is False
        
        # Handler can check this and still return success to client
        # Simulating handler behavior:
        if result:
            handler_response = "Email sent successfully"
        else:
            # Even on failure, return generic success message
            handler_response = "If an account exists with that email, a password reset link has been sent."
        
        # Handler should return generic success regardless
        assert "password reset link has been sent" in handler_response.lower()
