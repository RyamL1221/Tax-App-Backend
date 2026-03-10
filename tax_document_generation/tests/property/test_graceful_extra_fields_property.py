"""
Property Test: Graceful Handling of Extra Fields

Feature: fix-pdf-form-field-error
Property 2: Graceful Handling of Extra Fields

Tests that document generation completes successfully when form data contains
extra fields not present in the template, and that the output is a valid PDF.

**Validates: Requirements 3.3**
"""

import pytest
from hypothesis import given, strategies as st, settings
import os
from io import BytesIO

try:
    import fitz  # PyMuPDF
except ImportError:
    pytest.skip("PyMuPDF not installed", allow_module_level=True)

from tax_document_generation.document_generator import generate_document
from tax_document_generation.exceptions import GenerationError


# Load the actual 1099-DIV template once
def get_1099_div_template():
    """Load the actual 1099-DIV template from the project root."""
    # Get the project root (3 levels up from this test file)
    test_dir = os.path.dirname(os.path.abspath(__file__))
    tax_doc_dir = os.path.dirname(test_dir)
    project_root = os.path.dirname(tax_doc_dir)
    template_path = os.path.join(project_root, "1099-DIV.pdf")
    
    if not os.path.exists(template_path):
        pytest.skip(f"1099-DIV template not found at {template_path}")
    
    with open(template_path, "rb") as f:
        return f.read()


@st.composite
def form_data_with_extra_fields(draw):
    """
    Generate form data that includes both valid fields and extra fields
    not present in the 1099-DIV template.
    
    This strategy generates:
    - Some valid 1099-DIV fields (to ensure the document has some content)
    - Random extra fields with random names and values
    """
    # Start with some valid fields
    form_data = {
        "payerName": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), 
            blacklist_characters='\n\r\t'
        ))),
        "payerTIN": draw(st.from_regex(r'\d{2}-\d{7}', fullmatch=True)),
        "recipientTIN": draw(st.from_regex(r'\d{3}-\d{2}-\d{4}', fullmatch=True)),
        "recipientName": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Zs'), 
            blacklist_characters='\n\r\t'
        ))),
        "totalOrdinaryDividends": draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)),
    }
    
    # Add random extra fields that definitely don't exist in the template
    num_extra_fields = draw(st.integers(min_value=1, max_value=10))
    
    for i in range(num_extra_fields):
        # Generate field names that are unlikely to exist in the template
        field_name = draw(st.text(
            min_size=5, 
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                blacklist_characters='\n\r\t'
            )
        ))
        
        # Prefix with "extra_" to make it clear these are extra fields
        field_name = f"extra_{field_name}_{i}"
        
        # Generate random values of different types
        value_type = draw(st.sampled_from(['string', 'number', 'boolean']))
        
        if value_type == 'string':
            form_data[field_name] = draw(st.text(min_size=0, max_size=100))
        elif value_type == 'number':
            form_data[field_name] = draw(st.one_of(
                st.integers(min_value=-1000000, max_value=1000000),
                st.floats(min_value=-1000000, max_value=1000000, allow_nan=False, allow_infinity=False)
            ))
        else:  # boolean
            form_data[field_name] = draw(st.booleans())
    
    return form_data


@settings(max_examples=20, deadline=None)
@given(form_data=form_data_with_extra_fields())
def test_graceful_handling_of_extra_fields(form_data):
    """
    Property: For any form data that contains extra fields not present in the template,
    document generation should complete successfully and return a valid PDF.
    
    This test verifies that the document generator gracefully handles extra fields
    by ignoring them without causing errors.
    
    **Validates: Requirements 3.3**
    """
    # Load the actual 1099-DIV template
    template = get_1099_div_template()
    
    # Generate the document - this should complete successfully even with extra fields
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify the result is valid PDF bytes
    assert isinstance(result, bytes), "Result should be bytes"
    assert len(result) > 0, "Result should not be empty"
    
    # Verify we can open the generated PDF with PyMuPDF (validates it's a valid PDF)
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0, "Generated PDF should have at least one page"
    doc.close()


def test_graceful_extra_fields_minimal():
    """
    Unit test: Verify graceful handling of extra fields with minimal valid fields.
    
    This test uses only required fields plus several extra fields to ensure
    the generator handles extra fields correctly.
    """
    template = get_1099_div_template()
    
    form_data = {
        # Valid required fields
        "payerName": "Test Payer Inc",
        "payerTIN": "12-3456789",
        "recipientTIN": "123-45-6789",
        "recipientName": "John Doe",
        "totalOrdinaryDividends": 1000.00,
        
        # Extra fields that don't exist in the template
        "extra_field_1": "This field doesn't exist",
        "extra_field_2": 12345,
        "extra_field_3": True,
        "nonexistent_field": "Should be ignored",
        "random_data": 99.99,
    }
    
    # This should complete successfully
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can open the PDF with PyMuPDF
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0
    doc.close()


def test_graceful_extra_fields_only():
    """
    Unit test: Verify graceful handling when form data contains ONLY extra fields.
    
    This test ensures the generator handles the edge case where all provided
    fields are extra (none match the template).
    """
    template = get_1099_div_template()
    
    form_data = {
        # Only extra fields - none of these exist in the template
        "completely_fake_field_1": "Value 1",
        "completely_fake_field_2": "Value 2",
        "nonexistent_field_3": 123,
        "random_field_4": True,
        "another_fake_field_5": 456.78,
    }
    
    # This should complete successfully (produces a copy of the template)
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can open the PDF with PyMuPDF
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0
    doc.close()


def test_graceful_extra_fields_mixed():
    """
    Unit test: Verify graceful handling with a mix of valid and extra fields.
    
    This test uses a realistic scenario with many valid fields and many extra fields.
    """
    template = get_1099_div_template()
    
    form_data = {
        # Valid fields
        "payerName": "Vanguard Investments",
        "payerTIN": "23-1945930",
        "recipientTIN": "123-45-6789",
        "recipientName": "Jane Smith",
        "totalOrdinaryDividends": 5000.00,
        "qualifiedDividends": 3000.00,
        "payerStreetAddress": "100 Vanguard Blvd",
        "payerCity": "Malvern",
        "payerState": "PA",
        
        # Extra fields interspersed
        "extra_metadata_1": "Some metadata",
        "extra_internal_id": "ABC123",
        "extra_processing_flag": True,
        "extra_timestamp": "2025-01-01T00:00:00Z",
        "extra_user_id": 12345,
        "extra_batch_number": 999,
        "extra_validation_status": "passed",
        "extra_notes": "This is a test document",
    }
    
    # This should complete successfully
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can open the PDF with PyMuPDF
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0
    doc.close()
