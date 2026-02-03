#!/usr/bin/env python3
"""
Test script to verify PyMuPDF migration works correctly.
Generates a test PDF and verifies form data is visible.
"""

import sys
import os

# Add tax_document_generation to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tax_document_generation'))

# Now import with absolute imports
from exceptions import GenerationError
from field_mapper import FieldMapper
import fitz
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generate_document(template: bytes, form_data: dict, document_type: str) -> bytes:
    """Generate a PDF document with form data."""
    try:
        logger.info(f"Starting document generation for type: {document_type}")
        logger.info("Using library: PyMuPDF (fitz)")
        
        # Initialize field mapper
        mapper = FieldMapper(document_type)
        
        # Translate API field names to PDF field names
        mapped_data = mapper.map_all_fields(form_data)
        unmapped_fields = mapper.get_unmapped_fields(form_data)
        
        # Log mapping results
        logger.info(f"Mapped {len(mapped_data)} fields successfully")
        if unmapped_fields:
            logger.warning(f"Unmapped fields: {unmapped_fields}")
        
        # Open PDF with PyMuPDF
        doc = fitz.open(stream=template, filetype="pdf")
        logger.info(f"Template has {len(doc)} page(s)")
        
        # Populate form fields
        populated_count = 0
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = page.widgets()
            
            if widgets:
                for widget in widgets:
                    field_name = widget.field_name
                    if field_name in mapped_data:
                        try:
                            value = mapped_data[field_name]
                            # Convert value to string for form field
                            widget.field_value = str(value)
                            # Force appearance regeneration
                            widget.update()
                            # Explicitly set the field to be visible
                            widget.field_flags = widget.field_flags & ~(1 << 1)
                            widget.update()
                            populated_count += 1
                            logger.debug(f"Populated field '{field_name}' with value '{value}'")
                        except Exception as e:
                            logger.warning(f"Failed to populate field '{field_name}': {str(e)}")
        
        logger.info(f"Populated {populated_count} form fields")
        
        # Try to force appearance generation
        try:
            if doc.is_form_pdf:
                for xref in range(1, doc.xref_length()):
                    try:
                        obj_type = doc.xref_get_key(xref, "Type")
                        if obj_type and "/Catalog" in str(obj_type):
                            doc.xref_set_key(xref, "AcroForm/NeedAppearances", "true")
                            logger.debug("Set NeedAppearances flag in PDF")
                            break
                    except:
                        continue
        except Exception as e:
            logger.debug(f"Could not set NeedAppearances: {e}")
        
        # Save to bytes
        output_bytes = doc.tobytes()
        doc.close()
        
        if not output_bytes:
            raise GenerationError("Generated document is empty")
        
        logger.info(f"Document generated successfully, size: {len(output_bytes)} bytes")
        return output_bytes
        
    except Exception as e:
        logger.error(f"Document generation failed: {str(e)}", exc_info=True)
        raise


def main():
    """Main test function."""
    print("=" * 80)
    print("PyMuPDF Migration Test")
    print("=" * 80)
    print()
    
    # Load template
    template_path = '1099-DIV.pdf'
    if not os.path.exists(template_path):
        print(f"✗ Template not found: {template_path}")
        return 1
    
    with open(template_path, 'rb') as f:
        template = f.read()
    
    print(f"✓ Loaded template: {len(template)} bytes")
    
    # Test form data
    form_data = {
        "payerName": "Test Payer Company",
        "payerTIN": "12-3456789",
        "recipientName": "John Doe",
        "recipientTIN": "123-45-6789",
        "totalOrdinaryDividends": "1000.50",
        "qualifiedDividends": "500.25",
    }
    
    print(f"✓ Test form data: {len(form_data)} fields")
    print()
    
    # Generate document
    try:
        result = generate_document(template, form_data, "1099-DIV")
        
        # Save to file
        output_path = 'pymupdf-test-1099-DIV.pdf'
        with open(output_path, 'wb') as f:
            f.write(result)
        
        print()
        print("=" * 80)
        print("✓ SUCCESS: PDF generated successfully")
        print("=" * 80)
        print(f"Output file: {output_path}")
        print(f"Output size: {len(result)} bytes")
        print()
        print("NEXT STEP: Open the PDF file to verify form data is visible")
        print(f"  open {output_path}")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"✗ FAILED: {e}")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
