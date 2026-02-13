#!/usr/bin/env python3
"""
Detailed inspection of LeftCol fields to find recipient name.
"""

from inspect_pdf_fields import extract_field_info


def main():
    pdf_path = "../samples/SAMPLE-1099-DIV-MULTI-COPY.pdf"
    
    print("="*80)
    print("DETAILED LEFTCOL FIELD INSPECTION")
    print("="*80)
    print()
    
    # Extract all fields
    fields = extract_field_info(pdf_path)
    
    # Filter to Copy1 LeftCol fields only
    copy1_leftcol = [f for f in fields if f.form_copy == "Copy1" and f.column == "LeftCol"]
    
    print(f"Found {len(copy1_leftcol)} fields in Copy1 LeftCol")
    print()
    
    # Display each field with detailed nearby text
    for i, field in enumerate(copy1_leftcol, 1):
        print(f"{i}. {field.name}")
        print(f"   Position: x={field.rect[0]:.1f}, y={field.rect[1]:.1f}")
        print(f"   Dimensions: {field.rect[2]:.1f} × {field.rect[3]:.1f}")
        print(f"   Nearby text (all): {', '.join(field.nearby_text)}")
        
        # Check if nearby text contains "RECIPIENT" and "name"
        nearby_lower = ' '.join(field.nearby_text).lower()
        if 'recipient' in nearby_lower and 'name' in nearby_lower:
            print(f"   ★★★ CONTAINS 'RECIPIENT' AND 'name' ★★★")
        elif 'recipient' in nearby_lower:
            print(f"   ★ CONTAINS 'RECIPIENT' ★")
        
        print()
    
    print("="*80)
    print("ANALYSIS")
    print("="*80)
    print()
    
    # Based on IRS 1099-DIV form structure:
    # - f2_2: Payer's name (large field at top)
    # - f2_3: Payer's street address (left half)
    # - f2_4: Payer's city/state/ZIP (right half)
    # - f2_5: ??? (below payer address)
    # - f2_6: ??? (below f2_5)
    # - f2_7: Payer's TIN (confirmed correct)
    # - f2_8: Recipient's TIN (confirmed correct)
    
    print("Expected IRS 1099-DIV structure:")
    print("  - Payer's name (top)")
    print("  - Payer's street address")
    print("  - Payer's city, state, ZIP")
    print("  - Payer's TIN")
    print("  - RECIPIENT'S name")
    print("  - Recipient's street address")
    print("  - Recipient's city, state, ZIP")
    print("  - RECIPIENT'S TIN")
    print()
    
    print("Likely field assignments:")
    print("  f2_2[0] = Payer's name")
    print("  f2_3[0] = Payer's street address (left)")
    print("  f2_4[0] = Payer's city/state/ZIP (right)")
    print("  f2_5[0] = ??? (candidate for recipient name)")
    print("  f2_6[0] = ??? (candidate for recipient address)")
    print("  f2_7[0] = Payer's TIN ✓")
    print("  f2_8[0] = Recipient's TIN ✓")
    print()
    
    # Check f2_5 specifically
    f2_5 = next((f for f in copy1_leftcol if 'f2_5[0]' in f.name), None)
    if f2_5:
        print("Detailed analysis of f2_5[0]:")
        print(f"  Position: y={f2_5.rect[1]:.1f} (between payer address and payer TIN)")
        print(f"  Dimensions: {f2_5.rect[2]:.1f} × {f2_5.rect[3]:.1f}")
        nearby_text = ' '.join(f2_5.nearby_text)
        if 'RECIPIENT' in nearby_text:
            print(f"  ✓ Contains 'RECIPIENT' in nearby text")
        if 'name' in nearby_text.lower():
            print(f"  ✓ Contains 'name' in nearby text")
        print()


if __name__ == "__main__":
    main()
