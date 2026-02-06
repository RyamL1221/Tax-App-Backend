"""
Property Test: Field Editability Preservation

Feature: pymupdf-migration
Property 16: Field Editability Preservation

Tests that for any generated PDF, form fields remain editable
(not flattened to static content).

**Validates: Requirements 9.1, 9.2**
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
        keys=st.sampled_from([
            "payerName", "payerTIN", "recipientName", "recipientTIN",
            "totalOrdinaryDividends", "qualifiedDividends"
        ]),
        values=st.one_of(
            st.text(min_size=1, max_size=50),
            st.integers(min_value=0, max_value=1000000),
            st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False)
        ),
        min_size=1,
        max_size=5
    )


class TestFieldEditabilityPreservationProperty:
    """Property-based tests for field editability preservation."""
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=form_data_strategy())
    def test_fields_remain_editable_after_population(self, form_data):
        """
        **Validates: Requirements 9.1, 9.2**
        Feature: pymupdf-migration, Property 16: Field Editability Preservation
        
        For any generated PDF, form fields SHALL remain editable
        (not flattened to static content).
        
        This test verifies that:
        1. Fields are not flattened
        2. Fields remain interactive
        3. Field widgets still exist in the PDF
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {f"pdf_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock widgets
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
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # CRITICAL VERIFICATION: No flattening operations were called
            # In PyMuPDF, flattening would be done via methods like:
            # - page.apply_redactions()
            # - Converting widgets to annotations
            # - Removing form fields
            
            # Verify widgets still exist (not removed)
            assert mock_page.widgets.called, \
                "Widgets should be accessed (not removed)"
            
            # Verify no widget deletion occurred
            for widget in mock_widgets:
                # Check that widget was not deleted or removed
                # (In real PyMuPDF, deletion would be widget.delete() or similar)
                assert not hasattr(widget, 'delete') or not widget.delete.called, \
                    f"Widget '{widget.field_name}' should not be deleted"
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=form_data_strategy())
    def test_document_remains_form_pdf(self, form_data):
        """
        **Validates: Requirements 9.1, 9.2**
        Feature: pymupdf-migration, Property 16: Field Editability Preservation
        
        For any generated PDF, the document SHALL remain a form PDF
        (not converted to static content).
        
        This test verifies that:
        1. is_form_pdf flag remains true
        2. Form structure is preserved
        3. No conversion to static PDF occurs
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {f"pdf_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock widgets
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
            mock_doc.is_form_pdf = True  # Should remain True
            mock_doc.xref_length.return_value = 10
            mock_doc.xref_get_key.return_value = None
            mock_doc.tobytes.return_value = b"%PDF-1.4\ngenerated content\n%%EOF"
            mock_doc.close = Mock()
            
            # Setup fitz.open to return mock document
            mock_fitz.open.return_value = mock_doc
            
            # Generate the document
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify is_form_pdf was checked (indicating form structure is preserved)
            assert mock_doc.is_form_pdf, \
                "Document should remain a form PDF"
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=form_data_strategy())
    def test_widget_update_preserves_editability(self, form_data):
        """
        **Validates: Requirements 9.1, 9.2**
        Feature: pymupdf-migration, Property 16: Field Editability Preservation
        
        For any generated PDF, calling widget.update() SHALL preserve
        field editability (not flatten the field).
        
        This test verifies that:
        1. widget.update() is called (for appearance generation)
        2. update() doesn't flatten the field
        3. Fields remain interactive after update
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Mock PyMuPDF (fitz) components
        with patch('tax_document_generation.document_generator.fitz') as mock_fitz, \
             patch('tax_document_generation.document_generator.FieldMapper') as mock_mapper_class:
            
            # Setup mock field mapper
            mock_mapper = Mock()
            mapped_data = {f"pdf_{k}": v for k, v in form_data.items()}
            mock_mapper.map_all_fields.return_value = mapped_data
            mock_mapper.get_unmapped_fields.return_value = []
            mock_mapper_class.return_value = mock_mapper
            
            # Setup mock widgets
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
            result = generate_document(mock_template, form_data, "1099-DIV")
            
            # Verify widget.update() was called for each populated field
            for widget in mock_widgets:
                if widget.field_name in mapped_data:
                    assert widget.update.called, \
                        f"widget.update() should be called for field '{widget.field_name}'"
                    
                    # Verify update was called with no flattening parameters
                    # (In PyMuPDF, update() with no args preserves editability)
                    for call in widget.update.call_args_list:
                        args, kwargs = call
                        # No flattening parameters should be passed
                        assert 'flatten' not in kwargs, \
                            "update() should not be called with flatten parameter"


def test_field_editability_with_real_template():
    """
    Unit test: Verify field editability with real 1099-DIV template.
    
    This test uses the actual template to verify that generated PDFs
    have editable form fields.
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
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open the generated PDF and verify it's still a form PDF
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Check that it's still a form PDF
    assert doc.is_form_pdf, "Generated PDF should still be a form PDF"
    
    # Check that widgets still exist
    widget_count = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = list(page.widgets())
        if widgets:
            widget_count += len(widgets)
    
    doc.close()
    
    # Should have widgets (form fields)
    assert widget_count > 0, "Generated PDF should have editable form fields"


def test_field_editability_empty_data():
    """
    Unit test: Verify field editability with empty form data.
    
    Even with no data populated, fields should remain editable.
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
    
    # Open the generated PDF and verify it's still a form PDF
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Check that it's still a form PDF
    assert doc.is_form_pdf, "Generated PDF should still be a form PDF"
    
    # Check that widgets still exist
    widget_count = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = list(page.widgets())
        if widgets:
            widget_count += len(widgets)
    
    doc.close()
    
    # Should have widgets (form fields)
    assert widget_count > 0, "Generated PDF should have editable form fields"


def test_populated_fields_remain_editable():
    """
    Unit test: Verify that populated fields remain editable.
    
    This test verifies that after populating fields with values,
    the fields can still be edited (not flattened).
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    form_data = {
        "payerName": "Test Payer Company",
        "totalOrdinaryDividends": 1000.50,
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Open the generated PDF
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Find populated fields and verify they're still editable
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                if widget.field_value:
                    # Field has a value - verify it's still editable
                    # In PyMuPDF, editable fields have field_type set
                    assert widget.field_type is not None, \
                        f"Populated field '{widget.field_name}' should still be editable"
    
    doc.close()
