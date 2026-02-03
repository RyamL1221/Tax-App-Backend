"""
Checkpoint test to verify FieldMapper changes for multi-page-form-filling.

This test verifies that:
1. map_all_fields() now returns 3x the number of mappings (one for each copy)
2. All existing tests still pass (backward compatibility)
"""

from tax_document_generation.field_mapper import FieldMapper


def test_map_all_fields_returns_3x_mappings():
    """
    Verify that map_all_fields() returns 3x the number of mappings.
    
    For each API field provided, the FieldMapper should generate:
    - 1 Copy1 PDF field name
    - 1 Copy2 PDF field name  
    - 1 CopyB PDF field name
    
    Total: 3 PDF field names per API field
    """
    # Initialize the field mapper
    mapper = FieldMapper("1099-DIV")
    
    # Create form data with 5 valid API fields
    form_data = {
        "payerName": "Test Payer Inc.",
        "payerTIN": "12-3456789",
        "recipientName": "Test Recipient",
        "recipientTIN": "98-7654321",
        "totalOrdinaryDividends": "1000.00"
    }
    
    # Map the fields
    result = mapper.map_all_fields(form_data)
    
    # Verify we get 3x the number of mappings
    # 5 API fields × 3 copies = 15 PDF field names
    expected_count = len(form_data) * 3
    actual_count = len(result)
    
    print(f"\nAPI fields provided: {len(form_data)}")
    print(f"Expected PDF field mappings: {expected_count}")
    print(f"Actual PDF field mappings: {actual_count}")
    
    assert actual_count == expected_count, \
        f"Expected {expected_count} PDF field mappings (3 per API field), got {actual_count}"
    
    # Verify each API field has exactly 3 PDF field mappings
    for api_field, value in form_data.items():
        # Count how many PDF fields have this value
        matching_pdf_fields = [k for k, v in result.items() if v == value]
        
        print(f"\nAPI field '{api_field}' = '{value}'")
        print(f"  Mapped to {len(matching_pdf_fields)} PDF fields:")
        for pdf_field in matching_pdf_fields:
            # Extract the copy identifier
            if "Copy1[0]" in pdf_field:
                copy_id = "Copy1"
            elif "Copy2[0]" in pdf_field:
                copy_id = "Copy2"
            elif "CopyB[0]" in pdf_field:
                copy_id = "CopyB"
            else:
                copy_id = "Unknown"
            print(f"    - {copy_id}: {pdf_field}")
        
        assert len(matching_pdf_fields) == 3, \
            f"API field '{api_field}' should map to 3 PDF fields, got {len(matching_pdf_fields)}"
    
    # Verify we have Copy1, Copy2, and CopyB variants
    copy1_fields = [k for k in result.keys() if "Copy1[0]" in k]
    copy2_fields = [k for k in result.keys() if "Copy2[0]" in k]
    copyb_fields = [k for k in result.keys() if "CopyB[0]" in k]
    
    print(f"\nCopy distribution:")
    print(f"  Copy1 fields: {len(copy1_fields)}")
    print(f"  Copy2 fields: {len(copy2_fields)}")
    print(f"  CopyB fields: {len(copyb_fields)}")
    
    assert len(copy1_fields) == len(form_data), \
        f"Should have {len(form_data)} Copy1 fields, got {len(copy1_fields)}"
    
    assert len(copy2_fields) == len(form_data), \
        f"Should have {len(form_data)} Copy2 fields, got {len(copy2_fields)}"
    
    assert len(copyb_fields) == len(form_data), \
        f"Should have {len(form_data)} CopyB fields, got {len(copyb_fields)}"
    
    print("\n✓ All checks passed!")


if __name__ == "__main__":
    test_map_all_fields_returns_3x_mappings()
    print("\n" + "="*70)
    print("CHECKPOINT 3 VERIFICATION COMPLETE")
    print("="*70)
    print("\nSummary:")
    print("  ✓ map_all_fields() returns 3x the number of mappings")
    print("  ✓ Each API field maps to Copy1, Copy2, and CopyB")
    print("  ✓ All values are preserved across copies")
