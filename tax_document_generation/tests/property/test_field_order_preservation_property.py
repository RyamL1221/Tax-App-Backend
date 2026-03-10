"""
Property Test: Field Order Preservation

Feature: pymupdf-migration
Property 18: Field Order Preservation

Tests that for any template PDF with multiple form fields, the generated PDF
maintains the same field order and tab sequence.

**Validates: Requirements 9.4**
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


class TestFieldOrderPreservationProperty:
    """Property-based tests for field order preservation."""
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=form_data_strategy())
    def test_field_order_preserved(self, form_data):
        """
        **Validates: Requirements 9.4**
        Feature: pymupdf-migration, Property 18: Field Order Preservation
        
        For any template PDF with multiple form fields, the generated PDF SHALL
        maintain the same field order.
        
        This test verifies that:
        1. Fields appear in the same order
        2. Field sequence is preserved
        3. No reordering occurs
        """
        template = get_1099_div_template()
        
        # Open template to get original field order
        template_doc = fitz.open(stream=template, filetype="pdf")
        original_field_order = []
        
        for page_num in range(len(template_doc)):
            page = template_doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                if widget.field_name:
                    original_field_order.append((page_num, widget.field_name))
        
        template_doc.close()
        
        # Generate document
        result = generate_document(template, form_data, "1099-DIV")
        
        # Open generated document and verify field order
        result_doc = fitz.open(stream=result, filetype="pdf")
        result_field_order = []
        
        for page_num in range(len(result_doc)):
            page = result_doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                if widget.field_name:
                    result_field_order.append((page_num, widget.field_name))
        
        result_doc.close()
        
        # Verify field order is preserved
        assert original_field_order == result_field_order, \
            f"Field order changed.\nOriginal: {original_field_order}\nResult: {result_field_order}"
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=form_data_strategy())
    def test_page_field_distribution_preserved(self, form_data):
        """
        **Validates: Requirements 9.4**
        Feature: pymupdf-migration, Property 18: Field Order Preservation
        
        For any template PDF with multiple pages, the generated PDF SHALL
        maintain the same distribution of fields across pages.
        
        This test verifies that:
        1. Fields remain on their original pages
        2. No fields move between pages
        3. Page structure is preserved
        """
        template = get_1099_div_template()
        
        # Open template to get field distribution by page
        template_doc = fitz.open(stream=template, filetype="pdf")
        original_page_fields = {}
        
        for page_num in range(len(template_doc)):
            page = template_doc[page_num]
            widgets = list(page.widgets())
            field_names = [w.field_name for w in widgets if w.field_name]
            original_page_fields[page_num] = set(field_names)
        
        template_doc.close()
        
        # Generate document
        result = generate_document(template, form_data, "1099-DIV")
        
        # Open generated document and verify field distribution
        result_doc = fitz.open(stream=result, filetype="pdf")
        result_page_fields = {}
        
        for page_num in range(len(result_doc)):
            page = result_doc[page_num]
            widgets = list(page.widgets())
            field_names = [w.field_name for w in widgets if w.field_name]
            result_page_fields[page_num] = set(field_names)
        
        result_doc.close()
        
        # Verify field distribution is preserved
        assert original_page_fields == result_page_fields, \
            f"Field distribution changed.\nOriginal: {original_page_fields}\nResult: {result_page_fields}"
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=form_data_strategy())
    def test_field_sequence_within_page_preserved(self, form_data):
        """
        **Validates: Requirements 9.4**
        Feature: pymupdf-migration, Property 18: Field Order Preservation
        
        For any template PDF page with multiple fields, the generated PDF SHALL
        maintain the same field sequence within each page.
        
        This test verifies that:
        1. Within-page field order is preserved
        2. Tab sequence remains unchanged
        3. Field iteration order is consistent
        """
        template = get_1099_div_template()
        
        # Open template to get field sequence per page
        template_doc = fitz.open(stream=template, filetype="pdf")
        original_page_sequences = {}
        
        for page_num in range(len(template_doc)):
            page = template_doc[page_num]
            widgets = list(page.widgets())
            field_sequence = [w.field_name for w in widgets if w.field_name]
            original_page_sequences[page_num] = field_sequence
        
        template_doc.close()
        
        # Generate document
        result = generate_document(template, form_data, "1099-DIV")
        
        # Open generated document and verify field sequences
        result_doc = fitz.open(stream=result, filetype="pdf")
        result_page_sequences = {}
        
        for page_num in range(len(result_doc)):
            page = result_doc[page_num]
            widgets = list(page.widgets())
            field_sequence = [w.field_name for w in widgets if w.field_name]
            result_page_sequences[page_num] = field_sequence
        
        result_doc.close()
        
        # Verify field sequences are preserved
        for page_num in original_page_sequences:
            assert original_page_sequences[page_num] == result_page_sequences.get(page_num, []), \
                f"Field sequence on page {page_num} changed.\n" \
                f"Original: {original_page_sequences[page_num]}\n" \
                f"Result: {result_page_sequences.get(page_num, [])}"
    
    @settings(max_examples=20, deadline=None)
    @given(form_data=form_data_strategy())
    def test_populated_fields_maintain_order(self, form_data):
        """
        **Validates: Requirements 9.4**
        Feature: pymupdf-migration, Property 18: Field Order Preservation
        
        For any form data, populated fields SHALL maintain their original order
        relative to unpopulated fields.
        
        This test verifies that:
        1. Populating fields doesn't change order
        2. Populated and unpopulated fields remain in sequence
        3. Field order is independent of population status
        """
        template = get_1099_div_template()
        
        # Open template to get original field order
        template_doc = fitz.open(stream=template, filetype="pdf")
        original_field_order = []
        
        for page_num in range(len(template_doc)):
            page = template_doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                if widget.field_name:
                    original_field_order.append(widget.field_name)
        
        template_doc.close()
        
        # Generate document
        result = generate_document(template, form_data, "1099-DIV")
        
        # Open generated document and verify field order
        result_doc = fitz.open(stream=result, filetype="pdf")
        result_field_order = []
        
        for page_num in range(len(result_doc)):
            page = result_doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                if widget.field_name:
                    result_field_order.append(widget.field_name)
        
        result_doc.close()
        
        # Verify field order is preserved regardless of population
        assert original_field_order == result_field_order, \
            f"Field order changed after population.\n" \
            f"Original: {original_field_order}\n" \
            f"Result: {result_field_order}"


def test_field_order_preservation_with_real_template():
    """
    Unit test: Verify field order preservation with real 1099-DIV template.
    
    This test uses the actual template to verify that field order
    is preserved after document generation.
    """
    template = get_1099_div_template()
    
    # Open template to get original field order
    template_doc = fitz.open(stream=template, filetype="pdf")
    original_field_order = []
    
    for page_num in range(len(template_doc)):
        page = template_doc[page_num]
        widgets = list(page.widgets())
        for widget in widgets:
            if widget.field_name:
                original_field_order.append(widget.field_name)
    
    template_doc.close()
    
    # Generate document
    form_data = {
        "payerName": "Test Payer Company",
        "payerTIN": "12-3456789",
        "recipientName": "John Doe",
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Open generated document and verify field order
    result_doc = fitz.open(stream=result, filetype="pdf")
    result_field_order = []
    
    for page_num in range(len(result_doc)):
        page = result_doc[page_num]
        widgets = list(page.widgets())
        for widget in widgets:
            if widget.field_name:
                result_field_order.append(widget.field_name)
    
    result_doc.close()
    
    # Verify field order is preserved
    assert original_field_order == result_field_order, \
        f"Field order changed"


def test_field_order_preservation_empty_data():
    """
    Unit test: Verify field order preservation with empty form data.
    
    Even with no data populated, field order should be preserved.
    """
    template = get_1099_div_template()
    
    # Open template to get original field order
    template_doc = fitz.open(stream=template, filetype="pdf")
    original_field_order = []
    
    for page_num in range(len(template_doc)):
        page = template_doc[page_num]
        widgets = list(page.widgets())
        for widget in widgets:
            if widget.field_name:
                original_field_order.append(widget.field_name)
    
    template_doc.close()
    
    # Generate document with empty data
    form_data = {}
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Open generated document and verify field order
    result_doc = fitz.open(stream=result, filetype="pdf")
    result_field_order = []
    
    for page_num in range(len(result_doc)):
        page = result_doc[page_num]
        widgets = list(page.widgets())
        for widget in widgets:
            if widget.field_name:
                result_field_order.append(widget.field_name)
    
    result_doc.close()
    
    # Verify field order is preserved
    assert original_field_order == result_field_order, \
        f"Field order changed with empty data"
