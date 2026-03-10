#!/usr/bin/env python3
"""
Test script to generate 1099-DIV PDF with all five critical fields and validate positions.

This script:
1. Creates test data with all five critical fields
2. Generates a test 1099-DIV PDF using corrected mappings
3. Runs position validation tool on generated PDF
4. Reports validation results

Requirements: 4.1, 4.2, 4.3
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from document_generator import generate_document
from validate_field_positions import validate_field_positions, print_validation_report

# Test data with all five critical fields
TEST_FORM_DATA = {
    # Critical Field 1: Payer Name
    "payerName": "Example Corporation",
    
    # Critical Field 2: Payer TIN
    "payerTIN": "12-3456789",
    
    # Critical Field 3: Recipient Name
    "recipientName": "John Doe",
    
    # Critical Field 4: Recipient TIN
    "recipientTIN": "987-65-4321",
    
    # Critical Field 5: Total Ordinary Dividends
    "totalOrdinaryDividends": "1000.00",
    
    # Additional fields for completeness
    "calendarYear": "2024",
    "payerStreetAddress": "123 Main Street",
    "payerCity": "New York, NY 10001",
    "qualifiedDividends": "500.00",
}


def main():
    """Generate test PDF and validate field positions."""
    print("="*80)
    print("1099-DIV FIELD POSITION TEST")
    print("="*80)
    print()
    
    # Step 1: Load template
    print("Step 1: Loading PDF template...")
    template_path = Path(__file__).parent.parent / "samples" / "SAMPLE-1099-DIV-MULTI-COPY.pdf"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    with open(template_path, 'rb') as f:
        template_bytes = f.read()
    
    print(f"✓ Loaded template: {template_path}")
    print(f"  Template size: {len(template_bytes)} bytes")
    print()
    
    # Step 2: Generate test PDF
    print("Step 2: Generating test PDF with all five critical fields...")
    print()
    print("Test Data:")
    print("-" * 80)
    for field, value in TEST_FORM_DATA.items():
        if field in ["payerName", "payerTIN", "recipientName", "recipientTIN", "totalOrdinaryDividends"]:
            print(f"  ★ {field}: {value}")
        else:
            print(f"    {field}: {value}")
    print()
    
    try:
        generated_pdf = generate_document(
            template=template_bytes,
            form_data=TEST_FORM_DATA,
            document_type="1099-DIV"
        )
        print(f"✓ Generated PDF successfully")
        print(f"  Output size: {len(generated_pdf)} bytes")
        print()
    except Exception as e:
        print(f"✗ Failed to generate PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 3: Save generated PDF
    print("Step 3: Saving generated PDF...")
    output_path = Path(__file__).parent / "test-output-field-positions.pdf"
    
    with open(output_path, 'wb') as f:
        f.write(generated_pdf)
    
    print(f"✓ Saved to: {output_path}")
    print()
    
    # Step 4: Validate field positions
    print("Step 4: Validating field positions...")
    print()
    
    try:
        report = validate_field_positions(str(output_path))
        print_validation_report(report, str(output_path))
        
        # Return appropriate exit code
        if len(report.correct_fields) == report.total_fields:
            print()
            print("="*80)
            print("✅ TEST PASSED: All five critical fields in correct positions!")
            print("="*80)
            return 0
        else:
            print()
            print("="*80)
            print("❌ TEST FAILED: Some fields in incorrect positions")
            print("="*80)
            return 1
            
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
