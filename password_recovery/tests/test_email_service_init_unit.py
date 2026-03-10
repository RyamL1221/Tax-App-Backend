"""
Unit tests for EmailService initialization.

Tests the enhanced __init__ method with SES client configuration,
environment-based endpoint detection, and configuration validation.
"""

import os
import pytest
from unittest.mock import Mock, patch
from password_recovery.email_service import EmailService


class TestEmailServiceInitialization:
    """Test EmailService initialization with various configurations."""
    
    def test_init_with_all_required_env_vars(self):
        """Test initialization succeeds with all required environment variables."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1'
        }):
            mock_ses = Mock()
            service = EmailService(ses_client=mock_ses)
            
            assert service.from_email == 'noreply@example.com'
            assert service.base_url == 'https://example.com'
            assert service.ses_region == 'us-east-1'
            assert service.ses == mock_ses
    
    def test_init_with_dependency_injection(self):
        """Test initialization with dependency injection parameters."""
        mock_ses = Mock()
        service = EmailService(
            ses_client=mock_ses,
            from_email='test@example.com',
            base_url='https://test.com',
            ses_region='us-west-2',
            configuration_set='test-config-set'
        )
        
        assert service.from_email == 'test@example.com'
        assert service.base_url == 'https://test.com'
        assert service.ses_region == 'us-west-2'
        assert service.configuration_set == 'test-config-set'
        assert service.ses == mock_ses
    
    def test_init_missing_from_email_raises_error(self):
        """Test initialization fails when FROM_EMAIL is missing."""
        with patch.dict(os.environ, {
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1'
        }, clear=True):
            with pytest.raises(ValueError) as exc_info:
                EmailService()
            
            assert 'FROM_EMAIL' in str(exc_info.value)
    
    def test_init_missing_ses_region_raises_error(self):
        """Test initialization fails when SES_REGION is missing."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com'
        }, clear=True):
            with pytest.raises(ValueError) as exc_info:
                EmailService()
            
            assert 'SES_REGION' in str(exc_info.value)
    
    def test_init_missing_base_url_raises_error(self):
        """Test initialization fails when BASE_URL is missing."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'SES_REGION': 'us-east-1'
        }, clear=True):
            with pytest.raises(ValueError) as exc_info:
                EmailService()
            
            assert 'BASE_URL' in str(exc_info.value)
    
    def test_init_missing_multiple_vars_raises_error(self):
        """Test initialization fails with multiple missing variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                EmailService()
            
            error_msg = str(exc_info.value)
            assert 'FROM_EMAIL' in error_msg
            assert 'SES_REGION' in error_msg
            assert 'BASE_URL' in error_msg
    
    @patch('password_recovery.email_service.boto3.client')
    def test_init_localstack_mode_with_localhost(self, mock_boto3_client):
        """Test initialization detects LocalStack mode with localhost endpoint."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1',
            'AWS_ENDPOINT_URL': 'http://localhost:4566'
        }):
            mock_ses = Mock()
            mock_boto3_client.return_value = mock_ses
            
            service = EmailService()
            
            # Verify boto3.client was called with endpoint_url
            mock_boto3_client.assert_called_once_with(
                'ses',
                region_name='us-east-1',
                endpoint_url='http://localhost:4566'
            )
            assert service.ses == mock_ses
    
    @patch('password_recovery.email_service.boto3.client')
    def test_init_localstack_mode_with_localstack_keyword(self, mock_boto3_client):
        """Test initialization detects LocalStack mode with 'localstack' in URL."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1',
            'AWS_ENDPOINT_URL': 'http://localstack:4566'
        }):
            mock_ses = Mock()
            mock_boto3_client.return_value = mock_ses
            
            service = EmailService()
            
            mock_boto3_client.assert_called_once_with(
                'ses',
                region_name='us-east-1',
                endpoint_url='http://localstack:4566'
            )
    
    @patch('password_recovery.email_service.boto3.client')
    def test_init_localstack_mode_with_docker_ip(self, mock_boto3_client):
        """Test initialization detects LocalStack mode with Docker IP."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1',
            'AWS_ENDPOINT_URL': 'http://172.18.0.1:4566'
        }):
            mock_ses = Mock()
            mock_boto3_client.return_value = mock_ses
            
            service = EmailService()
            
            mock_boto3_client.assert_called_once_with(
                'ses',
                region_name='us-east-1',
                endpoint_url='http://172.18.0.1:4566'
            )
    
    @patch('password_recovery.email_service.boto3.client')
    def test_init_aws_mode_without_endpoint_url(self, mock_boto3_client):
        """Test initialization uses AWS mode when AWS_ENDPOINT_URL is not set."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1'
        }, clear=True):
            mock_ses = Mock()
            mock_boto3_client.return_value = mock_ses
            
            service = EmailService()
            
            # Verify boto3.client was called WITHOUT endpoint_url
            mock_boto3_client.assert_called_once_with(
                'ses',
                region_name='us-east-1'
            )
    
    def test_init_configuration_set_from_env(self):
        """Test initialization reads CONFIGURATION_SET_NAME from environment."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1',
            'CONFIGURATION_SET_NAME': 'my-config-set'
        }):
            mock_ses = Mock()
            service = EmailService(ses_client=mock_ses)
            
            assert service.configuration_set == 'my-config-set'
    
    def test_init_configuration_set_optional(self):
        """Test initialization works without CONFIGURATION_SET_NAME."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1'
        }, clear=True):
            mock_ses = Mock()
            service = EmailService(ses_client=mock_ses)
            
            assert service.configuration_set is None


class TestEmailMasking:
    """Test email masking for secure logging."""
    
    def test_mask_email_standard(self):
        """Test masking a standard email address."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1'
        }):
            mock_ses = Mock()
            service = EmailService(ses_client=mock_ses)
            
            masked = service._mask_email('user@example.com')
            assert masked == 'use***@example.com'
    
    def test_mask_email_short_local_part(self):
        """Test masking email with short local part."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1'
        }):
            mock_ses = Mock()
            service = EmailService(ses_client=mock_ses)
            
            masked = service._mask_email('ab@test.com')
            assert masked == 'ab***@test.com'
    
    def test_mask_email_single_char_local_part(self):
        """Test masking email with single character local part."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1'
        }):
            mock_ses = Mock()
            service = EmailService(ses_client=mock_ses)
            
            masked = service._mask_email('a@test.com')
            assert masked == 'a***@test.com'
    
    def test_mask_email_long_local_part(self):
        """Test masking email with long local part."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1'
        }):
            mock_ses = Mock()
            service = EmailService(ses_client=mock_ses)
            
            masked = service._mask_email('verylongemailaddress@example.com')
            assert masked == 'ver***@example.com'
    
    def test_mask_email_no_at_symbol(self):
        """Test masking invalid email without @ symbol."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1'
        }):
            mock_ses = Mock()
            service = EmailService(ses_client=mock_ses)
            
            masked = service._mask_email('notanemail')
            assert masked == '***'
    
    def test_mask_email_empty_string(self):
        """Test masking empty string."""
        with patch.dict(os.environ, {
            'FROM_EMAIL': 'noreply@example.com',
            'BASE_URL': 'https://example.com',
            'SES_REGION': 'us-east-1'
        }):
            mock_ses = Mock()
            service = EmailService(ses_client=mock_ses)
            
            masked = service._mask_email('')
            assert masked == '***'
