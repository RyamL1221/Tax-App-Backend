"""
Check the structure of the PDF to see which pages have which copies.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    import pymupdf as fitz
except ImportError:
    import fitz

pdf_path = "samples/debug-calendar-year-2024.pdf"

if not os.path.exists(pdf_path):
    print(f"Error: PDF not found at {pdf_path}")
    sys.exit(1)

print(f"Opening PDF: {pdf_path}")
doc = fitz.open(pdf_path)

print(f"\nPDF has {len(doc)} pages\n")

# Check each page for copy identifiers
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    
    # Look for copy identifiers in the text
    copy_type = "Unknown"
    if "Copy A" in text or "COPY A" in text:
        copy_type = "CopyA"
    elif "Copy 1" in text or "COPY 1" in text:
        copy_type = "Copy1"
    elif "Copy B" in text or "COPY B" in text:
        copy_type = "CopyB"
    elif "Copy 2" in text or "COPY 2" in text:
        copy_type = "Copy2"
    
    # Check for calendar year field
    has_calendar_field = False
    widgets = list(page.widgets())
    for widget in widgets:
        if widget.field_name and "CalendarYear" in widget.field_name:
            has_calendar_field = True
            print(f"Page {page_num + 1}: {copy_type} - Has calendar year field: {widget.field_name}")
            break
    
    if not has_calendar_field:
        print(f"Page {page_num + 1}: {copy_type} - No calendar year field")

doc.close()
