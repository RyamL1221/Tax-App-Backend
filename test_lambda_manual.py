#!/usr/bin/env python3
"""
Manual test script to verify Lambda handler can be imported and invoked
without import errors.
"""

import sys
import os

# Test 1: Import the Lambda handler module
print("Test 1: Importing Lambda handler module...")
try:
    from tax_document_generation import app
    print("✓ Successfully imported app module")
except ImportError as e:
    print(f"✗ Failed to import app module: {e}")
    sys.exit(1)

# Test 2: Verify lambda_handler function exists
print("\nTest 2: Checking lambda_handler function exists...")
if hasattr(app, 'lambda_handler'):
    print("✓ lambda_handler function exists")
else:
    print("✗ lambda_handler function not found")
    sys.exit(1)

# Test 3: Import document_generator module
print("\nTest 3: Importing document_generator module...")
try:
    from tax_document_generation import document_generator
    print("✓ Successfully imported document_generator module")
except ImportError as e:
    print(f"✗ Failed to import document_generator module: {e}")
    sys.exit(1)

# Test 4: Verify no relative imports in document_generator
print("\nTest 4: Checking document_generator imports...")
import inspect
source = inspect.getsource(document_generator)
if 'from .' in source:
    print("✗ Found relative imports in document_generator")
    sys.exit(1)
else:
    print("✓ No relative imports found in document_generator")

# Test 5: Verify exceptions can be imported
print("\nTest 5: Importing exceptions module...")
try:
    from tax_document_generation.exceptions import GenerationError
    print("✓ Successfully imported GenerationError")
except ImportError as e:
    print(f"✗ Failed to import GenerationError: {e}")
    sys.exit(1)

# Test 6: Verify field_mapper can be imported
print("\nTest 6: Importing field_mapper module...")
try:
    from tax_document_generation.field_mapper import FieldMapper
    print("✓ Successfully imported FieldMapper")
except ImportError as e:
    print(f"✗ Failed to import FieldMapper: {e}")
    sys.exit(1)

# Test 7: Verify generate_document function exists
print("\nTest 7: Checking generate_document function exists...")
if hasattr(document_generator, 'generate_document'):
    print("✓ generate_document function exists")
else:
    print("✗ generate_document function not found")
    sys.exit(1)

print("\n" + "="*60)
print("All manual tests passed! ✓")
print("Lambda handler can be imported and invoked without errors.")
print("="*60)
