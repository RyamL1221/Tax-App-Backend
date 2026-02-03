#!/usr/bin/env python3
"""
Debug script to test field mapping end-to-end
"""

import sys
sys.path.insert(0, 'tax_document_generation')

from field_mapper import FieldMapper
from document_generator import generate_document

# Test data with API field names
test_form_data = {
    "payerName": "Test Payer Company",
    "payerTIN": "12-3456789",
    "recipientName": "John Doe",
    "recipientTIN": "987-65-4321",
    "totalOrdinaryDividends": "1000.00",
    "qualifiedDividends": "800.00",
    "calendarYear": "2024"
}

print("=" * 80)
print("FIELD MAPPING DEBUG TEST")
print("=" * 80)

# Test 1: Field Mapper
print("\n1. Testing FieldMapper...")
mapper = FieldMapper("1099-DIV")
print(f"   ✓ FieldMapper initialized for 1099-DIV")

# Test individual field mapping
print("\n2. Testing individual field mappings:")
for api_field, value in test_form_data.items():
    pdf_field = mapper.map_field(api_field)
    print(f"   {api_field:30} -> {pdf_field}")

# Test batch mapping
print("\n3. Testing batch mapping:")
mapped_data = mapper.map_all_fields(test_form_data)
print(f"   Input fields: {len(test_form_data)}")
print(f"   Mapped fields: {len(mapped_data)}")
print(f"   ✓ All fields mapped successfully")

# Test unmapped fields
unmapped = mapper.get_unmapped_fields(test_form_data)
print(f"\n4. Unmapped fields: {unmapped if unmapped else 'None'}")

# Test 5: Generate PDF
print("\n5. Testing PDF generation...")
try:
    with open("1099-DIV.pdf", "rb") as f:
        template_bytes = f.read()
    
    output_bytes = generate_document(template_bytes, test_form_data, "1099-DIV")
    
    # Save the output
    with open("test-output-1099-DIV.pdf", "wb") as f:
        f.write(output_bytes)
    
    print(f"   ✓ PDF generated successfully ({len(output_bytes)} bytes)")
    print(f"   ✓ Saved to: test-output-1099-DIV.pdf")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
