"""
Diagnostic script to inspect calendar year fields in the 1099-DIV PDF template.

This script extracts detailed information about the calendar year fields to help
debug why they are not being filled in the generated PDF.
"""

import fitz  # PyMuPDF
import os


def inspect_calendar_year_fields():
    """Inspect calendar year fields in the PDF template."""
    
    # Path to template
    template_path = os.path.join(os.path.dirname(__file__), '..', 'samples', '1099-DIV.pdf')
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"📄 Opening template: {template_path}\n")
    
    # Open PDF
    doc = fitz.open(template_path)
    
    # Expected calendar year field names
    expected_fields = [
        "topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]",
        "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]",
        "topmostSubform[0].Copy2[0].CopyHeader[0].CalendarYear[0].f2_1[0]",
        "topmostSubform[0].CopyB[0].CopyHeader[0].CalendarYear[0].f2_1[0]",
    ]
    
    print("="*80)
    print("CALENDAR YEAR FIELD INSPECTION")
    print("="*80)
    
    found_fields = []
    
    # Iterate through all pages
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = list(page.widgets())
        
        for widget in widgets:
            field_name = widget.field_name
            
            # Check if this is a calendar year field
            if field_name and "CalendarYear[0]" in field_name:
                found_fields.append(field_name)
                
                print(f"\n📍 Found Calendar Year Field on Page {page_num + 1}")
                print(f"   Field Name: {field_name}")
                print(f"   Field Type: {widget.field_type} ({widget.field_type_string})")
                print(f"   Position: ({widget.rect.x0:.2f}, {widget.rect.y0:.2f})")
                print(f"   Dimensions: {widget.rect.width:.2f} x {widget.rect.height:.2f} points")
                print(f"   Field Value: '{widget.field_value}'")
                print(f"   Field Flags: {widget.field_flags}")
                
                # Check for hidden/readonly flags
                is_hidden = widget.field_flags & (1 << 1)  # Bit 1 = Hidden
                is_readonly = widget.field_flags & (1 << 0)  # Bit 0 = ReadOnly
                
                if is_hidden:
                    print(f"   ⚠️  WARNING: Field is HIDDEN")
                if is_readonly:
                    print(f"   ⚠️  WARNING: Field is READ-ONLY")
                
                # Get text properties
                try:
                    print(f"   Text Font: {widget.text_font}")
                    print(f"   Text Font Size: {widget.text_fontsize}")
                    print(f"   Text Color: {widget.text_color}")
                except:
                    print(f"   Text Properties: Not available")
                
                # Check if field name matches expected
                if field_name in expected_fields:
                    print(f"   ✅ Field name matches expected mapping")
                else:
                    print(f"   ❌ Field name does NOT match expected mapping")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Expected fields: {len(expected_fields)}")
    print(f"Found fields: {len(found_fields)}")
    
    if len(found_fields) == len(expected_fields):
        print("✅ All expected calendar year fields found in PDF")
    else:
        print("❌ Mismatch between expected and found fields")
    
    print("\nExpected field names:")
    for field in expected_fields:
        if field in found_fields:
            print(f"  ✅ {field}")
        else:
            print(f"  ❌ {field} (NOT FOUND)")
    
    print("\nFound field names:")
    for field in found_fields:
        if field in expected_fields:
            print(f"  ✅ {field}")
        else:
            print(f"  ⚠️  {field} (UNEXPECTED)")
    
    doc.close()


if __name__ == "__main__":
    inspect_calendar_year_fields()
