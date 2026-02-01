# LocalStack + SAM Local Integration - Setup Guide

This document explains the changes made to get SAM Local working with LocalStack for local development.

## Problem Summary

When running `sam local start-api`, the Lambda function couldn't connect to LocalStack's DynamoDB, resulting in timeout errors and "invalid security token" errors.

## Root Causes

1. **Lambda import errors** - Lambda couldn't import local modules
2. **Missing environment variables** - Lambda didn't know where to find LocalStack
3. **Docker networking issues** - Lambda containers couldn't reach LocalStack container
4. **Missing DynamoDB table** - Table wasn't created in LocalStack

## Solutions Implemented

### 1. Fixed Lambda Imports

**File:** `user_registration/app.py`

**Problem:** Lambda was trying to import with `from user_registration.validator import ...` which failed in the Lambda environment.

**Solution:** Changed to relative imports and added path configuration:

```python
import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

from validator import ValidationError, validate_registration_data
from password_hasher import hash_password
from user_repository import create_user, DuplicateUserError, DatabaseError
from response_formatter import (
    success_response,
    validation_error_response,
    duplicate_user_response,
    internal_error_response
)
```

### 2. Added LocalStack Endpoint Support

**File:** `user_registration/user_repository.py`

**Problem:** boto3 was trying to connect to real AWS instead of LocalStack.

**Solution:** Added endpoint_url configuration based on environment variable:

```python
# Configure endpoint for LocalStack if AWS_ENDPOINT_URL is set
endpoint_url = os.environ.get('AWS_ENDPOINT_URL')

# Debug logging
import logging
logger = logging.getLogger()
logger.info(f"DynamoDB Config - Region: {region}, Endpoint: {endpoint_url}, Table: {table_name}")

if endpoint_url:
    dynamodb = boto3.client('dynamodb', region_name=region, endpoint_url=endpoint_url)
else:
    dynamodb = boto3.client('dynamodb', region_name=region)
```

### 3. Configured Environment Variables in SAM Template

**File:** `template.yaml`

**Problem:** SAM's `--env-vars` flag wasn't reliably passing environment variables to Lambda containers. Also, we needed different configurations for local vs production.

**Solution:** Added CloudFormation parameters and conditional logic:

```yaml
Parameters:
  Environment:
    Type: String
    Default: local
    AllowedValues:
      - local
      - production
    Description: Environment type (local for LocalStack, production for AWS)

Conditions:
  IsLocal: !Equals [!Ref Environment, local]

# In UserRegistrationFunction:
Environment:
  Variables:
    USER_TABLE_NAME: !Ref Users
    AWS_ENDPOINT_URL: !If [IsLocal, "http://172.18.0.1:4566", !Ref "AWS::NoValue"]
```

**How it works:**
- When `Environment=local`: Sets `AWS_ENDPOINT_URL` to LocalStack
- When `Environment=production`: Doesn't set `AWS_ENDPOINT_URL` (uses real AWS)
- No manual editing required - just pass the parameter!

**Usage:**
```bash
# Local development
sam build --parameter-overrides Environment=local
sam local start-api --docker-network tax-app-network --parameter-overrides Environment=local

# Production deployment
sam build --parameter-overrides Environment=production
sam deploy --guided --parameter-overrides Environment=production
```

### 4. Increased Lambda Timeout

**File:** `template.yaml`

**Problem:** Default 3-second timeout was too short for local development.

**Solution:** Increased global timeout to 30 seconds:

```yaml
Globals:
  Function:
    Timeout: 30  # Increased from 3 seconds
```

### 5. Simplified LocalStack Docker Compose

**File:** `docker-compose.yml`

**Problem:** Volume mount issues causing LocalStack startup failures.

**Solution:** Simplified configuration, removed problematic volume mounts:

```yaml
version: '3.8'

services:
  localstack:
    image: localstack/localstack:latest
    container_name: tax-app-localstack
    ports:
      - "4566:4566"
      - "4510-4559:4510-4559"
    environment:
      - SERVICES=dynamodb
      - DEBUG=1
      - LAMBDA_EXECUTOR=local
      - AWS_DEFAULT_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"
    networks:
      - tax-app-network

networks:
  tax-app-network:
    driver: bridge
```

### 6. Created Environment Configuration Files

**File:** `env.json` (created but not used - kept for reference)

```json
{
  "UserRegistrationFunction": {
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_ENDPOINT_URL": "http://host.docker.internal:4566",
    "USER_TABLE_NAME": "Users"
  }
}
```

**Note:** This file was created but the `--env-vars` flag proved unreliable. We use `template.yaml` environment variables instead.

**File:** `ENV_VARS_EXPLAINED.md` (documentation)

Comprehensive guide explaining the difference between `.env.local`, `env.json`, `.env.example`, and `.env`.

### 7. Updated Makefile

**File:** `Makefile`

Added convenience command for starting SAM:

```makefile
sam-start: ## Start SAM local API Gateway with LocalStack connection
	@echo "Starting SAM local API Gateway..."
	@echo "Make sure LocalStack is running first (make localstack-start)"
	sam local start-api --docker-network tax-app-network
```

## Complete Workflow

### Initial Setup (One Time)

```bash
# 0. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 1. Start LocalStack
docker-compose up -d

# 2. Wait for LocalStack to be ready (10-15 seconds)
sleep 15

# 3. Create DynamoDB table
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:4566 \
  --region us-east-1
```

### Daily Development Workflow

