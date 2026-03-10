"""
Unit tests for the template retriever module.

This module contains unit tests for the template retriever functionality,
testing specific scenarios including successful template retrieval, template
not found errors, and other S3 failures.
"""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from tax_document_generation.template_retriever import get_template
from tax_document_generation.exceptions import TemplateNotFoundError, S3Error


class TestGetTemplate:
    """Unit tests for the get_template function."""
    
    def test_successful_template_retrieval(self):
        """Test successful retrieval of a template from S3."""
        # Arrange
        bucket = "test-bucket"
        document_type = "1040"
        expected_content = b"PDF content here"
        
        mock_response = {
            'Body': Mock(read=Mock(return_value=expected_content))
        }
        
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = Mock()
            mock_s3.get_object.return_value = mock_response
            mock_boto_client.return_value = mock_s3
            
            # Act
            result = get_template(bucket, document_type)
            
            # Assert
            assert result == expected_content
            mock_s3.get_object.assert_called_once_with(
                Bucket=bucket,
                Key="templates/irs/1040.pdf"
            )
    
    def test_template_not_found_raises_error(self):
        """Test that NoSuchKey error raises TemplateNotFoundError."""
        # Arrange
        bucket = "test-bucket"
        document_type = "9999"
        
        error_response = {
            'Error': {
                'Code': 'NoSuchKey',
                'Message': 'The specified key does not exist.'
            }
        }
        
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = Mock()
            mock_s3.get_object.side_effect = ClientError(error_response, 'GetObject')
            mock_boto_client.return_value = mock_s3
            
            # Act & Assert
            with pytest.raises(TemplateNotFoundError) as exc_info:
                get_template(bucket, document_type)
            
            assert "IRS template for document type '9999' not found" in str(exc_info.value)
    
    def test_s3_permission_error_raises_s3_error(self):
        """Test that S3 permission errors raise S3Error."""
        # Arrange
        bucket = "test-bucket"
        document_type = "1040"
        
        error_response = {
            'Error': {
                'Code': 'AccessDenied',
                'Message': 'Access Denied'
            }
        }
        
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = Mock()
            mock_s3.get_object.side_effect = ClientError(error_response, 'GetObject')
            mock_boto_client.return_value = mock_s3
            
            # Act & Assert
            with pytest.raises(S3Error) as exc_info:
                get_template(bucket, document_type)
            
            assert "Failed to retrieve template from S3" in str(exc_info.value)
    
    def test_s3_network_error_raises_s3_error(self):
        """Test that network errors raise S3Error."""
        # Arrange
        bucket = "test-bucket"
        document_type = "1040"
        
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = Mock()
            mock_s3.get_object.side_effect = Exception("Network timeout")
            mock_boto_client.return_value = mock_s3
            
            # Act & Assert
            with pytest.raises(S3Error) as exc_info:
                get_template(bucket, document_type)
            
            assert "Unexpected error while retrieving template" in str(exc_info.value)
    
    def test_s3_key_construction_with_different_document_types(self):
        """Test that S3 key is correctly constructed for various document types."""
        # Arrange
        bucket = "test-bucket"
        test_cases = [
            ("1040", "templates/irs/1040.pdf"),
            ("1099", "templates/irs/1099.pdf"),
            ("W2", "templates/irs/W2.pdf"),
            ("1040-EZ", "templates/irs/1040-EZ.pdf"),
        ]
        
        for document_type, expected_key in test_cases:
            mock_response = {
                'Body': Mock(read=Mock(return_value=b"content"))
            }
            
            with patch('boto3.client') as mock_boto_client:
                mock_s3 = Mock()
                mock_s3.get_object.return_value = mock_response
                mock_boto_client.return_value = mock_s3
                
                # Act
                get_template(bucket, document_type)
                
                # Assert
                mock_s3.get_object.assert_called_once_with(
                    Bucket=bucket,
                    Key=expected_key
                )
    
    def test_empty_document_type(self):
        """Test handling of empty document type."""
        # Arrange
        bucket = "test-bucket"
        document_type = ""
        expected_key = "templates/irs/.pdf"
        
        mock_response = {
            'Body': Mock(read=Mock(return_value=b"content"))
        }
        
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = Mock()
            mock_s3.get_object.return_value = mock_response
            mock_boto_client.return_value = mock_s3
            
            # Act
            get_template(bucket, document_type)
            
            # Assert - should still construct key even if empty
            mock_s3.get_object.assert_called_once_with(
                Bucket=bucket,
                Key=expected_key
            )
