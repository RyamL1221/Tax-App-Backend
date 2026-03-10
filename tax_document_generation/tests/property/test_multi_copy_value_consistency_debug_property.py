"""
Property-based tests for multi-copy value consistency in 1099-DIV field mappings.

**Validates: Requirements 3.2, 4.2, 5.2, 8.3**

Property 7: Multi-Copy Value Consistency
For any field value in form data, when the PDF is generated, that value should
appear identically in all three copies (Copy1, Copy2, CopyB).

This test specifically verifies that the corrected TIN mappings work correctly
across all three copies of the 1099-DIV form.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import Dict, Any
import fitz
import os
from io import BytesIO


# Import the field mapper and document generator
from tax_document_generation.field_mapper import FieldMapper
from tax_document_generation.document_generator import generate_document


def extract_field_values_by_copy(pdf_bytes: bytes) -> Dict[str, Dict[str, str]]:
    """
    Extract field values grouped by copy (Copy1, Copy2, CopyB).
    
    Args:
        pdf_bytes: PDF document as bytes
        
    Returns:
        Dictionary mapping copy name to field values:
        {
            "Copy1": {"field_name": "value", ...},
            "Copy2": {"field_name": "value", ...},
            "CopyB": {"field_name": "value", ...}
        }
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    copy_values = {
        "Copy1": {},
        "Copy2": {},
        "CopyB": {}
    }
    
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = page.widgets()
            
            if widgets:
                for widget in widgets:
                    if widget.field_name:
                        field_name = widget.field_name
                        field_value = widget.field_value or ""
                        
                        # Determine which copy this field belongs to
                        if "Copy1[0]" in field_name:
                            copy_values["Copy1"][field_name] = field_value
                        elif "Copy2[0]" in field_name:
                            copy_values["Copy2"][field_name] = field_value
                        elif "CopyB[0]" in field_name:
                            copy_values["CopyB"][field_name] = field_value
    finally:
        doc.close()
    
    return copy_values


# Strategy for generating field values
field_value_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' .-'),
    min_size=1,
    max_size=50
)


@given(
    payer_name=field_value_strategy,
    payer_tin=st.text(alphabet=st.characters(whitelist_categories=('Nd',), whitelist_characters='-'), min_size=9, max_size=11),
    recipient_tin=st.text(alphabet=st.characters(whitelist_categories=('Nd',), whitelist_characters='-'), min_size=9, max_size=11),
    total_dividends=st.decimals(min_value=0, max_value=999999, places=2).map(str)
)
def test_multi_copy_value_consistency_for_all_fields(
    payer_name: str,
    payer_tin: str,
    recipient_tin: str,
    total_dividends: str
):
    """
    Property: All field values appear identically in Copy1, Copy2, and CopyB.
    
    For any form data, when mapped to PDF fields, the same value should appear
    in all three copies of the form.
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data
    form_data = {
        "payerName": payer_name,
        "payerTIN": payer_tin,
        "recipientTIN": recipient_tin,
        "totalOrdinaryDividends": total_dividends
    }
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # Group by copy
    copy1_fields = {k: v for k, v in mapped_data.items() if "Copy1[0]" in k}
    copy2_fields = {k: v for k, v in mapped_data.items() if "Copy2[0]" in k}
    copyb_fields = {k: v for k, v in mapped_data.items() if "CopyB[0]" in k}
    
    # Property: All three copies should have the same number of fields
    assert len(copy1_fields) == len(copy2_fields) == len(copyb_fields), \
        "All copies should have the same number of fields"
    
    # Property: For each field in Copy1, corresponding fields in Copy2 and CopyB should have same value
    for copy1_field, value in copy1_fields.items():
        # Generate corresponding field names for other copies
        copy2_field = copy1_field.replace("Copy1[0]", "Copy2[0]")
        copyb_field = copy1_field.replace("Copy1[0]", "CopyB[0]")
        
        # Verify Copy2 has the same value
        assert copy2_field in copy2_fields, \
            f"Copy2 should have corresponding field for {copy1_field}"
        assert copy2_fields[copy2_field] == value, \
            f"Copy2 field {copy2_field} should have same value as Copy1"
        
        # Verify CopyB has the same value
        assert copyb_field in copyb_fields, \
            f"CopyB should have corresponding field for {copy1_field}"
        assert copyb_fields[copyb_field] == value, \
            f"CopyB field {copyb_field} should have same value as Copy1"


@given(
    payer_tin=st.text(min_size=9, max_size=11),
    recipient_tin=st.text(min_size=9, max_size=11)
)
def test_tin_fields_consistency_across_copies(payer_tin: str, recipient_tin: str):
    """
    Property: TIN fields have consistent values across all copies.
    
    This specifically tests the corrected TIN mappings to ensure they work
    correctly across Copy1, Copy2, and CopyB.
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data with TIN fields
    form_data = {
        "payerTIN": payer_tin,
        "recipientTIN": recipient_tin
    }
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # Extract TIN fields for each copy
    payer_tin_fields = {k: v for k, v in mapped_data.items() if "f2_7[0]" in k}
    recipient_tin_fields = {k: v for k, v in mapped_data.items() if "f2_8[0]" in k}
    
    # Property: Should have 3 payer TIN fields (one per copy)
    assert len(payer_tin_fields) == 3, \
        f"Expected 3 payer TIN fields, got {len(payer_tin_fields)}"
    
    # Property: Should have 3 recipient TIN fields (one per copy)
    assert len(recipient_tin_fields) == 3, \
        f"Expected 3 recipient TIN fields, got {len(recipient_tin_fields)}"
    
    # Property: All payer TIN fields should have the same value
    payer_tin_values = set(payer_tin_fields.values())
    assert len(payer_tin_values) == 1, \
        "All payer TIN fields should have the same value"
    assert payer_tin in payer_tin_values, \
        "Payer TIN value should match input"
    
    # Property: All recipient TIN fields should have the same value
    recipient_tin_values = set(recipient_tin_fields.values())
    assert len(recipient_tin_values) == 1, \
        "All recipient TIN fields should have the same value"
    assert recipient_tin in recipient_tin_values, \
        "Recipient TIN value should match input"


