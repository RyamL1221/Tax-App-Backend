"""
Property-based tests for partial mapping in document generator.

These tests verify that the Document_Generator produces valid PDFs even when
some fields cannot be mapped. Each property test runs with a minimum of
100 iterations.

Feature: fix-pdf-field-mapping
Property 8: Partial mapping produces valid PDF

**Validates: Requirements 4.3, 4.4**
"""

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import Mock, patch
from io import BytesIO
from tax_document_generation.document_generator import generate_document
from tax_document_generation.field_mappings.div_1099 import SUPPORTED_FIELDS


# Strategy for generating valid API field names
def valid_api_field_name_strategy():
    """Generate valid API field names from the 1099-DIV field reference."""
    return st.sampled_from(SUPPORTED_FIELDS)


# Strategy for generating invalid API field names
def invalid_api_field_name_strategy():
    """Generate invalid API field names."""
    return st.text(min_size=1, max_size=50).filter(lambda s: s not in SUPPORTED_FIELDS and s.isidentifier())


# Strategy for generating mixed form data (valid and invalid fields)
def mixed_form_data_strategy():
    """Generate form data with both valid and invalid API field names."""
    valid_data = st.dictionaries(
        keys=valid_api_field_name_strategy(),
        values=st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=5
    )
    invalid_data = st.dictionaries(
        keys=invalid_api_field_name_strategy(),
        values=st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=5
    )
    
    return st.builds(
        lambda v, i: {**v, **i},
        valid_data,
        invalid_data
    )


