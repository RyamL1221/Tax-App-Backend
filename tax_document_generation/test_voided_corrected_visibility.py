"""
Test VOIDED and CORRECTED checkbox visibility in generated PDFs.

This script generates test PDFs with different checkbox combinations to verify
that checkmarks are visible in Adobe Reader, Preview, and Chrome PDF viewer.

Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
"""

import os
import pymupdf as fitz
from document_generator import generate_document


def test_voided_checkbox():
    """Test VOIDED checkbox visibility."""
    print("\n" + "=" * 80)
    print("TEST: VOIDED CHECKBOX VISIBILITY")
    print("=" * 80)
    
    # Load template
    template_path = "samples/1099-DIV.pdf"
    with open(template_path, 'rb') as f:
        template = f.read()
    
    # Form data with voided=true
    form_data = {
        "calendarYear": "2024",
        "voided": True,
        "payerName": "Test Corp",
        "payerTIN": "12-3456789",
        "recipientName": "John Doe",
        "recipientTIN": "123-45-6789",
        "totalOrdinaryDividends": 1000.00
    }
    
    print("\nGenerating PDF with voided=True...")
    print(f"Form data: {form_data}")
    
    # Generate PDF
    pdf_bytes = generate_document(template, form_data, "1099-DIV")
    
    # Save output
    output_path = "samples/test-voided-checkbox.pdf"
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"\n✅ Generated PDF: {output_path}")
    print("📋 Please open in Adobe Reader/Preview/Chrome to verify VOIDED checkbox is visible")
    print("   Expected: VOIDED checkbox checked on CopyA (page 2), Copy1 (page 3), Copy2 (page 6)")
    print("   Expected: CopyB (page 4) has no VOIDED checkbox")
    
    # Inspect generated PDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    print(f"\n📊 Generated PDF has {len(doc)} pages")
    
    # Check for checkmarks on pages (checkmarks are drawn as graphics)
    for page_num in range(len(doc)):
        page = doc[page_num]
        drawings = page.get_drawings()
        if drawings:
            print(f"  Page {page_num + 1}: {len(drawings)} drawing(s) found (checkmarks are graphics)")
    
    doc.close()
    print("=" * 80)


def test_corrected_checkbox():
    """Test CORRECTED checkbox visibility."""
    print("\n" + "=" * 80)
    print("TEST: CORRECTED CHECKBOX VISIBILITY")
    print("=" * 80)
    
    # Load template
    template_path = "samples/1099-DIV.pdf"
    with open(template_path, 'rb') as f:
        template = f.read()
    
    # Form data with corrected=true
    form_data = {
        "calendarYear": "2024",
        "corrected": True,
        "payerName": "Test Corp",
        "payerTIN": "12-3456789",
        "recipientName": "John Doe",
        "recipientTIN": "123-45-6789",
        "totalOrdinaryDividends": 1000.00
    }
    
    print("\nGenerating PDF with corrected=True...")
    print(f"Form data: {form_data}")
    
    # Generate PDF
    pdf_bytes = generate_document(template, form_data, "1099-DIV")
    
    # Save output
    output_path = "samples/test-corrected-checkbox.pdf"
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"\n✅ Generated PDF: {output_path}")
    print("📋 Please open in Adobe Reader/Preview/Chrome to verify CORRECTED checkbox is visible")
    print("   Expected: CORRECTED checkbox checked on all 4 copies (pages 2, 3, 4, 6)")
    
    # Inspect generated PDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    print(f"\n📊 Generated PDF has {len(doc)} pages")
    
    # Check for checkmarks on pages
    for page_num in range(len(doc)):
        page = doc[page_num]
        drawings = page.get_drawings()
        if drawings:
            print(f"  Page {page_num + 1}: {len(drawings)} drawing(s) found (checkmarks are graphics)")
    
    doc.close()
    print("=" * 80)


