"""
Verify that calendar year appears in the generated PDF.

This script extracts text from the generated PDF and checks if "2024"
appears on all four copy pages.
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
    """Verify calendar year in generated PDF."""
    
    pdf_path = "samples/calendar-year-test-2024.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return 1
    
    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    print(f"PDF has {len(doc)} pages")
    
    # Pages where calendar year should appear:
    # Page 1 (index 0): CopyA
    # Page 2 (index 1): Copy1
    # Page 4 (index 3): CopyB
    # Page 6 (index 5): Copy2
    
    copy_pages = {
        0: 'CopyA',
        1: 'Copy1',
        3: 'CopyB',
        5: 'Copy2'
    }
    
    results = {}
    
    for page_num, copy_name in copy_pages.items():
        if page_num >= len(doc):
            print(f"⚠️  Page {page_num + 1} ({copy_name}) not found in PDF")
            results[copy_name] = False
            continue
        
        page = doc[page_num]
        text = page.get_text()
        
        # Check if "2024" appears in the text
        has_2024 = "2024" in text
        
        results[copy_name] = has_2024
        
        if has_2024:
            print(f"✅ Page {page_num + 1} ({copy_name}): Calendar year '2024' found")
        else:
            print(f"❌ Page {page_num + 1} ({copy_name}): Calendar year '2024' NOT found")
        
        # Show a snippet of text around "2024" if found
        if has_2024:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if '2024' in line:
                    print(f"   Context: {line.strip()}")
                    break
    
    doc.close()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    all_found = all(results.values())
    found_count = sum(results.values())
    total_count = len(results)
    
    print(f"Calendar year found on {found_count}/{total_count} copies")
    
    for copy_name, found in results.items():
        status = "✅" if found else "❌"
        print(f"  {status} {copy_name}")
    
    if all_found:
        print("\n🎉 SUCCESS: Calendar year appears on all 4 copies!")
        return 0
    else:
        print("\n⚠️  WARNING: Calendar year missing from some copies")
        return 1

if __name__ == '__main__':
    sys.exit(main())
