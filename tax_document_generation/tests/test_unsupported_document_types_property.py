"""
Property-based tests for unsupported document type handling.

These tests verify that the FieldMapper raises clear errors when initialized
with unsupported document types. Each property test runs with a minimum of
100 iterations.

Feature: fix-pdf-field-mapping
Property 4: Unsupported document types raise clear errors

**Validates: Requirements 2.2**
"""

import pytest
from hypothesis import given, settings, strategies as st
from tax_document_generation.field_mapper import FieldMapper


# Strategy for generating invalid document types (anything except "1099-DIV")
def invalid_document_type_strategy():
    """Generate invalid document type strings."""
    return st.one_of(
        # Random strings
        st.text(min_size=1, max_size=50).filter(lambda s: s != "1099-DIV"),
        # Common variations that might be tried
        st.sampled_from([
            "1099-MISC",
            "1099-INT",
            "1099-B",
            "1099-R",
            "1099-G",
            "1099-C",
            "1099-A",
            "1099-S",
            "1099-K",
            "1099-Q",
            "1099-SA",
            "1099-LTC",
            "1099-OID",
            "1099-PATR",
            "1099-CAP",
            "1040",
            "W-2",
            "W-4",
            "1040-ES",
            "1040-SR",
            "1040-NR",
            "1040-X",
            "Schedule A",
            "Schedule C",
            "Schedule D",
            "Schedule E",
            "",  # Empty string
            " ",  # Whitespace
            "1099DIV",  # Missing dash
            "1099 DIV",  # Space instead of dash
            "1099_DIV",  # Underscore instead of dash
            "1099-div",  # Lowercase
            "1099-Div",  # Mixed case
            "div-1099",  # Reversed
            "DIV-1099",  # Reversed uppercase
        ]),
        # Numeric values as strings
        st.integers().map(str),
        # Special characters
        st.text(alphabet="!@#$%^&*()[]{}|\\;:'\",.<>?/~`", min_size=1, max_size=20),
    )


class TestUnsupportedDocumentTypesProperty:
    """Property-based tests for unsupported document type handling."""
    
    @settings(max_examples=100)
    @given(document_type=invalid_document_type_strategy())
    def test_unsupported_document_type_raises_value_error(self, document_type):
        """
        **Validates: Requirements 2.2**
        Feature: fix-pdf-field-mapping, Property 4: Unsupported document types raise clear errors
        
        For any document type string that is not "1099-DIV",
        when initializing a FieldMapper, it should raise a ValueError
        with a clear message indicating the document type is not supported.
        
        This test verifies that:
        1. Unsupported document types are rejected
        2. ValueError is raised (not a different exception type)
        3. Error message is clear and informative
        4. Error message mentions the unsupported document type
        5. Error message lists supported types
        """
        # Verification: Initializing FieldMapper with unsupported type should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            FieldMapper(document_type)
        
        # Verify the error message is clear and informative
        error_message = str(exc_info.value)
        
        # Error message should mention the document type that was attempted
        assert document_type in error_message, \
            f"Error message should mention the attempted document type '{document_type}': {error_message}"
        
        # Error message should indicate it's not supported
        assert "not supported" in error_message.lower(), \
            f"Error message should indicate the type is not supported: {error_message}"
        
        # Error message should list supported types
        assert "1099-DIV" in error_message, \
            f"Error message should list supported types (1099-DIV): {error_message}"
    
    @settings(max_examples=100)
    @given(document_type=invalid_document_type_strategy())
    def test_error_message_format_is_consistent(self, document_type):
        """
        **Validates: Requirements 2.2**
        Feature: fix-pdf-field-mapping, Property 4: Unsupported document types raise clear errors
        
        For any unsupported document type,
        the error message format should be consistent and follow the pattern:
        "Document type '{type}' is not supported. Supported types: [...]"
        
        This test verifies that:
        1. Error messages follow a consistent format
        2. Users can rely on the error message structure
        3. Error messages are machine-parseable if needed
        """
        # Verification: Error message should follow consistent format
        with pytest.raises(ValueError) as exc_info:
            FieldMapper(document_type)
        
        error_message = str(exc_info.value)
        
        # Check for expected format components
        assert "Document type" in error_message, \
            f"Error message should start with 'Document type': {error_message}"
        
        assert "Supported types:" in error_message, \
            f"Error message should include 'Supported types:': {error_message}"
    
    def test_supported_document_type_does_not_raise_error(self):
        """
        **Validates: Requirements 2.2**
        Feature: fix-pdf-field-mapping, Property 4: Unsupported document types raise clear errors
        
        For the supported document type "1099-DIV",
        initializing a FieldMapper should NOT raise any error.
        
        This test verifies that:
        1. The supported document type is correctly identified
        2. No false positives in validation
        3. FieldMapper can be successfully initialized with valid type
        """
        # Verification: Supported document type should not raise error
        # This should not raise any exception
        mapper = FieldMapper("1099-DIV")
        
        # Verify the mapper was created successfully
        assert mapper is not None
        assert mapper.document_type == "1099-DIV"
    
    @settings(max_examples=100)
    @given(
        prefix=st.text(min_size=0, max_size=10),
        suffix=st.text(min_size=0, max_size=10)
    )
    def test_variations_of_valid_type_are_rejected(self, prefix, suffix):
        """
        **Validates: Requirements 2.2**
        Feature: fix-pdf-field-mapping, Property 4: Unsupported document types raise clear errors
        
        For any variation of the valid document type (with prefix/suffix),
        the FieldMapper should reject it unless it exactly matches "1099-DIV".
        
        This test verifies that:
        1. Document type matching is exact (not substring matching)
        2. Variations like "X1099-DIV" or "1099-DIVX" are rejected
        3. Only exact match is accepted
        """
        # Create a variation by adding prefix and/or suffix
        document_type = f"{prefix}1099-DIV{suffix}"
        
        # Skip if we accidentally created the exact match
        if document_type == "1099-DIV":
            return
        
        # Verification: Variations should be rejected
        with pytest.raises(ValueError) as exc_info:
            FieldMapper(document_type)
        
        error_message = str(exc_info.value)
        assert "not supported" in error_message.lower(), \
            f"Variation '{document_type}' should be rejected: {error_message}"
    
    @settings(max_examples=100)
    @given(
        whitespace_before=st.text(alphabet=" \t\n\r", min_size=0, max_size=5),
        whitespace_after=st.text(alphabet=" \t\n\r", min_size=0, max_size=5)
    )
    def test_whitespace_variations_are_rejected(self, whitespace_before, whitespace_after):
        """
        **Validates: Requirements 2.2**
        Feature: fix-pdf-field-mapping, Property 4: Unsupported document types raise clear errors
        
        For any document type with leading or trailing whitespace,
        the FieldMapper should reject it (no automatic trimming).
        
        This test verifies that:
        1. Document type matching is strict (no automatic whitespace trimming)
        2. " 1099-DIV" and "1099-DIV " are rejected
        3. Only exact match without whitespace is accepted
        """
        # Create a variation with whitespace
        document_type = f"{whitespace_before}1099-DIV{whitespace_after}"
        
        # Skip if we accidentally created the exact match (no whitespace)
        if document_type == "1099-DIV":
            return
        
        # Verification: Whitespace variations should be rejected
        with pytest.raises(ValueError) as exc_info:
            FieldMapper(document_type)
        
        error_message = str(exc_info.value)
        assert "not supported" in error_message.lower(), \
            f"Whitespace variation should be rejected: {error_message}"
