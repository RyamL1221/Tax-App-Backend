# Test Fixtures

This directory contains test fixtures for the tax document generation feature.

## Contents

- **sample_form_data.json**: Sample form data for testing
- **sample_1040_template.pdf**: Sample IRS Form 1040 template (to be added)
- **sample_jwt_tokens.json**: Sample JWT tokens for testing

## Usage

These fixtures are used by integration tests and property-based tests to ensure
consistent test data across test runs.

## Adding New Fixtures

When adding new fixtures:
1. Document the fixture format in this README
2. Ensure fixtures don't contain real PII or sensitive data
3. Use realistic but fake data for testing
