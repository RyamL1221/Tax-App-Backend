"""
Property-based tests for calendar year value consistency across all copies in FieldMapper.

These tests verify that all four calendar year PDF fields (CopyA, Copy1, Copy2, CopyB)
contain the same value when populated, ensuring data consistency across all form copies.

Feature: fix-calendar-year-multi-copy
Property 2: Value Consistency Across Copies

**Validates: Requirements 1.5**
"""

import pytest
from hypothesis import given, settings, strategies as st
from tax_document_generation.field_mapper import FieldMapper


# Strategy for generating valid calendar year values
def calendar_year_strategy():
    """
    Generate valid calendar year values.
    
    Returns years from 1900 to 2099 as strings.
    """
    return st.integers(min_value=1900, max_value=2099).map(str)


# Strategy for generating form data with calendar year
@st.composite
def form_data_with_calendar_year_strategy(draw):
    """
    Generate form data dictionaries with a calendar year field.
    
    Returns a dictionary with 'calendarYear' as a key and a random
    year value.
    """
    calendar_year = draw(calendar_year_strategy())
    
    # Optionally add other fields
    num_extra_fields = draw(st.integers(min_value=0, max_value=5))
    
    form_data = {"calendarYear": calendar_year}
    
    # Add some random extra fields for realism
    extra_field_names = [
        "payerName", "payerTIN", "recipientName", "recipientTIN",
        "totalOrdinaryDividends", "qualifiedDividends"
    ]
    
    for i in range(num_extra_fields):
        if i < len(extra_field_names):
            field_name = extra_field_names[i]
            field_value = draw(st.text(min_size=1, max_size=50))
            form_data[field_name] = field_value
    
    return form_data


