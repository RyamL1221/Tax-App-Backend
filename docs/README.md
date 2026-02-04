# Tax-App-Backend Documentation

This directory contains all project documentation organized by purpose.

## Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── CHANGELOG_*.md              # Project-wide changelogs
├── architecture/               # System design and architecture
├── development/                # Developer guides and setup
├── examples/                   # Example JSON payloads
├── specs/                      # Implementation summaries
└── testing/                    # Test results and verification
```

## Quick Links

### Getting Started
- [Project Overview](../README.md) - Main project README
- [Environment Setup](development/ENVIRONMENT_SETUP.md) - Initial setup instructions
- [LocalStack & SAM Setup](development/LOCALSTACK_SAM_SETUP.md) - Local development environment
- [Quick Reference](development/QUICK_REFERENCE.md) - Common commands and patterns

### Architecture
- [1099-DIV Field Reference](architecture/1099-DIV_FIELD_REFERENCE.md) - Complete field documentation
- [Field Mapping Corrections](architecture/FIELD_MAPPING_CORRECTIONS.md) - Field mapping fixes
- [Field Inspection Findings](architecture/FIELD_INSPECTION_FINDINGS.md) - PDF field analysis
- [Migration Guide](architecture/MIGRATION_GUIDE_FIELD_STANDARDIZATION.md) - Field standardization migration
- [Position Validation Guide](architecture/POSITION_VALIDATION_GUIDE.md) - Field position validation
- [Form Inputs Reference](architecture/FORM_INPUTS_REFERENCE.md) - Form input specifications
- [Field Dimension Analysis](architecture/FIELD_DIMENSION_ANALYSIS.md) - PDF field dimensions

### Development
- [Lambda Import Patterns](development/LAMBDA_IMPORT_PATTERNS.md) - **Critical import guidelines**
- [Environment Variables](development/ENV_VARS_EXPLAINED.md) - Environment configuration
- [Password Recovery Testing](development/PASSWORD_RECOVERY_TESTING.md) - Testing password flows
- [Tax Document Generation Guide](development/TAX_DOCUMENT_GENERATION_POSTMAN_GUIDE.md) - API testing
- [Manual Token Retrieval](development/MANUAL_TOKEN_RETRIEVAL.md) - JWT token retrieval
- [Iterative Field Mapping Guide](development/ITERATIVE_FIELD_MAPPING_GUIDE.md) - Systematic field mapping fixes

### Examples
- [1099-DIV Minimal Example](examples/1099-DIV-minimal-example.json) - Required fields only
- [1099-DIV Typical Example](examples/1099-DIV-typical-example.json) - Common use case
- [1099-DIV Complete Example](examples/1099-DIV-complete-example.json) - All available fields
- [Examples README](examples/README.md) - Example documentation

### Implementation Summaries
- [Tax Document Generation](specs/IMPLEMENTATION_SUMMARY.md) - Feature implementation summary
- [Field Standardization](specs/STANDARDIZATION_SUMMARY.md) - Standardization results

### Testing
- [Validation Results](testing/VALIDATION_RESULTS.md) - Field validation test results
- [Integration Test Results](testing/INTEGRATION_TEST_RESULTS.md) - Integration test outcomes
- [Multi-Copy Test Results](testing/MULTI_COPY_INTEGRATION_TEST_RESULTS.md) - Multi-copy tests
- [Task Summaries](testing/) - Individual task verification reports

## Documentation by Topic

### Tax Document Generation
**Architecture**:
- [1099-DIV Field Reference](architecture/1099-DIV_FIELD_REFERENCE.md)
- [Field Mapping Corrections](architecture/FIELD_MAPPING_CORRECTIONS.md)
- [Field Inspection Findings](architecture/FIELD_INSPECTION_FINDINGS.md)
- [Field Inspection Analysis](architecture/FIELD_INSPECTION_ANALYSIS.md)
- [Field Inspection Enhancements](architecture/FIELD_INSPECTION_ENHANCEMENTS.md)
- [Field Mapping Analysis](architecture/FIELD_MAPPING_ANALYSIS.md)
- [Position Validation Guide](architecture/POSITION_VALIDATION_GUIDE.md)
- [Recipient Name Field Report](architecture/RECIPIENT_NAME_FIELD_INSPECTION_REPORT.md)

**Examples**:
- [Minimal Example](examples/1099-DIV-minimal-example.json)
- [Typical Example](examples/1099-DIV-typical-example.json)
- [Complete Example](examples/1099-DIV-complete-example.json)

**Implementation**:
- [Implementation Summary](specs/IMPLEMENTATION_SUMMARY.md)
- [Standardization Summary](specs/STANDARDIZATION_SUMMARY.md)

**Testing**:
- [Validation Results](testing/VALIDATION_RESULTS.md)
- [Task 3 Summary](testing/TASK_3_INSPECTION_SUMMARY.md)
- [Task 4 Summary](testing/TASK_4_FIELD_MAPPING_UPDATE_SUMMARY.md)
- [Task 5 Summary](testing/TASK_5_POSITION_VALIDATION_SUMMARY.md)
- [Task 6 Summary](testing/TASK_6_FIELD_POSITION_TEST_SUMMARY.md)
- [Task 7 Summary](testing/TASK_7_REGRESSION_TEST_SUMMARY.md)
- [Final Checkpoint](testing/FINAL_CHECKPOINT_VERIFICATION_RESULTS.md)

### User Authentication
**Development**:
- [Lambda Import Patterns](development/LAMBDA_IMPORT_PATTERNS.md) - **Must read!**
- [Environment Variables](development/ENV_VARS_EXPLAINED.md)

**Testing**:
- [Import Fix Summary](testing/IMPORT_FIX_SUMMARY.md)

### Password Recovery
**Development**:
- [Password Recovery Testing](development/PASSWORD_RECOVERY_TESTING.md)
- [Manual Token Retrieval](development/MANUAL_TOKEN_RETRIEVAL.md)

**Testing**:
- [Reset Password Test Results](testing/RESET_PASSWORD_TEST_RESULTS.md)

### Local Development
**Development**:
- [Environment Setup](development/ENVIRONMENT_SETUP.md)
- [LocalStack & SAM Setup](development/LOCALSTACK_SAM_SETUP.md)
- [Quick Reference](development/QUICK_REFERENCE.md)

### API Testing
**Development**:
- [Tax Document Generation Postman Guide](development/TAX_DOCUMENT_GENERATION_POSTMAN_GUIDE.md)
- [Postman Collection](development/postman_collection.json)

**Examples**:
- [All JSON Examples](examples/)

## Documentation Guidelines

For information on where to place documentation and how to organize it, see:
- [Documentation Guidelines](../.kiro/steering/documentation-guidelines.md) - Complete documentation standards

### Quick Guidelines
- **Architecture docs** → `docs/architecture/` - System design, field mappings, data structures
- **Development docs** → `docs/development/` - Setup guides, workflows, testing guides
- **Examples** → `docs/examples/` - Sample JSON payloads and usage examples
- **Spec summaries** → `docs/specs/` - Implementation summaries for completed features
- **Test results** → `docs/testing/` - Test results, verification reports, summaries

**Important**: Do NOT place documentation in Lambda function directories (e.g., `tax_document_generation/`, `user_login/`). All documentation belongs in `docs/`.

## Contributing to Documentation

When adding or updating documentation:

1. **Choose the right location** based on the documentation type
2. **Use descriptive filenames** that indicate the content
3. **Update this README** with a link to your new documentation
4. **Cross-reference** related documentation
5. **Follow markdown best practices** (clear headings, code blocks, tables)

See [Documentation Guidelines](../.kiro/steering/documentation-guidelines.md) for complete details.

## Additional Resources

- **Scripts**: See `../scripts/` for shell scripts and utilities
- **Samples**: See `../samples/` for sample PDF files
- **Steering Files**: See `../.kiro/steering/` for Kiro workspace guidelines
- **Specs**: See `../.kiro/specs/` for active feature specifications

## Changelog

- **2026-02-03**: Reorganized documentation from Lambda directories to `docs/` structure
- **2026-02-03**: Added comprehensive documentation guidelines
- **2026-02-03**: Created field standardization documentation
- **2026-02-03**: Added JSON example files for 1099-DIV API testing
- **2026-02-03**: Moved all task summaries and analysis docs to appropriate locations
