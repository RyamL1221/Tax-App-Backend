# Test Folder Reorganization

## Overview

This document describes the reorganization of test files from a flat naming-convention structure to a hierarchical subdirectory structure. Tests are now organized by type (unit, property, integration, regression) in dedicated subdirectories.

## Migration Summary

**Date**: March 10, 2026  
**Total Files Migrated**: 224 test files  
**Status**: ✅ Complete

## New Structure

Tests are now organized into subdirectories by type:

```
<lambda_function>/tests/
├── __init__.py
├── conftest.py (if exists)
├── unit/
│   ├── __init__.py
│   └── test_*_unit.py
├── property/
│   ├── __init__.py
│   └── test_*_property.py
├── integration/
│   ├── __init__.py
│   └── test_*_integration.py
└── regression/
    ├── __init__.py
    └── test_*_regression.py
```

## Before and After

### Before (Flat Structure)
```
user_login/tests/
├── test_validator_unit.py
├── test_cors_headers_property.py
├── test_lambda_handler_integration.py
└── ... (all tests in one directory)
```

### After (Hierarchical Structure)
```
user_login/tests/
├── unit/
│   └── test_validator_unit.py
├── property/
│   └── test_cors_headers_property.py
└── integration/
    └── test_lambda_handler_integration.py
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Tests by Category

**Unit tests only:**
```bash
pytest user_login/tests/unit/
pytest */tests/unit/
```

**Property-based tests only:**
```bash
pytest user_login/tests/property/
pytest */tests/property/
```

**Integration tests only:**
```bash
pytest user_login/tests/integration/
pytest */tests/integration/
```

**Regression tests only:**
```bash
pytest tax_document_generation/tests/regression/
```

### Run Tests for Specific Lambda
```bash
# All tests for user_login
pytest user_login/tests/

# Only unit tests for user_login
pytest user_login/tests/unit/

# Only property tests for tax_document_generation
pytest tax_document_generation/tests/property/
```

## Migration Statistics

### By Lambda Function

| Lambda Function | Unit | Property | Integration | Regression | Total |
|----------------|------|----------|-------------|------------|-------|
| user_login | 4 | 22 | 1 | 0 | 27 |
| user_registration | 3 | 8 | 2 | 0 | 13 |
| password_recovery | 9 | 25 | 6 | 0 | 40 |
| tax_document_generation | 37 | 68 | 24 | 1 | 130 |
| document_download | 4 | 3 | 1 | 0 | 8 |
| debug_tools | 5 | 0 | 0 | 0 | 5 |
| tests (root) | 1 | 5 | 1 | 0 | 7 |

**Total: 224 files migrated**

### By Test Type

- **Unit Tests**: 63 files (28%)
- **Property Tests**: 131 files (58%)
- **Integration Tests**: 35 files (16%)
- **Regression Tests**: 1 file (<1%)

## Benefits

### Improved Organization
- Tests are visually organized by type
- Easier to find specific test categories
- Clear separation of concerns

### Faster Test Execution
- Run only the tests you need
- Unit tests run faster than integration tests
- Property tests can be run separately

### Better Developer Experience
- Clearer test structure at a glance
- Easier onboarding for new developers
- Consistent organization across all Lambda functions

## Compatibility

### Pytest Discovery
Pytest automatically discovers tests in subdirectories. No configuration changes needed.

### Import Statements
All import statements were automatically updated during migration using `git mv` and `smartRelocate`.

### CI/CD
No changes required. Running `pytest` still discovers and runs all tests.

## Troubleshooting

### Tests Not Found
If pytest can't find tests, ensure `__init__.py` files exist in all test subdirectories:
```bash
find */tests -type d -exec test -f {}/__init__.py \; -print
```

### Import Errors
If you encounter import errors, verify the test file is in the correct subdirectory and imports are using package-prefixed paths:
```python
# Correct (in test files)
from user_login.validator import validate_email
```

### Running Specific Tests
Use the full path to the test file or directory:
```bash
pytest user_login/tests/unit/test_validator_unit.py
pytest user_login/tests/property/
```

## Related Documentation

- `.kiro/steering/testing-guidelines.md` - Testing best practices
- `.kiro/steering/quick-reference.md` - Quick command reference
- `.kiro/steering/workspace-organization.md` - Workspace organization rules

## Migration Scripts

The migration was performed using:
- `scripts/migrate_test_folders.py` - Migration planning script
- `scripts/batch_migrate_tests.py` - Batch migration execution
- `git mv` - File moves preserving git history

All migration scripts are preserved in the `scripts/` directory for reference.
