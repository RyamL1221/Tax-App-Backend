"""
Property-based tests for valid field mapping.

These tests verify that the FieldMapper correctly maps valid API field names
to their corresponding PDF field names. Each property test runs with a minimum
of 100 iterations.

Feature: fix-pdf-field-mapping
Property 1: Valid field mapping returns correct PDF field name

**Validates: Requirements 1.1**
"""

import pytest
from hypothesis import given, settings, strategies as st
from tax_document_generation.field_mapper import FieldMapper
from tax_document_generation.field_mappings.div_1099 import FIELD_MAPPING, SUPPORTED_FIELDS


# Strategy for generating valid API field names
def valid_api_field_name_strategy():
    """Generate valid API field names from the 1099-DIV field reference."""
    return st.sampled_from(SUPPORTED_FIELDS)


class TestValidFieldMappingProperty:
    """Property-based tests for valid field mapping."""
    
    @settings(max_examples=100)
    @given(api_field_name=valid_api_field_name_strategy())
    def test_valid_field_mapping_returns_correct_pdf_field_name(self, api_field_name):
        """
        **Validates: Requirements 1.1**
        Feature: fix-pdf-field-mapping, Property 1: Valid field mapping returns correct PDF field name
        
        For any valid API field name in the 1099-DIV field reference,
        when the Field_Mapper maps that field name, it should return
        the corresponding PDF field name from the mapping configuration.
        
        This test verifies that:
        1. Valid API field names are recognized
        2. The correct PDF field name is returned
        3. The mapping is consistent with the configuration
        4. No exceptions are raised for valid field names
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the API field name
        pdf_field_name = mapper.map_field(api_field_name)
        
        # Verify the mapping is correct
        expected_pdf_field_name = FIELD_MAPPING[api_field_name]
        
        assert pdf_field_name is not None, \
            f"Valid API field '{api_field_name}' should map to a PDF field name"
        
        assert pdf_field_name == expected_pdf_field_name, \
            f"API field '{api_field_name}' should map to '{expected_pdf_field_name}', got '{pdf_field_name}'"
    
    @settings(max_examples=100)
    @given(api_field_name=valid_api_field_name_strategy())
    def test_valid_field_mapping_returns_non_empty_string(self, api_field_name):
        """
        **Validates: Requirements 1.1**
        Feature: fix-pdf-field-mapping, Property 1: Valid field mapping returns correct PDF field name
        
        For any valid API field name,
        the mapped PDF field name should be a non-empty string.
        
        This test verifies that:
        1. PDF field names are never empty
        2. PDF field names are strings
        3. Mappings are complete and valid
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the API field name
        pdf_field_name = mapper.map_field(api_field_name)
        
        # Verify the result is a non-empty string
        assert isinstance(pdf_field_name, str), \
            f"PDF field name should be a string, got {type(pdf_field_name)}"
        
        assert len(pdf_field_name) > 0, \
            f"PDF field name should not be empty for API field '{api_field_name}'"
    
    @settings(max_examples=100)
    @given(api_field_name=valid_api_field_name_strategy())
    def test_valid_field_mapping_follows_pdf_naming_convention(self, api_field_name):
        """
        **Validates: Requirements 1.1**
        Feature: fix-pdf-field-mapping, Property 1: Valid field mapping returns correct PDF field name
        
        For any valid API field name,
        the mapped PDF field name should follow the IRS PDF naming convention:
        topmostSubform[0].Copy1[0].<section>[0].<field_id>[0]
        
        This test verifies that:
        1. PDF field names follow the expected structure
        2. PDF field names contain required components
        3. Mappings point to valid PDF form fields
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the API field name
        pdf_field_name = mapper.map_field(api_field_name)
        
        # Verify the PDF field name follows the expected pattern
        assert pdf_field_name.startswith("topmostSubform[0].Copy1[0]."), \
            f"PDF field name should start with 'topmostSubform[0].Copy1[0].', got '{pdf_field_name}'"
        
        # Verify it contains array notation [0]
        assert "[0]" in pdf_field_name, \
            f"PDF field name should contain array notation [0], got '{pdf_field_name}'"
        
        # Verify it ends with [0]
        assert pdf_field_name.endswith("[0]"), \
            f"PDF field name should end with [0], got '{pdf_field_name}'"
    
    @settings(max_examples=100)
    @given(api_field_name=valid_api_field_name_strategy())
    def test_valid_field_mapping_is_deterministic(self, api_field_name):
        """
        **Validates: Requirements 1.1**
        Feature: fix-pdf-field-mapping, Property 1: Valid field mapping returns correct PDF field name
        
        For any valid API field name,
        mapping it multiple times should always return the same PDF field name.
        
        This test verifies that:
        1. Mappings are deterministic
        2. No randomness or state affects mapping results
        3. Consistent behavior across multiple calls
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map the same field multiple times
        result1 = mapper.map_field(api_field_name)
        result2 = mapper.map_field(api_field_name)
        result3 = mapper.map_field(api_field_name)
        
        # Verify all results are identical
        assert result1 == result2 == result3, \
            f"Mapping should be deterministic for '{api_field_name}': got {result1}, {result2}, {result3}"
    
    @settings(max_examples=100)
    @given(api_field_name=valid_api_field_name_strategy())
    def test_valid_field_mapping_with_multiple_mappers(self, api_field_name):
        """
        **Validates: Requirements 1.1**
        Feature: fix-pdf-field-mapping, Property 1: Valid field mapping returns correct PDF field name
        
        For any valid API field name,
        mapping it with different FieldMapper instances should return the same result.
        
        This test verifies that:
        1. Mappings are consistent across instances
        2. No instance-specific state affects mappings
        3. Configuration is loaded correctly for each instance
        """
        # Initialize multiple field mappers
        mapper1 = FieldMapper("1099-DIV")
        mapper2 = FieldMapper("1099-DIV")
        mapper3 = FieldMapper("1099-DIV")
        
        # Map the same field with different instances
        result1 = mapper1.map_field(api_field_name)
        result2 = mapper2.map_field(api_field_name)
        result3 = mapper3.map_field(api_field_name)
        
        # Verify all results are identical
        assert result1 == result2 == result3, \
            f"Mapping should be consistent across instances for '{api_field_name}': got {result1}, {result2}, {result3}"
    
    def test_all_supported_fields_have_valid_mappings(self):
        """
        **Validates: Requirements 1.1**
        Feature: fix-pdf-field-mapping, Property 1: Valid field mapping returns correct PDF field name
        
        For all supported API field names,
        each should have a valid mapping to a PDF field name.
        
        This test verifies that:
        1. All fields in SUPPORTED_FIELDS have mappings
        2. No supported field returns None
        3. Configuration is complete
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Verify all supported fields have valid mappings
        for api_field_name in SUPPORTED_FIELDS:
            pdf_field_name = mapper.map_field(api_field_name)
            
            assert pdf_field_name is not None, \
                f"Supported field '{api_field_name}' should have a valid mapping"
            
            assert isinstance(pdf_field_name, str), \
                f"Mapping for '{api_field_name}' should be a string, got {type(pdf_field_name)}"
            
            assert len(pdf_field_name) > 0, \
                f"Mapping for '{api_field_name}' should not be empty"
