"""
Property-based tests for three-copy mapping cardinality in FieldMapper.

These tests verify that the map_all_fields() method generates exactly three
PDF field name mappings (one for Copy1, one for Copy2, and one for CopyB) for
each API field name, with all three copies receiving the same value.

Feature: multi-page-form-filling
Property 2: Three-Copy Mapping Cardinality

**Validates: Requirements 1.1, 1.3**
"""

import pytest
from hypothesis import given, settings, strategies as st
from tax_document_generation.field_mapper import FieldMapper
from tax_document_generation.field_mappings.div_1099 import SUPPORTED_FIELDS


# Strategy for generating valid API field names
def valid_api_field_name_strategy():
    """Generate valid API field names from the supported fields list."""
    return st.sampled_from(SUPPORTED_FIELDS)


# Strategy for generating form data with random API fields
@st.composite
def form_data_strategy(draw):
    """
    Generate random form data dictionaries with valid API field names.
    
    Returns a dictionary with 1-10 API field names as keys and random
    string values.
    """
    # Choose 1-10 random API fields
    num_fields = draw(st.integers(min_value=1, max_value=10))
    
    # Sample unique API field names
    api_fields = draw(st.lists(
        valid_api_field_name_strategy(),
        min_size=num_fields,
        max_size=num_fields,
        unique=True
    ))
    
    # Generate random values for each field
    form_data = {}
    for field in api_fields:
        value = draw(st.text(min_size=1, max_size=50))
        form_data[field] = value
    
    return form_data


# Strategy for generating form data with all supported fields
@st.composite
def complete_form_data_strategy(draw):
    """
    Generate form data with all supported API fields.
    
    Returns a dictionary with all API field names as keys and random
    string values.
    """
    form_data = {}
    for field in SUPPORTED_FIELDS:
        value = draw(st.text(min_size=1, max_size=50))
        form_data[field] = value
    
    return form_data


