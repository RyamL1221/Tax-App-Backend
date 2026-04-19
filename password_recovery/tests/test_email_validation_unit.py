"""
Unit tests for email validation in EmailService.

Tests the _validate_email method to ensure it correctly validates
email address formats before sending emails via SES.
"""

import pytest
from password_recovery.email_service import EmailService


class TestEmailValidation:
    """Test suite for email address validation."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        # Create EmailService with minimal configuration for testing
        # We don't need a real SES client for validation tests
        import os
        os.environ['FROM_EMAIL'] = 'test@example.com'
        os.environ['BASE_URL'] = 'http://localhost:3000'
        os.environ['SES_REGION'] = 'us-east-1'
        
        from unittest.mock import Mock
        mock_ses = Mock()
        self.service = EmailService(ses_client=mock_ses)
    
    def test_valid_simple_email(self):
        """Test validation of simple valid email address."""
        assert self.service._validate_email("user@example.com") is True
    
    def test_valid_email_with_subdomain(self):
        """Test validation of email with subdomain."""
        assert self.service._validate_email("user@mail.example.com") is True
    
    def test_valid_email_with_plus(self):
        """Test validation of email with plus sign (common for email aliases)."""
        assert self.service._validate_email("user+tag@example.com") is True
    
    def test_valid_email_with_dots(self):
        """Test validation of email with dots in local part."""
        assert self.service._validate_email("first.last@example.com") is True
    
    def test_valid_email_with_hyphen(self):
        """Test validation of email with hyphen in domain."""
        assert self.service._validate_email("user@my-domain.com") is True
    
    def test_valid_email_with_numbers(self):
        """Test validation of email with numbers."""
        assert self.service._validate_email("user123@example456.com") is True
    
    def test_valid_email_with_underscore(self):
        """Test validation of email with underscore in local part."""
        assert self.service._validate_email("user_name@example.com") is True
    
    def test_valid_email_with_long_tld(self):
        """Test validation of email with long TLD."""
        assert self.service._validate_email("user@example.museum") is True
    
    def test_valid_email_with_country_tld(self):
        """Test validation of email with country code TLD."""
        assert self.service._validate_email("user@example.co.uk") is True
    
    def test_invalid_email_no_at_symbol(self):
        """Test rejection of email without @ symbol."""
        assert self.service._validate_email("userexample.com") is False
    
    def test_invalid_email_no_domain(self):
        """Test rejection of email without domain."""
        assert self.service._validate_email("user@") is False
    
    def test_invalid_email_no_local_part(self):
        """Test rejection of email without local part."""
        assert self.service._validate_email("@example.com") is False
    
    def test_invalid_email_no_tld(self):
        """Test rejection of email without TLD."""
        assert self.service._validate_email("user@example") is False
    
    def test_invalid_email_short_tld(self):
        """Test rejection of email with single-character TLD."""
        assert self.service._validate_email("user@example.c") is False
    
    def test_invalid_email_multiple_at_symbols(self):
        """Test rejection of email with multiple @ symbols."""
        assert self.service._validate_email("user@@example.com") is False
    
    def test_invalid_email_spaces(self):
        """Test rejection of email with spaces."""
        assert self.service._validate_email("user @example.com") is False
        assert self.service._validate_email("user@ example.com") is False
    
    def test_invalid_email_empty_string(self):
        """Test rejection of empty string."""
        assert self.service._validate_email("") is False
    
    def test_invalid_email_none(self):
        """Test rejection of None value."""
        assert self.service._validate_email(None) is False
    
    def test_invalid_email_not_string(self):
        """Test rejection of non-string values."""
        assert self.service._validate_email(123) is False
        assert self.service._validate_email(['user@example.com']) is False
        assert self.service._validate_email({'email': 'user@example.com'}) is False
    
    def test_invalid_email_special_characters(self):
        """Test rejection of email with invalid special characters."""
        assert self.service._validate_email("user#name@example.com") is False
        assert self.service._validate_email("user$name@example.com") is False
        assert self.service._validate_email("user&name@example.com") is False


class TestEmailValidationIntegration:
    """Integration tests for email validation in send_reset_email."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        import os
        os.environ['FROM_EMAIL'] = 'test@example.com'
        os.environ['BASE_URL'] = 'http://localhost:3000'
        os.environ['SES_REGION'] = 'us-east-1'
        
        from unittest.mock import Mock
        mock_ses = Mock()
        self.service = EmailService(ses_client=mock_ses)
    
    def test_send_reset_email_rejects_invalid_email(self):
        """Test that send_reset_email rejects invalid email addresses."""
        from datetime import datetime, timedelta
        
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        # Test with invalid email
        success, message_id, error_code = self.service.send_reset_email(
            "invalid.email",
            "test-token",
            expiration
        )
        
        assert success is False
        assert message_id is None
        assert error_code == "InvalidEmailFormat"
    
    def test_send_reset_email_accepts_valid_email(self):
        """Test that send_reset_email accepts valid email addresses."""
        from datetime import datetime, timedelta
        from unittest.mock import Mock
        
        # Mock successful SES response
        self.service.ses.send_email = Mock(return_value={'MessageId': 'test-message-id'})
        
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        # Test with valid email
        success, message_id, error_code = self.service.send_reset_email(
            "user@example.com",
            "test-token",
            expiration
        )
        
        assert success is True
        assert message_id == 'test-message-id'
        assert error_code is None
    
    def test_send_reset_email_logs_invalid_email(self, caplog):
        """Test that invalid email addresses are logged."""
        from datetime import datetime, timedelta
        import logging
        
        caplog.set_level(logging.ERROR)
        
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        # Test with invalid email
        self.service.send_reset_email(
            "invalid.email",
            "test-token",
            expiration
        )
        
        # Check that error was logged
        assert any("Invalid email address format" in record.message for record in caplog.records)
        assert any("Email delivery aborted" in record.message for record in caplog.records)
    
    def test_send_reset_email_masks_invalid_email_in_logs(self, caplog):
        """Test that invalid email addresses are masked in logs."""
        from datetime import datetime, timedelta
        import logging
        
        caplog.set_level(logging.ERROR)
        
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        # Test with invalid email
        self.service.send_reset_email(
            "invalid.email",
            "test-token",
            expiration
        )
        
        # Check that full email is not in logs
        assert not any("invalid.email" in record.message for record in caplog.records)
        # Check that masked version is in logs (should be "inv***" since no @ symbol)
        assert any("***" in record.message for record in caplog.records)
