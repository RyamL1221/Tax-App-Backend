"""
Property-based tests for validation error logging.

**Validates: Requirements 2.3, 6.2**

Property 6: Validation Error Logging
For any invalid field mapping, the validation system should log the API field name,
the mapped PDF field name, and whether the PDF field exists.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import Dict, Set, List, Tuple
import logging
from io import StringIO


def validate_and_log_mappings(
    mapping: Dict[str, str],
    pdf_fields: Set[str],
    logger: logging.Logger
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """
    Validate mappings and log errors for invalid mappings.
    
    Args:
        mapping: Dictionary of API field name -> PDF field name
        pdf_fields: Set of actual PDF field names from template
        logger: Logger instance for logging errors
        
    Returns:
        Tuple of (valid_mappings, invalid_mappings)
    """
    valid_mappings = []
    invalid_mappings = []
    
    for api_field, pdf_field in mapping.items():
        if pdf_field in pdf_fields:
            valid_mappings.append((api_field, pdf_field))
            logger.debug(f"Valid mapping: {api_field} -> {pdf_field}")
        else:
            invalid_mappings.append((api_field, pdf_field))
            # Log with all required information
            logger.warning(
                f"Invalid mapping: API field '{api_field}' maps to "
                f"PDF field '{pdf_field}' which does not exist in template"
            )
    
    return valid_mappings, invalid_mappings


# Strategy for generating field names
field_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_[]()'),
    min_size=1,
    max_size=50
)


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20),
    invalid_field_names=st.sets(field_name_strategy, min_size=1, max_size=10)
)
def test_validation_logs_all_invalid_mappings(
    valid_pdf_fields: Set[str],
    invalid_field_names: Set[str]
):
    """
    Property: Every invalid mapping generates a log entry.
    
    For any set of invalid mappings, the validation should log
    an error/warning for each invalid mapping.
    """
    # Ensure invalid fields are truly invalid
    invalid_field_names = invalid_field_names - valid_pdf_fields
    assume(len(invalid_field_names) > 0)
    
    # Create mapping with only invalid fields
    mapping = {
        f"api_field_{i}": invalid_field
        for i, invalid_field in enumerate(invalid_field_names)
    }
    
    # Set up logger with string capture
    logger = logging.getLogger("test_validation")
    logger.setLevel(logging.DEBUG)
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
        # Validate and log
        valid_mappings, invalid_mappings = validate_and_log_mappings(
            mapping, valid_pdf_fields, logger
        )
        
        # Get log output
        log_output = log_capture.getvalue()
        
        # Property: Each invalid mapping should have a log entry
        for api_field, pdf_field in invalid_mappings:
            assert api_field in log_output, \
                f"API field '{api_field}' not found in log output"
            assert pdf_field in log_output, \
                f"PDF field '{pdf_field}' not found in log output"
        
        # Property: Number of log entries should match number of invalid mappings
        warning_count = log_output.count("Invalid mapping:")
        assert warning_count == len(invalid_mappings), \
            f"Expected {len(invalid_mappings)} log entries, but found {warning_count}"
    
    finally:
        logger.removeHandler(handler)


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=5, max_size=20),
    num_valid=st.integers(min_value=1, max_value=10),
    num_invalid=st.integers(min_value=1, max_value=10)
)
def test_validation_logs_only_invalid_mappings(
    valid_pdf_fields: Set[str],
    num_valid: int,
    num_invalid: int
):
    """
    Property: Only invalid mappings generate warning logs.
    
    For any mix of valid and invalid mappings, only the invalid ones
    should generate warning log entries.
    """
    valid_pdf_fields_list = list(valid_pdf_fields)
    assume(len(valid_pdf_fields_list) >= num_valid)
    
    # Create valid mappings
    valid_mapping = {
        f"valid_api_{i}": valid_pdf_fields_list[i]
        for i in range(num_valid)
    }
    
    # Create invalid mappings
    invalid_mapping = {
        f"invalid_api_{i}": f"nonexistent_field_{i}"
        for i in range(num_invalid)
    }
    
    # Combine mappings
    combined_mapping = {**valid_mapping, **invalid_mapping}
    
    # Set up logger with string capture
    logger = logging.getLogger("test_validation_mixed")
    logger.setLevel(logging.DEBUG)
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
        # Validate and log
        valid_results, invalid_results = validate_and_log_mappings(
            combined_mapping, valid_pdf_fields, logger
        )
        
        # Get log output
        log_output = log_capture.getvalue()
        
        # Property: Number of warning logs should match invalid mappings
        warning_count = log_output.count("Invalid mapping:")
        assert warning_count == num_invalid, \
            f"Expected {num_invalid} warning logs, but found {warning_count}"
        
        # Property: Valid mappings should not appear in warnings
        for api_field, pdf_field in valid_results:
            # Check that this specific mapping is not in a warning
            invalid_pattern = f"Invalid mapping: API field '{api_field}'"
            assert invalid_pattern not in log_output, \
                f"Valid mapping {api_field} should not generate warning"
    
    finally:
        logger.removeHandler(handler)


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20),
    api_field_name=st.text(min_size=3, max_size=30),
    pdf_field_name=st.text(min_size=3, max_size=50)
)
def test_validation_log_contains_required_information(
    valid_pdf_fields: Set[str],
    api_field_name: str,
    pdf_field_name: str
):
    """
    Property: Each validation log entry contains API field name and PDF field name.
    
    For any invalid mapping, the log entry should contain:
    1. The API field name
    2. The mapped PDF field name
    3. Indication that the field doesn't exist
    """
    # Ensure the PDF field doesn't exist
    assume(pdf_field_name not in valid_pdf_fields)
    
    # Create mapping with one invalid field
    mapping = {api_field_name: pdf_field_name}
    
    # Set up logger with string capture
    logger = logging.getLogger("test_validation_info")
    logger.setLevel(logging.DEBUG)
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
        # Validate and log
        validate_and_log_mappings(mapping, valid_pdf_fields, logger)
        
        # Get log output
        log_output = log_capture.getvalue()
        
        # Property: Log should contain API field name
        assert api_field_name in log_output, \
            "Log entry should contain API field name"
        
        # Property: Log should contain PDF field name
        assert pdf_field_name in log_output, \
            "Log entry should contain PDF field name"
        
        # Property: Log should indicate field doesn't exist
        existence_indicators = [
            "does not exist",
            "not found",
            "invalid",
            "missing"
        ]
        assert any(indicator in log_output.lower() for indicator in existence_indicators), \
            "Log entry should indicate that field doesn't exist"
    
    finally:
        logger.removeHandler(handler)


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20)
)
def test_validation_no_logs_for_empty_mapping(valid_pdf_fields: Set[str]):
    """
    Property: Empty mapping generates no validation logs.
    
    For an empty mapping, no validation warnings should be logged.
    """
    empty_mapping = {}
    
    # Set up logger with string capture
    logger = logging.getLogger("test_validation_empty")
    logger.setLevel(logging.DEBUG)
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
        # Validate and log
        validate_and_log_mappings(empty_mapping, valid_pdf_fields, logger)
        
        # Get log output
        log_output = log_capture.getvalue()
        
        # Property: No warning logs should be generated
        warning_count = log_output.count("Invalid mapping:")
        assert warning_count == 0, \
            "Empty mapping should generate no validation warnings"
    
    finally:
        logger.removeHandler(handler)


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20)
)
def test_validation_no_warnings_for_all_valid_mappings(valid_pdf_fields: Set[str]):
    """
    Property: All valid mappings generate no warning logs.
    
    For any set of valid mappings, no validation warnings should be logged.
    """
    # Create mapping with all valid fields
    mapping = {
        f"api_field_{i}": pdf_field
        for i, pdf_field in enumerate(valid_pdf_fields)
    }
    
    # Set up logger with string capture
    logger = logging.getLogger("test_validation_all_valid")
    logger.setLevel(logging.DEBUG)
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
        # Validate and log
        validate_and_log_mappings(mapping, valid_pdf_fields, logger)
        
        # Get log output
        log_output = log_capture.getvalue()
        
        # Property: No warning logs should be generated
        warning_count = log_output.count("Invalid mapping:")
        assert warning_count == 0, \
            "All valid mappings should generate no validation warnings"
    
    finally:
        logger.removeHandler(handler)


@given(
    valid_pdf_fields=st.sets(field_name_strategy, min_size=1, max_size=20),
    invalid_field_names=st.sets(field_name_strategy, min_size=2, max_size=10)
)
def test_validation_logs_are_distinct_for_each_mapping(
    valid_pdf_fields: Set[str],
    invalid_field_names: Set[str]
):
    """
    Property: Each invalid mapping gets its own distinct log entry.
    
    For multiple invalid mappings, each should have a separate log entry
    with its specific API and PDF field names.
    """
    # Ensure invalid fields are truly invalid
    invalid_field_names = invalid_field_names - valid_pdf_fields
    assume(len(invalid_field_names) >= 2)
    
    # Create mapping with multiple invalid fields
    mapping = {
        f"api_field_{i}": invalid_field
        for i, invalid_field in enumerate(invalid_field_names)
    }
    
    # Set up logger with string capture
    logger = logging.getLogger("test_validation_distinct")
    logger.setLevel(logging.DEBUG)
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
        # Validate and log
        validate_and_log_mappings(mapping, valid_pdf_fields, logger)
        
        # Get log output
        log_output = log_capture.getvalue()
        
        # Property: Each API field should appear in log
        for api_field in mapping.keys():
            assert api_field in log_output, \
                f"API field '{api_field}' should appear in log"
        
        # Property: Each PDF field should appear in log
        for pdf_field in mapping.values():
            assert pdf_field in log_output, \
                f"PDF field '{pdf_field}' should appear in log"
        
        # Property: Number of log entries should match number of mappings
        warning_count = log_output.count("Invalid mapping:")
        assert warning_count == len(mapping), \
            f"Expected {len(mapping)} distinct log entries"
    
    finally:
        logger.removeHandler(handler)


def test_validation_logging_integration_with_real_scenario():
    """
    Integration test: Verify logging works with realistic field names.
    
    This test uses realistic 1099-DIV field names to ensure logging
    works correctly with actual field naming patterns.
    """
    # Realistic PDF field names from 1099-DIV
    pdf_fields = {
        "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",
        "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",
        "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",
        "topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]",
    }
    
    # Create mapping with some valid and some invalid
    mapping = {
        "payerName": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",  # Valid
        "payerTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_4[0]",   # Invalid (wrong field)
        "recipientTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",  # Valid
        "totalDividends": "topmostSubform[0].Copy1[0].RghtCol[0].f2_99[0]",  # Invalid (doesn't exist)
    }
    
    # Set up logger
    logger = logging.getLogger("test_validation_realistic")
    logger.setLevel(logging.DEBUG)
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
        # Validate and log
        valid_results, invalid_results = validate_and_log_mappings(
            mapping, pdf_fields, logger
        )
        
        # Get log output
        log_output = log_capture.getvalue()
        
        # Verify correct number of valid and invalid mappings
        assert len(valid_results) == 2, "Should have 2 valid mappings"
        assert len(invalid_results) == 2, "Should have 2 invalid mappings"
        
        # Verify invalid mappings are logged
        assert "payerTIN" in log_output, "Invalid payerTIN mapping should be logged"
        assert "totalDividends" in log_output, "Invalid totalDividends mapping should be logged"
        assert "f2_4[0]" in log_output, "Invalid PDF field f2_4[0] should be logged"
        assert "f2_99[0]" in log_output, "Invalid PDF field f2_99[0] should be logged"
        
        # Verify 2 warning entries
        warning_count = log_output.count("Invalid mapping:")
        assert warning_count == 2, f"Expected 2 warnings, found {warning_count}"
    
    finally:
        logger.removeHandler(handler)
