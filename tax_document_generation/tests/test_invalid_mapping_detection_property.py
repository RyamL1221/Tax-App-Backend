"""
Property-based tests for invalid mapping detection.

**Validates: Requirements 2.1, 5.3, 6.1**

Property 4: Invalid Mapping Detection
For any field mapping configuration and PDF template, validation should identify
all API fields that map to non-existent PDF field names.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import Dict, Set
import fitz


def validate_mappings_against_pdf(mapping: Dict[str, str], pdf_fields: Set[str]) -> tuple:
    """
    Validate that all mappings point to real PDF fields.
    
    Args:
        mapping: Dictionary of API field name -> PDF field name
        pdf_fields: Set of actual PDF field names from template
        
    Returns:
        Tuple of (valid_mappings, invalid_mappings)
    """
    valid_mappings = []
    invalid_mappings = []
    
    for api_field, pdf_field in mapping.items():
        if pdf_field in pdf_fields:
            valid_mappings.append((api_field, pdf_field))
        else:
            invalid_mappings.append((api_field, pdf_field))
    
    return valid_mappings, invalid_mappings


# Strategy for generating field names
field_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_[]()'),
    min_size=1,
    max_size=50
)

# Strategy for generating API field names (user-friendly names)
api_field_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters='_'),
    min_size=3,
    max_size=30
).filter(lambda x: x and not x.startswith('_') and not x.endswith('_'))


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20),
    invalid_field_names=st.sets(field_name_strategy, min_size=1, max_size=10)
)
def test_invalid_mapping_detection_identifies_all_invalid_mappings(
    valid_pdf_fields: Set[str],
    invalid_field_names: Set[str]
):
    """
    Property: All mappings to non-existent PDF fields are detected as invalid.
    
    For any set of valid PDF fields and any set of invalid field names,
    when we create mappings that point to invalid fields,
    the validation should identify ALL of them as invalid.
    """
    # Ensure invalid fields are truly invalid (not in valid set)
    invalid_field_names = invalid_field_names - valid_pdf_fields
    assume(len(invalid_field_names) > 0)
    
    # Create a mapping with only invalid fields
    mapping = {
        f"api_field_{i}": invalid_field
        for i, invalid_field in enumerate(invalid_field_names)
    }
    
    # Validate the mappings
    valid_mappings, invalid_mappings = validate_mappings_against_pdf(mapping, valid_pdf_fields)
    
    # Property: All mappings should be detected as invalid
    assert len(invalid_mappings) == len(mapping), \
        f"Expected {len(mapping)} invalid mappings, but found {len(invalid_mappings)}"
    
    # Property: No mappings should be detected as valid
    assert len(valid_mappings) == 0, \
        f"Expected 0 valid mappings, but found {len(valid_mappings)}"
    
    # Property: All API fields should appear in invalid mappings
    invalid_api_fields = {api_field for api_field, _ in invalid_mappings}
    assert invalid_api_fields == set(mapping.keys()), \
        "Not all API fields with invalid mappings were detected"


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=5, max_size=20),
    num_valid_mappings=st.integers(min_value=1, max_value=10),
    num_invalid_mappings=st.integers(min_value=1, max_value=10)
)
def test_invalid_mapping_detection_distinguishes_valid_from_invalid(
    valid_pdf_fields: Set[str],
    num_valid_mappings: int,
    num_invalid_mappings: int
):
    """
    Property: Validation correctly distinguishes valid from invalid mappings.
    
    For any mix of valid and invalid mappings,
    the validation should correctly categorize each mapping.
    """
    valid_pdf_fields_list = list(valid_pdf_fields)
    assume(len(valid_pdf_fields_list) >= num_valid_mappings)
    
    # Create valid mappings (pointing to real PDF fields)
    valid_mapping = {
        f"valid_api_{i}": valid_pdf_fields_list[i]
        for i in range(num_valid_mappings)
    }
    
    # Create invalid mappings (pointing to non-existent fields)
    invalid_mapping = {
        f"invalid_api_{i}": f"nonexistent_field_{i}"
        for i in range(num_invalid_mappings)
    }
    
    # Combine mappings
    combined_mapping = {**valid_mapping, **invalid_mapping}
    
    # Validate the mappings
    valid_results, invalid_results = validate_mappings_against_pdf(
        combined_mapping, valid_pdf_fields
    )
    
    # Property: Number of valid mappings should match expected
    assert len(valid_results) == num_valid_mappings, \
        f"Expected {num_valid_mappings} valid mappings, but found {len(valid_results)}"
    
    # Property: Number of invalid mappings should match expected
    assert len(invalid_results) == num_invalid_mappings, \
        f"Expected {num_invalid_mappings} invalid mappings, but found {len(invalid_results)}"
    
    # Property: Valid API fields should be in valid results
    valid_api_fields = {api_field for api_field, _ in valid_results}
    assert valid_api_fields == set(valid_mapping.keys()), \
        "Valid mappings were not correctly identified"
    
    # Property: Invalid API fields should be in invalid results
    invalid_api_fields = {api_field for api_field, _ in invalid_results}
    assert invalid_api_fields == set(invalid_mapping.keys()), \
        "Invalid mappings were not correctly identified"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20)
)
def test_invalid_mapping_detection_handles_empty_mapping(pdf_fields: Set[str]):
    """
    Property: Validation handles empty mappings correctly.
    
    For any set of PDF fields, when given an empty mapping,
    validation should report zero valid and zero invalid mappings.
    """
    empty_mapping = {}
    
    valid_mappings, invalid_mappings = validate_mappings_against_pdf(empty_mapping, pdf_fields)
    
    # Property: Empty mapping should have no valid mappings
    assert len(valid_mappings) == 0, \
        "Empty mapping should have no valid mappings"
    
    # Property: Empty mapping should have no invalid mappings
    assert len(invalid_mappings) == 0, \
        "Empty mapping should have no invalid mappings"


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20)
)
def test_invalid_mapping_detection_all_valid_mappings(valid_pdf_fields: Set[str]):
    """
    Property: When all mappings are valid, no invalid mappings are detected.
    
    For any set of valid PDF fields, when all mappings point to valid fields,
    validation should report zero invalid mappings.
    """
    # Create mappings that all point to valid PDF fields
    mapping = {
        f"api_field_{i}": pdf_field
        for i, pdf_field in enumerate(valid_pdf_fields)
    }
    
    valid_mappings, invalid_mappings = validate_mappings_against_pdf(mapping, valid_pdf_fields)
    
    # Property: All mappings should be valid
    assert len(valid_mappings) == len(mapping), \
        f"Expected {len(mapping)} valid mappings, but found {len(valid_mappings)}"
    
    # Property: No mappings should be invalid
    assert len(invalid_mappings) == 0, \
        f"Expected 0 invalid mappings, but found {len(invalid_mappings)}"


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20),
    duplicate_count=st.integers(min_value=2, max_value=5)
)
def test_invalid_mapping_detection_handles_duplicate_pdf_fields(
    valid_pdf_fields: Set[str],
    duplicate_count: int
):
    """
    Property: Multiple API fields can map to the same PDF field (all valid).
    
    For any valid PDF field, multiple API fields can map to it,
    and all should be detected as valid mappings.
    """
    valid_pdf_fields_list = list(valid_pdf_fields)
    assume(len(valid_pdf_fields_list) > 0)
    
    # Pick one PDF field and map multiple API fields to it
    target_pdf_field = valid_pdf_fields_list[0]
    mapping = {
        f"api_field_{i}": target_pdf_field
        for i in range(duplicate_count)
    }
    
    valid_mappings, invalid_mappings = validate_mappings_against_pdf(mapping, valid_pdf_fields)
    
    # Property: All mappings should be valid (even though they point to same PDF field)
    assert len(valid_mappings) == duplicate_count, \
        f"Expected {duplicate_count} valid mappings, but found {len(valid_mappings)}"
    
    # Property: No mappings should be invalid
    assert len(invalid_mappings) == 0, \
        "Duplicate mappings to same PDF field should all be valid"


def test_invalid_mapping_detection_with_real_1099_div_template():
    """
    Integration test: Validate against real 1099-DIV template.
    
    This test uses the actual 1099-DIV PDF template to verify that
    invalid mapping detection works with real PDF files.
    """
    import os
    from pathlib import Path
    
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
    
    # Create a mapping with some valid and some invalid fields
    valid_field = list(pdf_fields)[0]
    mapping = {
        "valid_field": valid_field,
        "invalid_field_1": "nonexistent_field_xyz",
        "invalid_field_2": "another_fake_field_abc",
    }
    
    # Validate
    valid_mappings, invalid_mappings = validate_mappings_against_pdf(mapping, pdf_fields)
    
    # Assertions
    assert len(valid_mappings) == 1, "Should detect 1 valid mapping"
    assert len(invalid_mappings) == 2, "Should detect 2 invalid mappings"
    assert valid_mappings[0][0] == "valid_field", "Valid field should be identified"
    
    invalid_api_fields = {api_field for api_field, _ in invalid_mappings}
    assert invalid_api_fields == {"invalid_field_1", "invalid_field_2"}, \
        "Both invalid fields should be detected"
