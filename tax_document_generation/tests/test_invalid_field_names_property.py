"""
Property-based tests for invalid field name handling.

These tests verify that the FieldMapper returns None for invalid API field names
without raising exceptions. Each property test runs with a minimum of 100 iterations.

Feature: fix-pdf-field-mapping
Property 3: Invalid field names return None

**Validates: Requirements 1.3, 4.1**
"""

import pytest
from hypothesis import given, settings, strategies as st
from tax_document_generation.field_mapper import FieldMapper
from tax_document_generation.field_mappings.div_1099 import SUPPORTED_FIELDS


# Strategy for generating invalid API field names
def invalid_api_field_name_strategy():
    """Generate invalid API field names (anything not in SUPPORTED_FIELDS)."""
    return st.one_of(
        # Random strings
        st.text(min_size=1, max_size=100).filter(lambda s: s not in SUPPORTED_FIELDS),
        # Common field name variations that might be tried
        st.sampled_from([
            "payername",  # Lowercase
            "PayerName",  # PascalCase
            "PAYERNAME",  # Uppercase
            "payer_name",  # Snake case
            "payer-name",  # Kebab case
            "payer name",  # Space separated
            "payerName1",  # With number
            "payerNameX",  # With suffix
            "XpayerName",  # With prefix
            "totalordinarydividends",  # Lowercase
            "TotalOrdinaryDividends",  # PascalCase
            "TOTALORDINARYDIVIDENDS",  # Uppercase
            "total_ordinary_dividends",  # Snake case
            "total-ordinary-dividends",  # Kebab case
            "recipienttin",  # Lowercase
            "RecipientTIN",  # PascalCase
            "RECIPIENTTIN",  # Uppercase
            "recipient_tin",  # Snake case
            "recipient-tin",  # Kebab case
            "unknownField",
            "invalidField",
            "nonExistentField",
            "randomField",
            "testField",
            "dummyField",
            "fakeField",
            "box1a",  # Box number instead of field name
            "box1b",
            "box2a",
            "field1",
            "field2",
            "f2_1",  # PDF field ID instead of API name
            "f2_2",
            "topmostSubform",  # PDF structure name
            "",  # Empty string
            " ",  # Whitespace
            "   ",  # Multiple spaces
            "\t",  # Tab
            "\n",  # Newline
            "null",
            "None",
            "undefined",
            "NaN",
        ]),
        # Numeric values as strings
        st.integers().map(str),
        # Special characters
        st.text(alphabet="!@#$%^&*()[]{}|\\;:'\",.<>?/~`", min_size=1, max_size=50),
        # Very long strings
        st.text(min_size=100, max_size=1000).filter(lambda s: s not in SUPPORTED_FIELDS),
        # Unicode characters
        st.text(alphabet="αβγδεζηθικλμνξοπρστυφχψω", min_size=1, max_size=50),
        # Mixed valid and invalid (partial matches)
        st.text(min_size=1, max_size=50).map(lambda s: f"payerName_{s}"),
        st.text(min_size=1, max_size=50).map(lambda s: f"{s}_payerName"),
    )


