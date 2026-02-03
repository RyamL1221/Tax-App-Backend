"""
Property Test: String Value Conversion

Feature: pymupdf-migration
Property 19: String Value Conversion

Tests that for any form field value (numeric, boolean, string), the value is
converted to its string representation before setting widget.field_value.

**Validates: Requirements 10.3**
"""

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import Mock, patch
import os

from tax_document_generation.document_generator import generate_document


def get_1099_div_template():
    """Load the actual 1099-DIV template from the project root."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    tax_doc_dir = os.path.dirname(test_dir)
    project_root = os.path.dirname(tax_doc_dir)
    template_path = os.path.join(project_root, "1099-DIV.pdf")
    
    if not os.path.exists(template_path):
        pytest.skip(f"1099-DIV template not found at {template_path}")
    
    with open(template_path, "rb") as f:
        return f.read()


# Strategy for generating form data with various types
def mixed_type_form_data_strategy():
    """Generate form data dictionaries with various value types."""
    return st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        values=st.one_of(
            st.text(min_size=0, max_size=50, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc'),
                blacklist_characters='\n\r\t'
            )),
            st.integers(min_value=-1000000, max_value=1000000),
            st.floats(min_value=-1000000.0, max_value=1000000.0, allow_nan=False, allow_infinity=False),
            st.booleans()
        ),
        min_size=1,
        max_size=10
    )


def document_type_strategy():
    """Generate valid document types."""
    return st.sampled_from(["1099-DIV", "1099-INT", "W-2"])


class TestStringValueConversionProperty:
    """Property-based tests for string value conversion."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        form_data=mixed_type_form_data_strategy(),
        document_type=document_type_strategy()
    )
    def test_all_values_converted_to_strings(self, form_data, document_type):
        """
        **Validates: Requirements 10.3**
        Feature: pymupdf-migration, Property 19: String Value Conversion
        
        For any form field value (numeric, boolean, string),
        the value SHALL be converted to its string representation
        before setting widget.field_value.
        
        This test verifies that:
        1. Integer values are converted to strings
        2. Float values are converted to strings
        3. Boolean values are converted to strings
        4. String values remain strings
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            # Create mapped data with PDF field names
            mapped_data = {f"pdf_field_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock widgets with PDF field names
            mock_widgets = []
            for pdf_field_name, value in mapped_data.items():
                mock_widget = Mock()
                mock_widget.field_name = pdf_field_name
                mock_widget.field_value = None
                mock_widget.field_flags = 0
                mock_widget.update = Mock()
                mock_widgets.append(mock_widget)
            
            # Setup mock page with widgets
            mock_page = Mock()
            mock_page.widgets.return_value = mock_widgets
            
            # Setup mock PDF document
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_doc.close = Mock()
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # Generate the document
            result = generate_document(mock_template, form_data, document_type)
            
            # CRITICAL VERIFICATION: All values are converted to strings
            for widget in mock_widgets:
                if widget.field_name in mapped_data:
                    original_value = mapped_data[widget.field_name]
                    set_value = widget.field_value
                    
                    # Verify the value is a string
                    assert isinstance(set_value, str), \
                        f"Field '{widget.field_name}' should have string value, " \
                        f"but got {type(set_value).__name__}: {set_value}"
                    
                    # Verify the string matches str(original_value)
                    expected_str = str(original_value)
                    assert set_value == expected_str, \
                        f"Field '{widget.field_name}' should have value '{expected_str}', " \
                        f"but got '{set_value}'"
    
    @settings(max_examples=100, deadline=None)
    @given(
        integer_value=st.integers(min_value=-1000000, max_value=1000000),
        document_type=document_type_strategy()
    )
    def test_integer_values_converted_to_strings(self, integer_value, document_type):
        """
        **Validates: Requirements 10.3**
        Feature: pymupdf-migration, Property 19: String Value Conversion
        
        For any integer form field value,
        the value SHALL be converted to its string representation.
        
        This test specifically verifies integer conversion.
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        form_data = {"testField": integer_value}
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {"pdf_testField": integer_value}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock widget
            mock_widget = Mock()
            mock_widget.field_name = "pdf_testField"
            mock_widget.field_value = None
            mock_widget.field_flags = 0
            mock_widget.update = Mock()
            
            # Setup mock page with widget
            mock_page = Mock()
            mock_page.widgets.return_value = [mock_widget]
            
            # Setup mock PDF document
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_doc.close = Mock()
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # Generate the document
            result = generate_document(mock_template, form_data, document_type)
            
            # CRITICAL VERIFICATION: Integer was converted to string
            assert isinstance(mock_widget.field_value, str), \
                f"Integer value {integer_value} should be converted to string"
            assert mock_widget.field_value == str(integer_value), \
                f"Integer value {integer_value} should be converted to '{str(integer_value)}', " \
                f"but got '{mock_widget.field_value}'"
    
    @settings(max_examples=100, deadline=None)
    @given(
        float_value=st.floats(min_value=-1000000.0, max_value=1000000.0, allow_nan=False, allow_infinity=False),
        document_type=document_type_strategy()
    )
    def test_float_values_converted_to_strings(self, float_value, document_type):
        """
        **Validates: Requirements 10.3**
        Feature: pymupdf-migration, Property 19: String Value Conversion
        
        For any float form field value,
        the value SHALL be converted to its string representation.
        
        This test specifically verifies float conversion.
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        form_data = {"testField": float_value}
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {"pdf_testField": float_value}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock widget
            mock_widget = Mock()
            mock_widget.field_name = "pdf_testField"
            mock_widget.field_value = None
            mock_widget.field_flags = 0
            mock_widget.update = Mock()
            
            # Setup mock page with widget
            mock_page = Mock()
            mock_page.widgets.return_value = [mock_widget]
            
            # Setup mock PDF document
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_doc.close = Mock()
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # Generate the document
            result = generate_document(mock_template, form_data, document_type)
            
            # CRITICAL VERIFICATION: Float was converted to string
            assert isinstance(mock_widget.field_value, str), \
                f"Float value {float_value} should be converted to string"
            assert mock_widget.field_value == str(float_value), \
                f"Float value {float_value} should be converted to '{str(float_value)}', " \
                f"but got '{mock_widget.field_value}'"
    
    @settings(max_examples=100, deadline=None)
    @given(
        boolean_value=st.booleans(),
        document_type=document_type_strategy()
    )
    def test_boolean_values_converted_to_strings(self, boolean_value, document_type):
        """
        **Validates: Requirements 10.3**
        Feature: pymupdf-migration, Property 19: String Value Conversion
        
        For any boolean form field value,
        the value SHALL be converted to its string representation.
        
        This test specifically verifies boolean conversion.
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        form_data = {"testField": boolean_value}
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {"pdf_testField": boolean_value}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock widget
            mock_widget = Mock()
            mock_widget.field_name = "pdf_testField"
            mock_widget.field_value = None
            mock_widget.field_flags = 0
            mock_widget.update = Mock()
            
            # Setup mock page with widget
            mock_page = Mock()
            mock_page.widgets.return_value = [mock_widget]
            
            # Setup mock PDF document
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.is_form_pdf = True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_doc.close = Mock()
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # Generate the document
            result = generate_document(mock_template, form_data, document_type)
            
            # CRITICAL VERIFICATION: Boolean was converted to string
            assert isinstance(mock_widget.field_value, str), \
                f"Boolean value {boolean_value} should be converted to string"
            assert mock_widget.field_value == str(boolean_value), \
                f"Boolean value {boolean_value} should be converted to '{str(boolean_value)}', " \
                f"but got '{mock_widget.field_value}'"


