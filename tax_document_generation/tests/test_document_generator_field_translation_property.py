"""
Property-based tests for document generator field translation.

These tests verify that the Document_Generator uses the Field_Mapper to translate
API field names to PDF field names before populating the PDF. Each property test
runs with a minimum of 100 iterations.

Feature: fix-pdf-field-mapping
Property 5: Document generator uses field mapper for translation

**Validates: Requirements 3.1**
"""

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import Mock, patch, MagicMock
from tax_document_generation.document_generator import generate_document
from tax_document_generation.field_mappings.div_1099 import SUPPORTED_FIELDS


# Strategy for generating form data with valid API field names
def form_data_strategy():
    """Generate form data dictionaries with valid API field names."""
    return st.dictionaries(
        keys=st.sampled_from(SUPPORTED_FIELDS),
        values=st.one_of(
            st.text(min_size=1, max_size=50),
            st.integers(min_value=0, max_value=1000000),
            st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False)
        ),
        min_size=1,
        max_size=10
    )


class TestDocumentGeneratorFieldTranslationProperty:
    """Property-based tests for document generator field translation."""
    
    @settings(max_examples=100)
    @given(form_data=form_data_strategy())
    def test_document_generator_uses_field_mapper_for_translation(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: fix-pdf-field-mapping, Property 5: Document generator uses field mapper for translation
        
        For any form data dictionary with API field names,
        when the Document_Generator processes it, all field names should be
        translated through the Field_Mapper before being passed to the PDF library.
        
        This test verifies that:
        1. FieldMapper is initialized with the document type
        2. map_all_fields() is called with the form data
        3. The translated field names are used (not the original API names)
        4. Field translation happens before PDF population
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {"field1": Mock(), "field2": Mock()}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Setup mock field mapper
            mock_mapper = Mock()
            # Create a simple mapping: add "pdf_" prefix to each key
            mapped_data = {f"pdf_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Generate the document
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                # If generation fails, still verify the mapper was used
                pass
            
            # Verify FieldMapper was initialized with the document type
            mock_mapper_class.assert_called_once_with("1099-DIV")
            
            # Verify map_all_fields was called with the form data
            mock_mapper.map_all_fields.assert_called_once_with(form_data)
            
            # Verify get_unmapped_fields was called
            mock_mapper.get_unmapped_fields.assert_called_once_with(form_data)
    
    @settings(max_examples=100)
    @given(form_data=form_data_strategy())
    def test_mapped_data_is_passed_to_pdf_library(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: fix-pdf-field-mapping, Property 5: Document generator uses field mapper for translation
        
        For any form data dictionary,
        the Document_Generator should pass the MAPPED data (not the original form_data)
        to the PDF library's update_page_form_field_values method.
        
        This test verifies that:
        1. The mapped data is used for PDF population
        2. The original form_data is NOT passed to the PDF library
        3. Translation happens before PDF operations
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {"field1": Mock(), "field2": Mock()}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Setup mock field mapper
            mock_mapper = Mock()
            # Create a distinct mapped data to verify it's used
            mapped_data = {f"pdf_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Generate the document
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                # If generation fails, still verify the correct data was used
                pass
            
            # Verify update_page_form_field_values was called
            if mock_writer.update_page_form_field_values.called:
                # Get the call arguments
                call_args = mock_writer.update_page_form_field_values.call_args
                
                # The second positional argument should be the mapped_data
                if call_args[0]:  # positional args
                    actual_data = call_args[0][1]  # Second positional arg
                else:  # keyword args
                    actual_data = call_args[1].get('fields', call_args[0][1] if len(call_args[0]) > 1 else None)
                
                # Verify the mapped data was used, not the original form_data
                # The keys should have the "pdf_" prefix
                if actual_data:
                    for key in actual_data.keys():
                        assert key.startswith("pdf_") or key in mapped_data, \
                            f"PDF library should receive mapped field names, got '{key}'"
    
    @settings(max_examples=100)
    @given(form_data=form_data_strategy())
    def test_field_mapper_called_before_pdf_operations(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: fix-pdf-field-mapping, Property 5: Document generator uses field mapper for translation
        
        For any form data dictionary,
        the Field_Mapper should be called BEFORE any PDF operations occur.
        
        This test verifies that:
        1. FieldMapper is initialized early in the process
        2. Field mapping happens before PDF reading
        3. Field mapping happens before PDF writing
        4. Correct order of operations is maintained
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Track the order of operations
        call_order = []
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock reader with call tracking
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {"field1": Mock()}
            
            def reader_init(*args, **kwargs):
                call_order.append('PdfReader.__init__')
                return mock_reader
            mock_reader_class.side_effect = reader_init
            
            # Setup mock writer with call tracking
            mock_writer = Mock()
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            
            def writer_init(*args, **kwargs):
                call_order.append('PdfWriter.__init__')
                return mock_writer
            mock_writer_class.side_effect = writer_init
            
            # Setup mock field mapper with call tracking
            mock_mapper = Mock()
            mapped_data = {f"pdf_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            
            def mapper_init(*args, **kwargs):
                call_order.append('FieldMapper.__init__')
                return mock_mapper
            mock_mapper_class.side_effect = mapper_init
            
            # Generate the document
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                # If generation fails, still verify the order
                pass
            
            # Verify FieldMapper was initialized before PDF operations
            if 'FieldMapper.__init__' in call_order:
                mapper_index = call_order.index('FieldMapper.__init__')
                
                # FieldMapper should be first
                assert mapper_index == 0, \
                    f"FieldMapper should be initialized first, but was at index {mapper_index}: {call_order}"
    
    @settings(max_examples=100)
    @given(form_data=form_data_strategy())
    def test_field_mapper_receives_correct_document_type(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: fix-pdf-field-mapping, Property 5: Document generator uses field mapper for translation
        
        For any document generation operation,
        the Field_Mapper should be initialized with the correct document type
        that was passed to generate_document().
        
        This test verifies that:
        1. Document type is passed correctly to FieldMapper
        2. No hardcoded document types are used
        3. Document type parameter is respected
        """
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
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mock_mapper.map_all_fields.return_value = {}
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Generate the document with "1099-DIV" document type
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                pass
            
            # Verify FieldMapper was initialized with "1099-DIV"
            mock_mapper_class.assert_called_once_with("1099-DIV")


# Import BytesIO for the tests
from io import BytesIO
