"""
Property-based tests for configuration preservation and backward compatibility.

**Validates: Requirements 7.1, 7.3**

Property 10: Configuration Preservation
For any configuration update, all API field names that were present before the
update should remain present after the update (backward compatibility).

This test verifies that the corrected TIN mappings maintain backward compatibility
by preserving all existing API field names.
"""

import pytest
from hypothesis import given, strategies as st
from typing import Dict, Set


# Import the field mapping
from tax_document_generation.field_mappings.div_1099 import FIELD_MAPPING, SUPPORTED_FIELDS


# Expected API field names that should always be present
EXPECTED_API_FIELDS = {
    # Calendar year
    "calendarYear",
    
    # Payer information
    "payerName",
    "payerTIN",
    "payerStreetAddress",
    "payerCity",
    "payerState",
    "payerZip",
    "payerCountry",
    "payerPhone",
    
    # Recipient information
    "recipientTIN",
    "recipientName",
    "recipientStreetAddress",
    "recipientCity",
    "recipientState",
    "recipientZip",
    "recipientCountry",
    
    # Account number
    "accountNumber",
    
    # Box 1: Dividends
    "totalOrdinaryDividends",
    "qualifiedDividends",
    
    # Box 2: Capital gains
    "totalCapitalGainDistributions",
    "unrecapturedSection1250Gain",
    "section1202Gain",
    "collectibles28Gain",
    "section897OrdinaryDividends",
    "section897CapitalGain",
    
    # Box 3-7
    "nondividendDistributions",
    "federalIncomeTaxWithheld",
    "section199ADividends",
    "investmentExpenses",
    "foreignTaxPaid",
    
    # Box 8-13
    "foreignCountry",
    "cashLiquidationDistributions",
    "noncashLiquidationDistributions",
    "fatcaFilingRequirement",
    "exemptInterestDividends",
    "specifiedPrivateActivityBondInterest",
    
    # Box 14-16: State tax
    "state",
    "stateIdentificationNumber",
    "stateTaxWithheld",
}


def test_all_expected_api_fields_present():
    """
    Test that all expected API field names are present in the mapping.
    
    This ensures backward compatibility - no API fields have been removed.
    """
    # Get actual API fields from mapping
    actual_api_fields = set(FIELD_MAPPING.keys())
    
    # Verify all expected fields are present
    missing_fields = EXPECTED_API_FIELDS - actual_api_fields
    assert len(missing_fields) == 0, \
        f"Missing API fields (backward compatibility broken): {missing_fields}"
    
    # Verify SUPPORTED_FIELDS matches FIELD_MAPPING keys
    assert set(SUPPORTED_FIELDS) == actual_api_fields, \
        "SUPPORTED_FIELDS should match FIELD_MAPPING keys"


def test_tin_fields_present_and_mapped():
    """
    Test that TIN fields are present and mapped to correct PDF fields.
    
    This specifically verifies the corrected TIN mappings are in place.
    """
    # Verify payer TIN field exists
    assert "payerTIN" in FIELD_MAPPING, \
        "payerTIN API field should be present"
    
    # Verify recipient TIN field exists
    assert "recipientTIN" in FIELD_MAPPING, \
        "recipientTIN API field should be present"
    
    # Verify payer TIN is mapped to correct PDF field (f2_7, not f2_4)
    payer_tin_mapping = FIELD_MAPPING["payerTIN"]
    assert "f2_7[0]" in payer_tin_mapping, \
        "payerTIN should be mapped to f2_7[0] (correct TIN field)"
    assert "f2_4[0]" not in payer_tin_mapping, \
        "payerTIN should NOT be mapped to f2_4[0] (city field)"
    
    # Verify recipient TIN is mapped to correct PDF field (f2_8, not f2_39)
    recipient_tin_mapping = FIELD_MAPPING["recipientTIN"]
    assert "f2_8[0]" in recipient_tin_mapping, \
        "recipientTIN should be mapped to f2_8[0] (correct TIN field)"
    assert "f2_39[0]" not in recipient_tin_mapping, \
        "recipientTIN should NOT be mapped to f2_39[0] (account number field)"


