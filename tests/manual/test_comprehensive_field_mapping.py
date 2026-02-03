#!/usr/bin/env python3
"""
Comprehensive test script for field mapping with all fields populated.

This script generates a test 1099-DIV PDF with comprehensive data to verify
that all fields render correctly with the adaptive font sizing implementation.

Task: 6.1 - Generate test PDF with all fields populated
Requirements: 8.1
"""

import sys
import os

# Add tax_document_generation to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tax_document_generation'))

from document_generator import generate_document

# Comprehensive test data with all 1099-DIV fields
COMPREHENSIVE_TEST_DATA = {
    # Payer Information (LeftCol fields)
    "payerName": "Acme Investment Corporation",
    "payerTIN": "12-3456789",
    "payerStreetAddress": "123 Wall Street, Suite 500",
    "payerCity": "New York",
    "payerState": "NY",
    "payerZip": "10005",
    "payerPhoneNumber": "212-555-0100",
    
    # Recipient Information (LeftCol fields)
    "recipientName": "John Q. Taxpayer",
    "recipientTIN": "987-65-4321",
    "recipientStreetAddress": "456 Main Street",
    "recipientCity": "Springfield",
    "recipientState": "IL",
    "recipientZip": "62701",
    "accountNumber": "ACC-123456",
    
    # Box 1a - Total ordinary dividends (RghtCol field)
    "totalOrdinaryDividends": "1500.00",
    
    # Box 1b - Qualified dividends (RghtCol field)
    "qualifiedDividends": "1200.00",
    
    # Box 2a - Total capital gain distributions (RghtCol field)
    "totalCapitalGainDistributions": "250.00",
    
    # Box 2b - Unrecaptured Section 1250 gain (RghtCol field)
    "unrecapturedSection1250Gain": "50.00",
    
    # Box 2c - Section 1202 gain (RghtCol field)
    "section1202Gain": "25.00",
    
    # Box 2d - Collectibles (28%) gain (RghtCol field)
    "collectiblesGain": "15.00",
    
    # Box 2e - Section 897 ordinary dividends (RghtCol field)
    "section897OrdinaryDividends": "10.00",
    
    # Box 2f - Section 897 capital gain (RghtCol field)
    "section897CapitalGain": "5.00",
    
    # Box 3 - Nondividend distributions (RghtCol field)
    "nondividendDistributions": "100.00",
    
    # Box 4 - Federal income tax withheld (RghtCol field)
    "federalIncomeTaxWithheld": "150.00",
    
    # Box 5 - Section 199A dividends (RghtCol field)
    "section199ADividends": "800.00",
    
    # Box 6 - Investment expenses (RghtCol field)
    "investmentExpenses": "25.00",
    
    # Box 7 - Foreign tax paid (RghtCol field)
    "foreignTaxPaid": "75.00",
    
    # Box 8 - Foreign country or U.S. possession (RghtCol field)
    "foreignCountry": "Canada",
    
    # Box 9 - Cash liquidation distributions (RghtCol field)
    "cashLiquidationDistributions": "0.00",
    
    # Box 10 - Noncash liquidation distributions (RghtCol field)
    "noncashLiquidationDistributions": "0.00",
    
    # Box 11 - FATCA filing requirement (checkbox)
    "fatcaFilingRequirement": "X",
    
    # Box 12 - Exempt-interest dividends (RghtCol field)
    "exemptInterestDividends": "50.00",
    
    # Box 13 - Specified private activity bond interest dividends (RghtCol field)
    "privateActivityBondDividends": "20.00",
    
    # Box 14 - State (LeftCol field)
    "state": "NY",
    
    # Box 15 - State identification number (LeftCol field)
    "stateIdNumber": "12-3456789",
    
    # Box 16 - State tax withheld (RghtCol field)
    "stateTaxWithheld": "50.00",
}


def main():
    """Generate comprehensive test PDF."""
    print("=" * 80)
    print("COMPREHENSIVE FIELD MAPPING TEST")
    print("=" * 80)
    print()
    print("This test generates a 1099-DIV PDF with all fields populated to verify")
    print("that the adaptive font sizing implementation works correctly.")
    print()
    
    # Load the PDF template
    template_path = "1099-DIV.pdf"
    if not os.path.exists(template_path):
        print(f"ERROR: Template file not found: {template_path}")
        print("Please ensure 1099-DIV.pdf is in the current directory.")
        return 1
    
    print(f"Loading template: {template_path}")
    with open(template_path, "rb") as f:
        template_bytes = f.read()
    
    print(f"Template size: {len(template_bytes)} bytes")
    print()
    
    # Display test data summary
    print("Test Data Summary:")
    print(f"  Total fields: {len(COMPREHENSIVE_TEST_DATA)}")
    print(f"  Payer: {COMPREHENSIVE_TEST_DATA['payerName']}")
    print(f"  Recipient: {COMPREHENSIVE_TEST_DATA['recipientName']}")
    print(f"  Total Ordinary Dividends: ${COMPREHENSIVE_TEST_DATA['totalOrdinaryDividends']}")
    print(f"  Qualified Dividends: ${COMPREHENSIVE_TEST_DATA['qualifiedDividends']}")
    print()
    
    # Generate the document
    print("Generating PDF with comprehensive data...")
    print("-" * 80)
    try:
        result_bytes = generate_document(
            template=template_bytes,
            form_data=COMPREHENSIVE_TEST_DATA,
            document_type="1099-DIV"
        )
        print("-" * 80)
        print()
        
        # Save the result
        output_path = "test-comprehensive-field-mapping-1099-DIV.pdf"
        with open(output_path, "wb") as f:
            f.write(result_bytes)
        
        print(f"✓ PDF generated successfully!")
        print(f"  Output file: {output_path}")
        print(f"  Output size: {len(result_bytes)} bytes")
        print()
        
        print("Next Steps:")
        print("  1. Open the generated PDF in Adobe Reader")
        print("  2. Verify that all fields are visible and correctly positioned")
        print("  3. Check all three copies (Copy A, Copy B, Copy C)")
        print("  4. Verify monetary values appear in the right column boxes")
        print("  5. Verify payer/recipient information appears in left column boxes")
        print()
        
        return 0
        
    except Exception as e:
        print("-" * 80)
        print()
        print(f"✗ ERROR: Failed to generate PDF")
        print(f"  {type(e).__name__}: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
