"""
Property-Based Tests for Keyword Field Identification

Tests that the inspect_pdf_fields module correctly identifies and highlights
fields containing specific keywords.

**Validates: Requirements 1.4**
"""

import os
import sys

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from inspect_pdf_fields import contains_keyword


@given(
    keyword=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_keyword_identification_case_insensitive_property(keyword: str):
    """
    Property: Keyword matching is case-insensitive. If a keyword appears in a field name
    in any case combination, it should be detected.
    
    **Validates: Requirements 1.4**
    """
    # Create field name containing the keyword in various cases
    field_with_keyword_lower = f"prefix_{keyword.lower()}_suffix"
    field_with_keyword_upper = f"prefix_{keyword.upper()}_suffix"
    field_with_keyword_mixed = f"prefix_{keyword}_suffix"
    
    keywords = [keyword]
    
    # Property: Keyword is detected regardless of case
    assert contains_keyword(field_with_keyword_lower, keywords), \
        f"Keyword '{keyword}' not detected in '{field_with_keyword_lower}'"
    
    assert contains_keyword(field_with_keyword_upper, keywords), \
        f"Keyword '{keyword}' not detected in '{field_with_keyword_upper}'"
    
    assert contains_keyword(field_with_keyword_mixed, keywords), \
        f"Keyword '{keyword}' not detected in '{field_with_keyword_mixed}'"


@given(
    keywords=st.lists(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'), min_size=1, max_size=5)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_multiple_keyword_detection_property(keywords: list):
    """
    Property: If any keyword from a list appears in a field name, the field
    should be identified as containing a keyword.
    
    **Validates: Requirements 1.4**
    """
    # Create field name containing the first keyword
    if keywords:
        first_keyword = keywords[0]
        field_name = f"test_{first_keyword}_field"
        
        # Property: Field is detected when it contains any keyword
        assert contains_keyword(field_name, keywords), \
            f"Field '{field_name}' not detected with keywords {keywords}"


def test_specific_keywords_detection():
    """
    Test that the specific keywords mentioned in requirements are detected:
    TIN, Name, City, Account
    
    **Validates: Requirements 1.4**
    """
    keywords = ["TIN", "Name", "City", "Account"]
    
    # Test field names that should be detected
    test_cases = [
        ("topmostSubform[0].Copy1[0].LeftCol[0].PayerTIN[0]", True),
        ("topmostSubform[0].Copy1[0].RghtCol[0].RecipientName[0]", True),
        ("topmostSubform[0].Copy1[0].LeftCol[0].CityStateZip[0]", True),
        ("topmostSubform[0].Copy1[0].RghtCol[0].AccountNumber[0]", True),
        ("topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]", False),  # No keyword
        ("topmostSubform[0].Copy1[0].RghtCol[0].Box1[0]", False),  # No keyword
    ]
    
    for field_name, should_match in test_cases:
        result = contains_keyword(field_name, keywords)
        assert result == should_match, \
            f"Field '{field_name}' should {'match' if should_match else 'not match'} keywords, but got {result}"


def test_keyword_as_substring():
    """
    Property: Keywords are detected even when they appear as substrings
    within larger words.
    
    **Validates: Requirements 1.4**
    """
    keywords = ["TIN", "Name"]
    
    # Test cases where keyword is part of a larger word
    assert contains_keyword("PayerTINNumber", keywords), \
        "TIN not detected in PayerTINNumber"
    
    assert contains_keyword("RecipientNameField", keywords), \
        "Name not detected in RecipientNameField"
    
    assert contains_keyword("PAYER_TIN_BOX", keywords), \
        "TIN not detected in PAYER_TIN_BOX"


def test_no_keyword_match():
    """
    Property: Fields without any keywords should not be identified.
    
    **Validates: Requirements 1.4**
    """
    keywords = ["TIN", "Name", "City", "Account"]
    
    # Field names without keywords
    non_matching_fields = [
        "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",
        "topmostSubform[0].Copy1[0].RghtCol[0].Box1[0]",
        "topmostSubform[0].Copy1[0].RghtCol[0].f1_9[0]",
        "CalendarYear",
        "CheckBox1",
    ]
    
    for field_name in non_matching_fields:
        assert not contains_keyword(field_name, keywords), \
            f"Field '{field_name}' should not match keywords, but it did"


def test_empty_keyword_list():
    """
    Property: If the keyword list is empty, no fields should be identified.
    
    **Validates: Requirements 1.4**
    """
    keywords = []
    
    # Any field name should not match empty keyword list
    field_names = [
        "PayerTIN",
        "RecipientName",
        "City",
        "AccountNumber",
        "RandomField",
    ]
    
    for field_name in field_names:
        assert not contains_keyword(field_name, keywords), \
            f"Field '{field_name}' should not match empty keyword list"


@given(
    field_name=st.text(min_size=1, max_size=50)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_keyword_function_returns_boolean_property(field_name: str):
    """
    Property: The contains_keyword function always returns a boolean value.
    
    **Validates: Requirements 1.4**
    """
    keywords = ["TIN", "Name", "City", "Account"]
    
    result = contains_keyword(field_name, keywords)
    
    # Property: Result is always a boolean
    assert isinstance(result, bool), \
        f"Expected bool, got {type(result)}"


def test_keyword_detection_with_special_characters():
    """
    Property: Keywords are detected even in field names with special characters.
    
    **Validates: Requirements 1.4**
    """
    keywords = ["TIN", "Name"]
    
    # Field names with special characters
    assert contains_keyword("Payer[TIN]Field", keywords), \
        "TIN not detected with brackets"
    
    assert contains_keyword("Recipient.Name.Box", keywords), \
        "Name not detected with dots"
    
    assert contains_keyword("PAYER_TIN_123", keywords), \
        "TIN not detected with underscores and numbers"
