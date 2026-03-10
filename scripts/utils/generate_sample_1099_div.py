"""
Generate a sample 1099-DIV PDF for manual inspection of multi-copy functionality.

This script generates a 1099-DIV with comprehensive form data to verify that
all three copies (Copy1, Copy2, CopyB) are populated with identical data.
"""

import sys
import os

# Add tax_document_generation to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tax_document_generation'))

from tax_document_generation.document_generator import generate_document
from tax_document_generation.field_mapper import FieldMapper
import tax_document_generation.exceptions
sys.modules['exceptions'] = tax_document_generation.exceptions
import fitz  # PyMuPDF


def main():
    """Generate a sample 1099-DIV PDF with multi-copy data."""
    
    # Comprehensive form data for 1099-DIV
    form_data = {
        # Payer information
        "payerName": "Acme Investment Corporation",
        "payerStreetAddress": "123 Wall Street, Suite 500",
        "payerCity": "New York",
        "payerState": "NY",
        "payerZip": "10005",
        "payerTIN": "12-3456789",
        "payerPhone": "212-555-1234",
        
        # Recipient information
        "recipientName": "John Q. Taxpayer",
        "recipientStreetAddress": "456 Main Street",
        "recipientCity": "Springfield",
        "recipientState": "IL",
        "recipientZip": "62701",
        "recipientTIN": "987-65-4321",
        "recipientAccountNumber": "ACC-123456",
        
        # Dividend amounts
        "totalOrdinaryDividends": "1500.00",
        "qualifiedDividends": "1200.00",
        "totalCapitalGainDistributions": "250.00",
        "unrecapturedSection1250Gain": "50.00",
        "section1202Gain": "25.00",
        "collectibles28Gain": "10.00",
        "nondividendDistributions": "100.00",
        "federalIncomeTaxWithheld": "150.00",
        "section199ADividends": "100.00",
        "investmentExpenses": "25.00",
        "foreignTaxPaid": "75.00",
        "foreignCountry": "Canada",
        "cashLiquidationDistributions": "0.00",
        "noncashLiquidationDistributions": "0.00",
        "exemptInterestDividends": "50.00",
        "specifiedPrivateActivityBondInterest": "20.00",
        
        # Additional fields
        "fatcaFilingRequirement": "X",
        "secondTINNotice": "",
    }
    
    print("=" * 80)
    print("GENERATING SAMPLE 1099-DIV FOR MULTI-COPY INSPECTION")
    print("=" * 80)
    print()
    
    # Load the template
    print("Loading 1099-DIV template...")
    with open("1099-DIV.pdf", "rb") as f:
        template_bytes = f.read()
    
    print(f"✓ Template loaded ({len(template_bytes)} bytes)")
    print()
    
    # Initialize field mapper to show mapping statistics
    print("Initializing field mapper...")
    mapper = FieldMapper("1099-DIV")
    mapped_data = mapper.map_all_fields(form_data)
    
    print(f"✓ Field mapper initialized")
    print(f"  - API fields: {len(form_data)}")
    print(f"  - PDF fields (all copies): {len(mapped_data)}")
    print(f"  - Expected ratio: 3:1 (3 PDF fields per API field)")
    print(f"  - Actual ratio: {len(mapped_data) / len(form_data):.1f}:1")
    print()
    
    # Count fields by copy
    copy1_count = sum(1 for k in mapped_data.keys() if "Copy1[0]" in k)
    copy2_count = sum(1 for k in mapped_data.keys() if "Copy2[0]" in k)
    copyb_count = sum(1 for k in mapped_data.keys() if "CopyB[0]" in k)
    
    print("Field distribution by copy:")
    print(f"  - Copy1: {copy1_count} fields")
    print(f"  - Copy2: {copy2_count} fields")
    print(f"  - CopyB: {copyb_count} fields")
    print()
    
    # Generate the document
    print("Generating PDF document...")
    output_pdf = generate_document(template_bytes, form_data, "1099-DIV")
    
    print(f"✓ Document generated ({len(output_pdf)} bytes)")
    print()
    
    # Save the output
    output_path = "SAMPLE-1099-DIV-MULTI-COPY.pdf"
    with open(output_path, "wb") as f:
        f.write(output_pdf)
    
    print(f"✓ PDF saved to: {output_path}")
    print()
    
    # Analyze the generated PDF
    print("Analyzing generated PDF...")
    doc = fitz.open(stream=output_pdf, filetype="pdf")
    
    print(f"✓ PDF has {len(doc)} pages")
    print()
    
    # Extract text from each copy page
    print("Extracting text from copy pages:")
    print()
    
    copy_pages = {
        "Copy1 (Taxpayer)": 2,  # Page 3 (0-indexed)
        "Copy2 (IRS)": 3,       # Page 4 (0-indexed)
        "CopyB (Recipient)": 5  # Page 6 (0-indexed)
    }
    
    extracted_texts = {}
    
    for copy_name, page_index in copy_pages.items():
        page = doc[page_index]
        text = page.get_text()
        extracted_texts[copy_name] = text
        
        print(f"{copy_name} (Page {page_index + 1}):")
        print("-" * 60)
        
        # Check for key data points
        checks = [
            ("Payer Name", "Acme Investment Corporation"),
            ("Payer TIN", "12-3456789"),
            ("Recipient Name", "John Q. Taxpayer"),
            ("Recipient TIN", "987-65-4321"),
            ("Total Ordinary Dividends", "1500.00"),
            ("Qualified Dividends", "1200.00"),
            ("Capital Gain Distributions", "250.00"),
            ("Federal Tax Withheld", "150.00"),
        ]
        
        for label, value in checks:
            # Check if value appears in text (may have formatting variations)
            found = value in text or value.replace("-", "") in text or value.replace(".", "") in text
            status = "✓" if found else "✗"
            print(f"  {status} {label}: {value}")
        
        print()
    
    doc.close()
    
    # Verify consistency across copies
    print("=" * 80)
    print("CONSISTENCY VERIFICATION")
    print("=" * 80)
    print()
    
    print("Checking that all three copies contain the same data...")
    print()
    
    # Check key values appear in all copies
    key_values = [
        "Acme Investment Corporation",
        "12-3456789",
        "John Q. Taxpayer",
        "987-65-4321",
        "1500.00",
        "1200.00",
        "250.00",
    ]
    
    all_consistent = True
    
    for value in key_values:
        copy1_has = value in extracted_texts["Copy1 (Taxpayer)"] or value.replace("-", "") in extracted_texts["Copy1 (Taxpayer)"]
        copy2_has = value in extracted_texts["Copy2 (IRS)"] or value.replace("-", "") in extracted_texts["Copy2 (IRS)"]
        copyb_has = value in extracted_texts["CopyB (Recipient)"] or value.replace("-", "") in extracted_texts["CopyB (Recipient)"]
        
        consistent = copy1_has == copy2_has == copyb_has
        status = "✓" if consistent else "✗"
        
        if not consistent:
            all_consistent = False
            print(f"{status} '{value}': Copy1={copy1_has}, Copy2={copy2_has}, CopyB={copyb_has}")
        else:
            print(f"{status} '{value}': Present in all copies" if copy1_has else f"{status} '{value}': Absent from all copies")
    
    print()
    
    if all_consistent:
        print("✅ SUCCESS: All checked values have consistent presence across all three copies!")
    else:
        print("⚠️  WARNING: Some values have inconsistent presence across copies")
    
    print()
    print("=" * 80)
    print("MANUAL INSPECTION INSTRUCTIONS")
    print("=" * 80)
    print()
    print(f"1. Open the generated PDF: {output_path}")
    print("2. Navigate to the following pages:")
    print("   - Page 3: Copy1 (For Taxpayer)")
    print("   - Page 4: Copy2 (For IRS)")
    print("   - Page 6: CopyB (For Recipient)")
    print("3. Verify that all three copies contain identical data")
    print("4. Check that the following fields are populated:")
    print("   - Payer information (name, address, TIN)")
    print("   - Recipient information (name, address, TIN)")
    print("   - Dividend amounts (boxes 1a, 1b, 2a, etc.)")
    print("   - Tax withheld (box 4)")
    print("5. Verify that the PDF is viewable in Adobe Reader")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
