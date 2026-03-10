"""
Property Test: Dependency Preservation

Feature: pymupdf-migration, Property 15: Dependency Preservation

**Validates: Requirements 7.3**

This test verifies that the requirements.txt file contains boto3, PyJWT,
and hypothesis dependencies after the PyMuPDF migration.
"""

import re
from pathlib import Path


def test_requirements_preserves_boto3():
    """
    Property 15: Dependency Preservation (boto3)
    
    For any requirements.txt file in the tax_document_generation module,
    it SHALL contain boto3 dependency.
    
    **Validates: Requirements 7.3**
    """
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    
    assert requirements_path.exists(), f"requirements.txt not found at {requirements_path}"
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            package_name = re.split(r'[>=<!\[]', line)[0].strip().lower()
            packages.append(package_name)
    
    assert 'boto3' in packages, "boto3 must be in requirements.txt"


def test_requirements_preserves_pyjwt():
    """
    Property 15: Dependency Preservation (PyJWT)
    
    For any requirements.txt file in the tax_document_generation module,
    it SHALL contain PyJWT dependency.
    
    **Validates: Requirements 7.3**
    """
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    
    assert requirements_path.exists(), f"requirements.txt not found at {requirements_path}"
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            package_name = re.split(r'[>=<!\[]', line)[0].strip().lower()
            packages.append(package_name)
    
    assert 'pyjwt' in packages, "PyJWT must be in requirements.txt"


def test_requirements_preserves_hypothesis():
    """
    Property 15: Dependency Preservation (hypothesis)
    
    For any requirements.txt file in the tax_document_generation module,
    it SHALL contain hypothesis dependency.
    
    **Validates: Requirements 7.3**
    """
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    
    assert requirements_path.exists(), f"requirements.txt not found at {requirements_path}"
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            package_name = re.split(r'[>=<!\[]', line)[0].strip().lower()
            packages.append(package_name)
    
    assert 'hypothesis' in packages, "hypothesis must be in requirements.txt"


def test_all_required_dependencies_preserved():
    """
    Property 15: Dependency Preservation (comprehensive check)
    
    For any requirements.txt file in the tax_document_generation module,
    it SHALL contain boto3, PyJWT, and hypothesis dependencies.
    
    **Validates: Requirements 7.3**
    """
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    
    assert requirements_path.exists(), f"requirements.txt not found at {requirements_path}"
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            package_name = re.split(r'[>=<!\[]', line)[0].strip().lower()
            packages.append(package_name)
    
    required_dependencies = ['boto3', 'pyjwt', 'hypothesis']
    
    missing_dependencies = [dep for dep in required_dependencies if dep not in packages]
    
    assert not missing_dependencies, (
        f"Missing required dependencies: {', '.join(missing_dependencies)}. "
        f"Found packages: {', '.join(packages)}"
    )
