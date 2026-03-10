"""
Unit tests for EmailService.

Tests specific examples and edge cases for email sending functionality.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from password_recovery.email_service import EmailService


class TestEmailServiceUnit:
    """Unit tests for EmailService class."""
    
    def test_initialization_with_defaults(self):
        """Test EmailService initialization with default values."""
        mock_ses = Mock()
        with patch.dict('os.environ', {
            'FROM_EMAIL': 'test@example.com',
            'BASE_URL': 'https://test.example.com'
        }):
            service = EmailService(ses_client=mock_ses)
            assert service.from_email == 'test@example.com'
            assert service.base_url == 'https://test.example.com'
    
    def test_initialization_with_custom_values(self):
        """Test EmailService initialization with custom values."""
        mock_ses = Mock()
        service = EmailService(
            ses_client=mock_ses,
            from_email='custom@example.com',
            base_url='https://custom.example.com'
        )
        assert service.ses == mock_ses
        assert service.from_email == 'custom@example.com'
        assert service.base_url == 'https://custom.example.com'
    
    def test_send_reset_email_success(self):
        """Test successful email sending."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id-123'}
        
        service = EmailService(
            ses_client=mock_ses,
            from_email='noreply@example.com',
            base_url='https://example.com'
        )
        
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        result = service.send_reset_email(
            'user@example.com',
            'test-token-abc123',
            expiration
        )
        
        assert result is True
        mock_ses.send_email.assert_called_once()
    
    def test_send_reset_email_includes_correct_recipient(self):
        """Test that email is sent to correct recipient."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        service.send_reset_email('user@example.com', 'token123', expiration)
        
        call_args = mock_ses.send_email.call_args
        assert call_args[1]['Destination']['ToAddresses'] == ['user@example.com']
    
    def test_send_reset_email_includes_token_in_body(self):
        """Test that reset token is included in email body."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-id'}
        
        service = EmailService(ses_client=mock_ses, base_url='https://example.com')
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        token = 'unique-token-xyz789'
        
        service.send_reset_email('user@example.com', token, expiration)
        
        call_args = mock_ses.send_email.call_args
        body_text = call_args[1]['Message']['Body']['Text']['Data']
        body_html = call_args[1]['Message']['Body']['Html']['Data']
        
        assert token in body_text
        assert token in body_html
    
    def test_send_reset_email_includes_reset_link(self):
        """Test that reset link is properly formatted in email."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-id'}
        
        service = EmailService(ses_client=mock_ses, base_url='https://myapp.com')
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        token = 'token123'
        
        service.send_reset_email('user@example.com', token, expiration)
        
        call_args = mock_ses.send_email.call_args
        body_text = call_args[1]['Message']['Body']['Text']['Data']
        body_html = call_args[1]['Message']['Body']['Html']['Data']
        
        expected_link = 'https://myapp.com/reset-password?token=token123'
        assert expected_link in body_text
        assert expected_link in body_html
    
    def test_send_reset_email_includes_expiration_time(self):
        """Test that expiration time is included in email."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        service.send_reset_email('user@example.com', 'token123', expiration)
        
        call_args = mock_ses.send_email.call_args
        body_text = call_args[1]['Message']['Body']['Text']['Data']
        body_html = call_args[1]['Message']['Body']['Html']['Data']
        
        expiration_str = '2024-12-31 23:59:59 UTC'
        assert expiration_str in body_text
        assert expiration_str in body_html
    
    def test_send_reset_email_includes_security_notice(self):
        """Test that security notice is included in email."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        service.send_reset_email('user@example.com', 'token123', expiration)
        
        call_args = mock_ses.send_email.call_args
        body_text = call_args[1]['Message']['Body']['Text']['Data']
        body_html = call_args[1]['Message']['Body']['Html']['Data']
        
        # Check for security-related keywords
        assert 'did not request' in body_text.lower() or "didn't request" in body_text.lower()
        assert 'ignore' in body_text.lower()
        assert 'did not request' in body_html.lower() or "didn't request" in body_html.lower()
        assert 'ignore' in body_html.lower()
    
    def test_send_reset_email_has_descriptive_subject(self):
        """Test that email has a clear subject line."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        service.send_reset_email('user@example.com', 'token123', expiration)
        
        call_args = mock_ses.send_email.call_args
        subject = call_args[1]['Message']['Subject']['Data']
        
        assert 'Password Reset' in subject
    
    def test_send_reset_email_has_both_text_and_html(self):
        """Test that email includes both text and HTML versions."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        service.send_reset_email('user@example.com', 'token123', expiration)
        
        call_args = mock_ses.send_email.call_args
        message_body = call_args[1]['Message']['Body']
        
        assert 'Text' in message_body
        assert 'Html' in message_body
        assert len(message_body['Text']['Data']) > 0
        assert len(message_body['Html']['Data']) > 0
    
    def test_send_reset_email_uses_correct_from_address(self):
        """Test that email uses the configured from address."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-id'}
        
        from_email = 'noreply@myapp.com'
        service = EmailService(ses_client=mock_ses, from_email=from_email)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        service.send_reset_email('user@example.com', 'token123', expiration)
        
        call_args = mock_ses.send_email.call_args
        assert call_args[1]['Source'] == from_email
    
    def test_send_reset_email_handles_ses_client_error(self):
        """Test handling of SES ClientError."""
        mock_ses = Mock()
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Email rejected'}},
            'SendEmail'
        )
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        result = service.send_reset_email('user@example.com', 'token123', expiration)
        
        assert result is False
    
    def test_send_reset_email_handles_generic_exception(self):
        """Test handling of generic exceptions."""
        mock_ses = Mock()
        mock_ses.send_email.side_effect = Exception("Unexpected error")
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        result = service.send_reset_email('user@example.com', 'token123', expiration)
        
        assert result is False
    
    def test_send_reset_email_logs_success(self):
        """Test that successful email sending is logged."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        with patch('password_recovery.email_service.logger') as mock_logger:
            service.send_reset_email('user@example.com', 'token123', expiration)
            
            # Should log success
            assert mock_logger.info.called
            log_message = str(mock_logger.info.call_args)
            assert 'test-message-id' in log_message
    
    def test_send_reset_email_logs_ses_error_without_sensitive_data(self):
        """Test that SES errors are logged without sensitive data."""
        mock_ses = Mock()
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Email rejected'}},
            'SendEmail'
        )
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        recipient = 'user@example.com'
        token = 'secret-token-123'
        
        with patch('password_recovery.email_service.logger') as mock_logger:
            service.send_reset_email(recipient, token, expiration)
            
            # Should log error
            assert mock_logger.error.called
            log_message = str(mock_logger.error.call_args)
            
            # Should not contain sensitive data
            assert recipient not in log_message
            assert token not in log_message
            # Should contain error code
            assert 'MessageRejected' in log_message or 'SES error' in log_message
    
    def test_send_reset_email_logs_generic_error_without_sensitive_data(self):
        """Test that generic errors are logged without sensitive data."""
        mock_ses = Mock()
        mock_ses.send_email.side_effect = ValueError("Some error")
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        recipient = 'user@example.com'
        token = 'secret-token-123'
        
        with patch('password_recovery.email_service.logger') as mock_logger:
            service.send_reset_email(recipient, token, expiration)
            
            # Should log error
            assert mock_logger.error.called
            log_message = str(mock_logger.error.call_args)
            
            # Should not contain sensitive data
            assert recipient not in log_message
            assert token not in log_message
    
    def test_compose_text_body_format(self):
        """Test plain text email body composition."""
        mock_ses = Mock()
        service = EmailService(ses_client=mock_ses)
        reset_link = 'https://example.com/reset-password?token=abc123'
        expiration_str = '2024-12-31 23:59:59 UTC'
        
        body = service._compose_text_body(reset_link, expiration_str)
        
        assert reset_link in body
        assert expiration_str in body
        assert 'password' in body.lower()
        assert 'reset' in body.lower()
        assert 'ignore' in body.lower()
    
    def test_compose_html_body_format(self):
        """Test HTML email body composition."""
        mock_ses = Mock()
        service = EmailService(ses_client=mock_ses)
        reset_link = 'https://example.com/reset-password?token=abc123'
        expiration_str = '2024-12-31 23:59:59 UTC'
        
        body = service._compose_html_body(reset_link, expiration_str)
        
        assert reset_link in body
        assert expiration_str in body
        assert '<html>' in body.lower()
        assert '<a href=' in body.lower()
        assert 'password' in body.lower()
        assert 'reset' in body.lower()
    
    def test_verify_email_address_success(self):
        """Test successful email verification."""
        mock_ses = Mock()
        mock_ses.verify_email_identity.return_value = {}
        
        service = EmailService(ses_client=mock_ses)
        result = service.verify_email_address('test@example.com')
        
        assert result is True
        mock_ses.verify_email_identity.assert_called_once_with(
            EmailAddress='test@example.com'
        )
    
    def test_verify_email_address_failure(self):
        """Test email verification failure."""
        mock_ses = Mock()
        mock_ses.verify_email_identity.side_effect = ClientError(
            {'Error': {'Code': 'InvalidParameterValue', 'Message': 'Invalid email'}},
            'VerifyEmailIdentity'
        )
        
        service = EmailService(ses_client=mock_ses)
        result = service.verify_email_address('invalid-email')
        
        assert result is False
    
    def test_html_body_has_button_style_link(self):
        """Test that HTML body includes a styled button for the reset link."""
        mock_ses = Mock()
        service = EmailService(ses_client=mock_ses)
        reset_link = 'https://example.com/reset-password?token=abc123'
        expiration_str = '2024-12-31 23:59:59 UTC'
        
        body = service._compose_html_body(reset_link, expiration_str)
        
        # Should have a styled link/button
        assert 'background-color' in body.lower()
        assert 'reset password' in body.lower()
    
    def test_email_includes_utf8_charset(self):
        """Test that email uses UTF-8 charset."""
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-id'}
        
        service = EmailService(ses_client=mock_ses)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        service.send_reset_email('user@example.com', 'token123', expiration)
        
        call_args = mock_ses.send_email.call_args
        message = call_args[1]['Message']
        
        assert message['Subject']['Charset'] == 'UTF-8'
        assert message['Body']['Text']['Charset'] == 'UTF-8'
        assert message['Body']['Html']['Charset'] == 'UTF-8'
