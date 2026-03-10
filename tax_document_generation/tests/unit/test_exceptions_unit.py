"""
Unit tests for custom exception classes.

This module tests that all custom exception classes can be imported,
instantiated, and raised correctly.
"""

import pytest
from tax_document_generation.exceptions import (
    AuthenticationError,
    ValidationError,
    TemplateNotFoundError,
    GenerationError,
    S3Error
)


class TestExceptionClasses:
    """Test suite for custom exception classes."""
    
    def test_authentication_error_can_be_raised(self):
        """Test that AuthenticationError can be raised and caught."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError("Invalid JWT token")
        
        assert str(exc_info.value) == "Invalid JWT token"
        assert isinstance(exc_info.value, Exception)
    
    def test_validation_error_can_be_raised(self):
        """Test that ValidationError can be raised and caught."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Missing required field: ssn")
        
        assert str(exc_info.value) == "Missing required field: ssn"
        assert isinstance(exc_info.value, Exception)
    
    def test_template_not_found_error_can_be_raised(self):
        """Test that TemplateNotFoundError can be raised and caught."""
        with pytest.raises(TemplateNotFoundError) as exc_info:
            raise TemplateNotFoundError("Template for document type '1040' not found")
        
        assert str(exc_info.value) == "Template for document type '1040' not found"
        assert isinstance(exc_info.value, Exception)
    
    def test_generation_error_can_be_raised(self):
        """Test that GenerationError can be raised and caught."""
        with pytest.raises(GenerationError) as exc_info:
            raise GenerationError("Failed to generate PDF document")
        
        assert str(exc_info.value) == "Failed to generate PDF document"
        assert isinstance(exc_info.value, Exception)
    
    def test_s3_error_can_be_raised(self):
        """Test that S3Error can be raised and caught."""
        with pytest.raises(S3Error) as exc_info:
            raise S3Error("Failed to upload document to S3")
        
        assert str(exc_info.value) == "Failed to upload document to S3"
        assert isinstance(exc_info.value, Exception)
    
    def test_all_exceptions_inherit_from_exception(self):
        """Test that all custom exceptions inherit from Exception."""
        assert issubclass(AuthenticationError, Exception)
        assert issubclass(ValidationError, Exception)
        assert issubclass(TemplateNotFoundError, Exception)
        assert issubclass(GenerationError, Exception)
        assert issubclass(S3Error, Exception)
    
    def test_exceptions_can_be_raised_without_message(self):
        """Test that exceptions can be raised without a message."""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError()
        
        with pytest.raises(ValidationError):
            raise ValidationError()
        
        with pytest.raises(TemplateNotFoundError):
            raise TemplateNotFoundError()
        
        with pytest.raises(GenerationError):
            raise GenerationError()
        
        with pytest.raises(S3Error):
            raise S3Error()
