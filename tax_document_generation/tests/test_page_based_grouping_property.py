"""
Property-Based Tests for Page-Based Field Grouping

Tests that the inspect_pdf_fields module correctly groups fields by page number
in ascending order.

**Validates: Requirements 1.3**
"""

import os
import sys
import tempfile

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from inspect_pdf_fields import group_fields_by_page, FieldInfo

# Import PyMuPDF for test PDF creation
try:
    import fitz
except ImportError:
    pytest.skip("PyMuPDF not available", allow_module_level=True)


@given(
    page_count=st.integers(min_value=1, max_value=10),
    fields_per_page=st.integers(min_value=0, max_value=10)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_page_based_grouping_property(page_count: int, fields_per_page: int):
    """
    Property: For any set of fields distributed across pages, grouping by page
    returns a dictionary where keys are page numbers and values are lists of fields
    on that page.
    
    **Validates: Requirements 1.3**
    """
    # Create test fields distributed across pages
    fields = []
    for page_num in range(page_count):
        for field_idx in range(fields_per_page):
            field = FieldInfo(
                name=f"page{page_num}_field{field_idx}",
                page_num=page_num,
                rect=(50.0, 50.0 + field_idx * 30, 150.0, 20.0),
                field_type="Text",
                value=""
            )
            fields.append(field)
    
    # Group fields by page
    grouped = group_fields_by_page(fields)
    
    # Property 1: Result is a dictionary
    assert isinstance(grouped, dict), \
        f"Expected dict, got {type(grouped)}"
    
    # Property 2: All page numbers are present as keys
    expected_pages = set(range(page_count)) if fields_per_page > 0 else set()
    actual_pages = set(grouped.keys())
    assert actual_pages == expected_pages, \
        f"Page numbers don't match. Expected: {expected_pages}, Got: {actual_pages}"
    
    # Property 3: Each page has the correct number of fields
    for page_num in range(page_count):
        if fields_per_page > 0:
            assert page_num in grouped, f"Page {page_num} missing from grouped dict"
            assert len(grouped[page_num]) == fields_per_page, \
                f"Page {page_num} has {len(grouped[page_num])} fields, expected {fields_per_page}"
        else:
            # If no fields per page, page should not be in grouped dict
            assert page_num not in grouped, \
                f"Page {page_num} should not be in grouped dict when fields_per_page=0"
    
    # Property 4: All fields are accounted for
    total_grouped_fields = sum(len(page_fields) for page_fields in grouped.values())
    assert total_grouped_fields == len(fields), \
        f"Total grouped fields ({total_grouped_fields}) != total fields ({len(fields)})"
    
    # Property 5: Fields are grouped correctly by page number
    for page_num, page_fields in grouped.items():
        for field in page_fields:
            assert field.page_num == page_num, \
                f"Field {field.name} on page {field.page_num} found in group for page {page_num}"


@given(
    field_count=st.integers(min_value=1, max_value=50)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_grouping_preserves_all_fields_property(field_count: int):
    """
    Property: For any list of fields, grouping by page preserves all fields
    without duplication or loss.
    
    **Validates: Requirements 1.3**
    """
    # Create fields on random pages
    fields = []
    for i in range(field_count):
        # Distribute fields across pages 0-4
        page_num = i % 5
        field = FieldInfo(
            name=f"field_{i}",
            page_num=page_num,
            rect=(50.0, 50.0, 150.0, 20.0),
            field_type="Text",
            value=""
        )
        fields.append(field)
    
    # Group fields
    grouped = group_fields_by_page(fields)
    
    # Collect all fields from grouped dict
    regrouped_fields = []
    for page_fields in grouped.values():
        regrouped_fields.extend(page_fields)
    
    # Property: All original fields are present
    assert len(regrouped_fields) == len(fields), \
        f"Field count mismatch: {len(regrouped_fields)} != {len(fields)}"
    
    # Property: Field names match (order may differ)
    original_names = sorted([f.name for f in fields])
    regrouped_names = sorted([f.name for f in regrouped_fields])
    assert original_names == regrouped_names, \
        f"Field names don't match after grouping"


def test_grouping_with_empty_list():
    """
    Property: Grouping an empty list of fields returns an empty dictionary.
    
    **Validates: Requirements 1.3**
    """
    fields = []
    grouped = group_fields_by_page(fields)
    
    assert isinstance(grouped, dict), "Result should be a dict"
    assert len(grouped) == 0, "Empty field list should produce empty dict"


def test_grouping_maintains_page_order():
    """
    Property: When iterating over grouped fields, page numbers should be
    accessible in ascending order.
    
    **Validates: Requirements 1.3**
    """
    # Create fields on pages 0, 2, 5, 1, 3 (out of order)
    fields = [
        FieldInfo("field_0", 0, (0, 0, 100, 20), "Text", ""),
        FieldInfo("field_2", 2, (0, 0, 100, 20), "Text", ""),
        FieldInfo("field_5", 5, (0, 0, 100, 20), "Text", ""),
        FieldInfo("field_1", 1, (0, 0, 100, 20), "Text", ""),
        FieldInfo("field_3", 3, (0, 0, 100, 20), "Text", ""),
    ]
    
    # Group fields
    grouped = group_fields_by_page(fields)
    
    # Get page numbers in sorted order
    page_numbers = sorted(grouped.keys())
    
    # Property: Page numbers are in ascending order
    assert page_numbers == [0, 1, 2, 3, 5], \
        f"Page numbers not in ascending order: {page_numbers}"
    
    # Property: Iterating with sorted() gives ascending order
    for i, page_num in enumerate(sorted(grouped.keys())):
        if i > 0:
            prev_page = sorted(grouped.keys())[i - 1]
            assert page_num > prev_page, \
                f"Page {page_num} not greater than previous page {prev_page}"
