"""
Property Test: No PdfObject Type Errors

Feature: fix-pdf-form-field-error
Property 1: No PdfObject Type Errors

Tests that document generation completes without raising "key must be PdfObject" errors
for any valid form data and the actual 1099-DIV template.

**Validates: Requirements 2.2, 2.4**
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
def valid_1099_div_form_data(draw):
    """
    Generate valid form data for 1099-DIV forms.
    
    This strategy generates random but valid form data that includes:
    - Required fields (payerName, payerTIN, recipientTIN, recipientName, totalOrdinaryDividends)
    - Random selection of optional fields
    - Properly formatted values (TINs, SSNs, amounts, etc.)
    """
    # Generate required fields
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
    
    # Randomly add optional payer information fields
    if draw(st.booleans()):
        form_data["payerStreetAddress"] = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pd'), 
            blacklist_characters='\n\r\t'
        )))
    
    if draw(st.booleans()):
        form_data["payerCity"] = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Zs'), 
            blacklist_characters='\n\r\t'
        )))
    
    if draw(st.booleans()):
        form_data["payerState"] = draw(st.sampled_from([
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
            "DC", "PR", "VI", "GU", "AS", "MP"
        ]))
    
    if draw(st.booleans()):
        form_data["payerZip"] = draw(st.one_of(
            st.from_regex(r'\d{5}', fullmatch=True),
            st.from_regex(r'\d{5}-\d{4}', fullmatch=True)
        ))
    
    # Randomly add optional recipient information fields
    if draw(st.booleans()):
        form_data["recipientStreetAddress"] = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pd'), 
            blacklist_characters='\n\r\t'
        )))
    
    if draw(st.booleans()):
        form_data["recipientCity"] = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Zs'), 
            blacklist_characters='\n\r\t'
        )))
    
    if draw(st.booleans()):
        form_data["recipientState"] = draw(st.sampled_from([
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
            "DC", "PR", "VI", "GU", "AS", "MP"
        ]))
    
    if draw(st.booleans()):
        form_data["recipientZip"] = draw(st.one_of(
            st.from_regex(r'\d{5}', fullmatch=True),
            st.from_regex(r'\d{5}-\d{4}', fullmatch=True)
        ))
    
    # Randomly add optional account and year fields
    if draw(st.booleans()):
        form_data["accountNumber"] = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Nd', 'Lu', 'Ll'), 
            blacklist_characters='\n\r\t'
        )))
    
    if draw(st.booleans()):
        form_data["calendarYear"] = str(draw(st.integers(min_value=2000, max_value=2100)))
    
    # Randomly add optional dividend fields
    if draw(st.booleans()):
        form_data["qualifiedDividends"] = draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False))
    
    if draw(st.booleans()):
        form_data["totalCapitalGainDistributions"] = draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False))
    
    if draw(st.booleans()):
        form_data["federalIncomeTaxWithheld"] = draw(st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False))
    
    if draw(st.booleans()):
        form_data["section199ADividends"] = draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False))
    
    if draw(st.booleans()):
        form_data["investmentExpenses"] = draw(st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False))
    
    if draw(st.booleans()):
        form_data["foreignTaxPaid"] = draw(st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False))
    
    return form_data


@settings(max_examples=20, deadline=None)
@given(form_data=valid_1099_div_form_data())
def test_no_pdfobject_type_errors(form_data):
    """
    Property: For any valid form data and the actual 1099-DIV template,
    document generation should complete without raising a "key must be PdfObject" error.
    
    This test verifies that the fix for the PDF form field manipulation issue works
    correctly across a wide range of random but valid inputs.
    
    **Validates: Requirements 2.2, 2.4**
    """
    # Load the actual 1099-DIV template
    template = get_1099_div_template()
    
    # Generate the document - this should NOT raise "key must be PdfObject" error
    try:
        result = generate_document(template, form_data, "1099-DIV")
        
        # Verify the result is valid PDF bytes
        assert isinstance(result, bytes), "Result should be bytes"
        assert len(result) > 0, "Result should not be empty"
        
        # Verify we can read the generated PDF (validates it's a valid PDF)
        reader = PdfReader(BytesIO(result))
        assert len(reader.pages) > 0, "Generated PDF should have at least one page"
        
    except GenerationError as e:
        # If a GenerationError is raised, it should NOT be due to "key must be PdfObject"
        error_message = str(e).lower()
        assert "key must be pdfobject" not in error_message, \
            f"Should not raise 'key must be PdfObject' error, but got: {e}"
        
        # If it's a different GenerationError, that's acceptable for this test
        # (e.g., template issues, but not the specific PdfObject error we're testing)
        pass


def test_no_pdfobject_errors_minimal_fields():
    """
    Unit test: Verify no PdfObject errors with minimal required fields.
    
    This test uses only the required fields to ensure the fix works
    in the simplest case.
    """
    template = get_1099_div_template()
    
    form_data = {
        "payerName": "Test Payer Inc",
        "payerTIN": "12-3456789",
        "recipientTIN": "123-45-6789",
        "recipientName": "John Doe",
        "totalOrdinaryDividends": 1000.00,
    }
    
    # This should NOT raise "key must be PdfObject" error
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can read the PDF
    reader = PdfReader(BytesIO(result))
    assert len(reader.pages) > 0


def test_no_pdfobject_errors_all_fields():
    """
    Unit test: Verify no PdfObject errors with all possible fields.
    
    This test uses a comprehensive set of fields to ensure the fix works
    when populating many form fields.
    """
    template = get_1099_div_template()
    
    form_data = {
        # Required fields
        "payerName": "Vanguard Investments",
        "payerTIN": "23-1945930",
        "recipientTIN": "123-45-6789",
        "recipientName": "Jane Smith",
        "totalOrdinaryDividends": 5000.00,
        
        # Optional payer information
        "payerStreetAddress": "100 Vanguard Blvd",
        "payerCity": "Malvern",
        "payerState": "PA",
        "payerZip": "19355",
        
        # Optional recipient information
        "recipientStreetAddress": "456 Main St",
        "recipientCity": "Boston",
        "recipientState": "MA",
        "recipientZip": "02101",
        
        # Optional account and year
        "accountNumber": "12345678",
        "calendarYear": "2025",
        
        # Optional dividend fields
        "qualifiedDividends": 3000.00,
        "totalCapitalGainDistributions": 1500.00,
        "federalIncomeTaxWithheld": 500.00,
        "section199ADividends": 2000.00,
        "investmentExpenses": 50.00,
        "foreignTaxPaid": 0.00,
    }
    
    # This should NOT raise "key must be PdfObject" error
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can read the PDF
    reader = PdfReader(BytesIO(result))
    assert len(reader.pages) > 0


def test_no_pdfobject_errors_empty_form_data():
    """
    Unit test: Verify no PdfObject errors with empty form data.
    
    This test ensures the fix works even when no form data is provided,
    which should produce a copy of the template.
    """
    template = get_1099_div_template()
    
    form_data = {}
    
    # This should NOT raise "key must be PdfObject" error
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can read the PDF
    reader = PdfReader(BytesIO(result))
    assert len(reader.pages) > 0
