"""
Debug calendar year generation with detailed logging.
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s'
)

from document_generator import generate_document
from field_mapper import FieldMapper

def main():
    """Generate test PDF with detailed logging."""
    
    # Load the 1099-DIV template
    template_path = "samples/1099-DIV.pdf"
    
    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        return 1
    
    with open(template_path, 'rb') as f:
        template_bytes = f.read()
    
    # Test with ONLY calendar year
    form_data = {
        'calendarYear': '2024'
    }
    
    print("="*80)
    print("TESTING CALENDAR YEAR MAPPING")
    print("="*80)
    
    # First, test the mapping
    mapper = FieldMapper("1099-DIV")
    mapped_data = mapper.map_all_fields(form_data)
    
    print(f"\nMapped {len(mapped_data)} fields:")
    for field_name, value in mapped_data.items():
        print(f"  '{field_name}' = '{value}'")
    
    print("\n" + "="*80)
    print("GENERATING PDF")
    print("="*80 + "\n")
    
    try:
        # Generate the PDF
        output_bytes = generate_document(
            template=template_bytes,
            form_data=form_data,
            document_type="1099-DIV"
        )
        
        # Save to samples directory
        output_path = "samples/debug-calendar-year-2024.pdf"
        with open(output_path, 'wb') as f:
            f.write(output_bytes)
        
        print(f"\n✅ PDF generated successfully!")
        print(f"📄 Saved to: {output_path}")
        print(f"📊 Size: {len(output_bytes)} bytes")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