def test_city_and_account_number_fields_preserved():
    """
    Test that city and account number fields are still present.
    
    This ensures that fixing the TIN mappings didn't remove the legitimate
    city and account number fields.
    """
    # Verify city field exists
    assert "payerCity" in FIELD_MAPPING, \
        "payerCity API field should be present"
    
    # Verify account number field exists
    assert "accountNumber" in FIELD_MAPPING, \
        "accountNumber API field should be present"
    
    # Verify city is mapped to f2_4
    city_mapping = FIELD_MAPPING["payerCity"]
    assert "f2_4[0]" in city_mapping, \
        "payerCity should be mapped to f2_4[0] (city field)"
    
    # Verify account number is mapped to f2_39
    account_mapping = FIELD_MAPPING["accountNumber"]
    assert "f2_39[0]" in account_mapping, \
        "accountNumber should be mapped to f2_39[0] (account number field)"


def test_all_mappings_are_strings():
    """
    Property: All API field names and PDF field names are strings.
    
    This ensures the mapping structure is correct.
    """
    for api_field, pdf_field in FIELD_MAPPING.items():
        assert isinstance(api_field, str), \
            f"API field name should be string, got {type(api_field)}"
        assert isinstance(pdf_field, str), \
            f"PDF field name should be string, got {type(pdf_field)}"
        assert len(api_field) > 0, \
            "API field name should not be empty"
        assert len(pdf_field) > 0, \
            "PDF field name should not be empty"


def test_all_pdf_fields_follow_naming_convention():
    """
    Property: All PDF field names follow the expected naming convention.
    
    PDF field names should follow the pattern:
    topmostSubform[0].Copy1[0].<section>[0].<field_id>[0]
    """
    for api_field, pdf_field in FIELD_MAPPING.items():
        # Should start with topmostSubform[0]
        assert pdf_field.startswith("topmostSubform[0]"), \
            f"PDF field {pdf_field} should start with 'topmostSubform[0]'"
        
        # Should contain Copy1[0]
        assert "Copy1[0]" in pdf_field, \
            f"PDF field {pdf_field} should contain 'Copy1[0]'"
        
        # Should end with [0]
        assert pdf_field.endswith("[0]"), \
            f"PDF field {pdf_field} should end with '[0]'"


def test_no_duplicate_api_field_names():
    """
    Property: All API field names are unique.
    
    There should be no duplicate API field names in the mapping.
    """
    api_fields = list(FIELD_MAPPING.keys())
    unique_api_fields = set(api_fields)
    
    assert len(api_fields) == len(unique_api_fields), \
        "API field names should be unique (no duplicates)"


def test_mapping_count_matches_expected():
    """
    Test that the mapping contains the expected number of fields.
    
    This helps detect if fields were accidentally removed.
    """
    expected_count = len(EXPECTED_API_FIELDS)
    actual_count = len(FIELD_MAPPING)
    
    assert actual_count >= expected_count, \
        f"Mapping should have at least {expected_count} fields, but has {actual_count}"


def test_required_fields_present():
    """
    Test that required fields for 1099-DIV are present.
    
    These are the minimum fields needed for a valid 1099-DIV form.
    """
    required_fields = {
        "payerName",
        "payerTIN",
        "recipientTIN",
        "totalOrdinaryDividends"
    }
    
    actual_fields = set(FIELD_MAPPING.keys())
    missing_required = required_fields - actual_fields
    
    assert len(missing_required) == 0, \
        f"Missing required fields: {missing_required}"


