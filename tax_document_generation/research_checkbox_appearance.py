"""
Research script for PyMuPDF checkbox appearance stream capabilities.

This script investigates:
1. widget.update_appearance() method availability
2. Appearance stream generation in PyMuPDF 1.23+
3. Checkbox-specific methods and properties
4. Recommended approach for checkbox visibility
"""

import fitz
import sys
import inspect


def check_pymupdf_version():
    """Check PyMuPDF version."""
    print("=" * 80)
    print("PyMuPDF Version Information")
    print("=" * 80)
    print(f"PyMuPDF version: {fitz.version}")
    print(f"PyMuPDF version tuple: {fitz.VersionBind}")
    print()


def inspect_widget_methods():
    """Inspect available methods on Widget objects."""
    print("=" * 80)
    print("Widget Class Methods and Attributes")
    print("=" * 80)
    
    # Get all methods and attributes of Widget class
    widget_members = inspect.getmembers(fitz.Widget)
    
    # Filter for public methods (not starting with _)
    public_methods = [name for name, obj in widget_members 
                     if not name.startswith('_') and callable(obj)]
    
    print("Public methods:")
    for method in sorted(public_methods):
        print(f"  - {method}")
    
    # Check for specific appearance-related methods
    print("\nAppearance-related methods:")
    appearance_methods = [m for m in public_methods if 'appear' in m.lower()]
    if appearance_methods:
        for method in appearance_methods:
            print(f"  ✓ {method}")
    else:
        print("  ✗ No appearance-related methods found")
    
    # Check for update methods
    print("\nUpdate-related methods:")
    update_methods = [m for m in public_methods if 'update' in m.lower()]
    if update_methods:
        for method in update_methods:
            print(f"  ✓ {method}")
    else:
        print("  ✗ No update-related methods found")
    
    print()


