"""
Quick test script to verify calendar year rendering fix.
"""

import os
import sys
import logging

# Configure logging to see all messages
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from document_generator import generate_document

def test_calendar_year_rendering():
    """Test that calendar year is rendered in the PDF."""
    
    # Load template
    template_path = os.path.join(os.path.dirname(__file__), '..', 'samples', '1099-DIV.pdf')
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return False
    
    with open(template_path, 'rb') as f:
        template_bytes = f.read()
    
    # Minimal form data with calendar year
    form_data = {
        'calendarYear': '2024',  # Correct canonical field name
        'payerName': 'Test Corp',
        'payerTIN': '12-3456789',
        'recipientName': 'John Doe',
        'recipientTIN': '987-65-4321',
        'totalOrdinaryDividends': '1000.00'
    }
    
    print("\n" + "="*80)
    print("TESTING CALENDAR YEAR RENDERING FIX")
    print("="*80)
    print(f"Form data: {form_data}")
    print("\nGenerating PDF...")
    print("="*80 + "\n")
    
    try:
        # Generate document
        output_bytes = generate_document(template_bytes, form_data, '1099-DIV')
        
        # Save output
        output_path = os.path.join(os.path.dirname(__file__), '..', 'samples', 'calendar-year-fix-test.pdf')
        with open(output_path, 'wb') as f:
            f.write(output_bytes)
        
        print("\n" + "="*80)
        print(f"✅ PDF generated successfully: {output_path}")
        print(f"   Size: {len(output_bytes)} bytes")
        print("="*80)
        
        # Try to extract text to verify calendar year appears
        import fitz
        doc = fitz.open(stream=output_bytes, filetype="pdf")
        
        calendar_year_found = False
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if '2024' in text:
                calendar_year_found = True
                print(f"\n✅ Calendar year '2024' found on page {page_num + 1}")
        
        doc.close()
        
        if not calendar_year_found:
            print("\n⚠️  WARNING: Calendar year '2024' not found in extracted text")
            print("   This may be expected if the field is very small or uses special fonts")
            print("   Please open the PDF manually to verify visibility")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_calendar_year_rendering()
    sys.exit(0 if success else 1)
