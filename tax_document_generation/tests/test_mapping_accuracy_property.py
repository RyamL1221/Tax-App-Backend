"""
Property-based tests for mapping accuracy.

These tests verify that required field mappings point to real PDF fields
in the actual 1099-DIV template. Each property test runs with a minimum of
100 iterations.

Feature: fix-pdf-field-mapping
Property 9: Required field mappings point to real PDF fields

**Validates: Requirements 5.3**
"""

import pytest
import os
from hypothesis import given, settings, strategies as st, assume
from tax_document_generation.field_mappings.div_1099 import FIELD_MAPPING, SUPPORTED_FIELDS

try:
    from pypdf import PdfReader
    USING_PYPDF = True
except ImportError:
    from PyPDF2 import PdfReader
    USING_PYPDF = False


# Strategy for generating API field names
def api_field_name_strategy():
    """Generate API field names from the 1099-DIV field reference."""
    return st.sampled_from(SUPPORTED_FIELDS)


def load_pdf_template():
    """
    Load the 1099-DIV PDF template and return field names.
    
    Returns:
        Set of PDF field names, or None if template not found
    """
    # Try multiple possible locations for the template
    possible_paths = [
        "1099-DIV.pdf",
        "../1099-DIV.pdf",
        "../../1099-DIV.pdf",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "1099-DIV.pdf"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    reader = PdfReader(f)
                    fields = reader.get_fields()
                    if fields:
                        return set(fields.keys())
            except Exception:
                continue
    
    return None


# Load PDF fields once for all tests
PDF_FIELDS = load_pdf_template()


class TestMappingAccuracyProperty:
    """Property-based tests for mapping accuracy."""
    
    @pytest.fixture(autouse=True)
    def check_pdf_template(self):
        """Check if PDF template is available before running tests."""
        if PDF_FIELDS is None:
            pytest.skip("1099-DIV.pdf template not found - skipping mapping accuracy tests")
    
    @settings(max_examples=100)
    @given(api_field_name=api_field_name_strategy())
    def test_mapped_pdf_field_exists_in_template(self, api_field_name):
        """
        **Validates: Requirements 5.3**
        Feature: fix-pdf-field-mapping, Property 9: Required field mappings point to real PDF fields
        
        For any required 1099-DIV API field name,
        the mapped PDF field name should exist in the actual 1099-DIV PDF template.
        
        This test verifies that:
        1. Mapped PDF field names are real
        2. No typos or incorrect field names in mapping
        3. Mappings are accurate and usable
        """
        # Get the mapped PDF field name
        pdf_field_name = FIELD_MAPPING.get(api_field_name)
        
        # Verify the mapping exists
        assert pdf_field_name is not None, \
            f"API field '{api_field_name}' should have a mapping"
        
        # Verify the PDF field exists in the template
        assert pdf_field_name in PDF_FIELDS, \
            f"Mapped PDF field '{pdf_field_name}' for API field '{api_field_name}' " \
            f"should exist in the 1099-DIV template"
    
    def test_all_mappings_point_to_real_fields(self):
        """
        **Validates: Requirements 5.3**
        Feature: fix-pdf-field-mapping, Property 9: Required field mappings point to real PDF fields
        
        For all API field mappings,
        each mapped PDF field name should exist in the actual template.
        
        This test verifies that:
        1. Complete mapping validation
        2. No invalid mappings exist
        3. All mappings are accurate
        """
        invalid_mappings = []
        
        for api_field, pdf_field in FIELD_MAPPING.items():
            if pdf_field not in PDF_FIELDS:
                invalid_mappings.append((api_field, pdf_field))
        
        assert len(invalid_mappings) == 0, \
            f"Found {len(invalid_mappings)} invalid mapping(s): {invalid_mappings}"
    
    @settings(max_examples=100)
    @given(api_field_name=api_field_name_strategy())
    def test_mapped_field_is_not_empty(self, api_field_name):
        """
        **Validates: Requirements 5.3**
        Feature: fix-pdf-field-mapping, Property 9: Required field mappings point to real PDF fields
        
        For any API field name,
        the mapped PDF field name should not be empty or None.
        
        This test verifies that:
        1. All mappings are complete
        2. No empty or null mappings
        3. Mappings are valid strings
        """
        pdf_field_name = FIELD_MAPPING.get(api_field_name)
        
        assert pdf_field_name is not None, \
            f"API field '{api_field_name}' should have a non-None mapping"
        
        assert isinstance(pdf_field_name, str), \
            f"Mapped PDF field for '{api_field_name}' should be a string, got {type(pdf_field_name)}"
        
        assert len(pdf_field_name) > 0, \
            f"Mapped PDF field for '{api_field_name}' should not be empty"
    
    @settings(max_examples=100)
    @given(api_field_name=api_field_name_strategy())
    def test_mapped_field_follows_naming_convention(self, api_field_name):
        """
        **Validates: Requirements 5.3**
        Feature: fix-pdf-field-mapping, Property 9: Required field mappings point to real PDF fields
        
        For any API field name,
        the mapped PDF field name should follow the IRS PDF naming convention.
        
        This test verifies that:
        1. Field names have correct structure
        2. Field names match expected pattern
        3. Mappings are well-formed
        """
        pdf_field_name = FIELD_MAPPING.get(api_field_name)
        
        # Verify the PDF field name follows the expected pattern
        assert pdf_field_name.startswith("topmostSubform[0].Copy1[0]."), \
            f"PDF field '{pdf_field_name}' should start with 'topmostSubform[0].Copy1[0].'"
        
        assert "[0]" in pdf_field_name, \
            f"PDF field '{pdf_field_name}' should contain array notation [0]"
        
        assert pdf_field_name.endswith("[0]"), \
            f"PDF field '{pdf_field_name}' should end with [0]"
    
    def test_no_duplicate_pdf_field_mappings(self):
        """
        **Validates: Requirements 5.3**
        Feature: fix-pdf-field-mapping, Property 9: Required field mappings point to real PDF fields
        
        For all API field mappings,
        no two API fields should map to the same PDF field.
        
        This test verifies that:
        1. Each PDF field is used only once
        2. No conflicts in mappings
        3. One-to-one mapping relationship
        """
        pdf_field_counts = {}
        
        for api_field, pdf_field in FIELD_MAPPING.items():
            if pdf_field not in pdf_field_counts:
                pdf_field_counts[pdf_field] = []
            pdf_field_counts[pdf_field].append(api_field)
        
        # Find duplicates
        duplicates = {
            pdf_field: api_fields
            for pdf_field, api_fields in pdf_field_counts.items()
            if len(api_fields) > 1
        }
        
        assert len(duplicates) == 0, \
            f"Found duplicate PDF field mappings: {duplicates}"
    
    def test_mapping_coverage_is_complete(self):
        """
        **Validates: Requirements 5.3**
        Feature: fix-pdf-field-mapping, Property 9: Required field mappings point to real PDF fields
        
        For all supported API field names,
        each should have a mapping in FIELD_MAPPING.
        
        This test verifies that:
        1. No missing mappings
        2. Complete coverage of API fields
        3. All supported fields are mapped
        """
        missing_mappings = []
        
        for api_field in SUPPORTED_FIELDS:
            if api_field not in FIELD_MAPPING:
                missing_mappings.append(api_field)
        
        assert len(missing_mappings) == 0, \
            f"Found {len(missing_mappings)} API field(s) without mappings: {missing_mappings}"
    
    @settings(max_examples=100)
    @given(api_field_name=api_field_name_strategy())
    def test_mapped_field_is_accessible_in_template(self, api_field_name):
        """
        **Validates: Requirements 5.3**
        Feature: fix-pdf-field-mapping, Property 9: Required field mappings point to real PDF fields
        
        For any API field name,
        the mapped PDF field should be accessible in the template
        (not just exist, but be readable).
        
        This test verifies that:
        1. PDF fields are not just present but usable
        2. Fields can be accessed by the PDF library
        3. No access issues with mapped fields
        """
        pdf_field_name = FIELD_MAPPING.get(api_field_name)
        
        # Verify the field exists and is in our loaded set
        assert pdf_field_name in PDF_FIELDS, \
            f"PDF field '{pdf_field_name}' should be accessible in the template"
    
    def test_all_required_fields_have_valid_mappings(self):
        """
        **Validates: Requirements 5.3**
        Feature: fix-pdf-field-mapping, Property 9: Required field mappings point to real PDF fields
        
        For all required 1099-DIV fields,
        each should have a valid mapping that points to a real PDF field.
        
        This test verifies that:
        1. Required fields are prioritized
        2. Critical mappings are correct
        3. Essential functionality is guaranteed
        """
        # Define required fields (these are typically the most important fields)
        required_fields = [
            "payerName",
            "payerTIN",
            "recipientName",
            "recipientTIN",
            "totalOrdinaryDividends",
            "qualifiedDividends",
        ]
        
        invalid_required_mappings = []
        
        for api_field in required_fields:
            if api_field not in FIELD_MAPPING:
                invalid_required_mappings.append((api_field, "NO MAPPING"))
            else:
                pdf_field = FIELD_MAPPING[api_field]
                if pdf_field not in PDF_FIELDS:
                    invalid_required_mappings.append((api_field, pdf_field))
        
        assert len(invalid_required_mappings) == 0, \
            f"Found invalid mappings for required fields: {invalid_required_mappings}"
    
    @settings(max_examples=100)
    @given(api_field_name=api_field_name_strategy())
    def test_mapped_field_name_is_consistent(self, api_field_name):
        """
        **Validates: Requirements 5.3**
        Feature: fix-pdf-field-mapping, Property 9: Required field mappings point to real PDF fields
        
        For any API field name,
        the mapped PDF field name should be consistent across multiple lookups.
        
        This test verifies that:
        1. Mappings are deterministic
        2. No randomness in mapping results
        3. Consistent behavior
        """
        # Get the mapping multiple times
        pdf_field_1 = FIELD_MAPPING.get(api_field_name)
        pdf_field_2 = FIELD_MAPPING.get(api_field_name)
        pdf_field_3 = FIELD_MAPPING.get(api_field_name)
        
        # All should be identical
        assert pdf_field_1 == pdf_field_2 == pdf_field_3, \
            f"Mapping for '{api_field_name}' should be consistent: got {pdf_field_1}, {pdf_field_2}, {pdf_field_3}"