def test_checkbox_with_template():
    """Test checkbox manipulation with actual IRS template."""
    print("=" * 80)
    print("Testing Checkbox with IRS Template")
    print("=" * 80)
    
    template_path = "samples/1099-DIV.pdf"
    
    try:
        # Open the template
        doc = fitz.open(template_path)
        print(f"✓ Opened template: {template_path}")
        print(f"  Pages: {len(doc)}")
        
        # Find checkbox fields
        checkbox_fields = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            for widget in page.widgets():
                if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    checkbox_fields.append({
                        'page': page_num,
                        'name': widget.field_name,
                        'rect': widget.rect,
                        'widget': widget
                    })
        
        print(f"\n✓ Found {len(checkbox_fields)} checkbox fields")
        
        if checkbox_fields:
            # Test with first checkbox
            test_checkbox = checkbox_fields[0]
            print(f"\nTesting with checkbox: {test_checkbox['name']}")
            print(f"  Page: {test_checkbox['page']}")
            print(f"  Rect: {test_checkbox['rect']}")
            
            widget = test_checkbox['widget']
            
            # Check available attributes
            print("\nCheckbox widget attributes:")
            attrs = ['field_value', 'field_type', 'field_name', 'rect', 
                    'field_flags', 'field_display', 'border_width', 
                    'border_color', 'fill_color']
            
            for attr in attrs:
                if hasattr(widget, attr):
                    try:
                        value = getattr(widget, attr)
                        print(f"  ✓ {attr}: {value}")
                    except Exception as e:
                        print(f"  ✗ {attr}: Error - {e}")
                else:
                    print(f"  ✗ {attr}: Not available")
            
            # Test setting checkbox value
            print("\nTesting checkbox value setting:")
            original_value = widget.field_value
            print(f"  Original value: {original_value}")
            
            # Set to checked
            widget.field_value = "Yes"
            print(f"  Set to 'Yes'")
            
            # Check if update_appearance exists
            print("\nTesting appearance methods:")
            if hasattr(widget, 'update_appearance'):
                print("  ✓ widget.update_appearance() exists")
                try:
                    widget.update_appearance()
                    print("  ✓ widget.update_appearance() executed successfully")
                except Exception as e:
                    print(f"  ✗ widget.update_appearance() failed: {e}")
            else:
                print("  ✗ widget.update_appearance() does NOT exist")
            
            # Check if update exists
            if hasattr(widget, 'update'):
                print("  ✓ widget.update() exists")
                try:
                    widget.update()
                    print("  ✓ widget.update() executed successfully")
                except Exception as e:
                    print(f"  ✗ widget.update() failed: {e}")
            else:
                print("  ✗ widget.update() does NOT exist")
            
            # Save test PDF
            output_path = "samples/checkbox_test_output.pdf"
            doc.save(output_path)
            print(f"\n✓ Saved test PDF to: {output_path}")
            
            # Re-open and verify
            doc2 = fitz.open(output_path)
            page2 = doc2[test_checkbox['page']]
            for widget2 in page2.widgets():
                if widget2.field_name == test_checkbox['name']:
                    print(f"\nVerification - Checkbox value after save: {widget2.field_value}")
                    break
            doc2.close()
        
        doc.close()
        
    except FileNotFoundError:
        print(f"✗ Template not found: {template_path}")
        print("  Please ensure the IRS 1099-DIV template is in the samples/ directory")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_appearance_stream_generation():
    """Test appearance stream generation capabilities."""
    print("=" * 80)
    print("Testing Appearance Stream Generation")
    print("=" * 80)
    
    try:
        # Create a simple test PDF with a checkbox
        doc = fitz.open()
        page = doc.new_page()
        
        # Add a checkbox widget
        rect = fitz.Rect(100, 100, 120, 120)
        
        # Check if we can create widgets programmatically
        print("Testing programmatic widget creation:")
        
        # Try to add a checkbox field
        try:
            widget = fitz.Widget()
            widget.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
            widget.field_name = "test_checkbox"
            widget.rect = rect
            widget.field_value = "Yes"
            
            # Try to add to page
            if hasattr(page, 'add_widget'):
                page.add_widget(widget)
                print("  ✓ Successfully added checkbox widget to page")
            else:
                print("  ✗ page.add_widget() not available")
            
        except Exception as e:
            print(f"  ✗ Failed to create checkbox programmatically: {e}")
        
        # Test drawing checkmark manually
        print("\nTesting manual checkmark drawing:")
        try:
            # Draw checkbox border
            page.draw_rect(rect, color=(0, 0, 0), width=1)
            print("  ✓ Drew checkbox border")
            
            # Draw checkmark
            x0, y0, x1, y1 = rect
            width = x1 - x0
            height = y1 - y0
            
            # Checkmark strokes
            p1 = fitz.Point(x0 + width * 0.2, y0 + height * 0.5)
            p2 = fitz.Point(x0 + width * 0.4, y0 + height * 0.7)
            p3 = fitz.Point(x0 + width * 0.4, y0 + height * 0.7)
            p4 = fitz.Point(x0 + width * 0.8, y0 + height * 0.3)
            
            page.draw_line(p1, p2, color=(0, 0, 0), width=2)
            page.draw_line(p3, p4, color=(0, 0, 0), width=2)
            print("  ✓ Drew checkmark")
            
            # Save test
            output_path = "samples/manual_checkbox_test.pdf"
            doc.save(output_path)
            print(f"  ✓ Saved manual checkbox test to: {output_path}")
            
        except Exception as e:
            print(f"  ✗ Failed to draw checkmark manually: {e}")
        
        doc.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def check_pdf_widget_constants():
    """Check available PDF widget type constants."""
    print("=" * 80)
    print("PDF Widget Type Constants")
    print("=" * 80)
    
    constants = [
        'PDF_WIDGET_TYPE_BUTTON',
        'PDF_WIDGET_TYPE_CHECKBOX',
        'PDF_WIDGET_TYPE_COMBOBOX',
        'PDF_WIDGET_TYPE_LISTBOX',
        'PDF_WIDGET_TYPE_RADIOBUTTON',
        'PDF_WIDGET_TYPE_SIGNATURE',
        'PDF_WIDGET_TYPE_TEXT',
        'PDF_WIDGET_TYPE_UNKNOWN'
    ]
    
    for const in constants:
        if hasattr(fitz, const):
            value = getattr(fitz, const)
            print(f"  ✓ {const} = {value}")
        else:
            print(f"  ✗ {const} not available")
    
    print()


def main():
    """Run all research tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PyMuPDF Checkbox Research" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    check_pymupdf_version()
    check_pdf_widget_constants()
    inspect_widget_methods()
    test_checkbox_with_template()
    test_appearance_stream_generation()
    
    print("=" * 80)
    print("Research Complete")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
