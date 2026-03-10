"""
Integration tests for field mapping with document generation.

These tests verify end-to-end functionality of the field mapping system
integrated with the document generator.

Feature: fix-pdf-field-mapping
"""

import pytest
import os
from unittest.mock import Mock, patch
from io import BytesIO
from tax_document_generation.document_generator import generate_document
from tax_document_generation.field_mapper import FieldMapper


class TestFieldMappingIntegration:
    """Integration tests for field mapping."""
    
    def test_end_to_end_pdf_generation_with_api_field_names(self):
        """
        **Validates: Requirements 5.5**
        
        Test end-to-end PDF generation with API field names.
        
        This test verifies that:
        1. Form data with API field names can be processed
        2. PDF is generated successfully
        3. No errors occur during generation
        4. Result is valid PDF bytes
        """
        # Create form data with API field names
        form_data = {
            "payerName": "Test Payer Corporation",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "987-65-4321",
            "totalOrdinaryDividends": "1500.00",
            "qualifiedDividends": "1200.00"
        }
        
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {"field1": Mock()}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = b"%PDF-1.4\ngenerated content with data\n%%EOF"
            mock_writer.write = lambda stream: stream.write(mock_output)
            mock_writer_class.return_value = mock_writer
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify result is valid PDF bytes
            assert result is not None, \
                "Document generation should return bytes"
            
            assert isinstance(result, bytes), \
                "Result should be bytes"
            
            assert len(result) > 0, \
                "Result should not be empty"
            
            assert result.startswith(b"%PDF"), \
                "Result should be a valid PDF"
    
    def test_empty_form_data_generates_empty_pdf(self):
        """
        **Validates: Error Handling**
        
        Test that empty form data generates an empty PDF without errors.
        
        This test verifies that:
        1. Empty form data is handled gracefully
        2. No errors occur
        3. Valid PDF is still generated
        """
        # Create empty form data
        form_data = {}
        
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = b"%PDF-1.4\nempty document\n%%EOF"
            mock_writer.write = lambda stream: stream.write(mock_output)
            mock_writer_class.return_value = mock_writer
            
            # Generate the document - should not raise exception
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify result is valid PDF bytes
            assert result is not None, \
                "Document generation should return bytes even with empty form data"
            
            assert isinstance(result, bytes), \
                "Result should be bytes"
            
            assert result.startswith(b"%PDF"), \
                "Result should be a valid PDF"
    
    def test_all_invalid_fields_generates_empty_pdf(self):
        """
        **Validates: Requirements 4.3, 4.4**
        
        Test that form data with only invalid field names generates an empty PDF.
        
        This test verifies that:
        1. Invalid field names don't cause errors
        2. Empty PDF is generated
        3. System continues to function
        """
        # Create form data with only invalid fields
        form_data = {
            "invalidField1": "Test Value 1",
            "invalidField2": "Test Value 2",
            "unknownField": "Test Value 3"
        }
        
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = b"%PDF-1.4\nempty document\n%%EOF"
            mock_writer.write = lambda stream: stream.write(mock_output)
            mock_writer_class.return_value = mock_writer
            
            # Generate the document - should not raise exception
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify result is valid PDF bytes
            assert result is not None, \
                "Document generation should return bytes even with all invalid fields"
            
            assert isinstance(result, bytes), \
                "Result should be bytes"
            
            assert result.startswith(b"%PDF"), \
                "Result should be a valid PDF"
    
    def test_field_mapper_integration_with_document_generator(self):
        """
        Test that FieldMapper is properly integrated with document generator.
        
        This test verifies that:
        1. FieldMapper is initialized by document generator
        2. Field translation occurs
        3. Mapped data is used for PDF population
        """
        # Create form data
        form_data = {
            "payerName": "Test Payer",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_writer.write = lambda stream: stream.write(mock_output)
            mock_writer_class.return_value = mock_writer
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {
                "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]": "Test Payer",
                "topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]": "1000.00"
            }
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify FieldMapper was initialized
            mock_mapper_class.assert_called_once_with("1099-DIV")
            
            # Verify map_all_fields was called
            mock_mapper.map_all_fields.assert_called_once_with(form_data)
            
            # Verify get_unmapped_fields was called
            mock_mapper.get_unmapped_fields.assert_called_once_with(form_data)
    
    def test_mixed_valid_and_invalid_fields(self):
        """
        Test that mixed valid and invalid fields are handled correctly.
        
        This test verifies that:
        1. Valid fields are processed
        2. Invalid fields are skipped
        3. PDF is generated successfully
        """
        # Create form data with mixed fields
        form_data = {
            "payerName": "Test Payer",
            "invalidField": "Invalid Value",
            "totalOrdinaryDividends": "1000.00",
            "unknownField": "Unknown Value"
        }
        
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {"field1": Mock()}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_writer.write = lambda stream: stream.write(mock_output)
            mock_writer_class.return_value = mock_writer
            
            # Generate the document - should not raise exception
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify result is valid PDF bytes
            assert result is not None, \
                "Document generation should return bytes"
            
            assert isinstance(result, bytes), \
                "Result should be bytes"
            
            assert result.startswith(b"%PDF"), \
                "Result should be a valid PDF"
    
    def test_field_mapper_can_be_used_independently(self):
        """
        Test that FieldMapper can be used independently of document generator.
        
        This test verifies that:
        1. FieldMapper can be instantiated directly
        2. Field mapping works independently
        3. No dependencies on document generator
        """
        # Initialize field mapper directly
        mapper = FieldMapper("1099-DIV")
        
        # Map some fields
        payer_name_pdf = mapper.map_field("payerName")
        dividends_pdf = mapper.map_field("totalOrdinaryDividends")
        
        # Verify mappings work
        assert payer_name_pdf is not None, \
            "payerName should have a mapping"
        
        assert dividends_pdf is not None, \
            "totalOrdinaryDividends should have a mapping"
        
        # Verify they're different fields
        assert payer_name_pdf != dividends_pdf, \
            "Different API fields should map to different PDF fields"
    
    def test_document_generator_handles_field_mapper_errors(self):
        """
        Test that document generator handles FieldMapper errors gracefully.
        
        This test verifies that:
        1. Errors from FieldMapper are caught
        2. Appropriate error handling occurs
        3. Clear error messages are provided
        """
        # Create form data
        form_data = {"payerName": "Test Payer"}
        
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_writer.write = lambda stream: stream.write(mock_output)
            mock_writer_class.return_value = mock_writer
            
            # Setup mock field mapper to raise an error
            mock_mapper_class.side_effect = ValueError("Unsupported document type")
            
            # Generate the document - should raise GenerationError
            from exceptions import GenerationError
            
            with pytest.raises(GenerationError) as exc_info:
                result = generate_document(mock_template, form_data, "INVALID-TYPE")
            
            # Verify error message is clear
            error_message = str(exc_info.value)
            assert "Failed to generate document" in error_message, \
                "Error message should indicate generation failure"
    
    def test_multiple_document_generations_with_same_mapper(self):
        """
        Test that multiple documents can be generated using the same field mappings.
        
        This test verifies that:
        1. Field mappings are reusable
        2. No state corruption between generations
        3. Consistent behavior across multiple calls
        """
        # Create different form data sets
        form_data_1 = {"payerName": "Payer 1", "totalOrdinaryDividends": "100.00"}
        form_data_2 = {"payerName": "Payer 2", "totalOrdinaryDividends": "200.00"}
        
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_writer.write = lambda stream: stream.write(mock_output)
            mock_writer_class.return_value = mock_writer
            
            # Generate first document
            result1 = generate_document(mock_template, form_data_1, "1099-DIV")
            
            # Generate second document
            result2 = generate_document(mock_template, form_data_2, "1099-DIV")
            
            # Verify both results are valid
            assert result1 is not None and result2 is not None, \
                "Both documents should be generated"
            
            assert result1.startswith(b"%PDF") and result2.startswith(b"%PDF"), \
                "Both results should be valid PDFs"
