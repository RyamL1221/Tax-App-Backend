"""
Unit tests for calendar year field mapping in FieldMapper.

These tests verify specific calendar year values and edge cases to ensure
the calendar year field is correctly mapped to all four copies (CopyA, Copy1,
Copy2, CopyB) of the 1099-DIV form.

Feature: fix-calendar-year-multi-copy

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
"""

import pytest
from tax_document_generation.field_mapper import FieldMapper


class TestCalendarYearMappingUnit:
    """Unit tests for calendar year field mapping with specific values."""
    
    def test_calendar_year_2024_maps_to_all_copies(self):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
        
        Test that calendar year "2024" is correctly mapped to all four copies.
        
        This test verifies that:
        1. CopyA calendar year field exists and has value "2024"
        2. Copy1 calendar year field exists and has value "2024"
        3. Copy2 calendar year field exists and has value "2024"
        4. CopyB calendar year field exists and has value "2024"
        5. All four values are identical
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year 2024
        form_data = {"calendarYear": "2024"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Expected field names based on the canonical mapping
        expected_copya = "topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]"
        expected_copy1 = "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copy2 = "topmostSubform[0].Copy2[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copyb = "topmostSubform[0].CopyB[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        
        # Verify all four fields exist in mapped data
        assert expected_copya in mapped_data, \
            f"CopyA calendar year field should exist in mapped data"
        
        assert expected_copy1 in mapped_data, \
            f"Copy1 calendar year field should exist in mapped data"
        
        assert expected_copy2 in mapped_data, \
            f"Copy2 calendar year field should exist in mapped data"
        
        assert expected_copyb in mapped_data, \
            f"CopyB calendar year field should exist in mapped data"
        
        # Verify all four fields have the correct value
        assert mapped_data[expected_copya] == "2024", \
            f"CopyA calendar year should be '2024', found '{mapped_data[expected_copya]}'"
        
        assert mapped_data[expected_copy1] == "2024", \
            f"Copy1 calendar year should be '2024', found '{mapped_data[expected_copy1]}'"
        
        assert mapped_data[expected_copy2] == "2024", \
            f"Copy2 calendar year should be '2024', found '{mapped_data[expected_copy2]}'"
        
        assert mapped_data[expected_copyb] == "2024", \
            f"CopyB calendar year should be '2024', found '{mapped_data[expected_copyb]}'"
    
    def test_calendar_year_2023_maps_to_all_copies(self):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
        
        Test that calendar year "2023" is correctly mapped to all four copies.
        
        This test verifies that:
        1. All four calendar year fields exist
        2. All four fields have value "2023"
        3. Values are consistent across all copies
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year 2023
        form_data = {"calendarYear": "2023"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Expected field names
        expected_copya = "topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]"
        expected_copy1 = "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copy2 = "topmostSubform[0].Copy2[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copyb = "topmostSubform[0].CopyB[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        
        # Verify all fields have the correct value
        assert mapped_data[expected_copya] == "2023"
        assert mapped_data[expected_copy1] == "2023"
        assert mapped_data[expected_copy2] == "2023"
        assert mapped_data[expected_copyb] == "2023"
    
    def test_calendar_year_2022_maps_to_all_copies(self):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
        
        Test that calendar year "2022" is correctly mapped to all four copies.
        
        This test verifies that:
        1. All four calendar year fields exist
        2. All four fields have value "2022"
        3. Values are consistent across all copies
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year 2022
        form_data = {"calendarYear": "2022"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Expected field names
        expected_copya = "topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]"
        expected_copy1 = "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copy2 = "topmostSubform[0].Copy2[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copyb = "topmostSubform[0].CopyB[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        
        # Verify all fields have the correct value
        assert mapped_data[expected_copya] == "2022"
        assert mapped_data[expected_copy1] == "2022"
        assert mapped_data[expected_copy2] == "2022"
        assert mapped_data[expected_copyb] == "2022"
    
    def test_calendar_year_1900_boundary_maps_to_all_copies(self):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
        
        Test that boundary year "1900" is correctly mapped to all four copies.
        
        This test verifies that:
        1. All four calendar year fields exist
        2. All four fields have value "1900"
        3. Boundary values are handled correctly
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with boundary year 1900
        form_data = {"calendarYear": "1900"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Expected field names
        expected_copya = "topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]"
        expected_copy1 = "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copy2 = "topmostSubform[0].Copy2[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copyb = "topmostSubform[0].CopyB[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        
        # Verify all fields have the correct value
        assert mapped_data[expected_copya] == "1900"
        assert mapped_data[expected_copy1] == "1900"
        assert mapped_data[expected_copy2] == "1900"
        assert mapped_data[expected_copyb] == "1900"
    
    def test_calendar_year_2099_boundary_maps_to_all_copies(self):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
        
        Test that boundary year "2099" is correctly mapped to all four copies.
        
        This test verifies that:
        1. All four calendar year fields exist
        2. All four fields have value "2099"
        3. Upper boundary values are handled correctly
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with boundary year 2099
        form_data = {"calendarYear": "2099"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Expected field names
        expected_copya = "topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]"
        expected_copy1 = "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copy2 = "topmostSubform[0].Copy2[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        expected_copyb = "topmostSubform[0].CopyB[0].CopyHeader[0].CalendarYear[0].f2_1[0]"
        
        # Verify all fields have the correct value
        assert mapped_data[expected_copya] == "2099"
        assert mapped_data[expected_copy1] == "2099"
        assert mapped_data[expected_copy2] == "2099"
        assert mapped_data[expected_copyb] == "2099"
    
    def test_calendar_year_field_names_match_actual_pdf_fields(self):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        
        Test that generated field names match the actual PDF field names.
        
        This test verifies that:
        1. CopyA field name matches expected structure
        2. Copy1 field name matches expected structure
        3. Copy2 field name matches expected structure
        4. CopyB field name matches expected structure
        5. Field names follow the correct pattern
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": "2024"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # Expected field names based on actual PDF structure
        expected_fields = [
            "topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]",
            "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]",
            "topmostSubform[0].Copy2[0].CopyHeader[0].CalendarYear[0].f2_1[0]",
            "topmostSubform[0].CopyB[0].CopyHeader[0].CalendarYear[0].f2_1[0]",
        ]
        
        # Verify all expected fields are present
        for expected_field in expected_fields:
            assert expected_field in calendar_year_fields, \
                f"Expected field '{expected_field}' not found in calendar year fields"
        
        # Verify no extra fields
        assert len(calendar_year_fields) == len(expected_fields), \
            f"Should have exactly {len(expected_fields)} calendar year fields, " \
            f"found {len(calendar_year_fields)}"
    
    def test_all_four_copies_are_generated(self):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        
        Test that all four copies (CopyA, Copy1, Copy2, CopyB) are generated.
        
        This test verifies that:
        1. Exactly 4 calendar year fields are generated
        2. CopyA is present
        3. Copy1 is present
        4. Copy2 is present
        5. CopyB is present
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": "2024"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # Verify exactly 4 fields
        assert len(calendar_year_fields) == 4, \
            f"Should have exactly 4 calendar year fields, found {len(calendar_year_fields)}"
        
        # Verify each copy is present
        has_copya = any("CopyA[0]" in field for field in calendar_year_fields)
        has_copy1 = any("Copy1[0]" in field for field in calendar_year_fields)
        has_copy2 = any("Copy2[0]" in field for field in calendar_year_fields)
        has_copyb = any("CopyB[0]" in field for field in calendar_year_fields)
        
        assert has_copya, "CopyA calendar year field should be present"
        assert has_copy1, "Copy1 calendar year field should be present"
        assert has_copy2, "Copy2 calendar year field should be present"
        assert has_copyb, "CopyB calendar year field should be present"
    
    def test_copya_uses_f1_prefix(self):
        """
        **Validates: Requirements 1.1**
        
        Test that CopyA calendar year field uses the f1_ prefix.
        
        This test verifies that:
        1. CopyA field contains "f1_" in the field name
        2. CopyA field does not contain "f2_" in the field name
        3. CopyA follows the correct naming pattern
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": "2024"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Find CopyA field
        copya_fields = [
            field for field in mapped_data.keys()
            if "CopyA[0]" in field and "CalendarYear[0]" in field
        ]
        
        # Should have exactly one CopyA field
        assert len(copya_fields) == 1, \
            f"Should have exactly 1 CopyA calendar year field, found {len(copya_fields)}"
        
        copya_field = copya_fields[0]
        
        # Verify CopyA uses f1_ prefix
        assert "f1_" in copya_field, \
            f"CopyA field should use 'f1_' prefix: {copya_field}"
        
        # Verify CopyA does not use f2_ prefix
        assert "f2_" not in copya_field, \
            f"CopyA field should not use 'f2_' prefix: {copya_field}"
    
    def test_copy1_copy2_copyb_use_f2_prefix(self):
        """
        **Validates: Requirements 1.2, 1.3, 1.4**
        
        Test that Copy1, Copy2, and CopyB calendar year fields use the f2_ prefix.
        
        This test verifies that:
        1. Copy1 field contains "f2_" in the field name
        2. Copy2 field contains "f2_" in the field name
        3. CopyB field contains "f2_" in the field name
        4. All three follow the same naming pattern
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": "2024"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Find Copy1, Copy2, and CopyB fields
        copy1_fields = [
            field for field in mapped_data.keys()
            if "Copy1[0]" in field and "CalendarYear[0]" in field
        ]
        copy2_fields = [
            field for field in mapped_data.keys()
            if "Copy2[0]" in field and "CalendarYear[0]" in field
        ]
        copyb_fields = [
            field for field in mapped_data.keys()
            if "CopyB[0]" in field and "CalendarYear[0]" in field
        ]
        
        # Should have exactly one of each
        assert len(copy1_fields) == 1
        assert len(copy2_fields) == 1
        assert len(copyb_fields) == 1
        
        copy1_field = copy1_fields[0]
        copy2_field = copy2_fields[0]
        copyb_field = copyb_fields[0]
        
        # Verify all use f2_ prefix
        assert "f2_" in copy1_field, \
            f"Copy1 field should use 'f2_' prefix: {copy1_field}"
        
        assert "f2_" in copy2_field, \
            f"Copy2 field should use 'f2_' prefix: {copy2_field}"
        
        assert "f2_" in copyb_field, \
            f"CopyB field should use 'f2_' prefix: {copyb_field}"
    
    def test_calendar_year_with_other_fields(self):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
        
        Test that calendar year mapping works correctly when other fields are present.
        
        This test verifies that:
        1. Calendar year is mapped correctly with other fields
        2. All four calendar year copies are generated
        3. Calendar year values are consistent
        4. Other fields don't interfere with calendar year mapping
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year and other fields
        form_data = {
            "calendarYear": "2024",
            "payerName": "Test Payer Corp",
            "recipientName": "John Doe",
            "totalOrdinaryDividends": "1000.00"
        }
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # Verify exactly 4 calendar year fields
        assert len(calendar_year_fields) == 4, \
            f"Should have exactly 4 calendar year fields, found {len(calendar_year_fields)}"
        
        # Verify all calendar year fields have the correct value
        for field in calendar_year_fields:
            assert mapped_data[field] == "2024", \
                f"Calendar year field '{field}' should have value '2024', " \
                f"found '{mapped_data[field]}'"
    
    def test_calendar_year_value_consistency_across_copies(self):
        """
        **Validates: Requirements 1.5**
        
        Test that calendar year value is consistent across all four copies.
        
        This test verifies that:
        1. All four calendar year fields have the same value
        2. No value transformation occurs
        3. Value consistency is maintained
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": "2024"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all calendar year field values
        calendar_year_values = [
            mapped_data[field] for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # Verify all values are identical
        unique_values = set(calendar_year_values)
        
        assert len(unique_values) == 1, \
            f"All calendar year fields should have the same value. " \
            f"Found {len(unique_values)} unique values: {unique_values}"
        
        # Verify the value matches the input
        assert "2024" in unique_values, \
            f"Calendar year value should be '2024', found: {unique_values}"
    
    def test_calendar_year_field_structure(self):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        
        Test that calendar year field names follow the correct structure.
        
        This test verifies that:
        1. All fields contain "topmostSubform[0]"
        2. All fields contain "CopyHeader[0]"
        3. All fields contain "CalendarYear[0]"
        4. Field structure is consistent
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": "2024"}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Get all calendar year field names
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # Verify structure of each field
        for field in calendar_year_fields:
            assert "topmostSubform[0]" in field, \
                f"Field should contain 'topmostSubform[0]': {field}"
            
            assert "CopyHeader[0]" in field, \
                f"Field should contain 'CopyHeader[0]': {field}"
            
            assert "CalendarYear[0]" in field, \
                f"Field should contain 'CalendarYear[0]': {field}"
            
            # Verify it has one of the expected copy prefixes
            has_copy_prefix = (
                "CopyA[0]" in field or
                "Copy1[0]" in field or
                "Copy2[0]" in field or
                "CopyB[0]" in field
            )
            
            assert has_copy_prefix, \
                f"Field should contain a copy prefix (CopyA, Copy1, Copy2, or CopyB): {field}"
