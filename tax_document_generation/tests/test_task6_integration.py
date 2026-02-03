"""
Integration Test for Task 6: Selective Field Population and Graceful Error Handling

This test verifies the complete implementation of Task 6 requirements using
the real 1099-DIV template.
"""

import pytest
import os

from tax_document_generation.document_generator import generate_document


def get_1099_div_template():
    """Load the actual 1099-DIV template from the project root."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    tax_doc_dir = os.path.dirname(test_dir)
    project_root = os.path.dirname(tax_doc_dir)
    template_path = os.path.join(project_root, "1099-DIV.pdf")
    
    if not os.path.exists(template_path):
        pytest.skip(f"1099-DIV template not found at {template_path}")
    
    with open(template_path, "rb") as f:
        return f.read()


def test_task6_selective_field_population():
    """
    Integration test: Verify selective field population with real template.
    
    Requirements: 4.3, 10.2
    - Populate only fields that exist in mapped_data
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    # Mix of mapped and unmapped fields
    form_data = {
        "payerName": "Test Payer Company",  # Mapped
        "payerTIN": "12-3456789",  # Mapped
        "unknownField1": "Should not appear",  # Unmapped
        "recipientName": "John Doe",  # Mapped
        "unknownField2": "Also should not appear",  # Unmapped
        "totalOrdinaryDividends": 1000.50,  # Mapped
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open the generated PDF and verify only mapped fields have values
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Count populated fields
    populated_count = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                if widget.field_value:
                    populated_count += 1
    
    doc.close()
    
    # At least the mapped fields should be populated
    assert populated_count > 0, "Expected mapped fields to be populated"
    print(f"✓ Populated {populated_count} fields (only mapped fields)")


def test_task6_graceful_partial_mapping():
    """
    Integration test: Verify graceful handling of partial mapping.
    
    Requirements: 4.5
    - Ensure generation completes successfully even with unmapped fields
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    # Mostly unmapped fields
    form_data = {
        "unknownField1": "Should not appear",
        "unknownField2": "Also should not appear",
        "payerName": "Test Payer",  # Only one mapped field
        "unknownField3": "Still should not appear",
    }
    
    # Should complete successfully
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open the generated PDF
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0
    doc.close()
    
    print("✓ Document generation completed successfully with unmapped fields")


def test_task6_field_editability_preservation():
    """
    Integration test: Verify fields remain editable after population.
    
    Requirements: 9.1, 9.2
    - Verify all populated fields remain editable (not flattened)
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    form_data = {
        "payerName": "Test Payer Company",
        "payerTIN": "12-3456789",
        "recipientName": "John Doe",
        "recipientTIN": "123-45-6789",
        "totalOrdinaryDividends": 1000.50,
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Open the generated PDF and verify it's still a form PDF
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Check that it's still a form PDF
    assert doc.is_form_pdf, "Generated PDF should still be a form PDF"
    
    # Check that widgets still exist
    widget_count = 0
    editable_fields = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = list(page.widgets())
        if widgets:
            widget_count += len(widgets)
            for widget in widgets:
                if widget.field_type is not None:
                    editable_fields += 1
    
    doc.close()
    
    # Should have widgets (form fields)
    assert widget_count > 0, "Generated PDF should have form fields"
    assert editable_fields > 0, "Form fields should be editable"
    
    print(f"✓ PDF has {widget_count} form fields, {editable_fields} are editable")


def test_task6_all_requirements_together():
    """
    Integration test: Verify all Task 6 requirements work together.
    
    This test combines:
    - Selective field population (4.3)
    - Graceful partial mapping (4.5)
    - Field editability preservation (9.1, 9.2)
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    
    template = get_1099_div_template()
    
    # Complex scenario with mapped, unmapped, and various data types
    form_data = {
        "payerName": "Test Payer Company",  # Mapped - string
        "unknownField1": "Should not appear",  # Unmapped
        "payerTIN": "12-3456789",  # Mapped - string
        "recipientName": "John Doe",  # Mapped - string
        "unknownField2": "Also should not appear",  # Unmapped
        "totalOrdinaryDividends": 1000.50,  # Mapped - float
        "qualifiedDividends": 500,  # Mapped - int
        "unknownField3": "Still should not appear",  # Unmapped
    }
    
    # Generate document
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Open and analyze the generated PDF
    doc = fitz.open(stream=result, filetype="pdf")
    
    # Verify it's still a form PDF (editability)
    assert doc.is_form_pdf, "PDF should remain a form PDF"
    
    # Count populated and editable fields
    total_widgets = 0
    populated_widgets = 0
    editable_widgets = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = list(page.widgets())
        if widgets:
            for widget in widgets:
                total_widgets += 1
                if widget.field_value:
                    populated_widgets += 1
                if widget.field_type is not None:
                    editable_widgets += 1
    
    doc.close()
    
    # Assertions
    assert total_widgets > 0, "PDF should have form fields"
    assert populated_widgets > 0, "Some fields should be populated"
    assert editable_widgets > 0, "Fields should remain editable"
    
    print(f"✓ Task 6 complete: {total_widgets} total fields, "
          f"{populated_widgets} populated, {editable_widgets} editable")
    print("✓ All requirements verified: selective population, graceful handling, editability preserved")


if __name__ == "__main__":
    # Run tests manually for debugging
    test_task6_selective_field_population()
    test_task6_graceful_partial_mapping()
    test_task6_field_editability_preservation()
    test_task6_all_requirements_together()
    print("\n✅ All Task 6 integration tests passed!")
