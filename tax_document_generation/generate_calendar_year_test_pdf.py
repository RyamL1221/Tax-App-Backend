"""
Generate test PDF with calendar year 2024 for manual verification.

This script generates a 1099-DIV PDF with calendar year "2024" to verify
that the calendar year rendering fix is working correctly.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from document_generator import generate_document

def main():
    """Generate test PDF with calendar year 2024."""
    
    # Load the 1099-DIV template
    template_path = "samples/1099-DIV.pdf"
    
    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        return 1
    
    with open(template_path, 'rb') as f:
        template_bytes = f.read()
    
    # Minimal form data with calendar year
    form_data = {
        'calendarYear': '2024',
        'payerName': 'Test Corporation',
        'payerTIN': '12-3456789',
        'recipientName': 'John Doe',
        'recipientTIN': '987-65-4321',
        'totalOrdinaryDividends': '1000.00'
    }
    
    print("Generating PDF with calendar year 2024...")
    print(f"Form data: {form_data}")
    
    try:
        # Generate the PDF
        output_bytes = generate_document(
            template=template_bytes,
            form_data=form_data,
            document_type="1099-DIV"
        )
        
        # Save to samples directory
        output_path = "samples/calendar-year-test-2024.pdf"
        with open(output_path, 'wb') as f:
            f.write(output_bytes)
        
        print(f"\n✅ PDF generated successfully!")
        print(f"📄 Saved to: {output_path}")
        print(f"📊 Size: {len(output_bytes)} bytes")
        print("\nPlease open the PDF in Adobe Reader and verify:")
        print("  1. Calendar year '2024' appears on all 4 copies")
        print("  2. Calendar year is visible and readable")
        print("  3. All other fields are populated correctly")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
