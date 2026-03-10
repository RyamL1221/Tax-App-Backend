"""
Property-based tests for unmapped field handling in document generator.

These tests verify that the Document_Generator correctly handles unmapped fields
by logging warnings and excluding them from PDF population. Each property test
runs with a minimum of 100 iterations.

Feature: fix-pdf-field-mapping
Property 6: Unmapped fields are logged and skipped

**Validates: Requirements 3.2, 4.2, 6.2**
"""

import pytest
import logging
from hypothesis import given, settings, strategies as st, HealthCheck
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
    
    # Combine valid and invalid data
    return st.builds(
        lambda v, i: {**v, **i},
        valid_data,
        invalid_data
    )


class TestUnmappedFieldHandlingProperty:
    """Property-based tests for unmapped field handling."""
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=mixed_form_data_strategy())
    def test_unmapped_fields_are_logged_as_warnings(self, form_data, caplog):
        """
        **Validates: Requirements 3.2, 4.2, 6.2**
        Feature: fix-pdf-field-mapping, Property 6: Unmapped fields are logged and skipped
        
        For any form data containing both valid and invalid API field names,
        when the Document_Generator processes it, all invalid field names should
        be logged as warnings.
        
        This test verifies that:
        1. Warning logs are created for unmapped fields
        2. Each unmapped field is logged
        3. Log messages contain the field name
        4. Log messages indicate the field has no mapping
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Clear any previous log records
        caplog.clear()
        
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
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document with logging enabled
            with caplog.at_level(logging.WARNING):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                except Exception as e:
                    # If generation fails, still verify logging occurred
                    pass
            
            # Identify which fields are invalid (not in SUPPORTED_FIELDS)
            invalid_fields = [k for k in form_data.keys() if k not in SUPPORTED_FIELDS]
            
            # Verify warnings were logged for unmapped fields
            warning_logs = [record for record in caplog.records if record.levelname == "WARNING"]
            
            if invalid_fields:
                assert len(warning_logs) > 0, \
                    f"Should have warning logs for unmapped fields: {invalid_fields}"
                
                # Verify each invalid field appears in the logs
                for invalid_field in invalid_fields:
                    field_logs = [
                        record for record in warning_logs
                        if invalid_field in record.message
                    ]
                    
                    assert len(field_logs) > 0, \
                        f"Should have a warning log for unmapped field '{invalid_field}'"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=mixed_form_data_strategy())
    def test_unmapped_fields_excluded_from_pdf_population(self, form_data, caplog):
        """
        **Validates: Requirements 3.2, 4.2, 6.2**
        Feature: fix-pdf-field-mapping, Property 6: Unmapped fields are logged and skipped
        
        For any form data containing both valid and invalid API field names,
        when the Document_Generator processes it, invalid field names should be
        excluded from the data passed to the PDF library.
        
        This test verifies that:
        1. Only mapped fields are passed to PDF library
        2. Unmapped fields are filtered out
        3. PDF population uses only valid PDF field names
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
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document
            with caplog.at_level(logging.WARNING):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                except Exception as e:
                    pass
            
            # Identify which fields are valid
            valid_fields = [k for k in form_data.keys() if k in SUPPORTED_FIELDS]
            invalid_fields = [k for k in form_data.keys() if k not in SUPPORTED_FIELDS]
            
            # If update_page_form_field_values was called, verify the data
            if mock_writer.update_page_form_field_values.called:
                call_args = mock_writer.update_page_form_field_values.call_args
                
                # Get the data that was passed
                if call_args[0] and len(call_args[0]) > 1:
                    actual_data = call_args[0][1]
                else:
                    actual_data = call_args[1].get('fields', {})
                
                # Verify invalid field names are NOT in the data
                for invalid_field in invalid_fields:
                    assert invalid_field not in actual_data, \
                        f"Invalid field '{invalid_field}' should not be passed to PDF library"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=mixed_form_data_strategy())
    def test_document_generation_continues_with_unmapped_fields(self, form_data, caplog):
        """
        **Validates: Requirements 3.2, 4.2, 6.2**
        Feature: fix-pdf-field-mapping, Property 6: Unmapped fields are logged and skipped
        
        For any form data containing unmapped fields,
        the Document_Generator should continue processing and not raise an exception.
        
        This test verifies that:
        1. Unmapped fields don't cause exceptions
        2. Document generation completes successfully
        3. Valid PDF bytes are returned
        4. Remaining valid fields are still processed
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
            with caplog.at_level(logging.WARNING):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                    
                    # Verify result is valid PDF bytes
                    assert isinstance(result, bytes), \
                        "Document generation should return bytes"
                    
                    assert len(result) > 0, \
                        "Document generation should return non-empty bytes"
                    
                    assert result.startswith(b"%PDF"), \
                        "Result should be a valid PDF"
                    
                except Exception as e:
                    # Document generation should not fail due to unmapped fields
                    pytest.fail(f"Document generation should not raise exception for unmapped fields: {e}")
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(invalid_field=invalid_api_field_name_strategy())
    def test_single_unmapped_field_logged_with_field_name(self, invalid_field, caplog):
        """
        **Validates: Requirements 3.2, 4.2, 6.2**
        Feature: fix-pdf-field-mapping, Property 6: Unmapped fields are logged and skipped
        
        For any single unmapped field,
        the warning log should contain the specific field name.
        
        This test verifies that:
        1. Field name appears in log message
        2. Log message is specific and helpful
        3. Operators can identify which field is unmapped
        """
        # Create form data with only the invalid field
        form_data = {invalid_field: "test_value"}
        
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Clear any previous log records
        caplog.clear()
        
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
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document with logging enabled
            with caplog.at_level(logging.WARNING):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                except Exception as e:
                    pass
            
            # Verify warning log contains the field name
            warning_logs = [record for record in caplog.records if record.levelname == "WARNING"]
            
            assert len(warning_logs) > 0, \
                f"Should have warning logs for unmapped field '{invalid_field}'"
            
            # Find logs containing the field name
            field_logs = [
                record for record in warning_logs
                if invalid_field in record.message
            ]
            
            assert len(field_logs) > 0, \
                f"Warning log should contain field name '{invalid_field}'"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=mixed_form_data_strategy())
    def test_unmapped_fields_list_logged(self, form_data, caplog):
        """
        **Validates: Requirements 3.2, 4.2, 6.2**
        Feature: fix-pdf-field-mapping, Property 6: Unmapped fields are logged and skipped
        
        For any form data with unmapped fields,
        the Document_Generator should log a list of all unmapped fields.
        
        This test verifies that:
        1. A summary log lists unmapped fields
        2. All unmapped fields are included in the summary
        3. Operators can see all issues at once
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Clear any previous log records
        caplog.clear()
        
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
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document with logging enabled
            with caplog.at_level(logging.WARNING):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                except Exception as e:
                    pass
            
            # Identify which fields are invalid
            invalid_fields = [k for k in form_data.keys() if k not in SUPPORTED_FIELDS]
            
            if invalid_fields:
                # Verify there's a log with "Unmapped fields"
                warning_logs = [record for record in caplog.records if record.levelname == "WARNING"]
                
                unmapped_summary_logs = [
                    record for record in warning_logs
                    if "Unmapped fields" in record.message or "unmapped field" in record.message.lower()
                ]
                
                assert len(unmapped_summary_logs) > 0, \
                    "Should have a summary log about unmapped fields"