class TestCalendarYearValueConsistencyProperty:
    """Property-based tests for calendar year value consistency across all copies."""
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_all_four_calendar_year_fields_have_same_value(self, calendar_year):
        """
        **Validates: Requirements 1.5**
        Feature: fix-calendar-year-multi-copy, Property 2: Value Consistency Across Copies
        
        For any calendar year value,
        all four calendar year PDF fields should contain the same value.
        
        This test verifies that:
        1. CopyA calendar year field has the correct value
        2. Copy1 calendar year field has the correct value
        3. Copy2 calendar year field has the correct value
        4. CopyB calendar year field has the correct value
        5. All four values are identical
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": calendar_year}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # Should have exactly 4 calendar year fields
        assert len(calendar_year_fields) == 4, \
            f"Should have exactly 4 calendar year fields, found {len(calendar_year_fields)}"
        
        # Get values for all four fields
        calendar_year_values = [mapped_data[field] for field in calendar_year_fields]
        
        # CRITICAL VERIFICATION: All values should be identical
        unique_values = set(calendar_year_values)
        
        assert len(unique_values) == 1, \
            f"All calendar year fields should have the same value. " \
            f"Found {len(unique_values)} unique values: {unique_values}"
        
        # Verify the value matches the input
        assert calendar_year in unique_values, \
            f"Calendar year value should be '{calendar_year}', found: {unique_values}"
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_calendar_year_strategy())
    def test_copya_copy1_copy2_copyb_values_are_identical(self, form_data):
        """
        **Validates: Requirements 1.5**
        Feature: fix-calendar-year-multi-copy, Property 2: Value Consistency Across Copies
        
        For any form data containing a calendar year,
        the values in CopyA, Copy1, Copy2, and CopyB should be identical.
        
        This test verifies that:
        1. CopyA value equals Copy1 value
        2. Copy1 value equals Copy2 value
        3. Copy2 value equals CopyB value
        4. All four values are the same
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get the base PDF field name (Copy1 version)
        base_pdf_field = mapper.map_field("calendarYear")
        
        # Generate expected field names for all four copies
        copya_field = base_pdf_field.replace("Copy1[0]", "CopyA[0]").replace("f2_", "f1_")
        copy1_field = base_pdf_field
        copy2_field = base_pdf_field.replace("Copy1[0]", "Copy2[0]")
        copyb_field = base_pdf_field.replace("Copy1[0]", "CopyB[0]")
        
        # Get values for each copy
        copya_value = mapped_data.get(copya_field)
        copy1_value = mapped_data.get(copy1_field)
        copy2_value = mapped_data.get(copy2_field)
        copyb_value = mapped_data.get(copyb_field)
        
        # All values should exist
        assert copya_value is not None, "CopyA calendar year value should exist"
        assert copy1_value is not None, "Copy1 calendar year value should exist"
        assert copy2_value is not None, "Copy2 calendar year value should exist"
        assert copyb_value is not None, "CopyB calendar year value should exist"
        
        # CRITICAL VERIFICATION: All values should be identical
        assert copya_value == copy1_value, \
            f"CopyA value '{copya_value}' should equal Copy1 value '{copy1_value}'"
        
        assert copy1_value == copy2_value, \
            f"Copy1 value '{copy1_value}' should equal Copy2 value '{copy2_value}'"
        
        assert copy2_value == copyb_value, \
            f"Copy2 value '{copy2_value}' should equal CopyB value '{copyb_value}'"
        
        # Verify the value matches the input
        expected_value = form_data["calendarYear"]
        assert copya_value == expected_value, \
            f"All calendar year values should be '{expected_value}', CopyA has '{copya_value}'"
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_calendar_year_value_matches_input(self, calendar_year):
        """
        **Validates: Requirements 1.5**
        Feature: fix-calendar-year-multi-copy, Property 2: Value Consistency Across Copies
        
        For any calendar year value,
        all four PDF fields should contain the exact value from the input.
        
        This test verifies that:
        1. The input calendar year value is preserved
        2. No transformation or modification occurs
        3. All four fields contain the original input value
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": calendar_year}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # CRITICAL VERIFICATION: All fields should have the input value
        for field in calendar_year_fields:
            field_value = mapped_data[field]
            assert field_value == calendar_year, \
                f"Field '{field}' should have value '{calendar_year}', found '{field_value}'"
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_calendar_year_strategy())
    def test_no_value_transformation_occurs(self, form_data):
        """
        **Validates: Requirements 1.5**
        Feature: fix-calendar-year-multi-copy, Property 2: Value Consistency Across Copies
        
        For any form data containing a calendar year,
        the calendar year value should not be transformed or modified.
        
        This test verifies that:
        1. The value is copied exactly as provided
        2. No formatting or conversion occurs
        3. The value type is preserved (string)
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get the input calendar year
        input_calendar_year = form_data["calendarYear"]
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # CRITICAL VERIFICATION: All fields should have the exact input value
        for field in calendar_year_fields:
            field_value = mapped_data[field]
            
            # Value should be identical (no transformation)
            assert field_value == input_calendar_year, \
                f"Field '{field}' value should be identical to input"
            
            # Type should be preserved
            assert type(field_value) == type(input_calendar_year), \
                f"Field '{field}' type should be {type(input_calendar_year)}, " \
                f"found {type(field_value)}"
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_calendar_year_consistency_with_specific_field_names(self, calendar_year):
        """
        **Validates: Requirements 1.5**
        Feature: fix-calendar-year-multi-copy, Property 2: Value Consistency Across Copies
        
        For any calendar year value,
        the specific PDF field names should all contain the same value.
        
        This test verifies that:
        1. The exact CopyA field has the correct value
        2. The exact Copy1 field has the correct value
        3. The exact Copy2 field has the correct value
        4. The exact CopyB field has the correct value
        5. All values are identical
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": calendar_year}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Expected field names based on the canonical mapping
        expected_copya = "topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]"
        expected_copy1 = "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copy2 = "topmostSubform[0].Copy2[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copyb = "topmostSubform[0].CopyB[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        
        # Get values for each specific field
        copya_value = mapped_data.get(expected_copya)
        copy1_value = mapped_data.get(expected_copy1)
        copy2_value = mapped_data.get(expected_copy2)
        copyb_value = mapped_data.get(expected_copyb)
        
        # All values should exist
        assert copya_value is not None, \
            f"CopyA field '{expected_copya}' should exist in mapped data"
        assert copy1_value is not None, \
            f"Copy1 field '{expected_copy1}' should exist in mapped data"
        assert copy2_value is not None, \
            f"Copy2 field '{expected_copy2}' should exist in mapped data"
        assert copyb_value is not None, \
            f"CopyB field '{expected_copyb}' should exist in mapped data"
        
        # CRITICAL VERIFICATION: All values should be identical and match input
        assert copya_value == calendar_year, \
            f"CopyA value should be '{calendar_year}', found '{copya_value}'"
        
        assert copy1_value == calendar_year, \
            f"Copy1 value should be '{calendar_year}', found '{copy1_value}'"
        
        assert copy2_value == calendar_year, \
            f"Copy2 value should be '{calendar_year}', found '{copy2_value}'"
        
        assert copyb_value == calendar_year, \
            f"CopyB value should be '{calendar_year}', found '{copyb_value}'"
        
        # Verify all are identical
        assert copya_value == copy1_value == copy2_value == copyb_value, \
            f"All calendar year values should be identical: " \
            f"CopyA={copya_value}, Copy1={copy1_value}, " \
            f"Copy2={copy2_value}, CopyB={copyb_value}"
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_calendar_year_strategy())
    def test_value_consistency_independent_of_other_fields(self, form_data):
        """
        **Validates: Requirements 1.5**
        Feature: fix-calendar-year-multi-copy, Property 2: Value Consistency Across Copies
        
        For any form data containing a calendar year and other fields,
        the calendar year value consistency should be independent of other fields.
        
        This test verifies that:
        1. Calendar year values are consistent regardless of other fields
        2. Other fields don't affect calendar year mapping
        3. Value consistency holds with varying form data
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get the input calendar year
        input_calendar_year = form_data["calendarYear"]
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # Get all calendar year values
        calendar_year_values = [mapped_data[field] for field in calendar_year_fields]
        
        # CRITICAL VERIFICATION: All values should be identical
        unique_values = set(calendar_year_values)
        
        assert len(unique_values) == 1, \
            f"All calendar year fields should have the same value, " \
            f"regardless of other fields. Found {len(unique_values)} unique values: {unique_values}"
        
        # Verify the value matches the input
        assert input_calendar_year in unique_values, \
            f"Calendar year value should be '{input_calendar_year}', found: {unique_values}"
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_calendar_year_value_not_duplicated_or_modified(self, calendar_year):
        """
        **Validates: Requirements 1.5**
        Feature: fix-calendar-year-multi-copy, Property 2: Value Consistency Across Copies
        
        For any calendar year value,
        the value should be replicated exactly across all copies without modification.
        
        This test verifies that:
        1. The value is not duplicated (e.g., "20242024")
        2. The value is not modified (e.g., "2024" -> "24")
        3. The value is not formatted (e.g., "2024" -> "2,024")
        4. The value is exactly as provided
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": calendar_year}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # CRITICAL VERIFICATION: All fields should have the exact input value
        for field in calendar_year_fields:
            field_value = mapped_data[field]
            
            # Value should be exactly the input (no duplication)
            assert field_value == calendar_year, \
                f"Field '{field}' should have exact value '{calendar_year}', found '{field_value}'"
            
            # Value should not be duplicated
            assert field_value != calendar_year + calendar_year, \
                f"Field '{field}' should not have duplicated value"
            
            # Value length should match input length
            assert len(field_value) == len(calendar_year), \
                f"Field '{field}' value length should be {len(calendar_year)}, " \
                f"found {len(field_value)}"
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_all_copies_have_non_empty_calendar_year_values(self, calendar_year):
        """
        **Validates: Requirements 1.5**
        Feature: fix-calendar-year-multi-copy, Property 2: Value Consistency Across Copies
        
        For any calendar year value,
        all four calendar year PDF fields should have non-empty values.
        
        This test verifies that:
        1. CopyA value is not empty
        2. Copy1 value is not empty
        3. Copy2 value is not empty
        4. CopyB value is not empty
        5. All values are the same non-empty value
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": calendar_year}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # CRITICAL VERIFICATION: All fields should have non-empty values
        for field in calendar_year_fields:
            field_value = mapped_data[field]
            
            # Value should not be None
            assert field_value is not None, \
                f"Field '{field}' should not have None value"
            
            # Value should not be empty string
            assert field_value != "", \
                f"Field '{field}' should not have empty string value"
            
            # Value should match the input
            assert field_value == calendar_year, \
                f"Field '{field}' should have value '{calendar_year}', found '{field_value}'"
