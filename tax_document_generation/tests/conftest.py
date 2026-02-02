"""
Pytest configuration for tax_document_generation tests.

This conftest.py sets up the import paths to allow production code with direct imports
to work correctly when imported by tests using package-prefixed imports.
"""

import sys
import os

# Get the project root and tax_document_generation directory
test_dir = os.path.dirname(os.path.abspath(__file__))
tax_doc_dir = os.path.dirname(test_dir)
project_root = os.path.dirname(tax_doc_dir)

# Add both to sys.path
# Project root allows: from tax_document_generation.module import ...
# tax_doc_dir allows: from module import ... (for production code)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if tax_doc_dir not in sys.path:
    sys.path.insert(0, tax_doc_dir)

# Import the exceptions module to ensure it's loaded as both
# 'exceptions' and 'tax_document_generation.exceptions'
import tax_document_generation.exceptions
sys.modules['exceptions'] = tax_document_generation.exceptions
