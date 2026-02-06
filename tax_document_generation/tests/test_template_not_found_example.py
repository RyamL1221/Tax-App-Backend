"""
Example test for template not found error.

This module contains an example-based test that validates the system's behavior
when a non-existent document type is requested. This test ensures that the
TemplateNotFoundError is raised with an appropriate error message.

**Validates: Requirements 3.3**
"""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from tax_document_generation.template_retriever import get_template
from tax_document_generation.exceptions import TemplateNotFoundError


class TestTemplateNotFoundExample:
    """Example test for template not found error handling."""
    
    def test_non_existent_document_type_9999(self):
        """
        Example 1: Template Not Found Error
        
        When requesting a document with a non-existent document type (e.g., "9999"),
        the system should return a TemplateNotFoundError with message
        "IRS template for document type '9999' not found".
        
        **Validates: Requirements 3.3**
        """
        # Arrange
        bucket = "test-bucket"
        document_type = "9999"
        
        # Mock S3 client to simulate NoSuchKey error
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
            
            # Verify the error message is appropriate
            expected_message = "IRS template for document type '9999' not found"
            assert expected_message in str(exc_info.value)
            
            # Verify the correct S3 key was attempted
            mock_s3.get_object.assert_called_once_with(
                Bucket=bucket,
                Key="templates/irs/9999.pdf"
            )