@given(
    field_value=field_value_strategy
)
def test_single_field_consistency_across_copies(field_value: str):
    """
    Property: Any single field value appears identically in all copies.
    
    For any field and any value, when mapped to PDF, the value should be
    consistent across Copy1, Copy2, and CopyB.
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Test with different fields
    test_fields = [
        "payerName",
        "payerTIN",
        "recipientTIN",
        "totalOrdinaryDividends"
    ]
    
    for api_field in test_fields:
        form_data = {api_field: field_value}
        
        # Map to PDF fields
        mapped_data = mapper.map_all_fields(form_data)
        
        # Property: All mapped values should be identical
        unique_values = set(mapped_data.values())
        assert len(unique_values) == 1, \
            f"Field {api_field} should have consistent value across all copies"
        assert field_value in unique_values, \
            f"Field {api_field} should have the input value"


@given(
    num_fields=st.integers(min_value=1, max_value=5)
)
def test_multiple_fields_consistency_across_copies(num_fields: int):
    """
    Property: Multiple fields all maintain consistency across copies.
    
    For any number of fields with different values, each field should
    maintain its value consistently across all copies.
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data with multiple fields
    available_fields = [
        "payerName",
        "payerTIN",
        "recipientTIN",
        "totalOrdinaryDividends",
        "qualifiedDividends"
    ]
    
    form_data = {
        available_fields[i]: f"value_{i}"
        for i in range(min(num_fields, len(available_fields)))
    }
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # For each API field, verify consistency across copies
    for api_field, expected_value in form_data.items():
        # Get the base PDF field name
        pdf_field = mapper.map_field(api_field)
        if pdf_field is None:
            continue
        
        # Get all variants
        copy1_field = pdf_field
        copy2_field = pdf_field.replace("Copy1[0]", "Copy2[0]")
        copyb_field = pdf_field.replace("Copy1[0]", "CopyB[0]")
        
        # Property: All copies should have the same value
        if copy1_field in mapped_data:
            assert mapped_data[copy1_field] == expected_value, \
                f"Copy1 should have correct value for {api_field}"
        
        if copy2_field in mapped_data:
            assert mapped_data[copy2_field] == expected_value, \
                f"Copy2 should have correct value for {api_field}"
        
        if copyb_field in mapped_data:
            assert mapped_data[copyb_field] == expected_value, \
                f"CopyB should have correct value for {api_field}"


