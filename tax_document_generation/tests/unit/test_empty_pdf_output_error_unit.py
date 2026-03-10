"""
Unit tests for empty PDF output error handling.

These tests verify that the Document_Generator raises a GenerationError
when the generated PDF is empty (zero bytes).

Feature: pymupdf-migration

**Validates: Requirements 5.2**
"""

import pytest
from unittest.mock import Mock, patch
from tax_document_generation.document_generator import generate_document
from tax_document_generation.exceptions import GenerationError


class TestEmptyPDFOutputError:
    """Unit tests for empty PDF output error handling."""
    
    def test_empty_pdf_output_raises_generation_error(self):
        """
        **Validates: Requirements 5.2**
        
        When an empty PDF is generated (zero bytes),
        the Document_Generator SHALL raise GenerationError.
        
        This test verifies that:
        1. Empty output is detected
        2. GenerationError is raised
        3. The error message mentions "empty"
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        form_data = {"field1": "value1"}
        document_type = "1099-DIV"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mock_mapper.map_all_fields.return_value = {"pdf_field1": "value1"}
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock PDF document that returns empty bytes
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b""  # Empty bytes!
            mock_doc.close = Mock()
            
            # Setup mock page with no widgets
            mock_page = Mock()
            mock_page.widgets.return_value = []
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # CRITICAL VERIFICATION: Empty output raises GenerationError
            with pytest.raises(GenerationError) as exc_info:
                generate_document(mock_template, form_data, document_type)
            
            # Verify the error message mentions "empty"
            assert "empty" in str(exc_info.value).lower(), \
                f"Error message should mention 'empty'. Got: {exc_info.value}"
    
    def test_empty_pdf_error_message_is_descriptive(self):
        """
        **Validates: Requirements 5.2**
        
        When an empty PDF is generated,
        the error message SHALL be descriptive and mention that the document is empty.
        
        This test verifies that:
        1. The error message is clear
        2. It helps developers understand what went wrong
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        form_data = {"field1": "value1"}
        document_type = "1099-DIV"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mock_mapper.map_all_fields.return_value = {"pdf_field1": "value1"}
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock PDF document that returns empty bytes
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b""  # Empty bytes!
            mock_doc.close = Mock()
            
            # Setup mock page with no widgets
            mock_page = Mock()
            mock_page.widgets.return_value = []
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # CRITICAL VERIFICATION: Error message is descriptive
            with pytest.raises(GenerationError) as exc_info:
                generate_document(mock_template, form_data, document_type)
            
            error_message = str(exc_info.value).lower()
            
            # Should mention "empty" and "document"
            assert "empty" in error_message, \
                f"Error message should mention 'empty'. Got: {exc_info.value}"
            assert "document" in error_message or "generated" in error_message, \
                f"Error message should mention 'document' or 'generated'. Got: {exc_info.value}"
    
    def test_non_empty_pdf_does_not_raise_error(self):
        """
        **Validates: Requirements 5.2**
        
        When a non-empty PDF is generated,
        the Document_Generator SHALL NOT raise an error about empty output.
        
        This test verifies that:
        1. Valid PDFs pass the empty check
        2. The function returns successfully
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        form_data = {"field1": "value1"}
        document_type = "1099-DIV"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mock_mapper.map_all_fields.return_value = {"pdf_field1": "value1"}
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock PDF document that returns valid bytes
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b"%PDF-1.4\nvalid content\n%%EOF"  # Non-empty!
            mock_doc.close = Mock()
            
            # Setup mock page with no widgets
            mock_page = Mock()
            mock_page.widgets.return_value = []
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # CRITICAL VERIFICATION: Non-empty output succeeds
            result = generate_document(mock_template, form_data, document_type)
            
            # Should return the PDF bytes
            assert result == b"%PDF-1.4\nvalid content\n%%EOF", \
                f"Should return the generated PDF bytes"
            assert len(result) > 0, \
                f"Result should not be empty"
    
    def test_empty_check_happens_after_generation(self):
        """
        **Validates: Requirements 5.2**
        
        The empty PDF check SHALL happen after the PDF is generated,
        before returning the result.
        
        This test verifies that:
        1. The check is performed at the right time
        2. All generation steps complete before the check
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        form_data = {"field1": "value1"}
        document_type = "1099-DIV"
        
        # Track the order of operations
        call_order = []
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mock_mapper.map_all_fields.return_value = {"pdf_field1": "value1"}
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock PDF document with call tracking
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            
            def tobytes_tracker():
                call_order.append('tobytes')
                return b""  # Empty bytes
            
            mock_doc.tobytes.side_effect = tobytes_tracker
            
            def close_tracker():
                call_order.append('close')
            
            mock_doc.close.side_effect = close_tracker
            
            # Setup mock page with no widgets
            mock_page = Mock()
            mock_page.widgets.return_value = []
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # CRITICAL VERIFICATION: Empty check happens after tobytes
            with pytest.raises(GenerationError):
                generate_document(mock_template, form_data, document_type)
            
            # Verify tobytes was called (generation completed)
            assert 'tobytes' in call_order, \
                f"tobytes should be called before empty check. Call order: {call_order}"
    
    def test_empty_pdf_closes_document_before_raising(self):
        """
        **Validates: Requirements 5.2**
        
        When an empty PDF is detected,
        the Document_Generator SHALL close the document before raising the error.
        
        This test verifies that:
        1. Resources are cleaned up even on error
        2. The document is closed before the exception is raised
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        form_data = {"field1": "value1"}
        document_type = "1099-DIV"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mock_mapper.map_all_fields.return_value = {"pdf_field1": "value1"}
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock PDF document that returns empty bytes
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b""  # Empty bytes!
            mock_doc.close = Mock()
            
            # Setup mock page with no widgets
            mock_page = Mock()
            mock_page.widgets.return_value = []
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # CRITICAL VERIFICATION: Document is closed even when error is raised
            with pytest.raises(GenerationError):
                generate_document(mock_template, form_data, document_type)
            
            # Verify close was called
            mock_doc.close.assert_called_once(), \
                f"Document should be closed before raising error"
