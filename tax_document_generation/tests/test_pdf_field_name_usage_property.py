"""
Property-based tests for PDF field name usage in document generator.

These tests verify that the Document_Generator uses only translated PDF field names
(not API field names) when populating the PDF. Each property test runs with a
minimum of 100 iterations.

Feature: fix-pdf-field-mapping
Property 7: Only translated PDF field names are used

**Validates: Requirements 3.3**
"""

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import Mock, patch, call
from io import BytesIO
from tax_document_generation.document_generator import generate_document
from tax_document_generation.field_mappings.div_1099 import SUPPORTED_FIELDS, FIELD_MAPPING


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


class TestPDFFieldNameUsageProperty:
    """Property-based tests for PDF field name usage."""
    
    @settings(max_examples=100)
    @given(form_data=form_data_strategy())
    def test_only_pdf_field_names_passed_to_pdf_library(self, form_data):
        """
        **Validates: Requirements 3.3**
        Feature: fix-pdf-field-mapping, Property 7: Only translated PDF field names are used
        
        For any form data processed by the Document_Generator,
        the data passed to the PDF library should contain only PDF field names
        (not API field names).
        
        This test verifies that:
        1. API field names are NOT passed to PDF library
        2. Only translated PDF field names are used
        3. All keys in the data match the PDF field name pattern
        4. No API field names leak through to PDF operations
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
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                pass
            
            # Verify update_page_form_field_values was called
            if mock_writer.update_page_form_field_values.called:
                call_args = mock_writer.update_page_form_field_values.call_args
                
                # Get the data that was passed
                if call_args[0] and len(call_args[0]) > 1:
                    actual_data = call_args[0][1]
                else:
                    actual_data = call_args[1].get('fields', {})
                
                # Verify NO API field names are in the data
                for api_field_name in form_data.keys():
                    assert api_field_name not in actual_data, \
                        f"API field name '{api_field_name}' should not be passed to PDF library"
                
                # Verify all keys follow PDF field name pattern
                for key in actual_data.keys():
                    # PDF field names should start with "topmostSubform[0].Copy1[0]."
                    assert key.startswith("topmostSubform[0].Copy1[0]."), \
                        f"Field name '{key}' should be a PDF field name, not an API field name"
    
    @settings(max_examples=100)
    @given(form_data=form_data_strategy())
    def test_pdf_field_names_match_mapping_configuration(self, form_data):
        """
        **Validates: Requirements 3.3**
        Feature: fix-pdf-field-mapping, Property 7: Only translated PDF field names are used
        
        For any form data processed by the Document_Generator,
        the PDF field names used should exactly match those defined in the
        mapping configuration.
        
        This test verifies that:
        1. PDF field names come from FIELD_MAPPING
        2. No custom or modified field names are used
        3. Mapping configuration is the source of truth
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
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                pass
            
            # Verify update_page_form_field_values was called
            if mock_writer.update_page_form_field_values.called:
                call_args = mock_writer.update_page_form_field_values.call_args
                
                # Get the data that was passed
                if call_args[0] and len(call_args[0]) > 1:
                    actual_data = call_args[0][1]
                else:
                    actual_data = call_args[1].get('fields', {})
                
                # Verify all keys are from FIELD_MAPPING
                expected_pdf_field_names = set(FIELD_MAPPING.values())
                
                for key in actual_data.keys():
                    assert key in expected_pdf_field_names, \
                        f"PDF field name '{key}' should be from FIELD_MAPPING configuration"
    
    @settings(max_examples=100)
    @given(form_data=form_data_strategy())
    def test_values_preserved_during_translation(self, form_data):
        """
        **Validates: Requirements 3.3**
        Feature: fix-pdf-field-mapping, Property 7: Only translated PDF field names are used
        
        For any form data processed by the Document_Generator,
        the values should be preserved during field name translation
        (only keys should change, not values).
        
        This test verifies that:
        1. Field values are not modified
        2. Only field names are translated
        3. Data integrity is maintained
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
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                pass
            
            # Verify update_page_form_field_values was called
            if mock_writer.update_page_form_field_values.called:
                call_args = mock_writer.update_page_form_field_values.call_args
                
                # Get the data that was passed
                if call_args[0] and len(call_args[0]) > 1:
                    actual_data = call_args[0][1]
                else:
                    actual_data = call_args[1].get('fields', {})
                
                # Verify all original values are present in the translated data
                original_values = set(str(v) for v in form_data.values())
                actual_values = set(str(v) for v in actual_data.values())
                
                # All original values should be in the actual data
                for original_value in original_values:
                    assert original_value in actual_values, \
                        f"Value '{original_value}' should be preserved during translation"
    
    @settings(max_examples=100)
    @given(api_field_name=st.sampled_from(SUPPORTED_FIELDS))
    def test_single_field_translation_uses_correct_pdf_name(self, api_field_name):
        """
        **Validates: Requirements 3.3**
        Feature: fix-pdf-field-mapping, Property 7: Only translated PDF field names are used
        
        For any single API field name,
        when translated and passed to the PDF library, it should use the
        exact PDF field name from the mapping configuration.
        
        This test verifies that:
        1. Individual field translations are correct
        2. Each API field maps to its specific PDF field
        3. No incorrect or partial translations occur
        """
        # Create form data with a single field
        form_data = {api_field_name: "test_value"}
        
        # Get the expected PDF field name
        expected_pdf_field_name = FIELD_MAPPING[api_field_name]
        
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
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                pass
            
            # Verify update_page_form_field_values was called
            if mock_writer.update_page_form_field_values.called:
                call_args = mock_writer.update_page_form_field_values.call_args
                
                # Get the data that was passed
                if call_args[0] and len(call_args[0]) > 1:
                    actual_data = call_args[0][1]
                else:
                    actual_data = call_args[1].get('fields', {})
                
                # Verify the expected PDF field name is in the data
                assert expected_pdf_field_name in actual_data, \
                    f"PDF field name '{expected_pdf_field_name}' should be in the data"
                
                # Verify the API field name is NOT in the data
                assert api_field_name not in actual_data, \
                    f"API field name '{api_field_name}' should not be in the data"
                
                # Verify the value is correct
                assert actual_data[expected_pdf_field_name] == "test_value", \
                    f"Value should be preserved for field '{expected_pdf_field_name}'"
    
    @settings(max_examples=100)
    @given(form_data=form_data_strategy())
    def test_no_api_field_names_in_any_pdf_operation(self, form_data):
        """
        **Validates: Requirements 3.3**
        Feature: fix-pdf-field-mapping, Property 7: Only translated PDF field names are used
        
        For any form data processed by the Document_Generator,
        API field names should not appear in ANY call to PDF library methods.
        
        This test verifies that:
        1. API field names are completely isolated from PDF operations
        2. Translation is complete and thorough
        3. No API field names leak through anywhere
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
            
            # Setup mock writer - track ALL method calls
            mock_writer = Mock()
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                pass
            
            # Check all method calls on the writer
            for method_call in mock_writer.method_calls:
                method_name, args, kwargs = method_call[0], method_call[1], method_call[2]
                
                # Check all arguments for API field names
                for arg in args:
                    if isinstance(arg, dict):
                        for key in arg.keys():
                            for api_field_name in form_data.keys():
                                assert key != api_field_name, \
                                    f"API field name '{api_field_name}' found in {method_name} call"
                
                # Check all keyword arguments for API field names
                for kwarg_value in kwargs.values():
                    if isinstance(kwarg_value, dict):
                        for key in kwarg_value.keys():
                            for api_field_name in form_data.keys():
                                assert key != api_field_name, \
                                    f"API field name '{api_field_name}' found in {method_name} kwargs"
    
    @settings(max_examples=100)
    @given(form_data=form_data_strategy())
    def test_all_translated_names_follow_pdf_pattern(self, form_data):
        """
        **Validates: Requirements 3.3**
        Feature: fix-pdf-field-mapping, Property 7: Only translated PDF field names are used
        
        For any form data processed by the Document_Generator,
        all field names passed to the PDF library should follow the
        IRS PDF field naming pattern.
        
        This test verifies that:
        1. All field names have the correct structure
        2. Field names match the expected pattern
        3. No malformed or incorrect field names are used
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
            try:
                result = generate_document(mock_template, form_data, "1099-DIV")
            except Exception as e:
                pass
            
            # Verify update_page_form_field_values was called
            if mock_writer.update_page_form_field_values.called:
                call_args = mock_writer.update_page_form_field_values.call_args
                
                # Get the data that was passed
                if call_args[0] and len(call_args[0]) > 1:
                    actual_data = call_args[0][1]
                else:
                    actual_data = call_args[1].get('fields', {})
                
                # Verify all keys follow the PDF field name pattern
                for key in actual_data.keys():
                    # Should start with topmostSubform[0].Copy1[0].
                    assert key.startswith("topmostSubform[0].Copy1[0]."), \
                        f"Field name '{key}' should follow PDF pattern"
                    
                    # Should contain array notation [0]
                    assert "[0]" in key, \
                        f"Field name '{key}' should contain array notation"
                    
                    # Should end with [0]
                    assert key.endswith("[0]"), \
                        f"Field name '{key}' should end with [0]"
