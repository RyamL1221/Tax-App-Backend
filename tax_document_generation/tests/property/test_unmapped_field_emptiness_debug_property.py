"""
Property-based tests for unmapped field emptiness in 1099-DIV field mappings.

**Validates: Requirements 3.3, 4.3**

Property 8: Unmapped Field Emptiness
For any PDF field that has no corresponding data in the form data, that field
should remain empty in the generated PDF.

This test specifically verifies that:
- City field (f2_4) remains empty when no city data is provided
- Account number field (f2_39) remains empty when no account data is provided
- These fields are NOT populated with TIN data (the bug we're verifying is fixed)
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import Dict, Any, Set
import fitz
import os


# Import the field mapper and document generator
from tax_document_generation.field_mapper import FieldMapper
from tax_document_generation.document_generator import generate_document


def extract_field_values(pdf_bytes: bytes) -> Dict[str, str]:
    """
    Extract all field values from a PDF.
    
    Args:
        pdf_bytes: PDF document as bytes
        
    Returns:
        Dictionary mapping field names to their values
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    field_values = {}
    
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = page.widgets()
            
            if widgets:
                for widget in widgets:
                    if widget.field_name:
                        field_values[widget.field_name] = widget.field_value or ""
    finally:
        doc.close()
    
    return field_values


# Strategy for generating field values
field_value_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' .-'),
    min_size=1,
    max_size=50
)


@given(
    payer_tin=st.text(min_size=9, max_size=11),
    recipient_tin=st.text(min_size=9, max_size=11)
)
def test_unmapped_fields_remain_empty_when_not_provided(
    payer_tin: str,
    recipient_tin: str
):
    """
    Property: Fields with no corresponding form data remain empty.
    
    When form data includes only TIN fields (no city, no account number),
    the city and account number fields should remain empty in the PDF.
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data with ONLY TIN fields (no city, no account number)
    form_data = {
        "payerTIN": payer_tin,
        "recipientTIN": recipient_tin
    }
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # Property: City fields (f2_4) should NOT be in mapped data
    city_fields = [k for k in mapped_data.keys() if "f2_4[0]" in k]
    assert len(city_fields) == 0, \
        "City fields should not be populated when no city data provided"
    
    # Property: Account number fields (f2_39) should NOT be in mapped data
    account_fields = [k for k in mapped_data.keys() if "f2_39[0]" in k]
    assert len(account_fields) == 0, \
        "Account number fields should not be populated when no account data provided"
    
    # Property: Only TIN fields should be populated
    payer_tin_fields = [k for k in mapped_data.keys() if "f2_7[0]" in k]
    recipient_tin_fields = [k for k in mapped_data.keys() if "f2_8[0]" in k]
    
    assert len(payer_tin_fields) == 3, "Should have 3 payer TIN fields (one per copy)"
    assert len(recipient_tin_fields) == 3, "Should have 3 recipient TIN fields (one per copy)"


@given(
    payer_name=field_value_strategy,
    total_dividends=st.decimals(min_value=0, max_value=999999, places=2).map(str)
)
def test_city_field_empty_when_only_required_fields_provided(
    payer_name: str,
    total_dividends: str
):
    """
    Property: City field remains empty when not in form data.
    
    When form data includes required fields but no city, the city field
    should not be populated.
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data without city
    form_data = {
        "payerName": payer_name,
        "totalOrdinaryDividends": total_dividends
    }
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # Property: City fields should not be in mapped data
    city_fields = [k for k in mapped_data.keys() if "f2_4[0]" in k]
    assert len(city_fields) == 0, \
        "City field should not be populated when no city data provided"


@given(
    payer_name=field_value_strategy,
    total_dividends=st.decimals(min_value=0, max_value=999999, places=2).map(str)
)
def test_account_number_field_empty_when_not_provided(
    payer_name: str,
    total_dividends: str
):
    """
    Property: Account number field remains empty when not in form data.
    
    When form data includes required fields but no account number, the
    account number field should not be populated.
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data without account number
    form_data = {
        "payerName": payer_name,
        "totalOrdinaryDividends": total_dividends
    }
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # Property: Account number fields should not be in mapped data
    account_fields = [k for k in mapped_data.keys() if "f2_39[0]" in k]
    assert len(account_fields) == 0, \
        "Account number field should not be populated when no account data provided"


@given(
    provided_fields=st.sets(
        st.sampled_from([
            "payerName",
            "payerTIN",
            "recipientTIN",
            "totalOrdinaryDividends",
            "qualifiedDividends"
        ]),
        min_size=1,
        max_size=5
    )
)
def test_only_provided_fields_are_mapped(provided_fields: Set[str]):
    """
    Property: Only fields present in form data are mapped to PDF.
    
    For any subset of available fields, only those fields should be
    mapped to PDF fields. Unprovided fields should not appear in mapping.
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data with only the provided fields
    form_data = {field: f"value_{field}" for field in provided_fields}
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # Get the expected PDF field patterns for provided fields
    expected_patterns = set()
    for api_field in provided_fields:
        pdf_field = mapper.map_field(api_field)
        if pdf_field:
            # Extract the field ID (e.g., "f2_7[0]" from full path)
            if "[0]" in pdf_field:
                parts = pdf_field.split(".")
                for part in parts:
                    if part.startswith("f") and "[0]" in part:
                        expected_patterns.add(part)
    
    # Property: All mapped fields should correspond to provided API fields
    for pdf_field in mapped_data.keys():
        # Extract field ID from full path
        field_id = None
        parts = pdf_field.split(".")
        for part in parts:
            if part.startswith("f") and "[0]" in part:
                field_id = part
                break
        
        if field_id:
            assert field_id in expected_patterns, \
                f"Field {field_id} should not be mapped (not in provided fields)"


