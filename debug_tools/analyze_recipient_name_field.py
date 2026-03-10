#!/usr/bin/env python3
"""
Analyze the recipient name field mapping for 1099-DIV form.

This script uses the visual field mapper to identify the correct field
for recipient name and compares it to the current mapping.
"""

import sys
from inspect_pdf_fields import extract_field_info, FieldInfo as InspectFieldInfo
from visual_field_mapper import VisualFieldMapper, FieldPurpose, FieldInfo as MapperFieldInfo


def convert_field_info(inspect_field: InspectFieldInfo) -> MapperFieldInfo:
    """Convert FieldInfo from inspect script to visual mapper format."""
    return MapperFieldInfo(
        name=inspect_field.name,
        page_num=inspect_field.page_num,
        rect=inspect_field.rect,
        field_type=inspect_field.field_type,
        column=inspect_field.column,
        nearby_text=inspect_field.nearby_text
    )


def main():
    pdf_path = "../samples/SAMPLE-1099-DIV-MULTI-COPY.pdf"
    
    print("="*80)
    print("RECIPIENT NAME FIELD ANALYSIS")
    print("="*80)
    print()
    
    # Extract all fields
    print("Extracting fields from PDF...")
    fields = extract_field_info(pdf_path)
    print(f"Found {len(fields)} fields")
    print()
    
    # Filter to Copy1 fields only
    copy1_fields = [f for f in fields if f.form_copy == "Copy1"]
    print(f"Copy1 has {len(copy1_fields)} fields")
    print()
    
    # Initialize visual field mapper
    mapper = VisualFieldMapper()
    
    # Find all fields that could be recipient name
    print("Analyzing fields for recipient name purpose...")
    print()
    
    recipient_name_candidates = []
    
    for field in copy1_fields:
        # Convert to mapper format
        mapper_field = convert_field_info(field)
        
        # Identify purpose
        purpose = mapper.identify_field_purpose(mapper_field)
        
        if purpose == FieldPurpose.RECIPIENT_NAME:
            recipient_name_candidates.append((field, purpose))
            print(f"✓ CANDIDATE FOUND:")
            print(f"  Field: {field.name}")
            print(f"  Column: {field.column}")
            print(f"  Position: x={field.rect[0]:.1f}, y={field.rect[1]:.1f}")
            print(f"  Dimensions: {field.rect[2]:.1f} × {field.rect[3]:.1f}")
            print(f"  Nearby text: {', '.join(field.nearby_text[:5])}")
            print()
    
    # Check current mapping
    print("="*80)
    print("CURRENT MAPPING ANALYSIS")
    print("="*80)
    print()
    
    current_mapping = "topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]"
    print(f"Current mapping: recipientName → {current_mapping}")
    print()
    
    # Find the currently mapped field
    current_field = None
    for field in copy1_fields:
        if field.name == current_mapping:
            current_field = field
            break
    
    if current_field:
        print("Current field details:")
        print(f"  Field: {current_field.name}")
        print(f"  Column: {current_field.column}")
        print(f"  Position: x={current_field.rect[0]:.1f}, y={current_field.rect[1]:.1f}")
        print(f"  Dimensions: {current_field.rect[2]:.1f} × {current_field.rect[3]:.1f}")
        print(f"  Nearby text: {', '.join(current_field.nearby_text[:10])}")
        print()
        
        # Identify what this field actually is
        mapper_field = convert_field_info(current_field)
        actual_purpose = mapper.identify_field_purpose(mapper_field)
        print(f"  Identified purpose: {actual_purpose.value}")
        print()
        
        if actual_purpose != FieldPurpose.RECIPIENT_NAME:
            print("⚠️  WARNING: Current mapping is NOT identified as recipient name!")
            print(f"   It appears to be: {actual_purpose.value}")
            print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    
    if len(recipient_name_candidates) == 0:
        print("❌ NO recipient name field found in Copy1!")
        print("   This suggests recipient name may not have a dedicated field,")
        print("   or it may be in an unexpected location.")
    elif len(recipient_name_candidates) == 1:
        field, purpose = recipient_name_candidates[0]
        if field.name == current_mapping:
            print("✅ Current mapping is CORRECT!")
            print(f"   {current_mapping} is the recipient name field")
        else:
            print("❌ Current mapping is INCORRECT!")
            print(f"   Current: {current_mapping}")
            print(f"   Correct: {field.name}")
            print()
            print("RECOMMENDATION:")
            print(f"   Update recipientName mapping to: {field.name}")
    else:
        print(f"⚠️  Multiple recipient name candidates found ({len(recipient_name_candidates)})")
        print("   Manual verification required:")
        for field, purpose in recipient_name_candidates:
            print(f"   - {field.name} ({field.column})")
    
    print()


if __name__ == "__main__":
    main()
