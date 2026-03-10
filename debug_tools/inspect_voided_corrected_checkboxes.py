"""
Inspect VOIDED and CORRECTED checkbox fields in 1099-DIV PDF template.

This script examines the checkbox fields in the PDF template to verify:
- Field names match the mappings in canonical_div_1099.py
- Field types are checkboxes
- Field flags (READ-ONLY, HIDDEN) that might prevent modification
- Checkbox dimensions and positions
- Checkbox on_state values

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

import pymupdf as fitz


def inspect_voided_corrected_checkboxes():
    """Inspect VOIDED and CORRECTED checkbox fields in the PDF template."""
    template_path = "samples/1099-DIV.pdf"
    doc = fitz.open(template_path)
    
    # Expected field names based on canonical_div_1099.py mappings
    checkbox_fields = [
        # CopyA (Page 2)
        "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[0]",  # VOIDED
        "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[1]",  # CORRECTED
        # Copy1 (Page 3)
        "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]",  # VOIDED
        "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[1]",  # CORRECTED
        # CopyB (Page 4) - CORRECTED only, no VOIDED
        "topmostSubform[0].CopyB[0].CopyHeader[0].c2_1[0]",  # CORRECTED
        # Copy2 (Page 6)
        "topmostSubform[0].Copy2[0].CopyHeader[0].c2_1[0]",  # VOIDED
        "topmostSubform[0].Copy2[0].CopyHeader[0].c2_1[1]",  # CORRECTED
    ]
    
    # Map field names to their purpose
    field_purposes = {
        "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[0]": "CopyA VOIDED",
        "topmostSubform[0].CopyA[0].CopyHeader[0].c1_1[1]": "CopyA CORRECTED",
        "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]": "Copy1 VOIDED",
        "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[1]": "Copy1 CORRECTED",
        "topmostSubform[0].CopyB[0].CopyHeader[0].c2_1[0]": "CopyB CORRECTED",
        "topmostSubform[0].Copy2[0].CopyHeader[0].c2_1[0]": "Copy2 VOIDED",
        "topmostSubform[0].Copy2[0].CopyHeader[0].c2_1[1]": "Copy2 CORRECTED",
    }
    
    print("=" * 80)
    print("VOIDED AND CORRECTED CHECKBOX INSPECTION")
    print("=" * 80)
    print(f"\nTemplate: {template_path}")
    print(f"Total pages: {len(doc)}")
    print(f"\nExpected checkbox fields: {len(checkbox_fields)}")
    print("=" * 80)
    
    found_fields = []
    
    # Scan all pages for checkbox fields
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = list(page.widgets())
        
        for widget in widgets:
            field_name = widget.field_name
            if field_name in checkbox_fields:
                found_fields.append(field_name)
                purpose = field_purposes.get(field_name, "Unknown")
                
                print(f"\n{'=' * 80}")
                print(f"Page {page_num + 1}: {purpose}")
                print(f"{'=' * 80}")
                print(f"Field Name: {field_name}")
                print(f"Field Type: {widget.field_type} (2 = checkbox)")
                print(f"Field Flags: {widget.field_flags}")
                print(f"  Is READ-ONLY: {bool(widget.field_flags & (1 << 0))}")
                print(f"  Is HIDDEN: {bool(widget.field_flags & (1 << 1))}")
                print(f"  Is REQUIRED: {bool(widget.field_flags & (1 << 2))}")
                print(f"Rectangle: {widget.rect}")
                print(f"Dimensions: {widget.rect.width:.1f}x{widget.rect.height:.1f} points")
                print(f"Position: x={widget.rect.x0:.1f}, y={widget.rect.y0:.1f}")
                
                # Try to get on_state
                try:
                    if hasattr(widget, 'on_state'):
                        on_state = widget.on_state()
                        print(f"On State: {on_state}")
                    else:
                        print(f"On State: Method not available")
                except Exception as e:
                    print(f"On State: Unable to determine ({type(e).__name__})")
                
                # Get current field value
                try:
                    current_value = widget.field_value
                    print(f"Current Value: {current_value}")
                except Exception as e:
                    print(f"Current Value: Unable to read ({type(e).__name__})")
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Expected fields: {len(checkbox_fields)}")
    print(f"Found fields: {len(found_fields)}")
    
    if len(found_fields) == len(checkbox_fields):
        print("✅ All expected checkbox fields found!")
    else:
        print("⚠️  Some checkbox fields are missing!")
        missing = set(checkbox_fields) - set(found_fields)
        if missing:
            print("\nMissing fields:")
            for field in missing:
                purpose = field_purposes.get(field, "Unknown")
                print(f"  - {purpose}: {field}")
    
    # Compare with FATCA checkbox (which works)
    print(f"\n{'=' * 80}")
    print("COMPARISON WITH FATCA CHECKBOX (WORKING REFERENCE)")
    print(f"{'=' * 80}")
    
    fatca_field = "topmostSubform[0].CopyA[0].LeftCol[0].c1_2[0]"
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = list(page.widgets())
        
        for widget in widgets:
            if widget.field_name == fatca_field:
                print(f"\nFATCA Checkbox (CopyA):")
                print(f"Field Name: {widget.field_name}")
                print(f"Field Type: {widget.field_type}")
                print(f"Field Flags: {widget.field_flags}")
                print(f"  Is READ-ONLY: {bool(widget.field_flags & (1 << 0))}")
                print(f"  Is HIDDEN: {bool(widget.field_flags & (1 << 1))}")
                print(f"Dimensions: {widget.rect.width:.1f}x{widget.rect.height:.1f} points")
                
                try:
                    if hasattr(widget, 'on_state'):
                        on_state = widget.on_state()
                        print(f"On State: {on_state}")
                except:
                    pass
                
                break
    
    doc.close()
    
    print(f"\n{'=' * 80}")
    print("INSPECTION COMPLETE")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    inspect_voided_corrected_checkboxes()
