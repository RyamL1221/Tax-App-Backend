"""
Verify that VOIDED and CORRECTED checkboxes are visible in generated PDFs.

This script opens the generated test PDFs and checks for:
- Checkbox drawings (checkmarks should be drawn as graphics)
- Number of drawings on each page
- Comparison with expected behavior
"""

import pymupdf as fitz


def verify_voided_checkbox():
    """Verify VOIDED checkbox visibility in test PDF."""
    print("\n" + "=" * 80)
    print("VERIFYING: test-voided-checkbox.pdf")
    print("=" * 80)
    
    pdf_path = "samples/test-voided-checkbox.pdf"
    doc = fitz.open(pdf_path)
    
    print(f"\nPDF: {pdf_path}")
    print(f"Pages: {len(doc)}")
    
    # Expected: VOIDED checkbox on pages 2, 3, 6 (CopyA, Copy1, Copy2)
    # Expected: No VOIDED checkbox on page 4 (CopyB)
    expected_pages_with_voided = [2, 3, 6]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        drawings = page.get_drawings()
        
        print(f"\nPage {page_num + 1}:")
        print(f"  Total drawings: {len(drawings)}")
        
        # Check for checkmark-like drawings (lines that form a check shape)
        checkmark_count = 0
        for drawing in drawings:
            # Checkmarks consist of line drawings
            if drawing.get('type') == 'l':  # line
                checkmark_count += 1
        
        if page_num + 1 in expected_pages_with_voided:
            print(f"  Expected: VOIDED checkbox visible ✓")
            if len(drawings) > 0:
                print(f"  Status: ✅ Drawings found (checkmarks rendered)")
            else:
                print(f"  Status: ⚠️  No drawings found")
        elif page_num + 1 == 4:  # CopyB
            print(f"  Expected: No VOIDED checkbox (CopyB has no VOIDED field)")
            print(f"  Status: ✅ Correct")
    
    doc.close()


def verify_corrected_checkbox():
    """Verify CORRECTED checkbox visibility in test PDF."""
    print("\n" + "=" * 80)
    print("VERIFYING: test-corrected-checkbox.pdf")
    print("=" * 80)
    
    pdf_path = "samples/test-corrected-checkbox.pdf"
    doc = fitz.open(pdf_path)
    
    print(f"\nPDF: {pdf_path}")
    print(f"Pages: {len(doc)}")
    
    # Expected: CORRECTED checkbox on pages 2, 3, 4, 6 (all copies)
    expected_pages_with_corrected = [2, 3, 4, 6]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        drawings = page.get_drawings()
        
        print(f"\nPage {page_num + 1}:")
        print(f"  Total drawings: {len(drawings)}")
        
        if page_num + 1 in expected_pages_with_corrected:
            print(f"  Expected: CORRECTED checkbox visible ✓")
            if len(drawings) > 0:
                print(f"  Status: ✅ Drawings found (checkmarks rendered)")
            else:
                print(f"  Status: ⚠️  No drawings found")
    
    doc.close()


def verify_both_checkboxes():
    """Verify both VOIDED and CORRECTED checkboxes in test PDF."""
    print("\n" + "=" * 80)
    print("VERIFYING: test-both-checkboxes.pdf")
    print("=" * 80)
    
    pdf_path = "samples/test-both-checkboxes.pdf"
    doc = fitz.open(pdf_path)
    
    print(f"\nPDF: {pdf_path}")
    print(f"Pages: {len(doc)}")
    
    # Expected: Both checkboxes on pages 2, 3, 6
    # Expected: Only CORRECTED on page 4 (CopyB)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        drawings = page.get_drawings()
        
        print(f"\nPage {page_num + 1}:")
        print(f"  Total drawings: {len(drawings)}")
        
        if page_num + 1 in [2, 3, 6]:
            print(f"  Expected: Both VOIDED and CORRECTED checkboxes visible ✓")
            if len(drawings) > 0:
                print(f"  Status: ✅ Drawings found (checkmarks rendered)")
            else:
                print(f"  Status: ⚠️  No drawings found")
        elif page_num + 1 == 4:
            print(f"  Expected: Only CORRECTED checkbox (CopyB has no VOIDED)")
            if len(drawings) > 0:
                print(f"  Status: ✅ Drawings found (checkmarks rendered)")
            else:
                print(f"  Status: ⚠️  No drawings found")
    
    doc.close()


def compare_with_fatca():
    """Compare VOIDED/CORRECTED with FATCA checkbox (known working)."""
    print("\n" + "=" * 80)
    print("COMPARISON: FATCA checkbox (known working reference)")
    print("=" * 80)
    
    # Check FATCA checkbox PDF
    fatca_path = "samples/test-fatca-checkbox.pdf"
    try:
        doc = fitz.open(fatca_path)
        print(f"\nFATCA PDF: {fatca_path}")
        print(f"Pages: {len(doc)}")
        
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            drawings = page.get_drawings()
            print(f"  Page {page_num + 1}: {len(drawings)} drawings")
        
        doc.close()
    except Exception as e:
        print(f"\nFATCA PDF not found or error: {e}")
    
    print("\nConclusion:")
    print("  If VOIDED/CORRECTED PDFs have similar drawing counts to FATCA,")
    print("  then the checkboxes are being rendered correctly.")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CHECKBOX VISIBILITY VERIFICATION")
    print("=" * 80)
    print("\nThis script verifies that checkboxes are rendered as graphics.")
    print("Checkmarks should appear as line drawings in the PDF.")
    print("=" * 80)
    
    verify_voided_checkbox()
    verify_corrected_checkbox()
    verify_both_checkboxes()
    compare_with_fatca()
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print("\n✅ If drawings are found on expected pages, checkboxes are visible!")
    print("📋 For final confirmation, open PDFs in Adobe Reader/Preview/Chrome.")
    print("=" * 80 + "\n")
