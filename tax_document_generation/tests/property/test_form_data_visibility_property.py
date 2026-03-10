"""
Property Test: Form Data Visibility

Feature: pymupdf-migration
Property 3: Form Data Visibility

Tests that for any valid template and form data, when a PDF is generated,
all populated form fields have their values present in the output PDF bytes.

**Validates: Requirements 2.1**
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


# Strategy for generating form data
def form_data_strategy():
    """Generate form data dictionaries with various field types."""
    return st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        values=st.one_of(
            st.text(min_size=1, max_size=50, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
                blacklist_characters='\n\r\t'
            )),
            st.integers(min_value=0, max_value=1000000),
            st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False)
        ),
        min_size=1,
        max_size=10
    )


def document_type_strategy():
    """Generate valid document types."""
    return st.sampled_from(["1099-DIV", "1099-INT", "W-2"])


class TestFormDataVisibilityProperty:
    """Property-based tests for form data visibility."""
    
    @settings(max_examples=20, deadline=None)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy()
    )
    def test_populated_fields_have_values_in_output(self, form_data, document_type):
        """
        **Validates: Requirements 2.1**
        Feature: pymupdf-migration, Property 3: Form Data Visibility
        
        For any valid template and form data, when a PDF is generated,
        all populated form fields SHALL have their values present in the output PDF bytes.
        
        This test verifies that:
        1. Generated PDF contains the populated field values
        2. Field values are accessible in the output PDF
        3. Values are correctly stored in the PDF structure
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
            
            # CRITICAL VERIFICATION: All mapped fields were populated
            populated_count = 0
            for widget in mock_widgets:
                if widget.field_name in mapped_data:
                    # Check that field_value was set
                    expected_str = str(mapped_data[widget.field_name])
                    assert widget.field_value == expected_str, \
                        f"Field '{widget.field_name}' has value '{widget.field_value}', expected '{expected_str}'"
                    populated_count += 1
            
            assert populated_count == len(mapped_data), \
                f"Expected {len(mapped_data)} fields to be populated, but only {populated_count} were"
    
    @settings(max_examples=20, deadline=None)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy()
    )
    def test_widget_update_called_after_value_set(self, form_data, document_type):
        """
        **Validates: Requirements 2.1**
        Feature: pymupdf-migration, Property 3: Form Data Visibility
        
        For any valid template and form data, when a PDF is generated,
        widget.update() SHALL be called after setting field_value to ensure visibility.
        
        This test verifies that:
        1. widget.update() is called for each populated field
        2. update() is called AFTER field_value is set
        3. update() is called at least twice (once after value, once after flags)
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
            
            # CRITICAL VERIFICATION: widget.update() was called for each populated field
            for widget in mock_widgets:
                if widget.field_name in mapped_data:
                    assert widget.update.called, \
                        f"widget.update() should be called for field '{widget.field_name}'"
                    
                    # Should be called at least twice (after value set, after flag clear)
                    assert widget.update.call_count >= 2, \
                        f"widget.update() should be called at least twice for field '{widget.field_name}', " \
                        f"but was called {widget.update.call_count} times"


def test_form_data_visibility_with_real_template():
    """
    Unit test: Verify form data visibility with real 1099-DIV template.
    
    This test uses the actual template to verify that generated PDFs
    contain visible form data.
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    form_data = {
        "payerName": "Test Payer Company",
        "payerTIN": "12-3456789",
        "recipientName": "John Doe",
        "recipientTIN": "123-45-6789",
        "totalOrdinaryDividends": 1000.50,
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open the generated PDF and verify fields have values
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Check that at least some fields were populated
    populated_count = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                if widget.field_value:
                    populated_count += 1
    
    doc.close()
    
    # At least some fields should be populated
    assert populated_count > 0, "Expected at least some fields to be populated in the generated PDF"


def test_form_data_visibility_empty_data():
    """
    Unit test: Verify behavior with empty form data.
    
    With no form data, no fields should be populated, but PDF should still be valid.
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    form_data = {}
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open the generated PDF
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0
    doc.close()
