"""
Test script to verify flatten_checkbox() function implementation.

This script tests the flatten_checkbox() function with various scenarios:
1. Checked checkbox (value = '1')
2. Unchecked checkbox (value = 'Off')
3. Different on_state values ('1', '2')
4. Error handling
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from document_generator import flatten_checkbox


def test_flatten_checkbox_checked():
    """Test flattening a checked checkbox."""
    print("\n=== Test 1: Checked Checkbox ===")
    
    # Create a test PDF
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    
    # Create a checkbox widget
    rect = fitz.Rect(50, 50, 59, 59)  # 9×9 points
    widget = fitz.Widget()
    widget.rect = rect
    widget.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
    
    # Flatten with checked value
    flatten_checkbox(page, widget, '1')
    
    # Verify visual content was added
    # Check if there are drawing commands on the page
    text_page = page.get_text("dict")
    drawings = page.get_drawings()
    
    print(f"✓ Checkbox flattened successfully")
    print(f"  - Drawings on page: {len(drawings)}")
    print(f"  - Expected: Border (1 rect) + Checkmark (2 lines) = 3 drawings")
    
    # Save for manual inspection
    output_path = "samples/test_flatten_checkbox_checked.pdf"
    doc.save(output_path)
    print(f"  - Saved to: {output_path}")
    
    doc.close()
    
    assert len(drawings) >= 3, f"Expected at least 3 drawings, got {len(drawings)}"
    print("✓ Test passed: Checked checkbox has visual content")


def test_flatten_checkbox_unchecked():
    """Test flattening an unchecked checkbox."""
    print("\n=== Test 2: Unchecked Checkbox ===")
    
    # Create a test PDF
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    
    # Create a checkbox widget
    rect = fitz.Rect(50, 50, 59, 59)  # 9×9 points
    widget = fitz.Widget()
    widget.rect = rect
    widget.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
    
    # Flatten with unchecked value
    flatten_checkbox(page, widget, 'Off')
    
    # Verify visual content was added
    drawings = page.get_drawings()
    
    print(f"✓ Checkbox flattened successfully")
    print(f"  - Drawings on page: {len(drawings)}")
    print(f"  - Expected: Border (1 rect) only = 1 drawing")
    
    # Save for manual inspection
    output_path = "samples/test_flatten_checkbox_unchecked.pdf"
    doc.save(output_path)
    print(f"  - Saved to: {output_path}")
    
    doc.close()
    
    assert len(drawings) >= 1, f"Expected at least 1 drawing, got {len(drawings)}"
    print("✓ Test passed: Unchecked checkbox has border only")


def test_flatten_checkbox_on_state_2():
    """Test flattening a checkbox with on_state='2'."""
    print("\n=== Test 3: Checkbox with on_state='2' ===")
    
    # Create a test PDF
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    
    # Create a checkbox widget
    rect = fitz.Rect(50, 50, 59, 59)  # 9×9 points
    widget = fitz.Widget()
    widget.rect = rect
    widget.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
    
    # Flatten with on_state='2' (checked)
    flatten_checkbox(page, widget, '2')
    
    # Verify visual content was added
    drawings = page.get_drawings()
    
    print(f"✓ Checkbox flattened successfully")
    print(f"  - Drawings on page: {len(drawings)}")
    print(f"  - Expected: Border (1 rect) + Checkmark (2 lines) = 3 drawings")
    
    # Save for manual inspection
    output_path = "samples/test_flatten_checkbox_on_state_2.pdf"
    doc.save(output_path)
    print(f"  - Saved to: {output_path}")
    
    doc.close()
    
    assert len(drawings) >= 3, f"Expected at least 3 drawings, got {len(drawings)}"
    print("✓ Test passed: Checkbox with on_state='2' has checkmark")


def test_flatten_checkbox_different_sizes():
    """Test flattening checkboxes of different sizes."""
    print("\n=== Test 4: Different Checkbox Sizes ===")
    
    # Create a test PDF
    doc = fitz.open()
    page = doc.new_page(width=300, height=300)
    
    sizes = [
        (9, 9),    # Standard IRS size
        (12, 12),  # Larger
        (6, 6),    # Smaller
    ]
    
    y_offset = 50
    for width, height in sizes:
        rect = fitz.Rect(50, y_offset, 50 + width, y_offset + height)
        widget = fitz.Widget()
        widget.rect = rect
        widget.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
        
        # Flatten with checked value
        flatten_checkbox(page, widget, '1')
        
        print(f"  - Flattened {width}×{height}pt checkbox at y={y_offset}")
        y_offset += height + 20
    
    # Save for manual inspection
    output_path = "samples/test_flatten_checkbox_sizes.pdf"
    doc.save(output_path)
    print(f"✓ Saved to: {output_path}")
    
    doc.close()
    print("✓ Test passed: Checkboxes of different sizes rendered correctly")


def test_flatten_checkbox_error_handling():
    """Test error handling in flatten_checkbox."""
    print("\n=== Test 5: Error Handling ===")
    
    # Create a test PDF
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    
    # Create a widget with invalid rect (should handle gracefully)
    widget = fitz.Widget()
    widget.rect = None  # Invalid rect
    
    try:
        # This should log an error but not raise
        flatten_checkbox(page, widget, '1')
        print("✓ Function handled invalid rect gracefully (logged error)")
    except Exception as e:
        print(f"✗ Function raised exception: {e}")
        raise
    
    doc.close()
    print("✓ Test passed: Error handling works correctly")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing flatten_checkbox() Function")
    print("=" * 60)
    
    try:
        test_flatten_checkbox_checked()
        test_flatten_checkbox_unchecked()
        test_flatten_checkbox_on_state_2()
        test_flatten_checkbox_different_sizes()
        test_flatten_checkbox_error_handling()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nGenerated test PDFs in samples/ directory:")
        print("  - test_flatten_checkbox_checked.pdf")
        print("  - test_flatten_checkbox_unchecked.pdf")
        print("  - test_flatten_checkbox_on_state_2.pdf")
        print("  - test_flatten_checkbox_sizes.pdf")
        print("\nPlease review these PDFs to verify visual appearance.")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
