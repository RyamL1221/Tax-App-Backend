"""
Property Test: API Signature Preservation

Feature: pymupdf-migration, Property 6: API Signature Preservation

**Validates: Requirements 3.1**

This test verifies that the generate_document function maintains its API signature:
- Accepts exactly three parameters: template (bytes), form_data (Dict), document_type (str)
- Returns bytes
- The signature remains unchanged after the PyMuPDF migration
"""

import inspect
from typing import Dict, get_type_hints
import pytest

from tax_document_generation.document_generator import generate_document


def test_generate_document_signature():
    """
    Property 6: API Signature Preservation
    
    For any call to generate_document, the function SHALL accept exactly three
    parameters (template: bytes, form_data: Dict, document_type: str) and return bytes.
    
    This test verifies that the function signature is preserved after migration,
    ensuring backward compatibility with existing calling code.
    
    **Validates: Requirements 3.1**
    """
    # Get the function signature
    sig = inspect.signature(generate_document)
    
    # Verify the function has exactly 3 parameters
    params = list(sig.parameters.keys())
    assert len(params) == 3, \
        f"generate_document should have exactly 3 parameters, found {len(params)}: {params}"
    
    # Verify parameter names
    assert params[0] == "template", \
        f"First parameter should be 'template', found '{params[0]}'"
    assert params[1] == "form_data", \
        f"Second parameter should be 'form_data', found '{params[1]}'"
    assert params[2] == "document_type", \
        f"Third parameter should be 'document_type', found '{params[2]}'"
    
    # Get type hints
    type_hints = get_type_hints(generate_document)
    
    # Verify parameter types
    assert type_hints.get('template') == bytes, \
        f"Parameter 'template' should be type bytes, found {type_hints.get('template')}"
    assert type_hints.get('form_data') == Dict, \
        f"Parameter 'form_data' should be type Dict, found {type_hints.get('form_data')}"
    assert type_hints.get('document_type') == str, \
        f"Parameter 'document_type' should be type str, found {type_hints.get('document_type')}"
    
    # Verify return type
    assert type_hints.get('return') == bytes, \
        f"Return type should be bytes, found {type_hints.get('return')}"


def test_generate_document_callable():
    """
    Unit test: Verify generate_document is callable.
    
    This test ensures the function exists and can be called.
    """
    assert callable(generate_document), "generate_document should be callable"


def test_generate_document_no_default_parameters():
    """
    Unit test: Verify generate_document has no default parameters.
    
    All three parameters should be required (no defaults).
    """
    sig = inspect.signature(generate_document)
    
    for param_name, param in sig.parameters.items():
        assert param.default == inspect.Parameter.empty, \
            f"Parameter '{param_name}' should not have a default value"


def test_generate_document_positional_parameters():
    """
    Unit test: Verify all parameters can be passed positionally.
    
    This ensures backward compatibility with code that calls the function
    with positional arguments.
    """
    sig = inspect.signature(generate_document)
    
    for param_name, param in sig.parameters.items():
        # Parameters should be POSITIONAL_OR_KEYWORD (not keyword-only)
        assert param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, 
                              inspect.Parameter.POSITIONAL_ONLY), \
            f"Parameter '{param_name}' should accept positional arguments"


def test_generate_document_no_var_args():
    """
    Unit test: Verify generate_document does not accept *args or **kwargs.
    
    The function should have a fixed signature with exactly 3 parameters.
    """
    sig = inspect.signature(generate_document)
    
    for param_name, param in sig.parameters.items():
        assert param.kind not in (inspect.Parameter.VAR_POSITIONAL, 
                                  inspect.Parameter.VAR_KEYWORD), \
            f"Function should not have *args or **kwargs, found {param_name}"


def test_generate_document_docstring_exists():
    """
    Unit test: Verify generate_document has a docstring.
    
    The function should be documented for maintainability.
    """
    assert generate_document.__doc__ is not None, \
        "generate_document should have a docstring"
    assert len(generate_document.__doc__.strip()) > 0, \
        "generate_document docstring should not be empty"
    
    # Verify key information is in the docstring
    docstring = generate_document.__doc__.lower()
    assert "template" in docstring, "Docstring should mention 'template' parameter"
    assert "form_data" in docstring, "Docstring should mention 'form_data' parameter"
    assert "document_type" in docstring, "Docstring should mention 'document_type' parameter"
    assert "bytes" in docstring, "Docstring should mention return type 'bytes'"
