"""
Property-based tests for email delivery.

Feature: password-recovery
Property 4: Email Delivery for Valid Requests

**Validates: Requirements 1.8, 6.1, 6.2, 6.3**

For any registered user requesting a password reset, the Email_Service should 
be invoked with the user's email address, the plaintext reset token, and the 
expiration timestamp.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from hypothesis import given, strategies as st, settings, assume
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


class TestEmailDeliveryProperty:
    """Property-based tests for email delivery."""
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_email_sent_with_correct_parameters(self, email, token):
        """
        Property: Email should be sent with correct recipient, token, and expiration.
        
        For any valid email and token, the email service should invoke SES
        with the correct parameters.
        """
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        result = service.send_reset_email(email, token, expiration)
        
        # Should return True for successful send
        success, message_id, error_code = result
        assert success is True
        
        # Verify SES was called
        mock_ses.send_email.assert_called_once()
        call_args = mock_ses.send_email.call_args
        
        # Verify recipient
        assert call_args[1]['Destination']['ToAddresses'] == [email]
        
        # Verify token is in the email body
        body_text = call_args[1]['Message']['Body']['Text']['Data']
        body_html = call_args[1]['Message']['Body']['Html']['Data']
        assert token in body_text
        assert token in body_html
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_email_contains_reset_link(self, email, token):
        """
        Property: Email should contain a reset link with the token.
        
        For any email and token, the email body should contain a properly
        formatted reset link including the token.
        """
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        service = EmailService(ses_client=mock_ses, base_url='https://example.com')
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        service.send_reset_email(email, token, expiration)
        
        call_args = mock_ses.send_email.call_args
        body_text = call_args[1]['Message']['Body']['Text']['Data']
        body_html = call_args[1]['Message']['Body']['Html']['Data']
        
        # Verify reset link format
        expected_link = f"https://example.com/reset-password?token={token}"
        assert expected_link in body_text
        assert expected_link in body_html
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_email_contains_expiration_time(self, email, token):
        """
        Property: Email should include the expiration time.
        
        For any email and token, the email body should include the expiration
        timestamp so users know how long the link is valid.
        """
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        service.send_reset_email(email, token, expiration)
        
        call_args = mock_ses.send_email.call_args
        body_text = call_args[1]['Message']['Body']['Text']['Data']
        body_html = call_args[1]['Message']['Body']['Html']['Data']
        
        # Verify expiration is mentioned
        expiration_str = expiration.strftime('%Y-%m-%d %H:%M:%S UTC')
        assert expiration_str in body_text
        assert expiration_str in body_html
        assert 'expire' in body_text.lower()
        assert 'expire' in body_html.lower()
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_email_contains_security_notice(self, email, token):
        """
        Property: Email should contain security notice.
        
        For any email, the body should include a security notice telling users
        to ignore the email if they didn't request it.
        """
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        service.send_reset_email(email, token, expiration)
        
        call_args = mock_ses.send_email.call_args
        body_text = call_args[1]['Message']['Body']['Text']['Data']
        body_html = call_args[1]['Message']['Body']['Html']['Data']
        
        # Verify security notice
        assert 'did not request' in body_text.lower() or 'didn\'t request' in body_text.lower()
        assert 'ignore' in body_text.lower()
        assert 'did not request' in body_html.lower() or 'didn\'t request' in body_html.lower()
        assert 'ignore' in body_html.lower()
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_email_has_both_text_and_html_versions(self, email, token):
        """
        Property: Email should have both text and HTML versions.
        
        For any email, both plain text and HTML versions should be provided
        for better compatibility with different email clients.
        """
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        service.send_reset_email(email, token, expiration)
        
        call_args = mock_ses.send_email.call_args
        message_body = call_args[1]['Message']['Body']
        
        # Both versions should be present
        assert 'Text' in message_body
        assert 'Html' in message_body
        
        # Both should have content
        assert len(message_body['Text']['Data']) > 0
        assert len(message_body['Html']['Data']) > 0
        
        # Both should contain the token
        assert token in message_body['Text']['Data']
        assert token in message_body['Html']['Data']
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_email_subject_is_descriptive(self, email, token):
        """
        Property: Email subject should be clear and descriptive.
        
        For any email, the subject line should clearly indicate it's a
        password reset request.
        """
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        service.send_reset_email(email, token, expiration)
        
        call_args = mock_ses.send_email.call_args
        subject = call_args[1]['Message']['Subject']['Data']
        
        # Subject should mention password reset
        assert 'password' in subject.lower()
        assert 'reset' in subject.lower()
        # Subject should not be empty
        assert len(subject) > 0
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_from_email_is_set(self, email, token):
        """
        Property: Email should have a valid from address.
        
        For any email, the from address should be set to a valid email address.
        """
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        from_email = 'noreply@example.com'
        service = EmailService(ses_client=mock_ses, from_email=from_email)
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        service.send_reset_email(email, token, expiration)
        
        call_args = mock_ses.send_email.call_args
        source = call_args[1]['Source']
        
        # From address should be set
        assert source == from_email
        assert '@' in source
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_successful_send_returns_true(self, email, token):
        """
        Property: Successful email delivery should return True.
        
        For any successful SES send_email call, the service should return True.
        """
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        result = service.send_reset_email(email, token, expiration)
        
        success, message_id, error_code = result
        assert success is True
    
    @given(valid_emails(), reset_tokens())
    @settings(max_examples=100)
    def test_ses_error_returns_false(self, email, token):
        """
        Property: SES errors should return False without raising exceptions.
        
        For any SES error, the service should return False and log the error
        without raising an exception.
        """
        mock_ses = Mock()
        from botocore.exceptions import ClientError
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Email rejected'}},
            'SendEmail'
        )
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        result = service.send_reset_email(email, token, expiration)
        
        # Should return False on error
        success, message_id, error_code = result
        assert success is False
        # Should not raise an exception
