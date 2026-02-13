"""
Verify the debug PDF has calendar year in text.
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

# Check text on each copy page
# Note: Page 1 is instructions, actual forms start on page 2
copy_pages = {
    1: 'CopyA',  # Page 2
    2: 'Copy1',  # Page 3
    3: 'CopyB',  # Page 4
    5: 'Copy2'   # Page 6
}

print(f"\nChecking for '2024' in text (excluding 'Rev. January 2024'):\n")

for page_num, copy_name in copy_pages.items():
    if page_num >= len(doc):
        continue
    
    page = doc[page_num]
    text_dict = page.get_text("dict")
    
    found_2024 = False
    for block in text_dict.get("blocks", []):
        if "lines" in block:
            for line in block["lines"]:
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if "2024" in text and "Rev" not in text:
                        bbox = span.get("bbox", [])
                        print(f"✅ Page {page_num + 1} ({copy_name}): Found '2024' at position {bbox}")
                        print(f"   Text: '{text}'")
                        found_2024 = True
                        break
                if found_2024:
                    break
        if found_2024:
            break
    
    if not found_2024:
        print(f"❌ Page {page_num + 1} ({copy_name}): '2024' not found in text")

doc.close()
