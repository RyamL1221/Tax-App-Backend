# Project Organization

This document describes the organization of files and directories in the Tax-App-Backend project.

## Directory Structure

```
Tax-App-Backend/
├── docs/                           # Documentation
│   ├── architecture/              # Architecture and design docs
│   ├── development/               # Development guides
│   ├── testing/                   # Test results and verification
│   └── README.md                  # Documentation index
├── scripts/                        # Shell scripts
│   ├── utils/                     # Python utility scripts
│   └── README.md                  # Scripts documentation
├── samples/                        # Sample PDF files
│   └── README.md                  # Samples documentation
├── tests/                          # Project-wide tests
│   ├── integration/               # Integration tests
│   ├── unit/                      # Unit tests
│   ├── manual/                    # Manual test scripts
│   └── README.md                  # Tests documentation
├── events/                         # Lambda event test files
├── .kiro/                          # Kiro configuration
│   ├── specs/                     # Feature specifications
│   ├── steering/                  # Workspace guidelines
│   └── hooks/                     # Agent hooks
├── user_registration/              # User registration Lambda
├── user_login/                     # User login Lambda
├── password_recovery/              # Password recovery Lambda
├── tax_document_generation/        # Tax document generation Lambda
├── README.md                       # Main project documentation
├── Makefile                        # Build and development commands
├── template.yaml                   # SAM template
├── docker-compose.yml              # LocalStack configuration
└── env.json                        # Environment variables for SAM

```

## Documentation (`docs/`)

### Architecture (`docs/architecture/`)
- `1099-DIV_FIELD_REFERENCE.md` - Field reference for 1099-DIV forms
- `FORM_INPUTS_REFERENCE.md` - Form input specifications
- `FIELD_DIMENSION_ANALYSIS.md` - PDF field dimension analysis
- `FIELD_MAPPING_VALIDATION_RESULTS.md` - Field mapping validation

### Development (`docs/development/`)
- `LAMBDA_IMPORT_PATTERNS.md` - Lambda import patterns (CRITICAL)
- `LOCALSTACK_SAM_SETUP.md` - LocalStack setup guide
- `ENVIRONMENT_SETUP.md` - Environment configuration
- `ENV_VARS_EXPLAINED.md` - Environment variables
- `PASSWORD_RECOVERY_TESTING.md` - Password recovery testing
- `TAX_DOCUMENT_GENERATION_POSTMAN_GUIDE.md` - API testing guide
- `MANUAL_TOKEN_RETRIEVAL.md` - JWT token retrieval
- `QUICK_REFERENCE.md` - Quick reference cheat sheet
- `postman_collection.json` - Postman API collection

### Testing (`docs/testing/`)
- Test results and verification summaries
- Task-specific test documentation
- PDF testing guides

## Scripts (`scripts/`)

### Shell Scripts
- `init-localstack.sh` - Initialize LocalStack resources
- `start-dev.sh` - Start development environment
- `test-*.sh` - Various testing scripts
- `get-*.sh` - Utility scripts for retrieving data
- `restart-sam.sh` - Restart SAM local
- `clear-sam-cache.sh` - Clear SAM cache
- `view-recent-logs.sh` - View CloudWatch logs

### Python Utilities (`scripts/utils/`)
- `view-dynamodb.py` - View DynamoDB contents
- `generate_sample_1099_div.py` - Generate sample PDFs
- `inspect-pdf-fields.py` - Inspect PDF fields

## Samples (`samples/`)

PDF files for testing:
- Template PDFs (blank forms)
- Generated PDFs (test outputs)
- Test PDFs (specific scenarios)

## Tests (`tests/`)

### Manual Tests (`tests/manual/`)
- `test_comprehensive_field_mapping.py`
- `test_field_mapping_debug.py`
- `test_lambda_manual.py`
- `test_pymupdf_migration.py`
- `test_task_4_1.py`

### Integration Tests (`tests/integration/`)
Cross-Lambda integration tests

### Unit Tests (`tests/unit/`)
Shared unit tests

## Lambda Functions

Each Lambda function has its own directory:
- `user_registration/`
- `user_login/`
- `password_recovery/`
- `tax_document_generation/`

Each contains:
- `app.py` or handler files
- Supporting modules
- `requirements.txt`
- `tests/` directory with unit, property, and integration tests

## Events (`events/`)

Lambda event test files:
- `event.json` - Generic test event
- `test-event-tax-doc.json` - Tax document test event
- `test-event-tax-doc-minimal.json` - Minimal tax document event

## Configuration Files

### Root Level
- `README.md` - Main project documentation
- `Makefile` - Build and development commands
- `template.yaml` - SAM CloudFormation template
- `docker-compose.yml` - LocalStack Docker configuration
- `env.json` - Environment variables for SAM local
- `.env.example` - Environment variable template
- `.env.local` - LocalStack environment (committed)
- `.gitignore` - Git ignore rules

### Kiro Configuration (`.kiro/`)
- `specs/` - Feature specifications
- `steering/` - Workspace guidelines
- `hooks/` - Agent hooks

## Key Changes from Previous Organization

### Before
- All shell scripts in root directory
- All documentation in root directory
- All PDF samples in root directory
- Manual test scripts in root directory

### After
- Shell scripts organized in `scripts/`
- Documentation organized in `docs/` by category
- PDF samples in `samples/`
- Manual test scripts in `tests/manual/`
- Python utilities in `scripts/utils/`
- Test events in `events/`

## Benefits

1. **Cleaner Root**: Root directory now contains only essential files
2. **Logical Grouping**: Related files are grouped together
3. **Easy Navigation**: Clear directory structure with README files
4. **Better Discovery**: Documentation index helps find information
5. **Maintainability**: Easier to maintain and update organized structure

## Finding Files

Use the README files in each directory:
- `docs/README.md` - Documentation index
- `scripts/README.md` - Scripts documentation
- `samples/README.md` - Samples documentation
- `tests/manual/README.md` - Manual tests documentation

Or use the quick reference:
- `docs/development/QUICK_REFERENCE.md` - Quick reference guide
