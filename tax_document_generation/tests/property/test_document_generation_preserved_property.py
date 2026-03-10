"""
Property Test: Document Generation Functionality Preserved

Feature: fix-tax-document-lambda-imports
Property 3: Document Generation Functionality Preserved

**Validates: Requirements 2.2**

This test verifies that converting relative imports to absolute imports
preserves all existing document generation functionality. The document
generator should produce non-empty PDF output with the same behavior
as before the import changes.
"""

import pytest
from hypothesis import given, strategies as st, settings
import os

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
def valid_form_data(draw):
    """
    Generate random valid form data for document generation testing.
    
    This strategy generates various combinations of valid form fields
    to test that document generation works across different inputs.
    """
    form_data = {}
    
    # Randomly include various fields to test different combinations
    if draw(st.booleans()):
        form_data["payerName"] = draw(st.text(
            min_size=1, 
            max_size=100, 
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), 
                blacklist_characters='\n\r\t'
            )
        ))
    
    if draw(st.booleans()):
        form_data["payerTIN"] = draw(st.from_regex(r'\d{2}-\d{7}', fullmatch=True))
    
    if draw(st.booleans()):
        form_data["recipientTIN"] = draw(st.from_regex(r'\d{3}-\d{2}-\d{4}', fullmatch=True))
    
    if draw(st.booleans()):
        form_data["recipientName"] = draw(st.text(
            min_size=1, 
            max_size=100, 
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Zs'), 
                blacklist_characters='\n\r\t'
            )
        ))
    
    if draw(st.booleans()):
        form_data["totalOrdinaryDividends"] = draw(st.floats(
            min_value=0, 
            max_value=1000000, 
            allow_nan=False, 
            allow_infinity=False
        ))
    
    if draw(st.booleans()):
        form_data["qualifiedDividends"] = draw(st.floats(
            min_value=0, 
            max_value=1000000, 
            allow_nan=False, 
            allow_infinity=False
        ))
    
    if draw(st.booleans()):
        form_data["totalCapitalGainDistributions"] = draw(st.floats(
            min_value=0, 
            max_value=1000000, 
            allow_nan=False, 
            allow_infinity=False
        ))
    
    if draw(st.booleans()):
        form_data["federalIncomeTaxWithheld"] = draw(st.floats(
            min_value=0, 
            max_value=100000, 
            allow_nan=False, 
            allow_infinity=False
        ))
    
    if draw(st.booleans()):
        form_data["section199ADividends"] = draw(st.floats(
            min_value=0, 
            max_value=1000000, 
            allow_nan=False, 
            allow_infinity=False
        ))
    
    if draw(st.booleans()):
        form_data["investmentExpenses"] = draw(st.floats(
            min_value=0, 
            max_value=10000, 
            allow_nan=False, 
            allow_infinity=False
        ))
    
    if draw(st.booleans()):
        form_data["foreignTaxPaid"] = draw(st.floats(
            min_value=0, 
            max_value=10000, 
            allow_nan=False, 
            allow_infinity=False
        ))
    
    if draw(st.booleans()):
        form_data["payerStreetAddress"] = draw(st.text(
            min_size=1, 
            max_size=100, 
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), 
                blacklist_characters='\n\r\t'
            )
        ))
    
    if draw(st.booleans()):
        form_data["payerCity"] = draw(st.text(
            min_size=1, 
            max_size=50, 
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Zs'), 
                blacklist_characters='\n\r\t'
            )
        ))
    
    if draw(st.booleans()):
        form_data["payerState"] = draw(st.from_regex(r'[A-Z]{2}', fullmatch=True))
    
    if draw(st.booleans()):
        form_data["payerZip"] = draw(st.from_regex(r'\d{5}', fullmatch=True))
    
    if draw(st.booleans()):
        form_data["recipientStreetAddress"] = draw(st.text(
            min_size=1, 
            max_size=100, 
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), 
                blacklist_characters='\n\r\t'
            )
        ))
    
    if draw(st.booleans()):
        form_data["recipientCity"] = draw(st.text(
            min_size=1, 
            max_size=50, 
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Zs'), 
                blacklist_characters='\n\r\t'
            )
        ))
    
    if draw(st.booleans()):
        form_data["recipientState"] = draw(st.from_regex(r'[A-Z]{2}', fullmatch=True))
    
    if draw(st.booleans()):
        form_data["recipientZip"] = draw(st.from_regex(r'\d{5}', fullmatch=True))
    
    if draw(st.booleans()):
        form_data["accountNumber"] = draw(st.text(
            min_size=1, 
            max_size=20, 
            alphabet=st.characters(
                whitelist_categories=('Nd',)
            )
        ))
    
    if draw(st.booleans()):
        form_data["calendarYear"] = draw(st.integers(min_value=2020, max_value=2030))
    
    return form_data


