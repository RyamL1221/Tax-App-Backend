# Scripts Directory

This directory contains shell scripts for common development, testing, and deployment tasks.

## Setup Scripts

### `init-localstack.sh`
Initializes LocalStack resources (DynamoDB tables, S3 buckets, etc.)

**Usage:**
```bash
bash scripts/init-localstack.sh
```

**Or via Makefile:**
```bash
make localstack-init
```

### `start-dev.sh`
Starts the complete development environment (LocalStack + SAM)

**Usage:**
```bash
bash scripts/start-dev.sh
```

## Testing Scripts

### `test-tax-document-generation.sh`
Tests the tax document generation endpoint with sample data

**Usage:**
```bash
bash scripts/test-tax-document-generation.sh
```

**Or via Makefile:**
```bash
make test-tax-docs-endpoint
```

### `test-forgot-password.sh`
Tests the forgot password endpoint

**Usage:**
```bash
bash scripts/test-forgot-password.sh
```

### `test-reset-password.sh`
Tests the reset password endpoint

**Usage:**
```bash
bash scripts/test-reset-password.sh
```

### `test-forgot-password-deployment.sh`
Tests forgot password after deployment

**Usage:**
```bash
bash scripts/test-forgot-password-deployment.sh
```

### `test-reset-password-deployment.sh`
Tests reset password after deployment

**Usage:**
```bash
bash scripts/test-reset-password-deployment.sh
```

### `test-localstack.sh`
Tests LocalStack connectivity and health

**Usage:**
```bash
bash scripts/test-localstack.sh
```

### `test-pdf-field-fix.sh`
Tests PDF field mapping fixes

**Usage:**
```bash
bash scripts/test-pdf-field-fix.sh
```

## Utility Scripts

### `get-reset-token.sh`
Retrieves a password reset token from DynamoDB

**Usage:**
```bash
bash scripts/get-reset-token.sh <email>
```

### `get-token-from-db.sh`
Retrieves a JWT token from the database

**Usage:**
```bash
bash scripts/get-token-from-db.sh <email>
```

### `view-recent-logs.sh`
Views recent CloudWatch logs for Lambda functions

**Usage:**
```bash
bash scripts/view-recent-logs.sh <function-name>
```

### `restart-sam.sh`
Restarts SAM local API

**Usage:**
```bash
bash scripts/restart-sam.sh
```

### `clear-sam-cache.sh`
Clears SAM build cache

**Usage:**
```bash
bash scripts/clear-sam-cache.sh
```

## Utility Python Scripts (`utils/`)

### `view-dynamodb.py`
Views DynamoDB table contents in a simple format

**Usage:**
```bash
python3 scripts/utils/view-dynamodb.py
```

**Or via Makefile:**
```bash
make view-db-simple
```

### `generate_sample_1099_div.py`
Generates sample 1099-DIV PDF forms for testing

**Usage:**
```bash
python3 scripts/utils/generate_sample_1099_div.py
```

### `inspect-pdf-fields.py`
Inspects PDF form fields and their properties

**Usage:**
```bash
python3 scripts/utils/inspect-pdf-fields.py <pdf-file>
```

## Script Conventions

All scripts follow these conventions:
- Use `#!/bin/bash` shebang
- Include error handling with `set -e`
- Provide helpful output messages
- Exit with appropriate status codes
- Can be run from project root directory

## Running Scripts

Scripts can be run in two ways:

1. **Directly:**
   ```bash
   bash scripts/script-name.sh
   ```

2. **Via Makefile** (when available):
   ```bash
   make target-name
   ```

Check the [Makefile](../Makefile) for available make targets.
