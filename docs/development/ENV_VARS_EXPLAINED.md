# Environment Variables Explained

This document explains the different environment variable files and their purposes.

## Files Overview

| File | Purpose | Safe to Commit? | When to Use |
|------|---------|----------------|-------------|
| `.env.local` | LocalStack config for your terminal | ✅ Yes | When running tests or AWS CLI commands locally |
| `env.json` | LocalStack config for SAM Lambda containers | ✅ Yes | When running `sam local start-api` |
| `.env.example` | Template for production AWS credentials | ✅ Yes | Reference for setting up `.env` |
| `.env` | Real production AWS credentials | ❌ NO | When deploying to real AWS (never commit!) |

## Why Two LocalStack Config Files?

### `.env.local` - For Your Terminal
Used when you run commands in your terminal:
```bash
source .env.local
awslocal dynamodb scan --table-name Users
pytest user_registration/tests/
```

**Endpoint:** `http://localhost:4566` (your machine's localhost)

### `env.json` - For SAM Lambda Containers
Used when SAM runs Lambda functions in Docker containers:
```bash
sam local start-api --env-vars env.json
```

**Endpoint:** `http://host.docker.internal:4566` (Docker's way to reach your machine's localhost)

## Key Difference: `host.docker.internal`

When Lambda runs in a Docker container, it can't use `localhost:4566` because that would refer to the container's own localhost, not your machine's. Docker provides a special hostname `host.docker.internal` that resolves to your machine's IP address.

```json
{
  "UserRegistrationFunction": {
    "AWS_ENDPOINT_URL": "http://host.docker.internal:4566"  // ← Docker container reaching your machine
  }
}
```

## Environment Variables Explained

### AWS_DEFAULT_REGION
- **Value:** `us-east-1`
- **Purpose:** AWS region for DynamoDB and other services
- **Note:** LocalStack ignores this but boto3 requires it

### AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY
- **Value:** `test` (for LocalStack)
- **Purpose:** Fake credentials that LocalStack accepts
- **Note:** LocalStack doesn't validate these, any value works

### AWS_ENDPOINT_URL
- **Value:** `http://localhost:4566` (terminal) or `http://host.docker.internal:4566` (Docker)
- **Purpose:** Tells boto3 to connect to LocalStack instead of real AWS
- **Note:** Without this, boto3 tries to connect to real AWS

### USER_TABLE_NAME
- **Value:** `Users`
- **Purpose:** Name of the DynamoDB table
- **Note:** Must match the table name in `template.yaml`

## Production vs Local

### Local Development (LocalStack)
```bash
# Terminal commands
source .env.local

# SAM local
sam local start-api --env-vars env.json
```

### Production Deployment (Real AWS)
```bash
# Create .env with real credentials (NEVER commit this!)
cp .env.example .env
# Edit .env with real AWS credentials

# Deploy
sam build
sam deploy --guided
```

**Important:** Production deployments don't need `AWS_ENDPOINT_URL` because boto3 connects to real AWS by default.
