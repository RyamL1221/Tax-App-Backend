"""
Property Test: Hidden Flag Clearing

Feature: pymupdf-migration
Property 5: Hidden Flag Clearing

Tests that for any populated form field in a generated PDF, the hidden flag
(bit 1 of field_flags) is cleared (value 0).

**Validates: Requirements 2.5, 10.5**
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


class TestHiddenFlagClearingProperty:
    """Property-based tests for hidden flag clearing."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy()
    )
    def test_hidden_flag_cleared_for_populated_fields(self, form_data, document_type):
        """
        **Validates: Requirements 2.5, 10.5**
        Feature: pymupdf-migration, Property 5: Hidden Flag Clearing
        
        For any populated form field in a generated PDF,
        the hidden flag (bit 1 of field_flags) SHALL be cleared (value 0).
        
        This test verifies that:
        1. field_flags is modified for each populated field
        2. The hidden flag (bit 1) is cleared using bitwise AND with ~(1 << 1)
        3. Fields remain visible after population
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
            # Start with various initial flag values (some with hidden flag set)
            mock_widgets = []
            for i, (pdf_field_name, value) in enumerate(mapped_data.items()):
                mock_widget = Mock()
                mock_widget.field_name = pdf_field_name
                mock_widget.field_value = None
                # Set initial flags - some with hidden flag (bit 1) set
                initial_flags = (1 << 1) if i % 2 == 0 else 0  # Alternate between hidden and visible
                mock_widget.field_flags = initial_flags
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
            
            # CRITICAL VERIFICATION: Hidden flag (bit 1) is cleared for all populated fields
            for widget in mock_widgets:
                if widget.field_name in mapped_data:
                    # Check that the hidden flag (bit 1) is cleared
                    hidden_flag_set = (widget.field_flags & (1 << 1)) != 0
                    
                    assert not hidden_flag_set, \
                        f"Hidden flag (bit 1) should be cleared for field '{widget.field_name}', " \
                        f"but field_flags is {widget.field_flags} (binary: {bin(widget.field_flags)})"
    
    @settings(max_examples=100, deadline=None)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy(),
        initial_flags=st.integers(min_value=0, max_value=255)
    )
    def test_hidden_flag_cleared_regardless_of_initial_state(self, form_data, document_type, initial_flags):
        """
        **Validates: Requirements 2.5, 10.5**
        Feature: pymupdf-migration, Property 5: Hidden Flag Clearing
        
        For any populated form field with any initial field_flags value,
        the hidden flag (bit 1) SHALL be cleared after population.
        
        This test verifies that the hidden flag is cleared regardless of
        the initial state of other flags.
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
                # Use the generated initial_flags value
                mock_widget.field_flags = initial_flags
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
            
            # CRITICAL VERIFICATION: Hidden flag (bit 1) is cleared regardless of initial state
            for widget in mock_widgets:
                if widget.field_name in mapped_data:
                    # Check that the hidden flag (bit 1) is cleared
                    hidden_flag_set = (widget.field_flags & (1 << 1)) != 0
                    
                    assert not hidden_flag_set, \
                        f"Hidden flag (bit 1) should be cleared for field '{widget.field_name}' " \
                        f"(initial flags: {initial_flags}, final flags: {widget.field_flags})"
    
    @settings(max_examples=100, deadline=None)
    @given(
        form_data=form_data_strategy(),
        document_type=document_type_strategy()
    )
    def test_other_flags_preserved_when_clearing_hidden(self, form_data, document_type):
        """
        **Validates: Requirements 2.5, 10.5**
        Feature: pymupdf-migration, Property 5: Hidden Flag Clearing
        
        For any populated form field,
        when clearing the hidden flag (bit 1), other flag bits SHALL be preserved.
        
        This test verifies that the bitwise AND operation (~(1 << 1))
        only clears bit 1 and leaves other bits unchanged.
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
            # Use flags with multiple bits set to verify preservation
            mock_widgets = []
            for i, (pdf_field_name, value) in enumerate(mapped_data.items()):
                mock_widget = Mock()
                mock_widget.field_name = pdf_field_name
                mock_widget.field_value = None
                # Set flags with multiple bits including hidden flag
                # Example: 0b00001111 (bits 0-3 set) or 0b00001110 (bits 1-3 set)
                initial_flags = 0b00001111 if i % 2 == 0 else 0b00001110
                mock_widget.field_flags = initial_flags
                mock_widget._initial_flags = initial_flags  # Store for verification
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
            
            # CRITICAL VERIFICATION: Other flags are preserved when clearing hidden flag
            for widget in mock_widgets:
                if widget.field_name in mapped_data:
                    initial_flags = widget._initial_flags
                    final_flags = widget.field_flags
                    
                    # Calculate expected flags: initial_flags & ~(1 << 1)
                    expected_flags = initial_flags & ~(1 << 1)
                    
                    # Verify that only bit 1 was cleared
                    assert final_flags == expected_flags, \
                        f"For field '{widget.field_name}', expected flags to be {expected_flags} " \
                        f"(initial {initial_flags} with bit 1 cleared), but got {final_flags}"
                    
                    # Verify hidden flag is cleared
                    hidden_flag_set = (final_flags & (1 << 1)) != 0
                    assert not hidden_flag_set, \
                        f"Hidden flag should be cleared for field '{widget.field_name}'"


def test_hidden_flag_clearing_with_real_template():
    """
    Unit test: Verify hidden flag clearing with real 1099-DIV template.
    
    This test uses the actual template to verify that generated PDFs
    have visible form fields (hidden flag cleared).
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
    
    # Open the generated PDF and verify fields are visible (hidden flag cleared)
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Check that populated fields don't have the hidden flag set
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                if widget.field_value:
                    # Check that hidden flag (bit 1) is not set
                    hidden_flag_set = (widget.field_flags & (1 << 1)) != 0
                    assert not hidden_flag_set, \
                        f"Field '{widget.field_name}' should not have hidden flag set"
    
    doc.close()


def test_hidden_flag_clearing_empty_data():
    """
    Unit test: Verify behavior with empty form data.
    
    With no form data, no fields should be modified, but PDF should still be valid.
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
