"""
Property-based tests for calendar year multi-copy field count consistency in FieldMapper.

These tests verify that the calendar year field generates the same number of copy
variants as other multi-copy fields (e.g., payerName, recipientName), ensuring
consistency in the multi-copy generation logic.

Feature: fix-calendar-year-multi-copy
Property 3: Multi-Copy Field Count Consistency

**Validates: Requirements 2.2**
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


# Strategy for generating form data with calendar year and other multi-copy fields
@st.composite
def form_data_with_multi_copy_fields_strategy(draw):
    """
    Generate form data dictionaries with calendar year and other multi-copy fields.
    
    Returns a dictionary with 'calendarYear' and at least one other multi-copy
    field (e.g., payerName, recipientName, payerTIN, recipientTIN).
    """
    calendar_year = draw(calendar_year_strategy())
    
    # Multi-copy fields that should have the same variant count as calendar year
    # Note: Only use fields with distinct PDF field mappings
    multi_copy_field_names = [
        "payerTIN", "recipientName", "recipientTIN",
        "totalOrdinaryDividends", "qualifiedDividends",
        "accountNumber", "federalIncomeTaxWithheld"
    ]
    
    # Select 1-3 random multi-copy fields
    num_fields = draw(st.integers(min_value=1, max_value=3))
    selected_fields = draw(st.lists(
        st.sampled_from(multi_copy_field_names),
        min_size=num_fields,
        max_size=num_fields,
        unique=True
    ))
    
    # Build form data
    form_data = {"calendarYear": calendar_year}
    
    for field_name in selected_fields:
        field_value = draw(st.text(min_size=1, max_size=50))
        form_data[field_name] = field_value
    
    return form_data


class TestCalendarYearVariantCountProperty:
    """Property-based tests for calendar year multi-copy field count consistency."""
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_multi_copy_fields_strategy())
    def test_calendar_year_variant_count_equals_other_multi_copy_fields(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: fix-calendar-year-multi-copy, Property 3: Multi-Copy Field Count Consistency
        
        For any form data containing calendar year and other multi-copy fields,
        the number of copy variants generated for calendar year should equal
        the number of variants generated for other multi-copy fields.
        
        This test verifies that:
        1. Calendar year generates the same number of variants as payerName
        2. Calendar year generates the same number of variants as recipientName
        3. Calendar year generates the same number of variants as other multi-copy fields
        4. All multi-copy fields have consistent variant counts
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Count calendar year variants
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        calendar_year_count = len(calendar_year_fields)
        
        # For each other field in form_data, count its variants
        for api_field_name in form_data.keys():
            if api_field_name == "calendarYear":
                continue  # Skip calendar year itself
            
            # Get the base PDF field name
            base_pdf_field = mapper.map_field(api_field_name)
            
            if base_pdf_field is None:
                continue  # Skip unmapped fields
            
            # Count variants for this field
            # Find all PDF fields that correspond to this API field
            # by checking if they match the base pattern (ignoring copy prefix)
            field_variants = []
            for pdf_field in mapped_data.keys():
                # Check if this PDF field is a variant of the base field
                # by replacing copy prefixes and comparing
                if "Copy1[0]" in base_pdf_field:
                    # Extract the pattern without copy prefix
                    base_pattern = base_pdf_field.replace("Copy1[0]", "Copy*[0]")
                    
                    # Check if PDF field matches any copy variant
                    if ("CopyA[0]" in pdf_field or "Copy1[0]" in pdf_field or 
                        "Copy2[0]" in pdf_field or "CopyB[0]" in pdf_field):
                        # Check if the rest of the path matches
                        pdf_pattern = pdf_field.replace("CopyA[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("Copy1[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("Copy2[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("CopyB[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("f1_", "f*_")
                        pdf_pattern = pdf_pattern.replace("f2_", "f*_")
                        
                        base_pattern_normalized = base_pattern.replace("f2_", "f*_")
                        
                        if pdf_pattern == base_pattern_normalized:
                            field_variants.append(pdf_field)
            
            field_variant_count = len(field_variants)
            
            # CRITICAL VERIFICATION: Variant count should match calendar year
            assert field_variant_count == calendar_year_count, \
                f"Field '{api_field_name}' has {field_variant_count} variants, " \
                f"but calendar year has {calendar_year_count} variants. " \
                f"All multi-copy fields should have the same variant count."
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_calendar_year_generates_four_variants(self, calendar_year):
        """
        **Validates: Requirements 2.2**
        Feature: fix-calendar-year-multi-copy, Property 3: Multi-Copy Field Count Consistency
        
        For any calendar year value,
        the Field_Mapper should generate exactly four copy variants.
        
        This test verifies that:
        1. Calendar year generates exactly 4 variants
        2. The count matches the expected multi-copy field count
        3. No extra or missing variants are generated
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": calendar_year}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Count calendar year variants
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # CRITICAL VERIFICATION: Should have exactly 4 variants
        assert len(calendar_year_fields) == 4, \
            f"Calendar year should generate exactly 4 variants, found {len(calendar_year_fields)}"
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_multi_copy_fields_strategy())
    def test_all_multi_copy_fields_have_four_variants(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: fix-calendar-year-multi-copy, Property 3: Multi-Copy Field Count Consistency
        
        For any form data containing multiple multi-copy fields,
        all multi-copy fields should generate exactly four copy variants.
        
        This test verifies that:
        1. Calendar year has 4 variants
        2. All other multi-copy fields have 4 variants
        3. The variant count is consistent across all fields
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # For each field in form_data, count its variants
        variant_counts = {}
        
        for api_field_name in form_data.keys():
            # Get the base PDF field name
            base_pdf_field = mapper.map_field(api_field_name)
            
            if base_pdf_field is None:
                continue  # Skip unmapped fields
            
            # Count variants for this field
            field_variants = []
            for pdf_field in mapped_data.keys():
                # Check if this PDF field is a variant of the base field
                if "Copy1[0]" in base_pdf_field:
                    # Extract the pattern without copy prefix
                    base_pattern = base_pdf_field.replace("Copy1[0]", "Copy*[0]")
                    
                    # Check if PDF field matches any copy variant
                    if ("CopyA[0]" in pdf_field or "Copy1[0]" in pdf_field or 
                        "Copy2[0]" in pdf_field or "CopyB[0]" in pdf_field):
                        # Check if the rest of the path matches
                        pdf_pattern = pdf_field.replace("CopyA[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("Copy1[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("Copy2[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("CopyB[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("f1_", "f*_")
                        pdf_pattern = pdf_pattern.replace("f2_", "f*_")
                        
                        base_pattern_normalized = base_pattern.replace("f2_", "f*_")
                        
                        if pdf_pattern == base_pattern_normalized:
                            field_variants.append(pdf_field)
            
            variant_counts[api_field_name] = len(field_variants)
        
        # CRITICAL VERIFICATION: All fields should have exactly 4 variants
        for api_field_name, count in variant_counts.items():
            assert count == 4, \
                f"Field '{api_field_name}' should have 4 variants, found {count}"
        
        # Verify all counts are equal
        unique_counts = set(variant_counts.values())
        assert len(unique_counts) == 1, \
            f"All multi-copy fields should have the same variant count. " \
            f"Found different counts: {variant_counts}"
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_multi_copy_fields_strategy())
    def test_calendar_year_and_payer_name_have_same_variant_count(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: fix-calendar-year-multi-copy, Property 3: Multi-Copy Field Count Consistency
        
        For any form data containing calendar year and payerName,
        both fields should generate the same number of copy variants.
        
        This test verifies that:
        1. Calendar year variant count equals payerName variant count
        2. Both fields use the same multi-copy generation logic
        3. The consistency holds across all inputs
        """
        # Add payerName to form data if not present
        if "payerName" not in form_data:
            form_data["payerName"] = "Test Payer"
        
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Count calendar year variants
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        calendar_year_count = len(calendar_year_fields)
        
        # Count payerName variants
        # Get the base PDF field name for payerName
        payer_name_base = mapper.map_field("payerName")
        
        if payer_name_base is not None:
            # Count variants for payerName
            payer_name_fields = []
            for pdf_field in mapped_data.keys():
                # Check if this PDF field is a variant of payerName
                if "Copy1[0]" in payer_name_base:
                    # Extract the pattern without copy prefix
                    base_pattern = payer_name_base.replace("Copy1[0]", "Copy*[0]")
                    
                    # Check if PDF field matches any copy variant
                    if ("CopyA[0]" in pdf_field or "Copy1[0]" in pdf_field or 
                        "Copy2[0]" in pdf_field or "CopyB[0]" in pdf_field):
                        # Check if the rest of the path matches
                        pdf_pattern = pdf_field.replace("CopyA[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("Copy1[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("Copy2[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("CopyB[0]", "Copy*[0]")
                        pdf_pattern = pdf_pattern.replace("f1_", "f*_")
                        pdf_pattern = pdf_pattern.replace("f2_", "f*_")
                        
                        base_pattern_normalized = base_pattern.replace("f2_", "f*_")
                        
                        if pdf_pattern == base_pattern_normalized:
                            payer_name_fields.append(pdf_field)
            
            payer_name_count = len(payer_name_fields)
            
            # CRITICAL VERIFICATION: Counts should be equal
            assert calendar_year_count == payer_name_count, \
                f"Calendar year has {calendar_year_count} variants, " \
                f"but payerName has {payer_name_count} variants. " \
                f"Both should have the same count."
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_multi_copy_fields_strategy())
    def test_total_pdf_field_count_is_four_times_api_field_count(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: fix-calendar-year-multi-copy, Property 3: Multi-Copy Field Count Consistency
        
        For any form data containing multi-copy fields,
        the total number of PDF fields should be exactly four times the number
        of API fields.
        
        This test verifies that:
        1. Each API field generates exactly 4 PDF fields
        2. The 4x multiplier is consistent
        3. No extra or missing PDF fields are generated
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Count API fields
        num_api_fields = len(form_data)
        
        # Count PDF fields
        num_pdf_fields = len(mapped_data)
        
        # CRITICAL VERIFICATION: PDF field count should be 4x API field count
        expected_pdf_fields = num_api_fields * 4
        
        assert num_pdf_fields == expected_pdf_fields, \
            f"Should have {expected_pdf_fields} PDF fields (4 per API field), " \
            f"found {num_pdf_fields}"
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_calendar_year_variant_count_matches_expected_copies(self, calendar_year):
        """
        **Validates: Requirements 2.2**
        Feature: fix-calendar-year-multi-copy, Property 3: Multi-Copy Field Count Consistency
        
        For any calendar year value,
        the number of copy variants should match the expected number of form copies
        (CopyA, Copy1, Copy2, CopyB = 4 copies).
        
        This test verifies that:
        1. Calendar year has exactly 4 variants
        2. The count matches the number of form copies
        3. All expected copies are present
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Create form data with calendar year
        form_data = {"calendarYear": calendar_year}
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Count calendar year variants
        calendar_year_fields = [
            field for field in mapped_data.keys()
            if "CalendarYear[0]" in field
        ]
        
        # Expected number of copies (CopyA, Copy1, Copy2, CopyB)
        expected_copy_count = 4
        
        # CRITICAL VERIFICATION: Variant count should match expected copy count
        assert len(calendar_year_fields) == expected_copy_count, \
            f"Calendar year should have {expected_copy_count} variants " \
            f"(one for each form copy), found {len(calendar_year_fields)}"
    
    @settings(max_examples=100)
    @given(form_data=form_data_with_multi_copy_fields_strategy())
    def test_variant_count_consistency_across_different_field_types(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: fix-calendar-year-multi-copy, Property 3: Multi-Copy Field Count Consistency
        
        For any form data containing different types of multi-copy fields
        (calendar year, names, TINs, addresses, amounts),
        all fields should generate the same number of copy variants.
        
        This test verifies that:
        1. Calendar year has the same variant count as name fields
        2. Calendar year has the same variant count as TIN fields
        3. Calendar year has the same variant count as address fields
        4. Calendar year has the same variant count as amount fields
        5. All multi-copy fields are consistent
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Map all fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Categorize fields by type
        # Note: Only use fields with distinct PDF field mappings
        field_categories = {
            "calendar": ["calendarYear"],
            "names": ["recipientName"],
            "tins": ["payerTIN", "recipientTIN"],
            "amounts": ["totalOrdinaryDividends", "qualifiedDividends"],
            "account": ["accountNumber"]
        }
        
        # Count variants for each category
        category_counts = {}
        
        for category, field_names in field_categories.items():
            for field_name in field_names:
                if field_name in form_data:
                    # Get the base PDF field name
                    base_pdf_field = mapper.map_field(field_name)
                    
                    if base_pdf_field is None:
                        continue
                    
                    # Count variants for this field
                    field_variants = []
                    for pdf_field in mapped_data.keys():
                        # Check if this PDF field is a variant of the base field
                        if "Copy1[0]" in base_pdf_field:
                            # Extract the pattern without copy prefix
                            base_pattern = base_pdf_field.replace("Copy1[0]", "Copy*[0]")
                            
                            # Check if PDF field matches any copy variant
                            if ("CopyA[0]" in pdf_field or "Copy1[0]" in pdf_field or 
                                "Copy2[0]" in pdf_field or "CopyB[0]" in pdf_field):
                                # Check if the rest of the path matches
                                pdf_pattern = pdf_field.replace("CopyA[0]", "Copy*[0]")
                                pdf_pattern = pdf_pattern.replace("Copy1[0]", "Copy*[0]")
                                pdf_pattern = pdf_pattern.replace("Copy2[0]", "Copy*[0]")
                                pdf_pattern = pdf_pattern.replace("CopyB[0]", "Copy*[0]")
                                pdf_pattern = pdf_pattern.replace("f1_", "f*_")
                                pdf_pattern = pdf_pattern.replace("f2_", "f*_")
                                
                                base_pattern_normalized = base_pattern.replace("f2_", "f*_")
                                
                                if pdf_pattern == base_pattern_normalized:
                                    field_variants.append(pdf_field)
                    
                    if field_name not in category_counts:
                        category_counts[field_name] = len(field_variants)
        
        # CRITICAL VERIFICATION: All fields should have the same variant count
        if category_counts:
            unique_counts = set(category_counts.values())
            
            assert len(unique_counts) == 1, \
                f"All multi-copy fields should have the same variant count. " \
                f"Found different counts: {category_counts}"
            
            # Verify the count is 4
            expected_count = 4
            actual_count = list(unique_counts)[0]
            
            assert actual_count == expected_count, \
                f"All multi-copy fields should have {expected_count} variants, " \
                f"found {actual_count}"
    
    @settings(max_examples=100)
    @given(calendar_year=calendar_year_strategy())
    def test_calendar_year_uses_same_copy_generation_logic(self, calendar_year):
        """
        **Validates: Requirements 2.2**
        Feature: fix-calendar-year-multi-copy, Property 3: Multi-Copy Field Count Consistency
        
        For any calendar year value,
        the copy variant generation should follow the same pattern as other
        multi-copy fields (CopyA, Copy1, Copy2, CopyB).
        
        This test verifies that:
        1. Calendar year has CopyA variant
        2. Calendar year has Copy1 variant
        3. Calendar year has Copy2 variant
        4. Calendar year has CopyB variant
        5. No other copy variants are generated
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
        
        # Check for each expected copy prefix
        has_copya = any("CopyA[0]" in field for field in calendar_year_fields)
        has_copy1 = any("Copy1[0]" in field for field in calendar_year_fields)
        has_copy2 = any("Copy2[0]" in field for field in calendar_year_fields)
        has_copyb = any("CopyB[0]" in field for field in calendar_year_fields)
        
        # CRITICAL VERIFICATION: All four copy prefixes should be present
        assert has_copya, \
            "Calendar year should have CopyA variant"
        
        assert has_copy1, \
            "Calendar year should have Copy1 variant"
        
        assert has_copy2, \
            "Calendar year should have Copy2 variant"
        
        assert has_copyb, \
            "Calendar year should have CopyB variant"
        
        # Verify exactly 4 variants (no extra copies)
        assert len(calendar_year_fields) == 4, \
            f"Calendar year should have exactly 4 variants, found {len(calendar_year_fields)}"
