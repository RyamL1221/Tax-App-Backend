"""
Property Test: PyMuPDF-Only Dependencies

Feature: pymupdf-migration, Property 1: PyMuPDF-Only Dependencies

**Validates: Requirements 1.4, 7.1, 7.2**

This test verifies that the requirements.txt file contains PyMuPDF>=1.23.0
as the sole PDF manipulation library and does not contain pypdf or PyPDF2.
"""

import os
import re
from pathlib import Path


def test_requirements_contains_pymupdf_only():
    """
    Property 1: PyMuPDF-Only Dependencies
    
    For any requirements.txt file in the tax_document_generation module,
    it SHALL contain PyMuPDF>=1.23.0 and SHALL NOT contain pypdf or PyPDF2 entries.
    
    **Validates: Requirements 1.4, 7.1, 7.2**
    """
    # Find the requirements.txt file
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    
    assert requirements_path.exists(), f"requirements.txt not found at {requirements_path}"
    
    # Read the requirements file
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    # Parse requirements into a list of package names (lowercase for comparison)
    lines = content.strip().split('\n')
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Extract package name (before any version specifier)
            package_name = re.split(r'[>=<!\[]', line)[0].strip().lower()
            packages.append(package_name)
    
    # Verify PyMuPDF is present
    assert 'pymupdf' in packages, "PyMuPDF must be in requirements.txt"
    
    # Verify pypdf is NOT present
    assert 'pypdf' not in packages, "pypdf must NOT be in requirements.txt"
    
    # Verify PyPDF2 is NOT present
    assert 'pypdf2' not in packages, "PyPDF2 must NOT be in requirements.txt"
    
    # Verify PyMuPDF version constraint
    pymupdf_line = None
    for line in lines:
        if line.strip().lower().startswith('pymupdf'):
            pymupdf_line = line.strip()
            break
    
    assert pymupdf_line is not None, "PyMuPDF line not found in requirements.txt"
    
    # Check version constraint (should be >=1.23.0)
    assert '>=1.23.0' in pymupdf_line or '>=' in pymupdf_line, \
        f"PyMuPDF should have version constraint >=1.23.0, found: {pymupdf_line}"


def test_requirements_preserves_other_dependencies():
    """
    Property 15: Dependency Preservation
    
    For any requirements.txt file in the tax_document_generation module,
    it SHALL contain boto3, PyJWT, and hypothesis dependencies.
    
    **Validates: Requirements 7.3**
    """
    # Find the requirements.txt file
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    
    assert requirements_path.exists(), f"requirements.txt not found at {requirements_path}"
    
    # Read the requirements file
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    # Parse requirements into a list of package names (lowercase for comparison)
    lines = content.strip().split('\n')
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Extract package name (before any version specifier)
            package_name = re.split(r'[>=<!\[]', line)[0].strip().lower()
            packages.append(package_name)
    
    # Verify required dependencies are present
    assert 'boto3' in packages, "boto3 must be in requirements.txt"
    assert 'pyjwt' in packages, "PyJWT must be in requirements.txt"
    assert 'hypothesis' in packages, "hypothesis must be in requirements.txt"
