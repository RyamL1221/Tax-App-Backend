"""
Test calendar year field mapping.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from field_mapper import FieldMapper

def main():
    """Test calendar year mapping."""
    
    mapper = FieldMapper("1099-DIV")
    
    form_data = {
        'calendarYear': '2024'
    }
    
    print("Testing calendar year mapping...")
    print(f"Input: {form_data}")
    print()
    
    # Map single field
    pdf_field = mapper.map_field('calendarYear')
    print(f"Single field mapping:")
    print(f"  'calendarYear' -> '{pdf_field}'")
    print()
    
    # Map all fields
    mapped_data = mapper.map_all_fields(form_data)
    print(f"All fields mapping (should generate 4 variants):")
    for pdf_field_name, value in mapped_data.items():
        print(f"  '{pdf_field_name}' = '{value}'")
    print()
    
    print(f"Total mapped fields: {len(mapped_data)}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