@settings(max_examples=20, deadline=None)
@given(form_data=valid_form_data())
def test_document_generation_preserved(form_data):
    """
    Property 3: Document Generation Functionality Preserved
    
    For any valid document generation request (with valid template and form data),
    the document generator SHALL produce a non-empty PDF output with the same
    behavior as before the import changes.
    
    This test verifies that:
    1. The document_generator.generate_document() function can be invoked successfully
    2. No exceptions are raised during document generation
    3. The output is non-empty PDF bytes
    4. The generated PDF is valid and can be opened with PyMuPDF
    
    The import changes (relative to absolute) should not affect runtime behavior.
    
    **Validates: Requirements 2.2**
    Feature: fix-tax-document-lambda-imports, Property 3: Document generation functionality preserved
    """
    # Load the actual 1099-DIV template
    template = get_1099_div_template()
    
    # Generate the document - this should not raise any exceptions
    try:
        result = generate_document(template, form_data, "1099-DIV")
    except GenerationError as e:
        pytest.fail(f"Document generation raised GenerationError: {e}")
    except Exception as e:
        pytest.fail(f"Document generation raised unexpected exception: {e}")
    
    # Verify output is non-empty PDF bytes
    assert isinstance(result, bytes), "Result should be bytes"
    assert len(result) > 0, "Result should have non-zero size (non-empty PDF)"
    
    # Verify the generated PDF is valid by opening it with PyMuPDF
    try:
        doc = fitz.open(stream=result, filetype="pdf")
        assert len(doc) > 0, "Generated PDF should have at least one page"
        doc.close()
    except Exception as e:
        pytest.fail(f"Generated PDF is not valid: {e}")


def test_document_generation_preserved_minimal():
    """
    Unit test: Verify document generation works with minimal form data.
    
    This test ensures that the import fix preserves functionality even
    with minimal input data.
    
    **Validates: Requirements 2.2**
    """
    template = get_1099_div_template()
    
    form_data = {
        "payerName": "Test Payer",
    }
    
    # Should not raise any exceptions
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can open the PDF
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0
    doc.close()


def test_document_generation_preserved_empty():
    """
    Unit test: Verify document generation works with empty form data.
    
    This test ensures that the import fix preserves functionality even
    with no input data (just copying the template).
    
    **Validates: Requirements 2.2**
    """
    template = get_1099_div_template()
    
    form_data = {}
    
    # Should not raise any exceptions
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can open the PDF
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0
    doc.close()


def test_document_generation_preserved_comprehensive():
    """
    Unit test: Verify document generation works with comprehensive form data.
    
    This test ensures that the import fix preserves functionality with
    many fields populated, testing the full field mapping and population logic.
    
    **Validates: Requirements 2.2**
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
    
    # Should not raise any exceptions
    result = generate_document(template, form_data, "1099-DIV")
    
    # Verify output is valid
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Verify we can open the PDF
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) > 0
    doc.close()


def test_document_generation_exception_types_preserved():
    """
    Unit test: Verify that exception types are preserved after import changes.
    
    This test ensures that the import fix preserves error handling behavior,
    specifically that GenerationError is still raised for invalid templates.
    
    **Validates: Requirements 2.4**
    """
    invalid_template = b"not a valid pdf"
    form_data = {"payerName": "Test"}
    
    # Should raise GenerationError (not ImportError or other exception)
    with pytest.raises(GenerationError) as exc_info:
        generate_document(invalid_template, form_data, "1099-DIV")
    
    assert "Failed to generate document" in str(exc_info.value)


def test_document_generation_imports_work():
    """
    Unit test: Verify that all imports in document_generator work correctly.
    
    This test specifically validates that the absolute imports allow
    the document_generator module to access its dependencies correctly.
    
    **Validates: Requirements 1.2, 2.1**
    """
    # Import the module - this should work with absolute imports
    from tax_document_generation.document_generator import generate_document
    from tax_document_generation.exceptions import GenerationError
    from tax_document_generation.field_mapper import FieldMapper
    
    # Verify all imports are accessible
    assert generate_document is not None
    assert GenerationError is not None
    assert FieldMapper is not None
    
    # Verify FieldMapper can be instantiated (tests that its imports work too)
    mapper = FieldMapper("1099-DIV")
    assert mapper is not None