def test_both_checkboxes():
    """Test both VOIDED and CORRECTED checkboxes."""
    print("\n" + "=" * 80)
    print("TEST: BOTH CHECKBOXES (VOIDED + CORRECTED)")
    print("=" * 80)
    
    # Load template
    template_path = "samples/1099-DIV.pdf"
    with open(template_path, 'rb') as f:
        template = f.read()
    
    # Form data with both=true
    form_data = {
        "calendarYear": "2024",
        "voided": True,
        "corrected": True,
        "payerName": "Test Corp",
        "payerTIN": "12-3456789",
        "recipientName": "John Doe",
        "recipientTIN": "123-45-6789",
        "totalOrdinaryDividends": 1000.00
    }
    
    print("\nGenerating PDF with voided=True AND corrected=True...")
    print(f"Form data: {form_data}")
    print("⚠️  Should see mutual exclusivity warning in logs")
    
    # Generate PDF
    pdf_bytes = generate_document(template, form_data, "1099-DIV")
    
    # Save output
    output_path = "samples/test-both-checkboxes.pdf"
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"\n✅ Generated PDF: {output_path}")
    print("📋 Please open in Adobe Reader/Preview/Chrome to verify both checkboxes are visible")
    print("   Expected: Both VOIDED and CORRECTED checked on applicable copies")
    
    # Inspect generated PDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    print(f"\n📊 Generated PDF has {len(doc)} pages")
    
    # Check for checkmarks on pages
    for page_num in range(len(doc)):
        page = doc[page_num]
        drawings = page.get_drawings()
        if drawings:
            print(f"  Page {page_num + 1}: {len(drawings)} drawing(s) found (checkmarks are graphics)")
    
    doc.close()
    print("=" * 80)


def test_unchecked_checkboxes():
    """Test unchecked checkboxes (voided=false, corrected=false)."""
    print("\n" + "=" * 80)
    print("TEST: UNCHECKED CHECKBOXES (DEFAULT)")
    print("=" * 80)
    
    # Load template
    template_path = "samples/1099-DIV.pdf"
    with open(template_path, 'rb') as f:
        template = f.read()
    
    # Form data with both=false (or omitted)
    form_data = {
        "calendarYear": "2024",
        "voided": False,
        "corrected": False,
        "payerName": "Test Corp",
        "payerTIN": "12-3456789",
        "recipientName": "John Doe",
        "recipientTIN": "123-45-6789",
        "totalOrdinaryDividends": 1000.00
    }
    
    print("\nGenerating PDF with voided=False AND corrected=False...")
    print(f"Form data: {form_data}")
    
    # Generate PDF
    pdf_bytes = generate_document(template, form_data, "1099-DIV")
    
    # Save output
    output_path = "samples/test-unchecked-checkboxes.pdf"
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"\n✅ Generated PDF: {output_path}")
    print("📋 Please open in Adobe Reader/Preview/Chrome to verify checkboxes are empty")
    print("   Expected: Empty checkbox boxes visible (no checkmarks)")
    
    # Inspect generated PDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    print(f"\n📊 Generated PDF has {len(doc)} pages")
    
    # Check for drawings on pages
    for page_num in range(len(doc)):
        page = doc[page_num]
        drawings = page.get_drawings()
        if drawings:
            print(f"  Page {page_num + 1}: {len(drawings)} drawing(s) found (checkbox borders)")
    
    doc.close()
    print("=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("VOIDED AND CORRECTED CHECKBOX VISIBILITY TESTS")
    print("=" * 80)
    print("\nThis script generates test PDFs to verify checkbox visibility.")
    print("After generation, open the PDFs in:")
    print("  - Adobe Reader")
    print("  - Preview (macOS)")
    print("  - Chrome PDF viewer")
    print("\nVerify that checkmarks are visible as static graphics.")
    print("=" * 80)
    
    # Run all tests
    test_voided_checkbox()
    test_corrected_checkbox()
    test_both_checkboxes()
    test_unchecked_checkboxes()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    print("\nGenerated PDFs:")
    print("  1. samples/test-voided-checkbox.pdf")
    print("  2. samples/test-corrected-checkbox.pdf")
    print("  3. samples/test-both-checkboxes.pdf")
    print("  4. samples/test-unchecked-checkboxes.pdf")
    print("\nPlease open these PDFs in Adobe Reader/Preview/Chrome to verify visibility.")
    print("=" * 80 + "\n")
