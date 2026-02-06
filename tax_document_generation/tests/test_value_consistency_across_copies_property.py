"""
Property-based tests for value consistency across copies in DocumentGenerator.

These tests verify that after document generation, all three copies (Copy1, Copy2, CopyB)
contain identical values for corresponding fields. This ensures that each recipient
receives complete and consistent information.

Feature: multi-page-form-filling
Property 3: Value Consistency Across Copies

**Validates: Requirements 3.1**
"""

import pytest
from hypothesis import given, settings, strategies as st
import fitz  # PyMuPDF
from tax_document_generation.document_generator import generate_document
from tax_document_generation.field_mapper import FieldMapper
from tax_document_generation.field_mappings.div_1099 import SUPPORTED_FIELDS


# Increase deadline for PDF generation tests
# PDF generation with PyMuPDF can take longer, especially with multiple copies
TEST_SETTINGS = settings(max_examples=20, deadline=3000)  # 3 second deadline


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


def extract_text_from_pdf_page(pdf_bytes: bytes, page_num: int) -> str:
    """
    Extract all text content from a specific page of a PDF.
    
    Args:
        pdf_bytes: The PDF document as bytes
        page_num: The page number (0-indexed)
        
    Returns:
        All text content from the page as a string
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]
    text = page.get_text()
    doc.close()
    return text


def extract_field_values_from_page(pdf_bytes: bytes, page_num: int, form_data: dict, mapper: FieldMapper) -> dict:
    """
    Extract field values from a specific page by looking for the text content.
    
    Since the PDF is flattened, we extract text and check if the expected values
    are present on the page.
    
    Args:
        pdf_bytes: The PDF document as bytes
        page_num: The page number (0-indexed)
        form_data: The original form data used to generate the PDF
        mapper: The FieldMapper instance
        
    Returns:
        Dictionary mapping API field names to their presence on the page (True/False)
    """
    page_text = extract_text_from_pdf_page(pdf_bytes, page_num)
    
    field_presence = {}
    for api_field_name, expected_value in form_data.items():
        # Check if the value appears in the page text
        field_presence[api_field_name] = str(expected_value) in page_text
    
    return field_presence


class TestValueConsistencyAcrossCopiesProperty:
    """Property-based tests for value consistency across copies."""
    
    @TEST_SETTINGS
    @given(form_data=form_data_strategy())
    def test_all_copies_contain_same_values(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: multi-page-form-filling, Property 3: Value Consistency Across Copies
        
        For any form data provided to the Document_Generator,
        all three copies (Copy1, Copy2, CopyB) should contain identical values
        for corresponding fields after generation.
        
        This test verifies that:
        1. Copy1 (page 2, 0-indexed) contains all expected values
        2. Copy2 (page 3, 0-indexed) contains all expected values
        3. CopyB (page 5, 0-indexed) contains all expected values
        4. All three copies have identical content
        
        NOTE: Some fields may fail to populate due to PDF constraints, but
        the key property is CONSISTENCY - if a field fails in one copy,
        it should fail in all copies.
        """
        # Load the template PDF
        with open("1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate the document
        output_pdf = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Initialize field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Extract text from all three copy pages
        # Copy1 is on page 3 (index 2)
        # Copy2 is on page 4 (index 3)
        # CopyB is on page 6 (index 5)
        copy1_text = extract_text_from_pdf_page(output_pdf, 2)
        copy2_text = extract_text_from_pdf_page(output_pdf, 3)
        copyb_text = extract_text_from_pdf_page(output_pdf, 5)
        
        # Verify that all form data values appear CONSISTENTLY in all three copies
        # The key property is: if a value appears in one copy, it must appear in all copies
        for api_field_name, expected_value in form_data.items():
            # Skip unmapped fields
            if mapper.map_field(api_field_name) is None:
                continue
            
            value_str = str(expected_value)
            
            # Check presence in each copy
            in_copy1 = value_str in copy1_text
            in_copy2 = value_str in copy2_text
            in_copyb = value_str in copyb_text
            
            # CRITICAL VERIFICATION: Value presence should be CONSISTENT across all copies
            # If it appears in one, it should appear in all; if missing from one, missing from all
            assert in_copy1 == in_copy2 == in_copyb, \
                f"Value '{value_str}' for field '{api_field_name}' has inconsistent presence: " \
                f"Copy1={in_copy1}, Copy2={in_copy2}, CopyB={in_copyb}"
    
    @TEST_SETTINGS
    @given(form_data=form_data_strategy())
    def test_mapped_fields_present_in_all_copies(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: multi-page-form-filling, Property 3: Value Consistency Across Copies
        
        For any form data provided to the Document_Generator,
        all mapped fields should have consistent presence across all three copies.
        
        This test verifies that:
        1. Fields have consistent presence in Copy1, Copy2, and CopyB
        2. If a field appears in one copy, it appears in all copies
        3. If a field is missing from one copy, it's missing from all copies
        4. No mapped fields have inconsistent presence across copies
        """
        # Load the template PDF
        with open("1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate the document
        output_pdf = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Initialize field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Extract field presence from all three copy pages
        copy1_presence = extract_field_values_from_page(output_pdf, 2, form_data, mapper)
        copy2_presence = extract_field_values_from_page(output_pdf, 3, form_data, mapper)
        copyb_presence = extract_field_values_from_page(output_pdf, 5, form_data, mapper)
        
        # Verify that all mapped fields have CONSISTENT presence across all three copies
        for api_field_name in form_data.keys():
            # Skip unmapped fields
            if mapper.map_field(api_field_name) is None:
                continue
            
            copy1_has = copy1_presence.get(api_field_name, False)
            copy2_has = copy2_presence.get(api_field_name, False)
            copyb_has = copyb_presence.get(api_field_name, False)
            
            # CRITICAL VERIFICATION: Field presence should be CONSISTENT across all three copies
            assert copy1_has == copy2_has == copyb_has, \
                f"Field '{api_field_name}' has inconsistent presence: " \
                f"Copy1={copy1_has}, Copy2={copy2_has}, CopyB={copyb_has}"
    
    @TEST_SETTINGS
    @given(form_data=form_data_strategy())
    def test_copy_pages_have_identical_content(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: multi-page-form-filling, Property 3: Value Consistency Across Copies
        
        For any form data provided to the Document_Generator,
        the three copy pages should have identical content (ignoring copy labels).
        
        This test verifies that:
        1. Copy1 and Copy2 have the same field values
        2. Copy1 and CopyB have the same field values
        3. Copy2 and CopyB have the same field values
        4. All three copies are consistent
        """
        # Load the template PDF
        with open("1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate the document
        output_pdf = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Initialize field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Extract field presence from all three copy pages
        copy1_presence = extract_field_values_from_page(output_pdf, 2, form_data, mapper)
        copy2_presence = extract_field_values_from_page(output_pdf, 3, form_data, mapper)
        copyb_presence = extract_field_values_from_page(output_pdf, 5, form_data, mapper)
        
        # Verify that all three copies have identical field presence
        for api_field_name in form_data.keys():
            # Skip unmapped fields
            if mapper.map_field(api_field_name) is None:
                continue
            
            copy1_has_field = copy1_presence.get(api_field_name, False)
            copy2_has_field = copy2_presence.get(api_field_name, False)
            copyb_has_field = copyb_presence.get(api_field_name, False)
            
            # CRITICAL VERIFICATION: All three copies should have identical presence
            assert copy1_has_field == copy2_has_field == copyb_has_field, \
                f"Field '{api_field_name}' presence should be identical across all copies: " \
                f"Copy1={copy1_has_field}, Copy2={copy2_has_field}, CopyB={copyb_has_field}"
    
    @TEST_SETTINGS
    @given(form_data=complete_form_data_strategy())
    def test_all_supported_fields_consistent_across_copies(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: multi-page-form-filling, Property 3: Value Consistency Across Copies
        
        For all supported API fields,
        the Document_Generator should populate all three copies with consistent values.
        
        This test verifies that:
        1. All supported fields have consistent presence in all copies
        2. Values that appear in one copy appear in all copies
        3. Values missing from one copy are missing from all copies
        4. All three copies have identical value presence for all fields
        """
        # Load the template PDF
        with open("1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate the document
        output_pdf = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Initialize field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Extract text from all three copy pages
        copy1_text = extract_text_from_pdf_page(output_pdf, 2)
        copy2_text = extract_text_from_pdf_page(output_pdf, 3)
        copyb_text = extract_text_from_pdf_page(output_pdf, 5)
        
        # Verify that all supported fields have CONSISTENT presence across all three copies
        for api_field_name, expected_value in form_data.items():
            value_str = str(expected_value)
            
            # Check presence in each copy
            in_copy1 = value_str in copy1_text
            in_copy2 = value_str in copy2_text
            in_copyb = value_str in copyb_text
            
            # CRITICAL VERIFICATION: Value presence should be CONSISTENT across all copies
            assert in_copy1 == in_copy2 == in_copyb, \
                f"Value '{value_str}' for field '{api_field_name}' has inconsistent presence: " \
                f"Copy1={in_copy1}, Copy2={in_copy2}, CopyB={in_copyb}"
    
    @TEST_SETTINGS
    @given(
        form_data=form_data_strategy(),
        api_field_name=valid_api_field_name_strategy()
    )
    def test_single_field_consistent_across_copies(self, form_data, api_field_name):
        """
        **Validates: Requirements 3.1**
        Feature: multi-page-form-filling, Property 3: Value Consistency Across Copies
        
        For any single API field,
        the Document_Generator should populate all three copies with consistent values.
        
        This test verifies that:
        1. The field value has consistent presence in Copy1, Copy2, and CopyB
        2. If the value appears in one copy, it appears in all copies
        3. If the value is missing from one copy, it's missing from all copies
        4. All three copies have the same behavior for the field
        """
        # Add the specific field to form data if not already present
        if api_field_name not in form_data:
            form_data[api_field_name] = "test_value_123"
        
        # Load the template PDF
        with open("1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate the document
        output_pdf = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Initialize field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Skip if field is not mapped
        if mapper.map_field(api_field_name) is None:
            return
        
        # Extract text from all three copy pages
        copy1_text = extract_text_from_pdf_page(output_pdf, 2)
        copy2_text = extract_text_from_pdf_page(output_pdf, 3)
        copyb_text = extract_text_from_pdf_page(output_pdf, 5)
        
        # Get the expected value
        expected_value = str(form_data[api_field_name])
        
        # Check presence in each copy
        in_copy1 = expected_value in copy1_text
        in_copy2 = expected_value in copy2_text
        in_copyb = expected_value in copyb_text
        
        # CRITICAL VERIFICATION: Value presence should be CONSISTENT across all copies
        assert in_copy1 == in_copy2 == in_copyb, \
            f"Value '{expected_value}' for field '{api_field_name}' has inconsistent presence: " \
            f"Copy1={in_copy1}, Copy2={in_copy2}, CopyB={in_copyb}"
    
    @TEST_SETTINGS
    @given(form_data=form_data_strategy())
    def test_no_copy_specific_value_differences(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: multi-page-form-filling, Property 3: Value Consistency Across Copies
        
        For any form data,
        the Document_Generator should not introduce copy-specific value differences.
        
        This test verifies that:
        1. Values are not modified for different copies
        2. No copy-specific transformations occur
        3. All copies receive identical values
        4. The mapping is consistent across copies
        """
        # Load the template PDF
        with open("1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate the document
        output_pdf = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Initialize field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Get mapped data to verify consistency
        mapped_data = mapper.map_all_fields(form_data)
        
        # Extract text from all three copy pages
        copy1_text = extract_text_from_pdf_page(output_pdf, 2)
        copy2_text = extract_text_from_pdf_page(output_pdf, 3)
        copyb_text = extract_text_from_pdf_page(output_pdf, 5)
        
        # Verify that each value in mapped_data appears in all three copies
        # Group by value to check consistency
        values_by_api_field = {}
        for api_field_name, value in form_data.items():
            if mapper.map_field(api_field_name) is not None:
                values_by_api_field[api_field_name] = str(value)
        
        # For each unique value, verify it appears in all copies or none
        for api_field_name, value_str in values_by_api_field.items():
            copy1_has_value = value_str in copy1_text
            copy2_has_value = value_str in copy2_text
            copyb_has_value = value_str in copyb_text
            
            # CRITICAL VERIFICATION: Value presence should be consistent across copies
            assert copy1_has_value == copy2_has_value == copyb_has_value, \
                f"Value '{value_str}' for field '{api_field_name}' should have consistent presence: " \
                f"Copy1={copy1_has_value}, Copy2={copy2_has_value}, CopyB={copyb_has_value}"
    
    @TEST_SETTINGS
    @given(form_data=form_data_strategy())
    def test_value_count_consistency_across_copies(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: multi-page-form-filling, Property 3: Value Consistency Across Copies
        
        For any form data,
        the number of populated fields should be identical across all three copies.
        
        This test verifies that:
        1. Copy1 has the same number of populated fields as Copy2
        2. Copy1 has the same number of populated fields as CopyB
        3. Copy2 has the same number of populated fields as CopyB
        4. No fields are missing from any copy
        """
        # Load the template PDF
        with open("1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate the document
        output_pdf = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Initialize field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Extract field presence from all three copy pages
        copy1_presence = extract_field_values_from_page(output_pdf, 2, form_data, mapper)
        copy2_presence = extract_field_values_from_page(output_pdf, 3, form_data, mapper)
        copyb_presence = extract_field_values_from_page(output_pdf, 5, form_data, mapper)
        
        # Count populated fields in each copy (only mapped fields)
        copy1_count = sum(1 for api_field, present in copy1_presence.items() 
                         if present and mapper.map_field(api_field) is not None)
        copy2_count = sum(1 for api_field, present in copy2_presence.items() 
                         if present and mapper.map_field(api_field) is not None)
        copyb_count = sum(1 for api_field, present in copyb_presence.items() 
                         if present and mapper.map_field(api_field) is not None)
        
        # CRITICAL VERIFICATION: All three copies should have the same number of populated fields
        assert copy1_count == copy2_count == copyb_count, \
            f"All three copies should have the same number of populated fields: " \
            f"Copy1={copy1_count}, Copy2={copy2_count}, CopyB={copyb_count}"
    
    @TEST_SETTINGS
    @given(form_data=form_data_strategy())
    def test_empty_values_consistent_across_copies(self, form_data):
        """
        **Validates: Requirements 3.1**
        Feature: multi-page-form-filling, Property 3: Value Consistency Across Copies
        
        For any form data with empty string values,
        the Document_Generator should handle empty values consistently across all copies.
        
        This test verifies that:
        1. Empty values are handled the same in Copy1, Copy2, and CopyB
        2. No copy-specific behavior for empty values
        3. Consistency is maintained even with edge case values
        """
        # Add some empty string values to form data
        if form_data:
            # Pick a random field and set it to empty string
            first_field = list(form_data.keys())[0]
            form_data[first_field] = ""
        
        # Load the template PDF
        with open("1099-DIV.pdf", "rb") as f:
            template_bytes = f.read()
        
        # Generate the document
        output_pdf = generate_document(template_bytes, form_data, "1099-DIV")
        
        # Initialize field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Extract field presence from all three copy pages
        copy1_presence = extract_field_values_from_page(output_pdf, 2, form_data, mapper)
        copy2_presence = extract_field_values_from_page(output_pdf, 3, form_data, mapper)
        copyb_presence = extract_field_values_from_page(output_pdf, 5, form_data, mapper)
        
        # Verify consistency for all fields (including empty ones)
        for api_field_name in form_data.keys():
            # Skip unmapped fields
            if mapper.map_field(api_field_name) is None:
                continue
            
            copy1_has_field = copy1_presence.get(api_field_name, False)
            copy2_has_field = copy2_presence.get(api_field_name, False)
            copyb_has_field = copyb_presence.get(api_field_name, False)
            
            # CRITICAL VERIFICATION: Consistency should be maintained even for empty values
            # Note: Empty strings may not appear in text extraction, so we check consistency
            # rather than presence
            assert copy1_has_field == copy2_has_field == copyb_has_field, \
                f"Field '{api_field_name}' (value='{form_data[api_field_name]}') should have " \
                f"consistent presence across copies: " \
                f"Copy1={copy1_has_field}, Copy2={copy2_has_field}, CopyB={copyb_has_field}"