class TestInvalidFieldNamesProperty:
    """Property-based tests for invalid field name handling."""
    
    @settings(max_examples=100)
    @given(api_field_name=invalid_api_field_name_strategy())
    def test_invalid_field_names_return_none(self, api_field_name):
        """
        **Validates: Requirements 1.3, 4.1**
        Feature: fix-pdf-field-mapping, Property 3: Invalid field names return None
        
        For any string that is not a valid API field name,
        when the Field_Mapper attempts to map it, it should return None
        without raising an exception.
        
        This test verifies that:
        1. Invalid field names are handled gracefully
        2. None is returned (not an exception)
        3. No errors or crashes occur
        4. System continues to function normally
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the invalid field name - should not raise exception
        result = mapper.map_field(api_field_name)
        
        # Verify None is returned
        assert result is None, \
            f"Invalid API field '{api_field_name}' should return None, got '{result}'"
    
    @settings(max_examples=100)
    @given(api_field_name=invalid_api_field_name_strategy())
    def test_invalid_field_names_do_not_raise_exceptions(self, api_field_name):
        """
        **Validates: Requirements 1.3, 4.1**
        Feature: fix-pdf-field-mapping, Property 3: Invalid field names return None
        
        For any invalid API field name,
        mapping it should not raise any exception.
        
        This test verifies that:
        1. No KeyError is raised
        2. No ValueError is raised
        3. No AttributeError is raised
        4. No other exceptions are raised
        5. Graceful degradation is maintained
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # This should not raise any exception
        try:
            result = mapper.map_field(api_field_name)
            # If we get here, no exception was raised (good!)
            assert result is None, \
                f"Invalid field should return None, got '{result}'"
        except Exception as e:
            pytest.fail(
                f"Mapping invalid field '{api_field_name}' should not raise exception, "
                f"but raised {type(e).__name__}: {e}"
            )
    
    @settings(max_examples=100)
    @given(api_field_name=invalid_api_field_name_strategy())
    def test_invalid_field_names_are_consistent(self, api_field_name):
        """
        **Validates: Requirements 1.3, 4.1**
        Feature: fix-pdf-field-mapping, Property 3: Invalid field names return None
        
        For any invalid API field name,
        mapping it multiple times should always return None.
        
        This test verifies that:
        1. Behavior is deterministic
        2. No state changes affect the result
        3. Consistent None return for invalid fields
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the same invalid field multiple times
        result1 = mapper.map_field(api_field_name)
        result2 = mapper.map_field(api_field_name)
        result3 = mapper.map_field(api_field_name)
        
        # Verify all results are None
        assert result1 is None, \
            f"First mapping of invalid field '{api_field_name}' should return None"
        assert result2 is None, \
            f"Second mapping of invalid field '{api_field_name}' should return None"
        assert result3 is None, \
            f"Third mapping of invalid field '{api_field_name}' should return None"
    
    @settings(max_examples=100)
    @given(
        valid_field=st.sampled_from(SUPPORTED_FIELDS),
        prefix=st.text(min_size=1, max_size=20),
    )
    def test_field_names_with_prefix_return_none(self, valid_field, prefix):
        """
        **Validates: Requirements 1.3, 4.1**
        Feature: fix-pdf-field-mapping, Property 3: Invalid field names return None
        
        For any valid field name with a prefix added,
        it should be treated as invalid and return None.
        
        This test verifies that:
        1. Field name matching is exact (not substring matching)
        2. Partial matches are not accepted
        3. Only exact field names are valid
        """
        # Create an invalid field by adding a prefix
        invalid_field = f"{prefix}{valid_field}"
        
        # Skip if we accidentally created a valid field
        if invalid_field in SUPPORTED_FIELDS:
            return
        
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the invalid field
        result = mapper.map_field(invalid_field)
        
        # Verify None is returned
        assert result is None, \
            f"Field with prefix '{invalid_field}' should return None, got '{result}'"
    
    @settings(max_examples=100)
    @given(
        valid_field=st.sampled_from(SUPPORTED_FIELDS),
        suffix=st.text(min_size=1, max_size=20),
    )
    def test_field_names_with_suffix_return_none(self, valid_field, suffix):
        """
        **Validates: Requirements 1.3, 4.1**
        Feature: fix-pdf-field-mapping, Property 3: Invalid field names return None
        
        For any valid field name with a suffix added,
        it should be treated as invalid and return None.
        
        This test verifies that:
        1. Field name matching is exact (not substring matching)
        2. Partial matches are not accepted
        3. Only exact field names are valid
        """
        # Create an invalid field by adding a suffix
        invalid_field = f"{valid_field}{suffix}"
        
        # Skip if we accidentally created a valid field
        if invalid_field in SUPPORTED_FIELDS:
            return
        
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the invalid field
        result = mapper.map_field(invalid_field)
        
        # Verify None is returned
        assert result is None, \
            f"Field with suffix '{invalid_field}' should return None, got '{result}'"
    
    @settings(max_examples=100)
    @given(valid_field=st.sampled_from(SUPPORTED_FIELDS))
    def test_case_variations_of_valid_fields_return_none(self, valid_field):
        """
        **Validates: Requirements 1.3, 4.1**
        Feature: fix-pdf-field-mapping, Property 3: Invalid field names return None
        
        For any case variation of a valid field name,
        it should be treated as invalid and return None (case-sensitive matching).
        
        This test verifies that:
        1. Field name matching is case-sensitive
        2. "payerName" != "PayerName" != "payername"
        3. Only exact case matches are valid
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Test uppercase variation
        uppercase_field = valid_field.upper()
        if uppercase_field != valid_field:
            result = mapper.map_field(uppercase_field)
            assert result is None, \
                f"Uppercase variation '{uppercase_field}' should return None, got '{result}'"
        
        # Test lowercase variation
        lowercase_field = valid_field.lower()
        if lowercase_field != valid_field:
            result = mapper.map_field(lowercase_field)
            assert result is None, \
                f"Lowercase variation '{lowercase_field}' should return None, got '{result}'"
        
        # Test title case variation
        title_field = valid_field.title()
        if title_field != valid_field:
            result = mapper.map_field(title_field)
            assert result is None, \
                f"Title case variation '{title_field}' should return None, got '{result}'"
    
    def test_empty_string_returns_none(self):
        """
        **Validates: Requirements 1.3, 4.1**
        Feature: fix-pdf-field-mapping, Property 3: Invalid field names return None
        
        For an empty string field name,
        it should return None without raising an exception.
        
        This test verifies that:
        1. Empty strings are handled gracefully
        2. No KeyError or other exception is raised
        3. None is returned
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map empty string
        result = mapper.map_field("")
        
        # Verify None is returned
        assert result is None, \
            f"Empty string should return None, got '{result}'"
    
    def test_whitespace_only_returns_none(self):
        """
        **Validates: Requirements 1.3, 4.1**
        Feature: fix-pdf-field-mapping, Property 3: Invalid field names return None
        
        For whitespace-only field names,
        they should return None without raising an exception.
        
        This test verifies that:
        1. Whitespace strings are handled gracefully
        2. No trimming or normalization occurs
        3. None is returned
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Test various whitespace strings
        whitespace_strings = [" ", "  ", "   ", "\t", "\n", "\r", " \t\n"]
        
        for whitespace in whitespace_strings:
            result = mapper.map_field(whitespace)
            assert result is None, \
                f"Whitespace string '{repr(whitespace)}' should return None, got '{result}'"