```bash
# 0. Activate virtual environment (do this first every day)
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 1. Start LocalStack (if not running)
docker-compose up -d

# 2. Build SAM application for local development
sam build --parameter-overrides Environment=local
# Or use: make sam-build-local

# 3. Start SAM local API Gateway
sam local start-api --docker-network tax-app-network --parameter-overrides Environment=local
# Or use: make sam-start

# 4. Test with Postman at http://localhost:3000/register
```

### After Code Changes

```bash
# 1. Rebuild for local
sam build --parameter-overrides Environment=local

# 2. Restart SAM (Ctrl+C first, then)
sam local start-api --docker-network tax-app-network --parameter-overrides Environment=local
```

### Production Deployment

```bash
# 1. Build for production
sam build --parameter-overrides Environment=production
# Or use: make sam-build-prod

# 2. Deploy to AWS
sam deploy --guided --parameter-overrides Environment=production
```

## Testing the Endpoint

### Using Postman

**URL:** `http://localhost:3000/register`  
**Method:** POST  
**Headers:** `Content-Type: application/json`  
**Body:**

```json
{
  "email": "john.doe@example.com",
  "name": "John Doe",
  "password": "SecurePass123!"
}
```

**Expected Response (201):**

```json
{
  "message": "User registered successfully",
  "email": "john.doe@example.com"
}
```

### Using curl

```bash
curl -X POST http://localhost:3000/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "SecurePass123!"
  }'
```

### Verify Data in DynamoDB

```bash
# View table contents
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws dynamodb scan \
  --table-name Users \
  --endpoint-url http://localhost:4566 \
  --region us-east-1
```

## Key Learnings

### Docker Networking with SAM Local

1. **SAM creates its own Lambda containers** that need network access to LocalStack
2. **The `--docker-network` flag** connects SAM containers to the same network as LocalStack
3. **Container hostnames don't always resolve** from SAM Lambda containers
4. **Docker bridge gateway IP** (`172.18.0.1`) is the most reliable way to connect

### Environment Variables

1. **SAM's `--env-vars` flag is unreliable** - environment variables don't always pass through
2. **Template-based environment variables work better** - defined in `template.yaml`
3. **Different endpoints for different contexts:**
   - Your terminal: `http://localhost:4566`
   - SAM Lambda containers: `http://172.18.0.1:4566`
   - Docker containers on same network: `http://tax-app-localstack:4566`

### LocalStack Quirks

1. **Table persistence** - Tables are lost when LocalStack restarts (unless using Pro with persistence)
2. **Fake credentials work** - `AWS_ACCESS_KEY_ID=test` and `AWS_SECRET_ACCESS_KEY=test` are accepted
3. **Services must be enabled** - Only enable services you need (we use `SERVICES=dynamodb`)

## Troubleshooting

### Lambda Times Out

**Symptoms:** 502 error, "Function timed out after 3 seconds"

**Solutions:**
1. Check LocalStack is running: `docker ps | grep localstack`
2. Verify endpoint in template.yaml: `AWS_ENDPOINT_URL: http://172.18.0.1:4566`
3. Ensure you're using `--docker-network tax-app-network`
4. Check LocalStack logs: `docker logs tax-app-localstack`

### Table Not Found

**Symptoms:** "Cannot do operations on a non-existent table"

**Solution:** Create the table:
```bash
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:4566 \
  --region us-east-1
```

### Invalid Security Token

**Symptoms:** "The security token included in the request is invalid"

**Solutions:**
1. Check `AWS_ENDPOINT_URL` is set in template.yaml
2. Verify Lambda is reading the environment variable (check logs)
3. Rebuild SAM: `sam build`

### Import Errors

**Symptoms:** "ModuleNotFoundError: No module named 'user_registration'"

**Solutions:**
1. Use relative imports in Lambda handler
2. Add `sys.path.insert(0, os.path.dirname(__file__))` to handler
3. Rebuild: `sam build`

## Production Deployment Notes

**GOOD NEWS:** No manual changes needed! The template automatically handles local vs production.

### Deploying to Production

```bash
# 1. Build for production
sam build --parameter-overrides Environment=production

# 2. Deploy
sam deploy --guided --parameter-overrides Environment=production
```

During `sam deploy --guided`, you'll be prompted for:
- Stack name
- AWS Region
- Confirm changes before deploy
- Allow SAM CLI IAM role creation
- Save arguments to configuration file

### What Happens in Production

- `AWS_ENDPOINT_URL` is **not set** (the `!If` condition removes it)
- boto3 automatically connects to real AWS DynamoDB
- Your code works exactly the same way
- No code changes needed!

### Switching Between Environments

**Local Development:**
```bash
sam build --parameter-overrides Environment=local
sam local start-api --docker-network tax-app-network --parameter-overrides Environment=local
```

**Production Deployment:**
```bash
sam build --parameter-overrides Environment=production
sam deploy --guided --parameter-overrides Environment=production
```

**Or use Makefile shortcuts:**
```bash
make sam-build-local   # Build for local
make sam-build-prod    # Build for production
make sam-start         # Start local (automatically uses Environment=local)
```

## Files Modified

- `user_registration/app.py` - Fixed imports
- `user_registration/user_repository.py` - Added LocalStack endpoint support
- `template.yaml` - Added environment variables, increased timeout
- `docker-compose.yml` - Simplified LocalStack configuration
- `Makefile` - Added `sam-start` command
- `env.json` - Created (for reference, not actively used)
- `ENV_VARS_EXPLAINED.md` - Created documentation

## Files Created

- `LOCALSTACK_SAM_SETUP.md` - This file
- `ENV_VARS_EXPLAINED.md` - Environment variables guide
- `env.json` - Environment variables template (reference only)
