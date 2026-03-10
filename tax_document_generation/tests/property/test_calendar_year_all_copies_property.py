"""
Property-based tests for calendar year population across all copies in FieldMapper.

These tests verify that the calendar year field is populated in all four copies
(CopyA, Copy1, Copy2, CopyB) of the 1099-DIV form, ensuring compliance with
IRS requirements.

Feature: fix-calendar-year-multi-copy
Property 1: Calendar Year Population Across All Copies

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**
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


class TestCalendarYearAllCopiesProperty:
    """Property-based tests for calendar year population across all copies."""
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_calendar_year_generates_four_pdf_field_names(self, calendar_year):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        Feature: fix-calendar-year-multi-copy, Property 1: Calendar Year Population Across All Copies
        
        For any calendar year value,
        the Field_Mapper should generate exactly four PDF field name mappings
        (one for CopyA, Copy1, Copy2, and CopyB).
        
        This test verifies that:
        1. CopyA calendar year field is in the mapped output
        2. Copy1 calendar year field is in the mapped output
        3. Copy2 calendar year field is in the mapped output
        4. CopyB calendar year field is in the mapped output
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": calendar_year}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get the base PDF field name (Copy1 version)
        base_pdf_field = mapper.map_field("calendarYear")
        
        assert base_pdf_field is not None, \
            "calendarYear field should have a mapping"
        
        # Generate expected CopyA, Copy1, Copy2, and CopyB field names
        # Base: topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]
        copy1_field = base_pdf_field
        copy2_field = base_pdf_field.replace("Copy1[0]", "Copy2[0]")
        copyb_field = base_pdf_field.replace("Copy1[0]", "CopyB[0]")
        copya_field = base_pdf_field.replace("Copy1[0]", "CopyA[0]").replace("f2_", "f1_")
        
        # CRITICAL VERIFICATION: All four calendar year fields should exist in mapped data
        assert copya_field in mapped_data, \
            f"CopyA calendar year field '{copya_field}' should exist in mapped data"
        
        assert copy1_field in mapped_data, \
            f"Copy1 calendar year field '{copy1_field}' should exist in mapped data"
        
        assert copy2_field in mapped_data, \
            f"Copy2 calendar year field '{copy2_field}' should exist in mapped data"
        
        assert copyb_field in mapped_data, \
            f"CopyB calendar year field '{copyb_field}' should exist in mapped data"
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_calendar_year_strategy())
    def test_all_four_calendar_year_fields_present(self, form_data):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        Feature: fix-calendar-year-multi-copy, Property 1: Calendar Year Population Across All Copies
        
        For any form data containing a calendar year,
        the Field_Mapper should generate mappings for all four copies.
        
        This test verifies that:
        1. All four PDF field names are present in the mapped output
        2. The mapping includes CopyA, Copy1, Copy2, and CopyB
        3. No copies are missing
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get the base PDF field name (Copy1 version)
        base_pdf_field = mapper.map_field("calendarYear")
        
        # Generate expected field names for all four copies
        expected_fields = [
            base_pdf_field.replace("Copy1[0]", "CopyA[0]").replace("f2_", "f1_"),  # CopyA
            base_pdf_field,  # Copy1
            base_pdf_field.replace("Copy1[0]", "Copy2[0]"),  # Copy2
            base_pdf_field.replace("Copy1[0]", "CopyB[0]"),  # CopyB
        ]
        
        # CRITICAL VERIFICATION: All four expected fields should be in mapped data
        for expected_field in expected_fields:
            assert expected_field in mapped_data, \
                f"Expected calendar year field '{expected_field}' not found in mapped data"
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_copya_field_name_has_correct_pattern(self, calendar_year):
        """
        **Validates: Requirements 1.1**
        Feature: fix-calendar-year-multi-copy, Property 1: Calendar Year Population Across All Copies
        
        For any calendar year value,
        the CopyA field name should follow the correct pattern with CopyA[0] and f1_ prefix.
        
        This test verifies that:
        1. CopyA field contains "CopyA[0]" in the path
        2. CopyA field uses "f1_" prefix (not "f2_")
        3. The field name structure is correct
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": calendar_year}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Find the CopyA field in mapped data
        copya_fields = [field for field in mapped_data.keys() if "CopyA[0]" in field]
        
        # CRITICAL VERIFICATION: Should have exactly one CopyA calendar year field
        assert len(copya_fields) == 1, \
            f"Should have exactly 1 CopyA calendar year field, found {len(copya_fields)}"
        
        copya_field = copya_fields[0]
        
        # Verify CopyA field structure
        assert "CopyA[0]" in copya_field, \
            f"CopyA field should contain 'CopyA[0]': {copya_field}"
        
        assert "f1_" in copya_field, \
            f"CopyA field should use 'f1_' prefix: {copya_field}"
        
        assert "CalendarYear[0]" in copya_field, \
            f"CopyA field should contain 'CalendarYear[0]': {copya_field}"
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_copy1_copy2_copyb_fields_have_correct_pattern(self, calendar_year):
        """
        **Validates: Requirements 1.2, 1.3, 1.4**
        Feature: fix-calendar-year-multi-copy, Property 1: Calendar Year Population Across All Copies
        
        For any calendar year value,
        the Copy1, Copy2, and CopyB field names should follow the correct pattern with f2_ prefix.
        
        This test verifies that:
        1. Copy1 field contains "Copy1[0]" and "f2_"
        2. Copy2 field contains "Copy2[0]" and "f2_"
        3. CopyB field contains "CopyB[0]" and "f2_"
        4. All three use the same field name pattern
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": calendar_year}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Find Copy1, Copy2, and CopyB fields
        copy1_fields = [field for field in mapped_data.keys() if "Copy1[0]" in field]
        copy2_fields = [field for field in mapped_data.keys() if "Copy2[0]" in field]
        copyb_fields = [field for field in mapped_data.keys() if "CopyB[0]" in field]
        
        # CRITICAL VERIFICATION: Should have exactly one of each
        assert len(copy1_fields) == 1, \
            f"Should have exactly 1 Copy1 calendar year field, found {len(copy1_fields)}"
        
        assert len(copy2_fields) == 1, \
            f"Should have exactly 1 Copy2 calendar year field, found {len(copy2_fields)}"
        
        assert len(copyb_fields) == 1, \
            f"Should have exactly 1 CopyB calendar year field, found {len(copyb_fields)}"
        
        copy1_field = copy1_fields[0]
        copy2_field = copy2_fields[0]
        copyb_field = copyb_fields[0]
        
        # Verify Copy1 field structure
        assert "Copy1[0]" in copy1_field, \
            f"Copy1 field should contain 'Copy1[0]': {copy1_field}"
        
        assert "f2_" in copy1_field, \
            f"Copy1 field should use 'f2_' prefix: {copy1_field}"
        
        # Verify Copy2 field structure
        assert "Copy2[0]" in copy2_field, \
            f"Copy2 field should contain 'Copy2[0]': {copy2_field}"
        
        assert "f2_" in copy2_field, \
            f"Copy2 field should use 'f2_' prefix: {copy2_field}"
        
        # Verify CopyB field structure
        assert "CopyB[0]" in copyb_field, \
            f"CopyB field should contain 'CopyB[0]': {copyb_field}"
        
        assert "f2_" in copyb_field, \
            f"CopyB field should use 'f2_' prefix: {copyb_field}"
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_calendar_year_strategy())
    def test_calendar_year_field_count_is_four(self, form_data):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        Feature: fix-calendar-year-multi-copy, Property 1: Calendar Year Population Across All Copies
        
        For any form data containing a calendar year,
        the Field_Mapper should generate exactly four calendar year PDF fields.
        
        This test verifies that:
        1. Exactly 4 calendar year fields are generated
        2. No extra or missing calendar year fields
        3. The count is consistent across all inputs
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Count calendar year fields (fields containing "CalendarYear[0]")
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # CRITICAL VERIFICATION: Should have exactly 4 calendar year fields
        assert len(calendar_year_fields) == 4, \
            f"Should have exactly 4 calendar year fields, found {len(calendar_year_fields)}: " \
            f"{calendar_year_fields}"
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_all_four_copies_have_distinct_field_names(self, calendar_year):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        Feature: fix-calendar-year-multi-copy, Property 1: Calendar Year Population Across All Copies
        
        For any calendar year value,
        all four calendar year PDF field names should be distinct.
        
        This test verifies that:
        1. CopyA, Copy1, Copy2, and CopyB have different field names
        2. No duplicate field names are generated
        3. Each copy has a unique field identifier
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
        
        # CRITICAL VERIFICATION: All field names should be unique
        unique_fields = set(calendar_year_fields)
        
        assert len(calendar_year_fields) == len(unique_fields), \
            f"All calendar year field names should be unique: " \
            f"{len(calendar_year_fields)} total, {len(unique_fields)} unique"
        
        # Verify we have exactly 4 unique fields
        assert len(unique_fields) == 4, \
            f"Should have exactly 4 unique calendar year fields, found {len(unique_fields)}"
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_calendar_year_strategy())
    def test_calendar_year_mapping_includes_all_copy_prefixes(self, form_data):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        Feature: fix-calendar-year-multi-copy, Property 1: Calendar Year Population Across All Copies
        
        For any form data containing a calendar year,
        the mapped output should include fields with all four copy prefixes.
        
        This test verifies that:
        1. At least one field contains "CopyA[0]"
        2. At least one field contains "Copy1[0]"
        3. At least one field contains "Copy2[0]"
        4. At least one field contains "CopyB[0]"
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # Check for each copy prefix
        has_copya = any("CopyA[0]" in field for field in calendar_year_fields)
        has_copy1 = any("Copy1[0]" in field for field in calendar_year_fields)
        has_copy2 = any("Copy2[0]" in field for field in calendar_year_fields)
        has_copyb = any("CopyB[0]" in field for field in calendar_year_fields)
        
        # CRITICAL VERIFICATION: All four copy prefixes should be present
        assert has_copya, \
            "Calendar year mapping should include CopyA[0] field"
        
        assert has_copy1, \
            "Calendar year mapping should include Copy1[0] field"
        
        assert has_copy2, \
            "Calendar year mapping should include Copy2[0] field"
        
        assert has_copyb, \
            "Calendar year mapping should include CopyB[0] field"
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_calendar_year_field_names_match_expected_structure(self, calendar_year):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        Feature: fix-calendar-year-multi-copy, Property 1: Calendar Year Population Across All Copies
        
        For any calendar year value,
        the generated PDF field names should match the expected structure.
        
        This test verifies that:
        1. CopyA field matches expected pattern
        2. Copy1 field matches expected pattern
        3. Copy2 field matches expected pattern
        4. CopyB field matches expected pattern
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
        
        # CRITICAL VERIFICATION: All expected field names should be in mapped data
        assert expected_copya in mapped_data, \
            f"Expected CopyA field '{expected_copya}' not found in mapped data"
        
        assert expected_copy1 in mapped_data, \
            f"Expected Copy1 field '{expected_copy1}' not found in mapped data"
        
        assert expected_copy2 in mapped_data, \
            f"Expected Copy2 field '{expected_copy2}' not found in mapped data"
        
        assert expected_copyb in mapped_data, \
            f"Expected CopyB field '{expected_copyb}' not found in mapped data"