def test_corrected_mappings_are_in_left_column():
    """
    Test that TIN fields are mapped to LeftCol (left column).
    
    TIN fields should be in the left column with payer/recipient information,
    not in the right column with box values.
    """
    # Payer TIN should be in LeftCol
    payer_tin_mapping = FIELD_MAPPING["payerTIN"]
    assert "LeftCol[0]" in payer_tin_mapping, \
        "payerTIN should be in LeftCol (left column)"
    assert "RghtCol[0]" not in payer_tin_mapping, \
        "payerTIN should NOT be in RghtCol (right column)"
    
    # Recipient TIN should be in LeftCol
    recipient_tin_mapping = FIELD_MAPPING["recipientTIN"]
    assert "LeftCol[0]" in recipient_tin_mapping, \
        "recipientTIN should be in LeftCol (left column)"
    assert "RghtCol[0]" not in recipient_tin_mapping, \
        "recipientTIN should NOT be in RghtCol (right column)"


def test_no_api_fields_removed_from_original():
    """
    Regression test: Verify no API fields were removed.
    
    This test ensures that the correction process didn't accidentally
    remove any existing API fields.
    """
    # These are all the fields that should exist based on the 1099-DIV form
    # and the original field mapping configuration
    original_fields = EXPECTED_API_FIELDS
    
    current_fields = set(FIELD_MAPPING.keys())
    removed_fields = original_fields - current_fields
    
    assert len(removed_fields) == 0, \
        f"API fields were removed (backward compatibility broken): {removed_fields}"


def test_api_field_names_follow_camel_case():
    """
    Property: All API field names follow camelCase convention.
    
    This ensures consistency in the API interface.
    """
    for api_field in FIELD_MAPPING.keys():
        # Should start with lowercase letter
        assert api_field[0].islower(), \
            f"API field {api_field} should start with lowercase letter (camelCase)"
        
        # Should not contain underscores (camelCase, not snake_case)
        assert "_" not in api_field, \
            f"API field {api_field} should use camelCase, not snake_case"
        
        # Should not contain spaces
        assert " " not in api_field, \
            f"API field {api_field} should not contain spaces"


@given(
    api_field=st.sampled_from(list(EXPECTED_API_FIELDS))
)
def test_every_expected_field_has_mapping(api_field: str):
    """
    Property: Every expected API field has a PDF mapping.
    
    For any expected API field, it should have a corresponding PDF field mapping.
    """
    assert api_field in FIELD_MAPPING, \
        f"API field {api_field} should have a PDF mapping"
    
    pdf_field = FIELD_MAPPING[api_field]
    assert pdf_field is not None, \
        f"API field {api_field} should have a non-null PDF mapping"
    assert len(pdf_field) > 0, \
        f"API field {api_field} should have a non-empty PDF mapping"


def test_supported_fields_list_is_complete():
    """
    Test that SUPPORTED_FIELDS list contains all mapping keys.
    
    This ensures the SUPPORTED_FIELDS list is kept in sync with FIELD_MAPPING.
    """
    mapping_keys = set(FIELD_MAPPING.keys())
    supported_set = set(SUPPORTED_FIELDS)
    
    assert mapping_keys == supported_set, \
        "SUPPORTED_FIELDS should exactly match FIELD_MAPPING keys"


def test_configuration_structure_is_valid():
    """
    Test that the configuration structure is valid.
    
    This ensures the mapping is a proper dictionary with string keys and values.
    """
    # Should be a dictionary
    assert isinstance(FIELD_MAPPING, dict), \
        "FIELD_MAPPING should be a dictionary"
    
    # Should not be empty
    assert len(FIELD_MAPPING) > 0, \
        "FIELD_MAPPING should not be empty"
    
    # All keys should be strings
    for key in FIELD_MAPPING.keys():
        assert isinstance(key, str), \
            f"All keys should be strings, got {type(key)}"
    
    # All values should be strings
    for value in FIELD_MAPPING.values():
        assert isinstance(value, str), \
            f"All values should be strings, got {type(value)}"
