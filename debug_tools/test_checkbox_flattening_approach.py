"""
Test script to validate checkbox flattening approach.

This script tests the recommended approach for making checkboxes visible:
1. Set checkbox field value
2. Flatten checkbox to static graphic (checkmark or empty box)
3. Verify visual appearance in generated PDF
"""

import fitz
import sys
from typing import Tuple


def flatten_checkbox(page: fitz.Page, widget: fitz.Widget, value: str) -> bool:
    """
    Flatten checkbox to static graphic.
    
    Args:
        page: PyMuPDF page object
        widget: PyMuPDF widget object for the checkbox
        value: "Yes" (checked) or "Off" (unchecked)
        
    Returns:
        bool: True if flattening succeeded, False otherwise
    """
    try:
        rect = widget.rect
        
        # Draw checkbox border (empty box)
        page.draw_rect(rect, color=(0, 0, 0), width=0.5)
        
        # If checked, draw checkmark
        if value == "Yes":
            # Calculate checkmark coordinates within box
            x0, y0, x1, y1 = rect
            width = x1 - x0
            height = y1 - y0
            
            # Checkmark proportions (relative to box size)
            # Left stroke: from bottom-left to middle
            p1 = fitz.Point(x0 + width * 0.2, y0 + height * 0.5)
            p2 = fitz.Point(x0 + width * 0.4, y0 + height * 0.7)
            
            # Right stroke: from middle to top-right
            p3 = fitz.Point(x0 + width * 0.4, y0 + height * 0.7)
            p4 = fitz.Point(x0 + width * 0.8, y0 + height * 0.3)
            
            # Draw checkmark strokes
            page.draw_line(p1, p2, color=(0, 0, 0), width=1.5)
            page.draw_line(p3, p4, color=(0, 0, 0), width=1.5)
        
        return True
        
    except Exception as e:
        print(f"Error flattening checkbox: {e}")
        return False


def test_checkbox_flattening():
    """Test checkbox flattening with IRS template."""
    print("=" * 80)
    print("Testing Checkbox Flattening Approach")
    print("=" * 80)
    
    template_path = "samples/1099-DIV.pdf"
    
    try:
        # Open the template
        doc = fitz.open(template_path)
        print(f"✓ Opened template: {template_path}")
        
        # Find FATCA checkbox (Box 11)
        fatca_checkboxes = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            for widget in page.widgets():
                if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    field_name = widget.field_name
                    # FATCA checkbox is typically named with "c1" pattern
                    if 'c1' in field_name.lower():
                        fatca_checkboxes.append({
                            'page_num': page_num,
                            'page': page,
                            'name': field_name,
                            'widget': widget,
                            'rect': widget.rect
                        })
        
        print(f"✓ Found {len(fatca_checkboxes)} FATCA checkbox fields")
        
        if not fatca_checkboxes:
            print("✗ No FATCA checkboxes found")
            return False
        
        # Test flattening with different values
        test_cases = [
            ("Yes", "checked"),
            ("Off", "unchecked")
        ]
        
        for value, description in test_cases:
            print(f"\n--- Testing {description} state (value='{value}') ---")
            
            # Create a copy of the document for this test
            test_doc = fitz.open(template_path)
            
            checkboxes_processed = 0
            for cb_info in fatca_checkboxes:
                # Get the corresponding page and widget in test_doc
                test_page = test_doc[cb_info['page_num']]
                
                # Find the widget by name
                for test_widget in test_page.widgets():
                    if test_widget.field_name == cb_info['name']:
                        # Set the field value
                        test_widget.field_value = value
                        
                        # Flatten the checkbox
                        success = flatten_checkbox(test_page, test_widget, value)
                        
                        if success:
                            checkboxes_processed += 1
                            print(f"  ✓ Flattened checkbox: {cb_info['name']}")
                        else:
                            print(f"  ✗ Failed to flatten: {cb_info['name']}")
                        
                        break
            
            # Save the test PDF
            output_path = f"samples/fatca_checkbox_{description}_test.pdf"
            test_doc.save(output_path)
            print(f"  ✓ Saved test PDF: {output_path}")
            print(f"  ✓ Processed {checkboxes_processed} checkboxes")
            
            test_doc.close()
        
        doc.close()
        
        print("\n" + "=" * 80)
        print("✓ Checkbox flattening test completed successfully")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Open the generated PDFs in Adobe Reader to verify visual appearance")
        print("2. Check that checked boxes show visible checkmarks")
        print("3. Check that unchecked boxes show empty boxes")
        print("4. Verify appearance is consistent across all copies")
        
        return True
        
    except FileNotFoundError:
        print(f"✗ Template not found: {template_path}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_checkbox_visual_content(pdf_path: str, checkbox_name: str) -> Tuple[bool, str]:
    """
    Verify that a checkbox has visual content (not just field value).
    
    Args:
        pdf_path: Path to PDF file
        checkbox_name: Name of checkbox field to verify
        
    Returns:
        Tuple of (has_visual_content, description)
    """
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Find the checkbox
            for widget in page.widgets():
                if widget.field_name == checkbox_name:
                    rect = widget.rect
                    
                    # Extract text and drawings in the checkbox area
                    # Expand rect slightly to capture drawn content
                    search_rect = fitz.Rect(
                        rect.x0 - 2, rect.y0 - 2,
                        rect.x1 + 2, rect.y1 + 2
                    )
                    
                    # Get page drawings (lines, rectangles, etc.)
                    drawings = page.get_drawings()
                    
                    # Check if any drawings intersect with checkbox area
                    has_drawings = False
                    for drawing in drawings:
                        if 'rect' in drawing:
                            draw_rect = drawing['rect']
                            if search_rect.intersects(draw_rect):
                                has_drawings = True
                                break
                    
                    field_value = widget.field_value
                    
                    doc.close()
                    
                    if has_drawings:
                        return True, f"Checkbox has visual content (field_value={field_value})"
                    else:
                        return False, f"Checkbox has no visual content (field_value={field_value})"
        
        doc.close()
        return False, f"Checkbox '{checkbox_name}' not found"
        
    except Exception as e:
        return False, f"Error verifying checkbox: {e}"


def test_visual_verification():
    """Test visual content verification."""
    print("\n" + "=" * 80)
    print("Testing Visual Content Verification")
    print("=" * 80)
    
    test_files = [
        ("samples/fatca_checkbox_checked_test.pdf", "checked"),
        ("samples/fatca_checkbox_unchecked_test.pdf", "unchecked")
    ]
    
    for pdf_path, description in test_files:
        print(f"\nVerifying {description} checkbox PDF:")
        
        try:
            doc = fitz.open(pdf_path)
            
            # Find first FATCA checkbox
            for page_num in range(len(doc)):
                page = doc[page_num]
                for widget in page.widgets():
                    if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                        if 'c1' in widget.field_name.lower():
                            checkbox_name = widget.field_name
                            doc.close()
                            
                            has_visual, msg = verify_checkbox_visual_content(pdf_path, checkbox_name)
                            
                            if has_visual:
                                print(f"  ✓ {msg}")
                            else:
                                print(f"  ✗ {msg}")
                            
                            break
                else:
                    continue
                break
            else:
                doc.close()
                print(f"  ✗ No FATCA checkbox found")
                
        except FileNotFoundError:
            print(f"  ⚠ File not found: {pdf_path}")
        except Exception as e:
            print(f"  ✗ Error: {e}")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Checkbox Flattening Test" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    success = test_checkbox_flattening()
    
    if success:
        test_visual_verification()
    
    print()


if __name__ == "__main__":
    main()
