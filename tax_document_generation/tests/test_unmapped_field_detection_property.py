"""
Property-based tests for unmapped field detection.

**Validates: Requirements 2.2**

Property 5: Unmapped Field Detection
For any field mapping configuration and PDF template, validation should identify
all PDF fields that exist in the template but have no API mapping.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import Dict, Set


def find_unmapped_pdf_fields(mapping: Dict[str, str], pdf_fields: Set[str]) -> Set[str]:
    """
    Find PDF fields that have no API mapping.
    
    Args:
        mapping: Dictionary of API field name -> PDF field name
        pdf_fields: Set of actual PDF field names from template
        
    Returns:
        Set of PDF fields with no mapping
    """
    mapped_pdf_fields = set(mapping.values())
    unmapped_pdf_fields = pdf_fields - mapped_pdf_fields
    return unmapped_pdf_fields


# Strategy for generating field names
field_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_[]()'),
    min_size=1,
    max_size=50
)


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=5, max_size=20),
    num_mapped=st.integers(min_value=1, max_value=10)
)
def test_unmapped_field_detection_identifies_all_unmapped_fields(
    pdf_fields: Set[str],
    num_mapped: int
):
    """
    Property: All PDF fields without mappings are detected as unmapped.
    
    For any set of PDF fields, when only some have mappings,
    the validation should identify ALL fields without mappings.
    """
    pdf_fields_list = list(pdf_fields)
    assume(len(pdf_fields_list) >= num_mapped)
    
    # Create mapping for only some of the PDF fields
    mapped_fields = pdf_fields_list[:num_mapped]
    mapping = {
        f"api_field_{i}": pdf_field
        for i, pdf_field in enumerate(mapped_fields)
    }
    
    # Find unmapped fields
    unmapped = find_unmapped_pdf_fields(mapping, pdf_fields)
    
    # Property: Unmapped fields should be exactly those not in mapping
    expected_unmapped = pdf_fields - set(mapped_fields)
    assert unmapped == expected_unmapped, \
        f"Expected {len(expected_unmapped)} unmapped fields, but found {len(unmapped)}"
    
    # Property: Number of unmapped fields should be correct
    assert len(unmapped) == len(pdf_fields) - num_mapped, \
        "Unmapped field count doesn't match expected"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20)
)
def test_unmapped_field_detection_when_all_fields_mapped(pdf_fields: Set[str]):
    """
    Property: When all PDF fields have mappings, no unmapped fields are detected.
    
    For any set of PDF fields, when every field has a mapping,
    validation should report zero unmapped fields.
    """
    # Create mapping for all PDF fields
    mapping = {
        f"api_field_{i}": pdf_field
        for i, pdf_field in enumerate(pdf_fields)
    }
    
    # Find unmapped fields
    unmapped = find_unmapped_pdf_fields(mapping, pdf_fields)
    
    # Property: No fields should be unmapped
    assert len(unmapped) == 0, \
        f"Expected 0 unmapped fields, but found {len(unmapped)}"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20)
)
def test_unmapped_field_detection_when_no_fields_mapped(pdf_fields: Set[str]):
    """
    Property: When no PDF fields have mappings, all fields are detected as unmapped.
    
    For any set of PDF fields, when the mapping is empty,
    validation should report all fields as unmapped.
    """
    # Empty mapping
    mapping = {}
    
    # Find unmapped fields
    unmapped = find_unmapped_pdf_fields(mapping, pdf_fields)
    
    # Property: All fields should be unmapped
    assert unmapped == pdf_fields, \
        "All PDF fields should be unmapped when mapping is empty"
    
    # Property: Count should match total PDF fields
    assert len(unmapped) == len(pdf_fields), \
        f"Expected {len(pdf_fields)} unmapped fields, but found {len(unmapped)}"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=5, max_size=20),
    duplicate_count=st.integers(min_value=2, max_value=5)
)
def test_unmapped_field_detection_with_duplicate_mappings(
    pdf_fields: Set[str],
    duplicate_count: int
):
    """
    Property: Multiple API fields mapping to same PDF field doesn't affect unmapped detection.
    
    For any PDF field, even if multiple API fields map to it,
    it should still be considered mapped (not unmapped).
    """
    pdf_fields_list = list(pdf_fields)
    assume(len(pdf_fields_list) >= 2)
    
    # Map multiple API fields to the first PDF field
    target_pdf_field = pdf_fields_list[0]
    mapping = {
        f"api_field_{i}": target_pdf_field
        for i in range(duplicate_count)
    }
    
    # Find unmapped fields
    unmapped = find_unmapped_pdf_fields(mapping, pdf_fields)
    
    # Property: Target field should NOT be in unmapped (it has mappings)
    assert target_pdf_field not in unmapped, \
        "PDF field with multiple mappings should not be unmapped"
    
    # Property: All other fields should be unmapped
    expected_unmapped = pdf_fields - {target_pdf_field}
    assert unmapped == expected_unmapped, \
        "Only the mapped field should be excluded from unmapped set"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=5, max_size=20),
    invalid_field_names=st.sets(field_name_strategy, min_size=1, max_size=10)
)
def test_unmapped_field_detection_ignores_invalid_mappings(
    pdf_fields: Set[str],
    invalid_field_names: Set[str]
):
    """
    Property: Mappings to non-existent PDF fields don't affect unmapped detection.
    
    For any set of mappings that point to non-existent fields,
    those invalid mappings should not affect which real PDF fields are unmapped.
    """
    # Ensure invalid fields are truly invalid
    invalid_field_names = invalid_field_names - pdf_fields
    assume(len(invalid_field_names) > 0)
    
    # Create mapping with only invalid fields
    mapping = {
        f"api_field_{i}": invalid_field
        for i, invalid_field in enumerate(invalid_field_names)
    }
    
    # Find unmapped fields
    unmapped = find_unmapped_pdf_fields(mapping, pdf_fields)
    
    # Property: All real PDF fields should be unmapped (invalid mappings don't count)
    assert unmapped == pdf_fields, \
        "All PDF fields should be unmapped when mappings point to non-existent fields"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=10, max_size=20),
    num_mapped=st.integers(min_value=1, max_value=5),
    num_invalid=st.integers(min_value=1, max_value=5)
)
def test_unmapped_field_detection_with_mixed_mappings(
    pdf_fields: Set[str],
    num_mapped: int,
    num_invalid: int
):
    """
    Property: Unmapped detection works correctly with mix of valid and invalid mappings.
    
    For any mix of valid mappings (to real PDF fields) and invalid mappings
    (to non-existent fields), only the valid mappings should affect unmapped detection.
    """
    pdf_fields_list = list(pdf_fields)
    assume(len(pdf_fields_list) >= num_mapped)
    
    # Create valid mappings
    mapped_fields = pdf_fields_list[:num_mapped]
    valid_mapping = {
        f"valid_api_{i}": pdf_field
        for i, pdf_field in enumerate(mapped_fields)
    }
    
    # Create invalid mappings
    invalid_mapping = {
        f"invalid_api_{i}": f"nonexistent_field_{i}"
        for i in range(num_invalid)
    }
    
    # Combine mappings
    combined_mapping = {**valid_mapping, **invalid_mapping}
    
    # Find unmapped fields
    unmapped = find_unmapped_pdf_fields(combined_mapping, pdf_fields)
    
    # Property: Unmapped should be all PDF fields except those with valid mappings
    expected_unmapped = pdf_fields - set(mapped_fields)
    assert unmapped == expected_unmapped, \
        "Only valid mappings should affect unmapped field detection"
    
    # Property: Invalid mappings should not reduce unmapped count
    assert len(unmapped) == len(pdf_fields) - num_mapped, \
        "Invalid mappings should not affect unmapped count"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20)
)
def test_unmapped_field_detection_returns_set(pdf_fields: Set[str]):
    """
    Property: Unmapped field detection always returns a set.
    
    For any input, the result should be a set (no duplicates, unordered).
    """
    mapping = {}
    unmapped = find_unmapped_pdf_fields(mapping, pdf_fields)
    
    # Property: Result should be a set
    assert isinstance(unmapped, set), \
        "Unmapped fields should be returned as a set"
    
    # Property: Set should contain no duplicates (inherent to set, but verify)
    assert len(unmapped) == len(list(unmapped)), \
        "Unmapped fields should have no duplicates"


def test_unmapped_field_detection_with_real_1099_div_template():
    """
    Integration test: Detect unmapped fields in real 1099-DIV template.
    
    This test uses the actual 1099-DIV PDF template to verify that
    unmapped field detection works with real PDF files.
    """
    import os
    import fitz
    
    # Try to find the 1099-DIV template
    possible_paths = [
        "1099-DIV.pdf",
        "../1099-DIV.pdf",
        "../../1099-DIV.pdf",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "1099-DIV.pdf"),
    ]
    
    template_path = None
    for path in possible_paths:
        if os.path.exists(path):
            template_path = path
            break
    
    if not template_path:
        pytest.skip("1099-DIV.pdf template not found")
    
    # Load the PDF and extract field names
    doc = fitz.open(template_path)
    pdf_fields = set()
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                if widget.field_name:
                    pdf_fields.add(widget.field_name)
    doc.close()
    
    if not pdf_fields:
        pytest.skip("No form fields found in 1099-DIV template")
    
    # Create partial mapping (map only a few fields)
    pdf_fields_list = list(pdf_fields)
    num_to_map = min(3, len(pdf_fields_list))
    mapping = {
        f"api_field_{i}": pdf_fields_list[i]
        for i in range(num_to_map)
    }
    
    # Find unmapped fields
    unmapped = find_unmapped_pdf_fields(mapping, pdf_fields)
    
    # Assertions
    assert len(unmapped) == len(pdf_fields) - num_to_map, \
        f"Expected {len(pdf_fields) - num_to_map} unmapped fields"
    
    # Verify mapped fields are not in unmapped set
    for pdf_field in mapping.values():
        assert pdf_field not in unmapped, \
            f"Mapped field {pdf_field} should not be in unmapped set"
    
    # Verify unmapped fields are real PDF fields
    assert unmapped.issubset(pdf_fields), \
        "All unmapped fields should be real PDF fields"
