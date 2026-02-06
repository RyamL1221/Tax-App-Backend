"""
Inspect the generated PDF to see what values are in the calendar year fields.

This script opens the generated PDF and checks the actual field values
(not just text extraction) to see if the calendar year fields were populated.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    import pymupdf as fitz
except ImportError:
    import fitz

def main():
    """Inspect calendar year fields in generated PDF."""
    
    pdf_path = "samples/calendar-year-test-2024.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return 1
    
    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    print(f"PDF has {len(doc)} pages\n")
    
    # Look for calendar year fields
    calendar_year_fields = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = list(page.widgets())
        
        for widget in widgets:
            field_name = widget.field_name
            if field_name and "CalendarYear" in field_name:
                calendar_year_fields.append({
                    'page': page_num + 1,
                    'field_name': field_name,
                    'field_value': widget.field_value,
                    'field_type': widget.field_type,
                    'rect': widget.rect
                })
    
    if not calendar_year_fields:
        print("⚠️  No calendar year fields found in PDF")
        print("This means the fields were successfully flattened (converted to static text)")
        print("\nLet's check if '2024' appears in the text near the expected location...")
        
        # Check text on each copy page
        copy_pages = {
            0: 'CopyA',
            1: 'Copy1',
            3: 'CopyB',
            5: 'Copy2'
        }
        
        for page_num, copy_name in copy_pages.items():
            if page_num >= len(doc):
                continue
            
            page = doc[page_num]
            
            # Get text with position information
            text_dict = page.get_text("dict")
            
            # Look for "2024" in the text blocks
            found_2024 = False
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            text = span.get("text", "")
                            if "2024" in text and "Rev" not in text:  # Exclude "Rev. January 2024"
                                bbox = span.get("bbox", [])
                                print(f"✅ Page {page_num + 1} ({copy_name}): Found '2024' at position {bbox}")
                                found_2024 = True
                                break
                        if found_2024:
                            break
                if found_2024:
                    break
            
            if not found_2024:
                print(f"❌ Page {page_num + 1} ({copy_name}): '2024' not found in text")
    else:
        print(f"Found {len(calendar_year_fields)} calendar year fields:\n")
        
        for field in calendar_year_fields:
            print(f"Page {field['page']}: {field['field_name']}")
            print(f"  Value: '{field['field_value']}'")
            print(f"  Type: {field['field_type']}")
            print(f"  Position: {field['rect']}")
            print()
    
    doc.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