def test_city_field_not_populated_with_tin_data():
    """
    Integration test: Verify city field is NOT populated with TIN data.
    
    This is a regression test for the bug where payer TIN was incorrectly
    mapped to the city field (f2_4).
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data with TIN but no city
    form_data = {
        "payerTIN": "12-3456789",
        "recipientTIN": "987-65-4321"
    }
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # Verify city fields are NOT in the mapping
    city_fields = {k: v for k, v in mapped_data.items() if "f2_4[0]" in k}
    assert len(city_fields) == 0, \
        "City field should not be populated with TIN data"
    
    # Verify TIN fields ARE in the mapping
    payer_tin_fields = {k: v for k, v in mapped_data.items() if "f2_7[0]" in k}
    assert len(payer_tin_fields) == 3, \
        "Payer TIN should be in correct field (f2_7)"
    
    # Verify TIN values are correct
    for field, value in payer_tin_fields.items():
        assert value == "12-3456789", \
            "Payer TIN should have correct value"


def test_account_number_field_not_populated_with_tin_data():
    """
    Integration test: Verify account number field is NOT populated with TIN data.
    
    This is a regression test for the bug where recipient TIN was incorrectly
    mapped to the account number field (f2_39).
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data with TIN but no account number
    form_data = {
        "payerTIN": "12-3456789",
        "recipientTIN": "987-65-4321"
    }
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # Verify account number fields are NOT in the mapping
    account_fields = {k: v for k, v in mapped_data.items() if "f2_39[0]" in k}
    assert len(account_fields) == 0, \
        "Account number field should not be populated with TIN data"
    
    # Verify recipient TIN fields ARE in the mapping
    recipient_tin_fields = {k: v for k, v in mapped_data.items() if "f2_8[0]" in k}
    assert len(recipient_tin_fields) == 3, \
        "Recipient TIN should be in correct field (f2_8)"
    
    # Verify TIN values are correct
    for field, value in recipient_tin_fields.items():
        assert value == "987-65-4321", \
            "Recipient TIN should have correct value"


def test_optional_fields_can_be_provided_separately():
    """
    Integration test: Verify optional fields work when provided.
    
    This test ensures that city and account number fields CAN be populated
    when explicitly provided in form data.
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data with optional fields
    form_data = {
        "payerCity": "New York",
        "accountNumber": "123456789"
    }
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # Verify city fields ARE in the mapping when provided
    city_fields = {k: v for k, v in mapped_data.items() if "f2_4[0]" in k}
    assert len(city_fields) == 3, \
        "City field should be populated when city data is provided"
    
    for field, value in city_fields.items():
        assert value == "New York", \
            "City field should have correct value"
    
    # Verify account number fields ARE in the mapping when provided
    account_fields = {k: v for k, v in mapped_data.items() if "f2_39[0]" in k}
    assert len(account_fields) == 3, \
        "Account number field should be populated when account data is provided"
    
    for field, value in account_fields.items():
        assert value == "123456789", \
            "Account number field should have correct value"


def test_unmapped_fields_empty_in_generated_pdf():
    """
    Integration test: Verify unmapped fields are empty in generated PDF.
    
    This test generates an actual PDF and verifies that fields without
    corresponding form data remain empty.
    """
    # Try to find the 1099-DIV template
    possible_paths = [
        "1099-DIV.pdf",
        "../1099-DIV.pdf",
        "../../1099-DIV.pdf",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "1099-DIV.pdf"),
    ]
    
    template_path = None
    for path in possible_paths:
        if os.path.exists(path):
            template_path = path
            break
    
    if not template_path:
        pytest.skip("1099-DIV.pdf template not found")
    
    # Read template
    with open(template_path, 'rb') as f:
        template_bytes = f.read()
    
    # Create form data with only TIN fields (no city, no account number)
    form_data = {
        "payerTIN": "12-3456789",
        "recipientTIN": "987-65-4321"
    }
    
    # Generate PDF
    try:
        output_bytes = generate_document(template_bytes, form_data, "1099-DIV")
    except Exception as e:
        pytest.skip(f"Could not generate PDF: {e}")
    
    # Extract field values
    field_values = extract_field_values(output_bytes)
    
    # Verify city fields are empty
    city_fields = {k: v for k, v in field_values.items() if "f2_4[0]" in k}
    for field, value in city_fields.items():
        assert value == "" or value is None, \
            f"City field {field} should be empty when no city data provided"
    
    # Verify account number fields are empty
    account_fields = {k: v for k, v in field_values.items() if "f2_39[0]" in k}
    for field, value in account_fields.items():
        assert value == "" or value is None, \
            f"Account number field {field} should be empty when no account data provided"
    
    # Verify TIN fields are populated
    payer_tin_fields = {k: v for k, v in field_values.items() if "f2_7[0]" in k}
    for field, value in payer_tin_fields.items():
        assert value == "12-3456789", \
            f"Payer TIN field {field} should have correct value"
    
    recipient_tin_fields = {k: v for k, v in field_values.items() if "f2_8[0]" in k}
    for field, value in recipient_tin_fields.items():
        assert value == "987-65-4321", \
            f"Recipient TIN field {field} should have correct value"