def test_string_value_conversion_with_real_template():
    """
    Unit test: Verify string value conversion with real 1099-DIV template.
    
    This test uses the actual template to verify that various value types
    are converted to strings.
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    # Mix of different value types
    form_data = {
        "payerName": "Test Payer Company",  # String
        "payerTIN": "12-3456789",  # String
        "recipientName": "John Doe",  # String
        "recipientTIN": "123-45-6789",  # String
        "totalOrdinaryDividends": 1000.50,  # Float
        "qualifiedDividends": 500,  # Integer
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open the generated PDF and verify fields have string values
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Check that populated fields have string values
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                if widget.field_value:
                    # All field values should be strings
                    assert isinstance(widget.field_value, str), \
                        f"Field '{widget.field_name}' should have string value, " \
                        f"but got {type(widget.field_value).__name__}"
    
    doc.close()


def test_string_value_conversion_numeric_types():
    """
    Unit test: Verify conversion of various numeric types.
    
    This test specifically checks integer and float conversion.
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    # Various numeric types
    form_data = {
        "totalOrdinaryDividends": 1234,  # Integer
        "qualifiedDividends": 567.89,  # Float
        "totalCapitalGainDistributions": 0,  # Zero integer
        "federalIncomeTaxWithheld": 0.0,  # Zero float
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open the generated PDF
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Verify at least some fields were populated
    populated_count = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                if widget.field_value:
                    populated_count += 1
                    # All values should be strings
                    assert isinstance(widget.field_value, str)
    
    doc.close()
    
    # At least some fields should be populated
    assert populated_count > 0
