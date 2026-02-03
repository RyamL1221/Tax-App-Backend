"""
Property Test: Field Property Preservation

Feature: pymupdf-migration
Property 17: Field Property Preservation

Tests that for any template PDF with form fields, the generated PDF preserves
all field properties (type, rect, font, etc.) except field_value.

**Validates: Requirements 9.3**
"""

import pytest
from hypothesis import given, settings, strategies as st
import os

try:
    import fitz  # PyMuPDF
except ImportError:
    pytest.skip("PyMuPDF not installed", allow_module_level=True)

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


class TestFieldPropertyPreservationProperty:
    """Property-based tests for field property preservation."""
    
    @settings(max_examples=100, deadline=None)
    @given(form_data=form_data_strategy())
    def test_field_type_preserved(self, form_data):
        """
        **Validates: Requirements 9.3**
        Feature: pymupdf-migration, Property 17: Field Property Preservation
        
        For any template PDF with form fields, the generated PDF SHALL preserve
        all field types (text, checkbox, etc.).
        
        This test verifies that:
        1. Field types remain unchanged
        2. No fields are converted to different types
        3. Field type properties are preserved
        """
        template = get_1099_div_template()
        
        # Open template to get original field types
        template_doc = fitz.open(stream=template, filetype="pdf")
        original_field_types = {}
        
        for page_num in range(len(template_doc)):
            page = template_doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                if widget.field_name:
                    original_field_types[widget.field_name] = widget.field_type
        
        template_doc.close()
        
        # Generate document
        result = generate_document(template, form_data, "1099-DIV")
        
        # Open generated document and verify field types
        result_doc = fitz.open(stream=result, filetype="pdf")
        
        for page_num in range(len(result_doc)):
            page = result_doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                if widget.field_name and widget.field_name in original_field_types:
                    assert widget.field_type == original_field_types[widget.field_name], \
                        f"Field '{widget.field_name}' type changed from {original_field_types[widget.field_name]} to {widget.field_type}"
        
        result_doc.close()
    
    @settings(max_examples=100, deadline=None)
    @given(form_data=form_data_strategy())
    def test_field_rect_preserved(self, form_data):
        """
        **Validates: Requirements 9.3**
        Feature: pymupdf-migration, Property 17: Field Property Preservation
        
        For any template PDF with form fields, the generated PDF SHALL preserve
        all field rectangles (position and size).
        
        This test verifies that:
        1. Field positions remain unchanged
        2. Field sizes remain unchanged
        3. Field rectangles are preserved
        """
        template = get_1099_div_template()
        
        # Open template to get original field rects
        template_doc = fitz.open(stream=template, filetype="pdf")
        original_field_rects = {}
        
        for page_num in range(len(template_doc)):
            page = template_doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                if widget.field_name:
                    original_field_rects[widget.field_name] = widget.rect
        
        template_doc.close()
        
        # Generate document
        result = generate_document(template, form_data, "1099-DIV")
        
        # Open generated document and verify field rects
        result_doc = fitz.open(stream=result, filetype="pdf")
        
        for page_num in range(len(result_doc)):
            page = result_doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                if widget.field_name and widget.field_name in original_field_rects:
                    # Compare rects (allowing for small floating point differences)
                    original_rect = original_field_rects[widget.field_name]
                    assert abs(widget.rect.x0 - original_rect.x0) < 0.1, \
                        f"Field '{widget.field_name}' rect x0 changed"
                    assert abs(widget.rect.y0 - original_rect.y0) < 0.1, \
                        f"Field '{widget.field_name}' rect y0 changed"
                    assert abs(widget.rect.x1 - original_rect.x1) < 0.1, \
                        f"Field '{widget.field_name}' rect x1 changed"
                    assert abs(widget.rect.y1 - original_rect.y1) < 0.1, \
                        f"Field '{widget.field_name}' rect y1 changed"
        
        result_doc.close()
    
    @settings(max_examples=100, deadline=None)
    @given(form_data=form_data_strategy())
    def test_field_name_preserved(self, form_data):
        """
        **Validates: Requirements 9.3**
        Feature: pymupdf-migration, Property 17: Field Property Preservation
        
        For any template PDF with form fields, the generated PDF SHALL preserve
        all field names.
        
        This test verifies that:
        1. Field names remain unchanged
        2. No fields are renamed
        3. All original fields still exist
        """
        template = get_1099_div_template()
        
        # Open template to get original field names
        template_doc = fitz.open(stream=template, filetype="pdf")
        original_field_names = set()
        
        for page_num in range(len(template_doc)):
            page = template_doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                if widget.field_name:
                    original_field_names.add(widget.field_name)
        
        template_doc.close()
        
        # Generate document
        result = generate_document(template, form_data, "1099-DIV")
        
        # Open generated document and verify field names
        result_doc = fitz.open(stream=result, filetype="pdf")
        result_field_names = set()
        
        for page_num in range(len(result_doc)):
            page = result_doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                if widget.field_name:
                    result_field_names.add(widget.field_name)
        
        result_doc.close()
        
        # Verify all original field names are preserved
        assert original_field_names == result_field_names, \
            f"Field names changed. Original: {original_field_names}, Result: {result_field_names}"
    
    @settings(max_examples=100, deadline=None)
    @given(form_data=form_data_strategy())
    def test_field_count_preserved(self, form_data):
        """
        **Validates: Requirements 9.3**
        Feature: pymupdf-migration, Property 17: Field Property Preservation
        
        For any template PDF with form fields, the generated PDF SHALL preserve
        the total number of form fields.
        
        This test verifies that:
        1. No fields are added
        2. No fields are removed
        3. Field count remains constant
        """
        template = get_1099_div_template()
        
        # Open template to count fields
        template_doc = fitz.open(stream=template, filetype="pdf")
        original_field_count = 0
        
        for page_num in range(len(template_doc)):
            page = template_doc[page_num]
            widgets = list(page.widgets())
            original_field_count += len(widgets)
        
        template_doc.close()
        
        # Generate document
        result = generate_document(template, form_data, "1099-DIV")
        
        # Open generated document and count fields
        result_doc = fitz.open(stream=result, filetype="pdf")
        result_field_count = 0
        
        for page_num in range(len(result_doc)):
            page = result_doc[page_num]
            widgets = list(page.widgets())
            result_field_count += len(widgets)
        
        result_doc.close()
        
        # Verify field count is preserved
        assert original_field_count == result_field_count, \
            f"Field count changed from {original_field_count} to {result_field_count}"