class TestThreeCopyMappingCardinalityProperty:
    """Property-based tests for three-copy mapping cardinality."""
    
    @settings(max_examples=20)
    @given(form_data=form_data_strategy())
    def test_exactly_three_pdf_fields_per_api_field(self, form_data):
        """
        **Validates: Requirements 1.1, 1.3**
        Feature: multi-page-form-filling, Property 2: Three-Copy Mapping Cardinality
        
        For any API field name in the form data,
        the Field_Mapper should generate exactly three PDF field name mappings
        (one for Copy1, one for Copy2, and one for CopyB).
        
        This test verifies that:
        1. Each API field generates exactly 3 PDF field mappings
        2. The total number of PDF fields is 3x the number of API fields
        3. All three copies are generated for each field
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Count the number of API fields that have mappings
        num_api_fields = len(form_data)
        
        # CRITICAL VERIFICATION: Total PDF fields should be 3x the number of API fields
        expected_pdf_fields = num_api_fields * 3
        actual_pdf_fields = len(mapped_data)
        
        assert actual_pdf_fields == expected_pdf_fields, \
            f"Should generate {expected_pdf_fields} PDF fields (3 per API field), " \
            f"got {actual_pdf_fields}"
    
    @settings(max_examples=20)
    @given(form_data=form_data_strategy())
    def test_each_api_field_maps_to_three_copies(self, form_data):
        """
        **Validates: Requirements 1.1, 1.3**
        Feature: multi-page-form-filling, Property 2: Three-Copy Mapping Cardinality
        
        For any API field name in the form data,
        the Field_Mapper should generate mappings for Copy1, Copy2, and CopyB.
        
        This test verifies that:
        1. Each API field has a Copy1 mapping
        2. Each API field has a Copy2 mapping
        3. Each API field has a CopyB mapping
        4. No other copy variants are generated
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # For each API field, verify it has exactly 3 PDF field mappings
        for api_field_name in form_data.keys():
            # Get the base PDF field name (Copy1 version)
            base_pdf_field = mapper.map_field(api_field_name)
            
            if base_pdf_field is None:
                # Skip unmapped fields
                continue
            
            # Generate expected Copy2 and CopyB field names
            copy1_field = base_pdf_field
            copy2_field = base_pdf_field.replace("Copy1[0]", "Copy2[0]")
            copyb_field = base_pdf_field.replace("Copy1[0]", "CopyB[0]")
            
            # CRITICAL VERIFICATION: All three copies should exist in mapped data
            assert copy1_field in mapped_data, \
                f"Copy1 field '{copy1_field}' should exist for API field '{api_field_name}'"
            
            assert copy2_field in mapped_data, \
                f"Copy2 field '{copy2_field}' should exist for API field '{api_field_name}'"
            
            assert copyb_field in mapped_data, \
                f"CopyB field '{copyb_field}' should exist for API field '{api_field_name}'"
    
    @settings(max_examples=20)
    @given(form_data=form_data_strategy())
    def test_all_three_copies_have_same_value(self, form_data):
        """
        **Validates: Requirements 1.1, 1.3**
        Feature: multi-page-form-filling, Property 2: Three-Copy Mapping Cardinality
        
        For any API field name in the form data,
        all three PDF field name mappings (Copy1, Copy2, CopyB) should have
        the same value from the form data.
        
        This test verifies that:
        1. Copy1, Copy2, and CopyB all have the same value
        2. The value matches the original API field value
        3. No value transformation occurs
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # For each API field, verify all three copies have the same value
        for api_field_name, expected_value in form_data.items():
            # Get the base PDF field name (Copy1 version)
            base_pdf_field = mapper.map_field(api_field_name)
            
            if base_pdf_field is None:
                # Skip unmapped fields
                continue
            
            # Generate expected Copy2 and CopyB field names
            copy1_field = base_pdf_field
            copy2_field = base_pdf_field.replace("Copy1[0]", "Copy2[0]")
            copyb_field = base_pdf_field.replace("Copy1[0]", "CopyB[0]")
            
            # Get the values from mapped data
            copy1_value = mapped_data.get(copy1_field)
            copy2_value = mapped_data.get(copy2_field)
            copyb_value = mapped_data.get(copyb_field)
            
            # CRITICAL VERIFICATION: All three copies should have the same value
            assert copy1_value == expected_value, \
                f"Copy1 value should be '{expected_value}', got '{copy1_value}'"
            
            assert copy2_value == expected_value, \
                f"Copy2 value should be '{expected_value}', got '{copy2_value}'"
            
            assert copyb_value == expected_value, \
                f"CopyB value should be '{expected_value}', got '{copyb_value}'"
            
            # Verify all three are identical
            assert copy1_value == copy2_value == copyb_value, \
                f"All three copies should have identical values: " \
                f"Copy1='{copy1_value}', Copy2='{copy2_value}', CopyB='{copyb_value}'"
    
    @settings(max_examples=20)
    @given(api_field_name=valid_api_field_name_strategy())
    def test_single_field_generates_three_mappings(self, api_field_name):
        """
        **Validates: Requirements 1.1, 1.3**
        Feature: multi-page-form-filling, Property 2: Three-Copy Mapping Cardinality
        
        For any single API field name,
        the Field_Mapper should generate exactly three PDF field name mappings.
        
        This test verifies that:
        1. A single API field generates exactly 3 PDF fields
        2. The cardinality is consistent regardless of the field
        3. No extra or missing mappings are generated
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with a single field
        form_data = {api_field_name: "test_value"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # CRITICAL VERIFICATION: Should generate exactly 3 PDF fields
        assert len(mapped_data) == 3, \
            f"Single API field should generate 3 PDF fields, got {len(mapped_data)}"
    
    @settings(max_examples=20)
    @given(form_data=complete_form_data_strategy())
    def test_all_supported_fields_generate_three_copies(self, form_data):
        """
        **Validates: Requirements 1.1, 1.3**
        Feature: multi-page-form-filling, Property 2: Three-Copy Mapping Cardinality
        
        For all supported API field names,
        the Field_Mapper should generate exactly three PDF field name mappings
        for each field.
        
        This test verifies that:
        1. All supported fields generate 3 copies
        2. The total count is correct for all fields
        3. No fields are missing or duplicated
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Count the number of API fields
        num_api_fields = len(SUPPORTED_FIELDS)
        
        # CRITICAL VERIFICATION: Total PDF fields should be 3x the number of API fields
        expected_pdf_fields = num_api_fields * 3
        actual_pdf_fields = len(mapped_data)
        
        assert actual_pdf_fields == expected_pdf_fields, \
            f"Should generate {expected_pdf_fields} PDF fields (3 per API field), " \
            f"got {actual_pdf_fields}"
    
    @settings(max_examples=20)
    @given(form_data=form_data_strategy())
    def test_copy_prefixes_are_distinct(self, form_data):
        """
        **Validates: Requirements 1.1, 1.3**
        Feature: multi-page-form-filling, Property 2: Three-Copy Mapping Cardinality
        
        For any API field name in the form data,
        the three PDF field name mappings should have distinct copy prefixes
        (Copy1[0], Copy2[0], CopyB[0]).
        
        This test verifies that:
        1. Copy1 fields contain "Copy1[0]"
        2. Copy2 fields contain "Copy2[0]"
        3. CopyB fields contain "CopyB[0]"
        4. No mixing of copy prefixes occurs
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Count fields by copy prefix
        copy1_count = 0
        copy2_count = 0
        copyb_count = 0
        
        for pdf_field_name in mapped_data.keys():
            if "Copy1[0]" in pdf_field_name:
                copy1_count += 1
            elif "Copy2[0]" in pdf_field_name:
                copy2_count += 1
            elif "CopyB[0]" in pdf_field_name:
                copyb_count += 1
        
        # CRITICAL VERIFICATION: All three copy types should have equal counts
        num_api_fields = len(form_data)
        
        assert copy1_count == num_api_fields, \
            f"Should have {num_api_fields} Copy1 fields, got {copy1_count}"
        
        assert copy2_count == num_api_fields, \
            f"Should have {num_api_fields} Copy2 fields, got {copy2_count}"
        
        assert copyb_count == num_api_fields, \
            f"Should have {num_api_fields} CopyB fields, got {copyb_count}"
        
        # Verify the total matches
        total_copies = copy1_count + copy2_count + copyb_count
        assert total_copies == len(mapped_data), \
            f"Total copies ({total_copies}) should match mapped data count ({len(mapped_data)})"
    
    @settings(max_examples=20)
    @given(
        form_data=form_data_strategy(),
        extra_value=st.text(min_size=1, max_size=50)
    )
    def test_cardinality_independent_of_values(self, form_data, extra_value):
        """
        **Validates: Requirements 1.1, 1.3**
        Feature: multi-page-form-filling, Property 2: Three-Copy Mapping Cardinality
        
        For any API field name in the form data,
        the number of PDF field name mappings should be independent of the
        field values.
        
        This test verifies that:
        1. Cardinality depends only on field names, not values
        2. Different values don't change the number of mappings
        3. The 3x multiplier is consistent
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map with original values
        mapped_data1 = mapper.map_all_fields(form_data)
        
        # Create modified form data with different values
        modified_form_data = {k: extra_value for k in form_data.keys()}
        
        # Map with modified values
        mapped_data2 = mapper.map_all_fields(modified_form_data)
        
        # CRITICAL VERIFICATION: Both should have the same number of PDF fields
        assert len(mapped_data1) == len(mapped_data2), \
            f"Cardinality should be independent of values: " \
            f"{len(mapped_data1)} vs {len(mapped_data2)}"
        
        # Verify both have 3x the number of API fields
        expected_count = len(form_data) * 3
        assert len(mapped_data1) == expected_count, \
            f"Should have {expected_count} PDF fields, got {len(mapped_data1)}"
        
        assert len(mapped_data2) == expected_count, \
            f"Should have {expected_count} PDF fields, got {len(mapped_data2)}"
    
    @settings(max_examples=20)
    @given(form_data=form_data_strategy())
    def test_no_duplicate_pdf_field_names(self, form_data):
        """
        **Validates: Requirements 1.1, 1.3**
        Feature: multi-page-form-filling, Property 2: Three-Copy Mapping Cardinality
        
        For any form data,
        the Field_Mapper should not generate duplicate PDF field names.
        
        This test verifies that:
        1. All PDF field names are unique
        2. No field is mapped multiple times
        3. The mapping is one-to-one for each copy
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all PDF field names
        pdf_field_names = list(mapped_data.keys())
        
        # CRITICAL VERIFICATION: All PDF field names should be unique
        unique_pdf_field_names = set(pdf_field_names)
        
        assert len(pdf_field_names) == len(unique_pdf_field_names), \
            f"All PDF field names should be unique: " \
            f"{len(pdf_field_names)} total, {len(unique_pdf_field_names)} unique"
    
    @settings(max_examples=20)
    @given(form_data=form_data_strategy())
    def test_empty_form_data_returns_empty_mapping(self, form_data):
        """
        **Validates: Requirements 1.1, 1.3**
        Feature: multi-page-form-filling, Property 2: Three-Copy Mapping Cardinality
        
        For empty form data,
        the Field_Mapper should return an empty mapping.
        
        This test verifies that:
        1. Empty input produces empty output
        2. No spurious mappings are generated
        3. The 3x multiplier applies to zero fields
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map empty form data
        mapped_data = mapper.map_all_fields({})
        
        # CRITICAL VERIFICATION: Empty form data should produce empty mapping
        assert len(mapped_data) == 0, \
            f"Empty form data should produce empty mapping, got {len(mapped_data)} fields"
        
        assert mapped_data == {}, \
            f"Empty form data should produce empty dict, got {mapped_data}"