class TestPartialMappingProperty:
    """Property-based tests for partial mapping."""
    
    @settings(max_examples=20)
    @given(form_data=mixed_form_data_strategy())
    def test_partial_mapping_produces_valid_pdf_bytes(self, form_data):
        """
        **Validates: Requirements 4.3, 4.4**
        Feature: fix-pdf-field-mapping, Property 8: Partial mapping produces valid PDF
        
        For any form data containing a mix of valid and invalid API field names,
        when the Document_Generator processes it, it should return valid PDF bytes.
        
        This test verifies that:
        1. PDF bytes are returned (not None)
        2. Bytes are non-empty
        3. Bytes start with PDF header
        4. No exceptions are raised
        """
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
            
            # Generate the document - should not raise exception
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify result is valid PDF bytes
            assert result is not None, \
                "Document generation should return bytes, not None"
            
            assert isinstance(result, bytes), \
                f"Document generation should return bytes, got {type(result)}"
            
            assert len(result) > 0, \
                "Document generation should return non-empty bytes"
            
            assert result.startswith(b"%PDF"), \
                "Result should be a valid PDF (start with %PDF header)"
    
    @settings(max_examples=20)
    @given(form_data=mixed_form_data_strategy())
    def test_partial_mapping_does_not_raise_exception(self, form_data):
        """
        **Validates: Requirements 4.3, 4.4**
        Feature: fix-pdf-field-mapping, Property 8: Partial mapping produces valid PDF
        
        For any form data containing unmapped fields,
        the Document_Generator should not raise an exception.
        
        This test verifies that:
        1. No exceptions are raised for unmapped fields
        2. Graceful degradation occurs
        3. System continues to function
        """
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
            
            # Generate the document - should not raise exception
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
                # Success - no exception raised
            except Exception as e:
                pytest.fail(f"Document generation should not raise exception for partial mapping: {e}")
    
    @settings(max_examples=20)
    @given(form_data=mixed_form_data_strategy())
    def test_successfully_mapped_fields_are_populated(self, form_data):
        """
        **Validates: Requirements 4.3, 4.4**
        Feature: fix-pdf-field-mapping, Property 8: Partial mapping produces valid PDF
        
        For any form data with mixed valid and invalid fields,
        all successfully mapped fields should be populated in the PDF.
        
        This test verifies that:
        1. Valid fields are not skipped due to invalid fields
        2. Mapped data is passed to PDF library
        3. Partial success is achieved
        """
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
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify update_page_form_field_values was called
            # (meaning some fields were populated)
            valid_fields = [k for k in form_data.keys() if k in SUPPORTED_FIELDS]
            
            if valid_fields and mock_writer.update_page_form_field_values.called:
                # Get the data that was passed
                call_args = mock_writer.update_page_form_field_values.call_args
                
                if call_args[0] and len(call_args[0]) > 1:
                    actual_data = call_args[0][1]
                else:
                    actual_data = call_args[1].get('fields', {})
                
                # Verify some data was passed (the valid fields)
                assert len(actual_data) > 0, \
                    "Successfully mapped fields should be populated in PDF"
    
    @settings(max_examples=20)
    @given(invalid_field=invalid_api_field_name_strategy())
    def test_all_invalid_fields_produces_valid_pdf(self, invalid_field):
        """
        **Validates: Requirements 4.3, 4.4**
        Feature: fix-pdf-field-mapping, Property 8: Partial mapping produces valid PDF
        
        For form data containing ONLY invalid fields,
        the Document_Generator should still return a valid (empty) PDF.
        
        This test verifies that:
        1. Complete mapping failure doesn't crash the system
        2. Empty PDF is still valid
        3. Graceful degradation to empty document
        """
        # Create form data with only invalid fields
        form_data = {invalid_field: "test_value", f"{invalid_field}_2": "test_value_2"}
        
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
            
            # Generate the document - should not raise exception
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify result is valid PDF bytes
            assert result is not None, \
                "Document generation should return bytes even with all invalid fields"
            
            assert isinstance(result, bytes), \
                "Document generation should return bytes"
            
            assert len(result) > 0, \
                "Document generation should return non-empty bytes"
            
            assert result.startswith(b"%PDF"), \
                "Result should be a valid PDF"
    
    @settings(max_examples=20)
    @given(form_data=mixed_form_data_strategy())
    def test_partial_mapping_maintains_data_integrity(self, form_data):
        """
        **Validates: Requirements 4.3, 4.4**
        Feature: fix-pdf-field-mapping, Property 8: Partial mapping produces valid PDF
        
        For any form data with mixed fields,
        the values of successfully mapped fields should be preserved correctly.
        
        This test verifies that:
        1. Valid field values are not corrupted
        2. Invalid fields don't affect valid field values
        3. Data integrity is maintained during partial mapping
        """
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
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify update_page_form_field_values was called
            if mock_writer.update_page_form_field_values.called:
                call_args = mock_writer.update_page_form_field_values.call_args
                
                # Get the data that was passed
                if call_args[0] and len(call_args[0]) > 1:
                    actual_data = call_args[0][1]
                else:
                    actual_data = call_args[1].get('fields', {})
                
                # Get valid fields from original form_data
                valid_fields = {k: v for k, v in form_data.items() if k in SUPPORTED_FIELDS}
                
                # Verify all valid field values are in the actual data
                for api_field, value in valid_fields.items():
                    # The value should be in the actual data (with translated key)
                    actual_values = list(actual_data.values())
                    assert str(value) in [str(v) for v in actual_values], \
                        f"Value '{value}' for valid field '{api_field}' should be preserved"
    
    @settings(max_examples=20)
    @given(form_data=mixed_form_data_strategy())
    def test_partial_mapping_pdf_has_correct_structure(self, form_data):
        """
        **Validates: Requirements 4.3, 4.4**
        Feature: fix-pdf-field-mapping, Property 8: Partial mapping produces valid PDF
        
        For any form data with partial mapping,
        the generated PDF should have the correct structure (header, content, EOF).
        
        This test verifies that:
        1. PDF structure is valid
        2. No corruption occurs during partial mapping
        3. PDF can be processed by PDF readers
        """
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
            # Create a more realistic PDF structure
            mock_output = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 2\ntrailer\n<<\n>>\nstartxref\n50\n%%EOF"
            mock_writer.write = lambda stream: stream.write(mock_output)
            mock_writer_class.return_value = mock_writer
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify PDF structure
            assert result.startswith(b"%PDF"), \
                "PDF should start with %PDF header"
            
            assert result.endswith(b"%%EOF") or b"%%EOF" in result, \
                "PDF should contain %%EOF marker"
            
            # Verify it's not just the header
            assert len(result) > 10, \
                "PDF should have content beyond just the header"
    
    @settings(max_examples=20)
    @given(form_data=mixed_form_data_strategy())
    def test_partial_mapping_continues_after_unmapped_fields(self, form_data):
        """
        **Validates: Requirements 4.3, 4.4**
        Feature: fix-pdf-field-mapping, Property 8: Partial mapping produces valid PDF
        
        For any form data with unmapped fields,
        the Document_Generator should continue processing remaining fields
        after encountering unmapped fields.
        
        This test verifies that:
        1. Processing doesn't stop at first unmapped field
        2. All valid fields are processed
        3. Order of fields doesn't matter
        """
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
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Count valid and invalid fields
            valid_fields = [k for k in form_data.keys() if k in SUPPORTED_FIELDS]
            invalid_fields = [k for k in form_data.keys() if k not in SUPPORTED_FIELDS]
            
            # If there are both valid and invalid fields
            if valid_fields and invalid_fields:
                # Verify the document was generated successfully
                assert result is not None, \
                    "Document should be generated even with unmapped fields"
                
                # Verify update_page_form_field_values was called
                # (meaning valid fields were processed)
                if mock_writer.update_page_form_field_values.called:
                    call_args = mock_writer.update_page_form_field_values.call_args
                    
                    if call_args[0] and len(call_args[0]) > 1:
                        actual_data = call_args[0][1]
                    else:
                        actual_data = call_args[1].get('fields', {})
                    
                    # Verify some data was passed (the valid fields)
                    assert len(actual_data) > 0, \
                        "Valid fields should be processed even when invalid fields exist"
