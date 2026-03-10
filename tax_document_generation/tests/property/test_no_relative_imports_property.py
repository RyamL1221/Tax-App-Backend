"""
Property Test: No Relative Imports in Lambda Modules

Feature: fix-tax-document-lambda-imports, Property 1: No Relative Imports in Lambda Modules

**Validates: Requirements 1.2, 3.1, 3.2, 3.3, 3.4, 4.4**

This test verifies that no Python files in the tax_document_generation module
use relative imports, which are incompatible with Lambda's execution environment.
"""

import ast
from pathlib import Path
from hypothesis import given, settings, strategies as st


def get_lambda_module_files():
    """
    Get all Python files in the tax_document_generation module (excluding tests).
    
    Returns:
        list: List of Path objects for Python files to check
    """
    module_dir = Path(__file__).parent.parent
    
    # Get all .py files in the module directory (not in subdirectories)
    python_files = []
    for file_path in module_dir.glob("*.py"):
        # Exclude __init__.py and test files
        if file_path.name != "__init__.py":
            python_files.append(file_path)
    
    return python_files


def has_relative_imports(file_path):
    """
    Check if a Python file contains relative imports.
    
    Args:
        file_path: Path to the Python file to check
        
    Returns:
        tuple: (has_relative_imports: bool, relative_imports: list)
    """
    with open(file_path, 'r') as f:
        source_code = f.read()
    
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        # If we can't parse the file, skip it
        return False, []
    
    relative_imports = []
    
    for node in ast.walk(tree):
        # Check for "from .X import Y" statements (relative imports)
        if isinstance(node, ast.ImportFrom):
            # node.level > 0 indicates a relative import
            # level=1 means "from .module", level=2 means "from ..module", etc.
            if node.level > 0:
                module_name = node.module if node.module else ""
                import_names = [alias.name for alias in node.names]
                relative_imports.append({
                    'module': module_name,
                    'names': import_names,
                    'level': node.level,
                    'lineno': node.lineno
                })
    
    return len(relative_imports) > 0, relative_imports


@given(st.sampled_from(get_lambda_module_files()))
@settings(max_examples=20)
def test_no_relative_imports_in_lambda_modules(file_path):
    """
    Property 1: No Relative Imports in Lambda Modules
    
    For any Python file in the tax_document_generation module (excluding tests),
    parsing the file's import statements SHALL find zero relative imports.
    
    Lambda's execution environment treats the handler module as top-level,
    making relative imports fail with "attempted relative import with no known parent package".
    
    **Validates: Requirements 1.2, 3.1, 3.2, 3.3, 3.4, 4.4**
    """
    has_relative, relative_imports = has_relative_imports(file_path)
    
    assert not has_relative, (
        f"File {file_path.name} contains relative imports which are incompatible with Lambda:\n"
        + "\n".join([
            f"  Line {imp['lineno']}: from {'.' * imp['level']}{imp['module']} import {', '.join(imp['names'])}"
            for imp in relative_imports
        ])
    )


def test_document_generator_has_no_relative_imports():
    """
    Specific test for document_generator.py to verify it has no relative imports.
    
    This is the file that was causing the Lambda import error.
    
    **Validates: Requirements 1.2, 1.3, 1.4**
    """
    document_generator_path = Path(__file__).parent.parent / "document_generator.py"
    
    assert document_generator_path.exists(), \
        f"document_generator.py not found at {document_generator_path}"
    
    has_relative, relative_imports = has_relative_imports(document_generator_path)
    
    assert not has_relative, (
        f"document_generator.py contains relative imports:\n"
        + "\n".join([
            f"  Line {imp['lineno']}: from {'.' * imp['level']}{imp['module']} import {', '.join(imp['names'])}"
            for imp in relative_imports
        ])
        + "\n\nExpected absolute imports like:\n"
        + "  from exceptions import GenerationError\n"
        + "  from field_mapper import FieldMapper"
    )


def test_all_lambda_modules_use_absolute_imports():
    """
    Comprehensive test that checks all Lambda module files for relative imports.
    
    This test provides a summary of all files checked and any issues found.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 4.4**
    """
    module_files = get_lambda_module_files()
    
    assert len(module_files) > 0, "No Python files found in tax_document_generation module"
    
    files_with_relative_imports = []
    
    for file_path in module_files:
        has_relative, relative_imports = has_relative_imports(file_path)
        if has_relative:
            files_with_relative_imports.append({
                'file': file_path.name,
                'imports': relative_imports
            })
    
    if files_with_relative_imports:
        error_msg = "The following files contain relative imports:\n\n"
        for file_info in files_with_relative_imports:
            error_msg += f"{file_info['file']}:\n"
            for imp in file_info['imports']:
                error_msg += f"  Line {imp['lineno']}: from {'.' * imp['level']}{imp['module']} import {', '.join(imp['names'])}\n"
            error_msg += "\n"
        error_msg += "All imports must be absolute for Lambda compatibility."
        assert False, error_msg
    
    # If we get here, all files use absolute imports
    print(f"✓ Verified {len(module_files)} Lambda module files use absolute imports")


def test_specific_modules_have_correct_imports():
    """
    Verify that specific modules that commonly need imports use absolute imports.
    
    **Validates: Requirements 1.3, 1.4, 3.3**
    """
    module_dir = Path(__file__).parent.parent
    
    # Check document_generator.py
    document_generator = module_dir / "document_generator.py"
    if document_generator.exists():
        has_relative, _ = has_relative_imports(document_generator)
        assert not has_relative, "document_generator.py must use absolute imports"
    
    # Check field_mapper.py
    field_mapper = module_dir / "field_mapper.py"
    if field_mapper.exists():
        has_relative, _ = has_relative_imports(field_mapper)
        assert not has_relative, "field_mapper.py must use absolute imports"
    
    # Check app.py (Lambda handler)
    app = module_dir / "app.py"
    if app.exists():
        has_relative, _ = has_relative_imports(app)
        assert not has_relative, "app.py must use absolute imports"
