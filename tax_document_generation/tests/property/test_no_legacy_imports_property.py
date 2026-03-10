"""
Property Test: No Legacy Library Imports

Feature: pymupdf-migration, Property 2: No Legacy Library Imports

**Validates: Requirements 1.5**

This test verifies that the document_generator module does not contain
import statements for pypdf or PyPDF2.
"""

import ast
from pathlib import Path


def test_document_generator_has_no_legacy_imports():
    """
    Property 2: No Legacy Library Imports
    
    For any source file in the document_generator module, it SHALL NOT contain
    import statements for pypdf or PyPDF2.
    
    **Validates: Requirements 1.5**
    """
    # Find the document_generator.py file
    document_generator_path = Path(__file__).parent.parent / "document_generator.py"
    
    assert document_generator_path.exists(), \
        f"document_generator.py not found at {document_generator_path}"
    
    # Read the source code
    with open(document_generator_path, 'r') as f:
        source_code = f.read()
    
    # Parse the AST to find all imports
    tree = ast.parse(source_code)
    
    imported_modules = set()
    
    for node in ast.walk(tree):
        # Check for "import X" statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.lower())
        
        # Check for "from X import Y" statements
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.lower())
    
    # Verify pypdf is NOT imported
    assert 'pypdf' not in imported_modules, \
        "document_generator.py must NOT import pypdf"
    
    # Verify PyPDF2 is NOT imported
    assert 'pypdf2' not in imported_modules, \
        "document_generator.py must NOT import PyPDF2"
    
    # Also check for string occurrences in comments or strings
    # (to catch any lingering references)
    lines = source_code.split('\n')
    for i, line in enumerate(lines, 1):
        # Skip if it's just a comment explaining the migration
        if 'pypdf' in line.lower() and 'import' in line.lower():
            # Check if it's an actual import statement (not commented out)
            stripped = line.strip()
            if not stripped.startswith('#'):
                assert False, \
                    f"Found pypdf/PyPDF2 import reference at line {i}: {line}"


def test_document_generator_imports_pymupdf():
    """
    Verify that document_generator.py imports PyMuPDF (fitz).
    
    This is a complementary test to ensure the module has the correct import.
    """
    # Find the document_generator.py file
    document_generator_path = Path(__file__).parent.parent / "document_generator.py"
    
    assert document_generator_path.exists(), \
        f"document_generator.py not found at {document_generator_path}"
    
    # Read the source code
    with open(document_generator_path, 'r') as f:
        source_code = f.read()
    
    # Parse the AST to find all imports
    tree = ast.parse(source_code)
    
    imported_modules = set()
    
    for node in ast.walk(tree):
        # Check for "import X" statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.lower())
        
        # Check for "from X import Y" statements
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.lower())
    
    # Verify fitz (PyMuPDF) is imported
    assert 'fitz' in imported_modules, \
        "document_generator.py must import fitz (PyMuPDF)"


def test_document_generator_has_no_library_flags():
    """
    Verify that document_generator.py does not contain USING_PYMUPDF or USING_PYPDF flags.
    
    These flags were used in the old fallback mechanism and should be removed.
    """
    # Find the document_generator.py file
    document_generator_path = Path(__file__).parent.parent / "document_generator.py"
    
    assert document_generator_path.exists(), \
        f"document_generator.py not found at {document_generator_path}"
    
    # Read the source code
    with open(document_generator_path, 'r') as f:
        source_code = f.read()
    
    # Check for flag definitions
    assert 'USING_PYMUPDF' not in source_code, \
        "document_generator.py must NOT contain USING_PYMUPDF flag"
    
    assert 'USING_PYPDF' not in source_code, \
        "document_generator.py must NOT contain USING_PYPDF flag"


def test_document_generator_has_clear_import_error():
    """
    Verify that document_generator.py raises a clear ImportError if PyMuPDF is not installed.
    
    The error message should include installation instructions.
    """
    # Find the document_generator.py file
    document_generator_path = Path(__file__).parent.parent / "document_generator.py"
    
    assert document_generator_path.exists(), \
        f"document_generator.py not found at {document_generator_path}"
    
    # Read the source code
    with open(document_generator_path, 'r') as f:
        source_code = f.read()
    
    # Check for ImportError with installation instructions
    assert 'ImportError' in source_code, \
        "document_generator.py should raise ImportError if PyMuPDF is not installed"
    
    assert 'pip install PyMuPDF' in source_code, \
        "ImportError message should include installation instructions"
    
    assert '>=1.23.0' in source_code, \
        "ImportError message should specify minimum PyMuPDF version"