def test_field_property_preservation_with_real_template():
    """
    Unit test: Verify field property preservation with real 1099-DIV template.
    
    This test uses the actual template to verify that field properties
    are preserved after document generation.
    """
    template = get_1099_div_template()
    
    # Open template to get original properties
    template_doc = fitz.open(stream=template, filetype="pdf")
    original_properties = {}
    
    for page_num in range(len(template_doc)):
        page = template_doc[page_num]
        widgets = list(page.widgets())
        for widget in widgets:
            if widget.field_name:
                original_properties[widget.field_name] = {
                    'type': widget.field_type,
                    'rect': widget.rect,
                }
    
    template_doc.close()
    
    # Generate document
    form_data = {
        "payerName": "Test Payer Company",
        "payerTIN": "12-3456789",
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Open generated document and verify properties
    result_doc = fitz.open(stream=result, filetype="pdf")
    
    for page_num in range(len(result_doc)):
        page = result_doc[page_num]
        widgets = list(page.widgets())
        for widget in widgets:
            if widget.field_name and widget.field_name in original_properties:
                original = original_properties[widget.field_name]
                
                # Verify type preserved
                assert widget.field_type == original['type'], \
                    f"Field '{widget.field_name}' type changed"
                
                # Verify rect preserved (with tolerance)
                assert abs(widget.rect.x0 - original['rect'].x0) < 0.1, \
                    f"Field '{widget.field_name}' rect changed"
    
    result_doc.close()


def test_field_property_preservation_empty_data():
    """
    Unit test: Verify field property preservation with empty form data.
    
    Even with no data populated, field properties should be preserved.
    """
    template = get_1099_div_template()
    
    # Open template to get original field count
    template_doc = fitz.open(stream=template, filetype="pdf")
    original_field_count = 0
    
    for page_num in range(len(template_doc)):
        page = template_doc[page_num]
        widgets = list(page.widgets())
        original_field_count += len(widgets)
    
    template_doc.close()
    
    # Generate document with empty data
    form_data = {}
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Open generated document and verify field count
    result_doc = fitz.open(stream=result, filetype="pdf")
    result_field_count = 0
    
    for page_num in range(len(result_doc)):
        page = result_doc[page_num]
        widgets = list(page.widgets())
        result_field_count += len(widgets)
    
    result_doc.close()
    
    # Verify field count is preserved
    assert original_field_count == result_field_count, \
        f"Field count changed from {original_field_count} to {result_field_count}"
