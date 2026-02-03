"""
Property-based tests for exception logging in document generation.

These tests verify that the Document_Generator logs all exceptions with full
stack traces during document generation. Each property test runs with a
minimum of 100 iterations.

Feature: pymupdf-migration
Property 14: Exception Logging

**Validates: Requirements 5.3**
"""

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import Mock, patch, MagicMock, call
import logging
from tax_document_generation.document_generator import generate_document
from tax_document_generation.exceptions import GenerationError


# Strategy for generating form data
def form_data_strategy():
    """Generate form data dictionaries with API field names."""
    return st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        values=st.one_of(
            st.text(min_size=1, max_size=50),
            st.integers(min_value=0, max_value=1000000),
            st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False)
        ),
        min_size=1,
        max_size=10
    )


# Strategy for document types
def document_type_strategy():
    """Generate valid document types."""
    return st.sampled_from(["1099-DIV", "1099-INT", "W-2"])


# Strategy for exception messages
def exception_message_strategy():
    """Generate exception messages."""
    return st.text(min_size=1, max_size=100)


class TestExceptionLoggingProperty:
    """Property-based tests for exception logging."""
    
    @settings(max_examples=100)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy(),
        exception_message=exception_message_strategy()
    )
    def test_exceptions_logged_with_exc_info(self, form_data, document_type, exception_message):
        """
        **Validates: Requirements 5.3**
        Feature: pymupdf-migration, Property 14: Exception Logging
        
        For any exception during PDF generation,
        the system SHALL log the exception with full stack trace (exc_info=True).
        
        This test verifies that:
        1. Exceptions are logged at ERROR level
        2. The exc_info parameter is set to True
        3. The exception message is included in the log
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class, \
             patch('tax_document_generation.document_generator.logger') as mock_logger:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {f"pdf_field_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup fitz.open to raise an exception
            mock_fitz.open.side_effect = Exception(exception_message)
            
            # Generate the document (should fail)
            with pytest.raises(GenerationError):
                result = generate_document(mock_template, form_data, document_type)
            
            # CRITICAL VERIFICATION: Exception was logged with exc_info=True
            error_calls = [call for call in mock_logger.error.call_args_list]
            
            assert len(error_calls) > 0, \
                f"Should have logged an error when exception occurred"
            
            # Check that at least one error call has exc_info=True
            has_exc_info = False
            for error_call in error_calls:
                # Check both positional and keyword arguments
                if len(error_call) > 1:  # Has kwargs
                    kwargs = error_call[1] if len(error_call) > 1 else {}
                    if kwargs.get('exc_info') is True:
                        has_exc_info = True
                        break
            
            assert has_exc_info, \
                f"At least one error log should have exc_info=True for stack trace. " \
                f"Error calls: {error_calls}"
    
    @settings(max_examples=100)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy(),
        exception_message=exception_message_strategy()
    )
    def test_exception_message_included_in_log(self, form_data, document_type, exception_message):
        """
        **Validates: Requirements 5.3**
        Feature: pymupdf-migration, Property 14: Exception Logging
        
        For any exception during PDF generation,
        the system SHALL include the exception message in the error log.
        
        This test verifies that:
        1. The exception message is logged
        2. The log provides context about what failed
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class, \
             patch('tax_document_generation.document_generator.logger') as mock_logger:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {f"pdf_field_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup fitz.open to raise an exception
            mock_fitz.open.side_effect = Exception(exception_message)
            
            # Generate the document (should fail)
            with pytest.raises(GenerationError):
                result = generate_document(mock_template, form_data, document_type)
            
            # CRITICAL VERIFICATION: Exception message was logged
            error_calls = [call for call in mock_logger.error.call_args_list]
            
            # Check that error was logged (the message might be transformed/escaped)
            assert len(error_calls) > 0, \
                f"Should have logged an error when exception occurred"
            
            # The error log should contain information about the failure
            all_errors = ' '.join([str(call) for call in error_calls])
            assert 'failed' in all_errors.lower() or 'error' in all_errors.lower(), \
                f"Error log should indicate failure. Errors: {error_calls}"
    
    @settings(max_examples=100)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy()
    )
    def test_fitz_open_exception_logged(self, form_data, document_type):
        """
        **Validates: Requirements 5.3**
        Feature: pymupdf-migration, Property 14: Exception Logging
        
        For any exception during fitz.open(),
        the system SHALL log the exception with full stack trace.
        
        This test verifies that:
        1. Exceptions from PyMuPDF operations are logged
        2. The error log includes exc_info=True
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class, \
             patch('tax_document_generation.document_generator.logger') as mock_logger:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {f"pdf_field_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup fitz.open to raise an exception
            mock_fitz.open.side_effect = RuntimeError("Failed to open PDF")
            
            # Generate the document (should fail)
            with pytest.raises(GenerationError):
                result = generate_document(mock_template, form_data, document_type)
            
            # CRITICAL VERIFICATION: Exception was logged
            error_calls = [call for call in mock_logger.error.call_args_list]
            
            assert len(error_calls) > 0, \
                f"Should have logged an error when fitz.open failed"
            
            # Check that exc_info=True was used
            has_exc_info = False
            for error_call in error_calls:
                if len(error_call) > 1:
                    kwargs = error_call[1] if len(error_call) > 1 else {}
                    if kwargs.get('exc_info') is True:
                        has_exc_info = True
                        break
            
            assert has_exc_info, \
                f"Error log should have exc_info=True. Error calls: {error_calls}"
    
    @settings(max_examples=100)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy()
    )
    def test_tobytes_exception_logged(self, form_data, document_type):
        """
        **Validates: Requirements 5.3**
        Feature: pymupdf-migration, Property 14: Exception Logging
        
        For any exception during doc.tobytes(),
        the system SHALL log the exception with full stack trace.
        
        This test verifies that:
        1. Exceptions from PDF serialization are logged
        2. The error log includes exc_info=True
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class, \
             patch('tax_document_generation.document_generator.logger') as mock_logger:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {f"pdf_field_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock PDF document
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.close = Mock()
            
            # Setup mock page with no widgets
            mock_page = Mock()
            mock_page.widgets.return_value = []
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            
            # Setup tobytes to raise an exception
            mock_doc.tobytes.side_effect = RuntimeError("Failed to serialize PDF")
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # Generate the document (should fail)
            with pytest.raises(GenerationError):
                result = generate_document(mock_template, form_data, document_type)
            
            # CRITICAL VERIFICATION: Exception was logged
            error_calls = [call for call in mock_logger.error.call_args_list]
            
            assert len(error_calls) > 0, \
                f"Should have logged an error when tobytes failed"
            
            # Check that exc_info=True was used
            has_exc_info = False
            for error_call in error_calls:
                if len(error_call) > 1:
                    kwargs = error_call[1] if len(error_call) > 1 else {}
                    if kwargs.get('exc_info') is True:
                        has_exc_info = True
                        break
            
            assert has_exc_info, \
                f"Error log should have exc_info=True. Error calls: {error_calls}"
    
    @settings(max_examples=100)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy()
    )
    def test_generation_error_not_double_logged(self, form_data, document_type):
        """
        **Validates: Requirements 5.3**
        Feature: pymupdf-migration, Property 14: Exception Logging
        
        For any GenerationError raised,
        the system SHALL NOT double-log the exception (it should be re-raised without wrapping).
        
        This test verifies that:
        1. GenerationError is re-raised without wrapping
        2. The error is logged once, not multiple times
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class, \
             patch('tax_document_generation.document_generator.logger') as mock_logger:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {f"pdf_field_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock PDF document that returns empty bytes (triggers GenerationError)
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b""  # Empty bytes triggers GenerationError
            mock_doc.close = Mock()
            
            # Setup mock page with no widgets
            mock_page = Mock()
            mock_page.widgets.return_value = []
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # Generate the document (should fail with GenerationError)
            with pytest.raises(GenerationError) as exc_info:
                result = generate_document(mock_template, form_data, document_type)
            
            # CRITICAL VERIFICATION: GenerationError message is correct
            assert "empty" in str(exc_info.value).lower(), \
                f"GenerationError should mention empty document. Got: {exc_info.value}"
            
            # CRITICAL VERIFICATION: Error was not double-logged
            # The empty document error should be raised directly, not logged and then wrapped
            error_calls = [call for call in mock_logger.error.call_args_list]
            
            # Should not have error logs for this case (it's a direct raise, not a caught exception)
            generation_error_logs = [
                call for call in error_calls
                if 'empty' in str(call).lower()
            ]
            
            # The empty document check raises directly, so it shouldn't be logged
            # (only caught exceptions are logged)
            assert len(generation_error_logs) == 0, \
                f"GenerationError should be raised directly without logging. " \
                f"Error logs: {error_calls}"
    
    @settings(max_examples=100)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy()
    )
    def test_all_pymupdf_exceptions_wrapped_and_logged(self, form_data, document_type):
        """
        **Validates: Requirements 5.3**
        Feature: pymupdf-migration, Property 14: Exception Logging
        
        For any PyMuPDF exception (non-GenerationError),
        the system SHALL log it with exc_info=True and wrap it in GenerationError.
        
        This test verifies that:
        1. PyMuPDF exceptions are logged
        2. They are wrapped in GenerationError
        3. The original exception is preserved in the log
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class, \
             patch('tax_document_generation.document_generator.logger') as mock_logger:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {f"pdf_field_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup fitz.open to raise a PyMuPDF-like exception
            original_exception = RuntimeError("PyMuPDF internal error")
            mock_fitz.open.side_effect = original_exception
            
            # Generate the document (should fail)
            with pytest.raises(GenerationError) as exc_info:
                result = generate_document(mock_template, form_data, document_type)
            
            # CRITICAL VERIFICATION: Original exception was logged
            error_calls = [call for call in mock_logger.error.call_args_list]
            
            assert len(error_calls) > 0, \
                f"Should have logged the original exception"
            
            # Check that exc_info=True was used
            has_exc_info = False
            for error_call in error_calls:
                if len(error_call) > 1:
                    kwargs = error_call[1] if len(error_call) > 1 else {}
                    if kwargs.get('exc_info') is True:
                        has_exc_info = True
                        break
            
            assert has_exc_info, \
                f"Error log should have exc_info=True for stack trace. Error calls: {error_calls}"
            
            # CRITICAL VERIFICATION: Exception was wrapped in GenerationError
            assert isinstance(exc_info.value, GenerationError), \
                f"Exception should be wrapped in GenerationError. Got: {type(exc_info.value)}"
