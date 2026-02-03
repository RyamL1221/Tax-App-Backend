# Manual Test Scripts

This directory contains manual test scripts used for ad-hoc testing and verification during development.

## Test Scripts

### `test_comprehensive_field_mapping.py`
Comprehensive test of PDF field mapping functionality

**Purpose:** Tests all field mappings for 1099-DIV forms

**Usage:**
```bash
python3 tests/manual/test_comprehensive_field_mapping.py
```

### `test_field_mapping_debug.py`
Debug script for field mapping issues

**Purpose:** Helps debug field mapping problems with detailed output

**Usage:**
```bash
python3 tests/manual/test_field_mapping_debug.py
```

### `test_lambda_manual.py`
Manual Lambda function testing

**Purpose:** Tests Lambda handlers directly without API Gateway

**Usage:**
```bash
python3 tests/manual/test_lambda_manual.py
```

### `test_pymupdf_migration.py`
PyMuPDF migration testing

**Purpose:** Tests the migration from PyPDF2 to PyMuPDF

**Usage:**
```bash
python3 tests/manual/test_pymupdf_migration.py
```

### `test_task_4_1.py`
Task 4.1 specific testing

**Purpose:** Tests adaptive font sizing integration (Task 4.1)

**Usage:**
```bash
python3 tests/manual/test_task_4_1.py
```

## When to Use Manual Tests

Manual tests are useful for:
- **Debugging**: When automated tests don't provide enough detail
- **Exploration**: Testing new features or approaches
- **Verification**: Quick verification of specific functionality
- **Development**: During active development of new features

## Automated Tests vs Manual Tests

- **Automated tests** (`<lambda>/tests/`): Run via pytest, part of CI/CD
- **Manual tests** (`tests/manual/`): Run directly, for development and debugging

## Running Manual Tests

Manual tests can be run directly with Python:

```bash
# From project root
python3 tests/manual/test_script_name.py

# With virtual environment
source venv/bin/activate
python3 tests/manual/test_script_name.py
```

## Notes

- Manual tests may require specific setup (LocalStack, environment variables, etc.)
- Check each script for specific requirements
- Manual tests are not run automatically in CI/CD
- Consider converting useful manual tests to automated tests when appropriate

## Shared Test Utilities

### `jwt_verifier.py`
Shared JWT verification utility used by multiple test suites

**Purpose:** Provides JWT token verification for testing authentication flows

**Used by:**
- `tests/test_jwt_verifier_unit.py`
- `tests/test_expired_token_rejection_property.py`
- `tests/test_valid_token_email_extraction_property.py`
- `password_recovery/tests/test_session_invalidation_integration.py`

### `test-secret-key-at-least-32-characters-long`
Test JWT secret key file

**Purpose:** Provides a consistent secret key for testing JWT functionality

**Note:** This is for testing only. Production uses environment variables.
