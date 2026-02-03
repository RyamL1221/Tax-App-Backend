#!/usr/bin/env python3
"""
Script to inspect PDF form fields in the 1099-DIV template
"""

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

def inspect_pdf_fields(pdf_path):
    """Inspect and print all form fields in a PDF"""
    reader = PdfReader(pdf_path)
    
    print(f"PDF: {pdf_path}")
    print(f"Pages: {len(reader.pages)}")
    print()
    
    fields = reader.get_fields()
    
    if not fields:
        print("No form fields found in this PDF!")
        return
    
    print(f"Total form fields: {len(fields)}")
    print("\nField Names:")
    print("-" * 80)
    
    for field_name, field_obj in sorted(fields.items()):
        field_type = field_obj.get('/FT', 'Unknown')
        field_value = field_obj.get('/V', '')
        print(f"  {field_name}")
        print(f"    Type: {field_type}")
        if field_value:
            print(f"    Default Value: {field_value}")
        print()

if __name__ == "__main__":
    inspect_pdf_fields("1099-DIV.pdf")
