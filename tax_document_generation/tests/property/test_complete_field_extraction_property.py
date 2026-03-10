"""
Property-Based Tests for PDF Field Extraction

Tests that the inspect_pdf_fields module correctly extracts all form fields
from PDF documents with complete information.

**Validates: Requirements 1.1, 1.2**
"""

import os
import sys
import tempfile
from typing import List

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from inspect_pdf_fields import extract_field_info, FieldInfo

# Import PyMuPDF for test PDF creation
try:
    import fitz
except ImportError:
    pytest.skip("PyMuPDF not available", allow_module_level=True)


def create_test_pdf_with_fields(field_count: int, page_count: int) -> bytes:
    """
    Create a test PDF with specified number of fields across pages.
    
    Args:
        field_count: Number of form fields to create
        page_count: Number of pages in the PDF
        
    Returns:
        PDF bytes
    """
    doc = fitz.open()
    
    # Create pages
    for _ in range(page_count):
        doc.new_page(width=612, height=792)  # Letter size
    
    # Distribute fields evenly across pages
    field_num = 0
    
    for page_num in range(page_count):
        page = doc[page_num]
        
        # Calculate how many fields for this page
        # Distribute remaining fields across remaining pages
        remaining_fields = field_count - field_num
        remaining_pages = page_count - page_num
        fields_this_page = (remaining_fields + remaining_pages - 1) // remaining_pages  # Ceiling division
        
        # Add fields to this page
        for i in range(fields_this_page):
            if field_num >= field_count:
                break
                
            # Create field at different positions
            y_pos = 50 + (i * 30)
            rect = fitz.Rect(50, y_pos, 200, y_pos + 20)
            
            # Add text field widget
            widget = fitz.Widget()
            widget.field_name = f"field_{field_num}"
            widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
            widget.rect = rect
            widget.field_value = ""
            
            page.add_widget(widget)
            field_num += 1
    
    # Return PDF as bytes
    pdf_bytes = doc.tobytes()
    doc.close()
    
    return pdf_bytes


@given(
    field_count=st.integers(min_value=1, max_value=50),
    page_count=st.integers(min_value=1, max_value=5)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_complete_field_extraction_property(field_count: int, page_count: int):
    """
    Property: For any PDF with N fields across M pages, extraction returns all N fields
    with complete information (name, page number, position, type).
    
    **Validates: Requirements 1.1, 1.2**
    """
    # Create test PDF
    pdf_bytes = create_test_pdf_with_fields(field_count, page_count)
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(pdf_bytes)
        pdf_path = tmp_file.name
    
    try:
        # Extract field information
        fields = extract_field_info(pdf_path)
    
        # Property 1: All fields are extracted
        assert len(fields) == field_count, \
            f"Expected {field_count} fields, but extracted {len(fields)}"
        
        # Property 2: Each field has complete information
        for field in fields:
            assert isinstance(field, FieldInfo), \
                f"Field is not a FieldInfo object: {type(field)}"
            
            # Field must have a name
            assert field.name, \
                "Field name is empty"
            
            # Page number must be valid (0-indexed)
            assert 0 <= field.page_num < page_count, \
                f"Invalid page number: {field.page_num} (expected 0-{page_count-1})"
            
            # Rect must have 4 components (x, y, width, height)
            assert len(field.rect) == 4, \
                f"Field rect has {len(field.rect)} components, expected 4"
            
            # Rect dimensions must be non-negative
            x, y, width, height = field.rect
            assert width >= 0, f"Field width is negative: {width}"
            assert height >= 0, f"Field height is negative: {height}"
            
            # Field type must be present
            assert field.field_type, \
                "Field type is empty"
            
            # Value must be a string (can be empty)
            assert isinstance(field.value, str), \
                f"Field value is not a string: {type(field.value)}"
    finally:
        # Clean up temporary file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


@given(
    field_count=st.integers(min_value=5, max_value=20)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_field_extraction_preserves_field_names_property(field_count: int):
    """
    Property: For any PDF with uniquely named fields, extraction preserves
    all field names exactly as they appear in the PDF.
    
    **Validates: Requirements 1.1**
    """
    # Create PDF with uniquely named fields
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    
    expected_names = []
    for i in range(field_count):
        field_name = f"unique_field_{i}_test"
        expected_names.append(field_name)
        
        rect = fitz.Rect(50, 50 + (i * 30), 200, 70 + (i * 30))
        widget = fitz.Widget()
        widget.field_name = field_name
        widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        widget.rect = rect
        page.add_widget(widget)
    
    pdf_bytes = doc.tobytes()
    doc.close()
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(pdf_bytes)
        pdf_path = tmp_file.name
    
    try:
        # Extract fields
        fields = extract_field_info(pdf_path)
        extracted_names = [field.name for field in fields]
        
        # Property: All field names are preserved exactly
        assert set(extracted_names) == set(expected_names), \
            f"Field names don't match. Expected: {expected_names}, Got: {extracted_names}"
        
        # Property: No duplicate field names in extraction
        assert len(extracted_names) == len(set(extracted_names)), \
            f"Duplicate field names found: {extracted_names}"
    finally:
        # Clean up temporary file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


@given(
    page_count=st.integers(min_value=1, max_value=10)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_field_extraction_handles_empty_pages_property(page_count: int):
    """
    Property: For any PDF with pages but no form fields, extraction returns
    an empty list without errors.
    
    **Validates: Requirements 1.1**
    """
    # Create PDF with pages but no fields
    doc = fitz.open()
    for _ in range(page_count):
        doc.new_page(width=612, height=792)
    
    pdf_bytes = doc.tobytes()
    doc.close()
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(pdf_bytes)
        pdf_path = tmp_file.name
    
    try:
        # Extract fields
        fields = extract_field_info(pdf_path)
        
        # Property: Empty PDF returns empty list
        assert len(fields) == 0, \
            f"Expected 0 fields from empty PDF, but got {len(fields)}"
        
        # Property: Result is a list
        assert isinstance(fields, list), \
            f"Expected list, got {type(fields)}"
    finally:
        # Clean up temporary file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def test_field_extraction_with_real_pdf():
    """
    Integration test: Verify field extraction works with real 1099-DIV PDF.
    
    **Validates: Requirements 1.1, 1.2**
    """
    # Find a sample PDF
    sample_pdf = "samples/SAMPLE-1099-DIV-MULTI-COPY.pdf"
    
    if not os.path.exists(sample_pdf):
        pytest.skip(f"Sample PDF not found: {sample_pdf}")
    
    # Extract fields
    fields = extract_field_info(sample_pdf)
    
    # Verify we got fields
    assert len(fields) > 0, "No fields extracted from sample PDF"
    
    # Verify all fields have required information
    for field in fields:
        assert field.name, "Field missing name"
        assert field.page_num >= 0, "Invalid page number"
        assert len(field.rect) == 4, "Invalid rect"
        assert field.field_type, "Field missing type"
        assert isinstance(field.value, str), "Field value not a string"
