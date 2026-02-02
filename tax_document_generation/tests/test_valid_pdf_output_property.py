"""
Property Test: Valid PDF Output

Feature: fix-pdf-form-field-error
Property 4: Valid PDF Output

Tests that document generation produces valid PDF output that can be read
and has non-zero size for any valid form data.

**Validates: Requirements 6.3, 6.4**
"""

import pytest
from hypothesis import given, strategies as st, settings
import os
from io import BytesIO

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

from tax_document_generation.document_generator import generate_document


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
def valid_form_data(draw):
    """
    Generate valid form data for testing PDF output.
    
    This strategy generates random but valid form data with various field combinations.
    """
    # Always include at least one field
    form_data = {}
    
    # Randomly add fields
    if draw(st.booleans()):
        form_data["payerName"] = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), 
            blacklist_characters='\n\r\t'
        )))
    
    if draw(st.booleans()):
        form_data["payerTIN"] = draw(st.from_regex(r'\d{2}-\d{7}', fullmatch=True))
    
    if draw(st.booleans()):
        form_data["recipientTIN"] = draw(st.from_regex(r'\d{3}-\d{2}-\d{4}', fullmatch=True))
    
    if draw(st.booleans()):
        form_data["recipientName"] = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Zs'), 
            blacklist_characters='\n\r\t'
        )))
    
    if draw(st.booleans()):
        form_data["totalOrdinaryDividends"] = draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False))
    
    if draw(st.booleans()):
        form_data["qualifiedDividends"] = draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False))
    
    if draw(st.booleans()):
        form_data["totalCapitalGainDistributions"] = draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False))
    
    if draw(st.booleans()):
        form_data["federalIncomeTaxWithheld"] = draw(st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False))
    
    return form_data


@settings(max_examples=20, deadline=None)
@given(form_data=valid_form_data())
def test_valid_pdf_output(form_data):
    """
    Property: For any valid form data, document generation should produce
    valid PDF output that can be read by PdfReader and has non-zero size.
    
    This test verifies that the generated output is always a valid, readable PDF.
    
    **Validates: Requirements 6.3, 6.4**
    """
    # Load the actual 1099-DIV template
    template = get_1099_div_template()
    
    # Generate the document
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify the result is bytes
    assert isinstance(result, bytes), "Result should be bytes"
    
    # Verify non-zero size (Requirement 6.4)
    assert len(result) > 0, "Result should have non-zero size"
    
    # Verify we can read the generated PDF (Requirement 6.3)
    try:
        reader = PdfReader(BytesIO(result))
        assert len(reader.pages) > 0, "Generated PDF should have at least one page"
    except Exception as e:
        pytest.fail(f"Generated PDF is not valid: {e}")


def test_valid_pdf_output_minimal():
    """
    Unit test: Verify valid PDF output with minimal form data.
    
    This test ensures that even with minimal data, the output is a valid PDF.
    """
    template = get_1099_div_template()
    
    form_data = {
        "payerName": "Test Payer",
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can read the PDF
    reader = PdfReader(BytesIO(result))
    assert len(reader.pages) > 0


def test_valid_pdf_output_empty():
    """
    Unit test: Verify valid PDF output with empty form data.
    
    This test ensures that even with no data, the output is a valid PDF
    (a copy of the template).
    """
    template = get_1099_div_template()
    
    form_data = {}
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can read the PDF
    reader = PdfReader(BytesIO(result))
    assert len(reader.pages) > 0


def test_valid_pdf_output_comprehensive():
    """
    Unit test: Verify valid PDF output with comprehensive form data.
    
    This test ensures that with many fields populated, the output is a valid PDF.
    """
    template = get_1099_div_template()
    
    form_data = {
        "payerName": "Vanguard Investments",
        "payerTIN": "23-1945930",
        "recipientTIN": "123-45-6789",
        "recipientName": "Jane Smith",
        "totalOrdinaryDividends": 5000.00,
        "qualifiedDividends": 3000.00,
        "totalCapitalGainDistributions": 1500.00,
        "federalIncomeTaxWithheld": 500.00,
        "section199ADividends": 2000.00,
        "investmentExpenses": 50.00,
        "foreignTaxPaid": 0.00,
        "payerStreetAddress": "100 Vanguard Blvd",
        "payerCity": "Malvern",
        "payerState": "PA",
        "payerZip": "19355",
        "recipientStreetAddress": "456 Main St",
        "recipientCity": "Boston",
        "recipientState": "MA",
        "recipientZip": "02101",
        "accountNumber": "12345678",
        "calendarYear": "2025",
    }
    
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can read the PDF
    reader = PdfReader(BytesIO(result))
    assert len(reader.pages) > 0
