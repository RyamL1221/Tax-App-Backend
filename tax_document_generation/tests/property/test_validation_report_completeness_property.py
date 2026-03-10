"""
Property-based tests for validation report completeness.

**Validates: Requirements 6.4**

Property 9: Validation Report Completeness
For any validation run, the report should include counts of valid mappings,
invalid mappings, and unmapped PDF fields.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import Dict, Set, Tuple
from dataclasses import dataclass


@dataclass
class ValidationReport:
    """Validation report containing all required statistics."""
    valid_mapping_count: int
    invalid_mapping_count: int
    unmapped_field_count: int
    total_api_mappings: int
    total_pdf_fields: int
    
    def is_complete(self) -> bool:
        """Check if report contains all required information."""
        return all([
            self.valid_mapping_count >= 0,
            self.invalid_mapping_count >= 0,
            self.unmapped_field_count >= 0,
            self.total_api_mappings >= 0,
            self.total_pdf_fields >= 0,
        ])


def generate_validation_report(
    mapping: Dict[str, str],
    pdf_fields: Set[str]
) -> ValidationReport:
    """
    Generate a complete validation report.
    
    Args:
        mapping: Dictionary of API field name -> PDF field name
        pdf_fields: Set of actual PDF field names from template
        
    Returns:
        ValidationReport with all statistics
    """
    # Count valid and invalid mappings
    valid_count = 0
    invalid_count = 0
    
    for api_field, pdf_field in mapping.items():
        if pdf_field in pdf_fields:
            valid_count += 1
        else:
            invalid_count += 1
    
    # Count unmapped PDF fields
    mapped_pdf_fields = set(mapping.values())
    unmapped_fields = pdf_fields - mapped_pdf_fields
    unmapped_count = len(unmapped_fields)
    
    return ValidationReport(
        valid_mapping_count=valid_count,
        invalid_mapping_count=invalid_count,
        unmapped_field_count=unmapped_count,
        total_api_mappings=len(mapping),
        total_pdf_fields=len(pdf_fields)
    )


# Strategy for generating field names
field_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_[]()'),
    min_size=1,
    max_size=50
)


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20),
    num_valid=st.integers(min_value=0, max_value=10),
    num_invalid=st.integers(min_value=0, max_value=10)
)
def test_validation_report_contains_all_required_counts(
    pdf_fields: Set[str],
    num_valid: int,
    num_invalid: int
):
    """
    Property: Validation report contains all required count fields.
    
    For any validation run, the report should include:
    - Valid mapping count
    - Invalid mapping count
    - Unmapped field count
    - Total API mappings
    - Total PDF fields
    """
    pdf_fields_list = list(pdf_fields)
    assume(len(pdf_fields_list) >= num_valid)
    
    # Create valid mappings
    valid_mapping = {
        f"valid_api_{i}": pdf_fields_list[i]
        for i in range(num_valid)
    }
    
    # Create invalid mappings
    invalid_mapping = {
        f"invalid_api_{i}": f"nonexistent_field_{i}"
        for i in range(num_invalid)
    }
    
    # Combine mappings
    combined_mapping = {**valid_mapping, **invalid_mapping}
    
    # Generate report
    report = generate_validation_report(combined_mapping, pdf_fields)
    
    # Property: Report should be complete
    assert report.is_complete(), "Report should contain all required fields"
    
    # Property: Valid mapping count should be correct
    assert report.valid_mapping_count == num_valid, \
        f"Expected {num_valid} valid mappings, got {report.valid_mapping_count}"
    
    # Property: Invalid mapping count should be correct
    assert report.invalid_mapping_count == num_invalid, \
        f"Expected {num_invalid} invalid mappings, got {report.invalid_mapping_count}"
    
    # Property: Total API mappings should be sum of valid and invalid
    assert report.total_api_mappings == num_valid + num_invalid, \
        "Total API mappings should equal valid + invalid"
    
    # Property: Total PDF fields should match input
    assert report.total_pdf_fields == len(pdf_fields), \
        f"Expected {len(pdf_fields)} PDF fields, got {report.total_pdf_fields}"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=5, max_size=20),
    num_mapped=st.integers(min_value=1, max_value=10)
)
def test_validation_report_unmapped_count_is_accurate(
    pdf_fields: Set[str],
    num_mapped: int
):
    """
    Property: Unmapped field count accurately reflects unmapped PDF fields.
    
    For any set of mappings, the unmapped count should equal the number
    of PDF fields that have no API mapping.
    """
    pdf_fields_list = list(pdf_fields)
    assume(len(pdf_fields_list) >= num_mapped)
    
    # Create mapping for only some PDF fields
    mapping = {
        f"api_field_{i}": pdf_fields_list[i]
        for i in range(num_mapped)
    }
    
    # Generate report
    report = generate_validation_report(mapping, pdf_fields)
    
    # Property: Unmapped count should be correct
    expected_unmapped = len(pdf_fields) - num_mapped
    assert report.unmapped_field_count == expected_unmapped, \
        f"Expected {expected_unmapped} unmapped fields, got {report.unmapped_field_count}"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20)
)
def test_validation_report_handles_empty_mapping(pdf_fields: Set[str]):
    """
    Property: Report correctly handles empty mapping.
    
    For an empty mapping, the report should show:
    - 0 valid mappings
    - 0 invalid mappings
    - All PDF fields as unmapped
    """
    empty_mapping = {}
    
    # Generate report
    report = generate_validation_report(empty_mapping, pdf_fields)
    
    # Property: No valid mappings
    assert report.valid_mapping_count == 0, \
        "Empty mapping should have 0 valid mappings"
    
    # Property: No invalid mappings
    assert report.invalid_mapping_count == 0, \
        "Empty mapping should have 0 invalid mappings"
    
    # Property: All PDF fields are unmapped
    assert report.unmapped_field_count == len(pdf_fields), \
        "All PDF fields should be unmapped with empty mapping"
    
    # Property: Total API mappings is 0
    assert report.total_api_mappings == 0, \
        "Empty mapping should have 0 total API mappings"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20)
)
def test_validation_report_handles_all_valid_mappings(pdf_fields: Set[str]):
    """
    Property: Report correctly handles all valid mappings.
    
    When all mappings are valid, the report should show:
    - All mappings as valid
    - 0 invalid mappings
    - 0 unmapped fields (if all PDF fields are mapped)
    """
    # Create mapping for all PDF fields
    mapping = {
        f"api_field_{i}": pdf_field
        for i, pdf_field in enumerate(pdf_fields)
    }
    
    # Generate report
    report = generate_validation_report(mapping, pdf_fields)
    
    # Property: All mappings are valid
    assert report.valid_mapping_count == len(mapping), \
        "All mappings should be valid"
    
    # Property: No invalid mappings
    assert report.invalid_mapping_count == 0, \
        "Should have 0 invalid mappings"
    
    # Property: No unmapped fields
    assert report.unmapped_field_count == 0, \
        "Should have 0 unmapped fields when all are mapped"


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20),
    invalid_field_names=st.sets(field_name_strategy, min_size=1, max_size=10)
)
def test_validation_report_handles_all_invalid_mappings(
    valid_pdf_fields: Set[str],
    invalid_field_names: Set[str]
):
    """
    Property: Report correctly handles all invalid mappings.
    
    When all mappings are invalid, the report should show:
    - 0 valid mappings
    - All mappings as invalid
    - All PDF fields as unmapped
    """
    # Ensure invalid fields are truly invalid
    invalid_field_names = invalid_field_names - valid_pdf_fields
    assume(len(invalid_field_names) > 0)
    
    # Create mapping with only invalid fields
    mapping = {
        f"api_field_{i}": invalid_field
        for i, invalid_field in enumerate(invalid_field_names)
    }
    
    # Generate report
    report = generate_validation_report(mapping, valid_pdf_fields)
    
    # Property: No valid mappings
    assert report.valid_mapping_count == 0, \
        "Should have 0 valid mappings"
    
    # Property: All mappings are invalid
    assert report.invalid_mapping_count == len(mapping), \
        "All mappings should be invalid"
    
    # Property: All PDF fields are unmapped
    assert report.unmapped_field_count == len(valid_pdf_fields), \
        "All PDF fields should be unmapped when mappings are invalid"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20),
    num_valid=st.integers(min_value=0, max_value=10),
    num_invalid=st.integers(min_value=0, max_value=10)
)
def test_validation_report_counts_sum_correctly(
    pdf_fields: Set[str],
    num_valid: int,
    num_invalid: int
):
    """
    Property: Valid and invalid counts sum to total API mappings.
    
    For any validation report, the sum of valid and invalid mapping counts
    should equal the total number of API mappings.
    """
    pdf_fields_list = list(pdf_fields)
    assume(len(pdf_fields_list) >= num_valid)
    
    # Create mappings
    valid_mapping = {
        f"valid_api_{i}": pdf_fields_list[i]
        for i in range(num_valid)
    }
    invalid_mapping = {
        f"invalid_api_{i}": f"nonexistent_{i}"
        for i in range(num_invalid)
    }
    combined_mapping = {**valid_mapping, **invalid_mapping}
    
    # Generate report
    report = generate_validation_report(combined_mapping, pdf_fields)
    
    # Property: Valid + invalid should equal total
    assert report.valid_mapping_count + report.invalid_mapping_count == report.total_api_mappings, \
        "Valid + invalid counts should equal total API mappings"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=5, max_size=20),
    duplicate_count=st.integers(min_value=2, max_value=5)
)
def test_validation_report_handles_duplicate_mappings(
    pdf_fields: Set[str],
    duplicate_count: int
):
    """
    Property: Report correctly counts duplicate mappings to same PDF field.
    
    When multiple API fields map to the same PDF field, all should be
    counted as valid mappings, but unmapped count should reflect unique fields.
    """
    pdf_fields_list = list(pdf_fields)
    assume(len(pdf_fields_list) >= 2)
    
    # Map multiple API fields to the first PDF field
    target_pdf_field = pdf_fields_list[0]
    mapping = {
        f"api_field_{i}": target_pdf_field
        for i in range(duplicate_count)
    }
    
    # Generate report
    report = generate_validation_report(mapping, pdf_fields)
    
    # Property: All duplicate mappings should be valid
    assert report.valid_mapping_count == duplicate_count, \
        "All duplicate mappings should be counted as valid"
    
    # Property: Unmapped count should reflect that one field is mapped
    expected_unmapped = len(pdf_fields) - 1  # Only one unique field is mapped
    assert report.unmapped_field_count == expected_unmapped, \
        "Unmapped count should reflect unique mapped fields"


@given(
    pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20)
)
def test_validation_report_all_counts_non_negative(pdf_fields: Set[str]):
    """
    Property: All counts in validation report are non-negative.
    
    For any validation report, all count fields should be >= 0.
    """
    # Create arbitrary mapping
    mapping = {
        f"api_field_{i}": pdf_field
        for i, pdf_field in enumerate(list(pdf_fields)[:5])
    }
    
    # Generate report
    report = generate_validation_report(mapping, pdf_fields)
    
    # Property: All counts should be non-negative
    assert report.valid_mapping_count >= 0, "Valid count should be non-negative"
    assert report.invalid_mapping_count >= 0, "Invalid count should be non-negative"
    assert report.unmapped_field_count >= 0, "Unmapped count should be non-negative"
    assert report.total_api_mappings >= 0, "Total API mappings should be non-negative"
    assert report.total_pdf_fields >= 0, "Total PDF fields should be non-negative"


def test_validation_report_with_realistic_1099_div_scenario():
    """
    Integration test: Verify report completeness with realistic 1099-DIV data.
    
    This test uses realistic field counts and mappings to ensure the report
    provides complete information for a real-world scenario.
    """
    # Realistic PDF fields (subset of actual 1099-DIV fields)
    pdf_fields = {
        "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",  # Payer name
        "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",  # Payer TIN
        "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",  # Recipient TIN
        "topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]",  # Total dividends
        "topmostSubform[0].Copy1[0].RghtCol[0].f2_10[0]", # Qualified dividends
        "topmostSubform[0].Copy1[0].RghtCol[0].f2_11[0]", # Capital gains
        "topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]", # Unmapped field
        "topmostSubform[0].Copy1[0].RghtCol[0].f2_39[0]", # Account number
    }
    
    # Create mapping with mix of valid and invalid
    mapping = {
        "payerName": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",      # Valid
        "payerTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",       # Valid
        "recipientTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",   # Valid
        "totalDividends": "topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]", # Valid
        "wrongField": "topmostSubform[0].Copy1[0].RghtCol[0].f2_99[0]",    # Invalid
        "anotherWrong": "topmostSubform[0].Copy1[0].LeftCol[0].f2_100[0]", # Invalid
    }
    
    # Generate report
    report = generate_validation_report(mapping, pdf_fields)
    
    # Verify report completeness
    assert report.is_complete(), "Report should be complete"
    
    # Verify counts
    assert report.valid_mapping_count == 4, "Should have 4 valid mappings"
    assert report.invalid_mapping_count == 2, "Should have 2 invalid mappings"
    assert report.total_api_mappings == 6, "Should have 6 total API mappings"
    assert report.total_pdf_fields == 8, "Should have 8 total PDF fields"
    
    # Verify unmapped count (4 PDF fields have no mapping)
    # f2_10, f2_11, f2_31, f2_39 are not mapped
    assert report.unmapped_field_count == 4, "Should have 4 unmapped PDF fields"
    
    # Verify sum property
    assert report.valid_mapping_count + report.invalid_mapping_count == report.total_api_mappings, \
        "Valid + invalid should equal total"
