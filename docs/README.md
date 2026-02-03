# Documentation Index

This directory contains comprehensive documentation for the Tax-App-Backend project.

## Directory Structure

### Architecture (`architecture/`)
Documentation about the system architecture, field mappings, and form structures:
- `1099-DIV_FIELD_REFERENCE.md` - Field reference for 1099-DIV forms
- `FORM_INPUTS_REFERENCE.md` - Form input specifications
- `FIELD_DIMENSION_ANALYSIS.md` - Analysis of PDF field dimensions
- `FIELD_MAPPING_VALIDATION_RESULTS.md` - Field mapping validation results

### Development (`development/`)
Guides for setting up and developing the application:
- `LAMBDA_IMPORT_PATTERNS.md` - Critical guide on Lambda import patterns
- `LOCALSTACK_SAM_SETUP.md` - LocalStack setup and usage
- `ENVIRONMENT_SETUP.md` - Environment configuration
- `ENV_VARS_EXPLAINED.md` - Environment variable documentation
- `PASSWORD_RECOVERY_TESTING.md` - Password recovery testing guide
- `TAX_DOCUMENT_GENERATION_POSTMAN_GUIDE.md` - API testing with Postman
- `MANUAL_TOKEN_RETRIEVAL.md` - Manual JWT token retrieval
- `QUICK_REFERENCE.md` - Quick reference cheat sheet

### Testing (`testing/`)
Test results, verification summaries, and testing documentation:
- `CHECKPOINT_3_RESULTS.md` - Checkpoint 3 test results
- `FINAL_CHECKPOINT_VERIFICATION_RESULTS.md` - Final verification results
- `INTEGRATION_TEST_RESULTS.md` - Integration test results
- `MULTI_COPY_INTEGRATION_TEST_RESULTS.md` - Multi-copy test results
- `PYMUPDF_MIGRATION_STATUS.md` - PyMuPDF migration status
- `TASK*.md` - Task-specific test summaries
- `FILLED_PDF_LOCATIONS.md` - PDF output locations
- `TEST_THESE_PDFS.md` - PDF testing guide

## Quick Links

### Getting Started
1. Read the main [README.md](../README.md) for project overview
2. Follow [development/LOCALSTACK_SAM_SETUP.md](development/LOCALSTACK_SAM_SETUP.md) for local setup
3. Review [development/LAMBDA_IMPORT_PATTERNS.md](development/LAMBDA_IMPORT_PATTERNS.md) for critical import rules

### Common Tasks
- **Testing**: See [testing/](testing/) directory for test results and guides
- **API Testing**: Use [development/TAX_DOCUMENT_GENERATION_POSTMAN_GUIDE.md](development/TAX_DOCUMENT_GENERATION_POSTMAN_GUIDE.md)
- **Quick Reference**: Check [development/QUICK_REFERENCE.md](development/QUICK_REFERENCE.md)

### Architecture
- **Field Mappings**: See [architecture/1099-DIV_FIELD_REFERENCE.md](architecture/1099-DIV_FIELD_REFERENCE.md)
- **Form Inputs**: See [architecture/FORM_INPUTS_REFERENCE.md](architecture/FORM_INPUTS_REFERENCE.md)

## Additional Resources

- **Scripts**: See `../scripts/` for shell scripts
- **Samples**: See `../samples/` for sample PDF files
- **Steering Files**: See `../.kiro/steering/` for Kiro workspace guidelines
- **Specs**: See `../.kiro/specs/` for feature specifications