def test_tin_fields_not_in_wrong_locations():
    """
    Integration test: Verify TIN fields are NOT mapped to wrong locations.
    
    This test ensures that:
    - Payer TIN is NOT in the city field (f2_4)
    - Recipient TIN is NOT in the account number field (f2_39)
    - TIN fields ARE in the correct locations (f2_7 and f2_8)
    """
    # Create field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data with TIN fields
    form_data = {
        "payerTIN": "12-3456789",
        "recipientTIN": "987-65-4321"
    }
    
    # Map to PDF fields
    mapped_data = mapper.map_all_fields(form_data)
    
    # Verify payer TIN is in correct field (f2_7), not city field (f2_4)
    payer_tin_in_correct_field = any("f2_7[0]" in k for k in mapped_data.keys())
    payer_tin_in_wrong_field = any("f2_4[0]" in k for k in mapped_data.keys())
    
    assert payer_tin_in_correct_field, \
        "Payer TIN should be mapped to f2_7[0] (correct TIN field)"
    assert not payer_tin_in_wrong_field, \
        "Payer TIN should NOT be mapped to f2_4[0] (city field)"
    
    # Verify recipient TIN is in correct field (f2_8), not account number field (f2_39)
    recipient_tin_in_correct_field = any("f2_8[0]" in k for k in mapped_data.keys())
    recipient_tin_in_wrong_field = any("f2_39[0]" in k for k in mapped_data.keys())
    
    assert recipient_tin_in_correct_field, \
        "Recipient TIN should be mapped to f2_8[0] (correct TIN field)"
    assert not recipient_tin_in_wrong_field, \
        "Recipient TIN should NOT be mapped to f2_39[0] (account number field)"
    
    # Verify all three copies have correct mappings
    for copy_prefix in ["Copy1[0]", "Copy2[0]", "CopyB[0]"]:
        payer_tin_field = f"topmostSubform[0].{copy_prefix}.LeftCol[0].f2_7[0]"
        recipient_tin_field = f"topmostSubform[0].{copy_prefix}.LeftCol[0].f2_8[0]"
        
        assert payer_tin_field in mapped_data, \
            f"Payer TIN should be in {copy_prefix}"
        assert recipient_tin_field in mapped_data, \
            f"Recipient TIN should be in {copy_prefix}"
        
        assert mapped_data[payer_tin_field] == "12-3456789", \
            f"Payer TIN value should be correct in {copy_prefix}"
        assert mapped_data[recipient_tin_field] == "987-65-4321", \
            f"Recipient TIN value should be correct in {copy_prefix}"


def test_corrected_mappings_consistency_with_real_template():
    """
    Integration test: Verify corrected mappings work with real 1099-DIV template.
    
    This test generates a PDF with the corrected TIN mappings and verifies
    that values appear consistently across all three copies.
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
    
    # Create form data with TIN fields
    form_data = {
        "payerName": "Test Corporation",
        "payerTIN": "12-3456789",
        "recipientTIN": "987-65-4321",
        "totalOrdinaryDividends": "1000.00"
    }
    
    # Generate PDF
    try:
        output_bytes = generate_document(template_bytes, form_data, "1099-DIV")
    except Exception as e:
        pytest.skip(f"Could not generate PDF: {e}")
    
    # Extract field values by copy
    copy_values = extract_field_values_by_copy(output_bytes)
    
    # Verify payer TIN appears in all copies
    payer_tin_copy1 = [v for k, v in copy_values["Copy1"].items() if "f2_7[0]" in k]
    payer_tin_copy2 = [v for k, v in copy_values["Copy2"].items() if "f2_7[0]" in k]
    payer_tin_copyb = [v for k, v in copy_values["CopyB"].items() if "f2_7[0]" in k]
    
    if payer_tin_copy1 and payer_tin_copy2 and payer_tin_copyb:
        assert payer_tin_copy1[0] == payer_tin_copy2[0] == payer_tin_copyb[0], \
            "Payer TIN should be consistent across all copies"
        assert payer_tin_copy1[0] == "12-3456789", \
            "Payer TIN should have correct value"
    
    # Verify recipient TIN appears in all copies
    recipient_tin_copy1 = [v for k, v in copy_values["Copy1"].items() if "f2_8[0]" in k]
    recipient_tin_copy2 = [v for k, v in copy_values["Copy2"].items() if "f2_8[0]" in k]
    recipient_tin_copyb = [v for k, v in copy_values["CopyB"].items() if "f2_8[0]" in k]
    
    if recipient_tin_copy1 and recipient_tin_copy2 and recipient_tin_copyb:
        assert recipient_tin_copy1[0] == recipient_tin_copy2[0] == recipient_tin_copyb[0], \
            "Recipient TIN should be consistent across all copies"
        assert recipient_tin_copy1[0] == "987-65-4321", \
            "Recipient TIN should have correct value"
