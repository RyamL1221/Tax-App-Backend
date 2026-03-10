"""
Unit Tests for Document Retriever

Tests document retrieval from S3.
"""

import pytest
from moto import mock_s3
import boto3

from document_download.document_retriever import get_document
from document_download.exceptions import DocumentNotFoundError, S3Error


@mock_s3
class TestDocumentRetriever:
    """Test suite for document retriever."""
    
    def setup_method(self):
        """Set up test S3 bucket."""
        self.s3 = boto3.client('s3', region_name='us-east-1')
        self.bucket_name = 'test-documents-bucket'
        self.s3.create_bucket(Bucket=self.bucket_name)
    
    def test_successful_document_retrieval(self):
        """Test successful document retrieval."""
        # Upload test document
        test_content = b'%PDF-1.4 fake pdf content'
        s3_key = 'outputs/user123/job456/form-1099-DIV.pdf'
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=test_content
        )
        
        # Retrieve document
        result = get_document(self.bucket_name, s3_key)
        
        assert result == test_content
        assert isinstance(result, bytes)
    
    def test_non_existent_document_raises_document_not_found_error(self):
        """Test that non-existent document raises DocumentNotFoundError."""
        s3_key = 'outputs/user123/nonexistent/form-1099-DIV.pdf'
        
        with pytest.raises(DocumentNotFoundError) as exc_info:
            get_document(self.bucket_name, s3_key)
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_binary_content_returned_correctly(self):
        """Test that binary content is returned correctly."""
        # Upload binary PDF content
        pdf_content = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
        s3_key = 'outputs/user789/job101/form-1099-INT.pdf'
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=pdf_content
        )
        
        # Retrieve document
        result = get_document(self.bucket_name, s3_key)
        
        assert result == pdf_content
        assert len(result) == len(pdf_content)
        assert isinstance(result, bytes)
    
    def test_large_document_retrieval(self):
        """Test retrieval of larger documents."""
        # Create a larger test document (1MB)
        large_content = b'X' * (1024 * 1024)
        s3_key = 'outputs/user999/job888/form-1099-DIV.pdf'
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=large_content
        )
        
        # Retrieve document
        result = get_document(self.bucket_name, s3_key)
        
        assert len(result) == len(large_content)
        assert result == large_content
    
    def test_empty_document_retrieval(self):
        """Test retrieval of empty document."""
        # Upload empty document
        empty_content = b''
        s3_key = 'outputs/user111/job222/form-empty.pdf'
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=empty_content
        )
        
        # Retrieve document
        result = get_document(self.bucket_name, s3_key)
        
        assert result == empty_content
        assert len(result) == 0
