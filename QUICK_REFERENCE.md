# Quick Reference Guide

## Environment Parameter System

This project uses a **single parameter** to switch between local development and production deployment. No manual code changes needed!

```yaml
# In template.yaml
Parameters:
  Environment:
    Type: String
    Default: local
    AllowedValues:
      - local        # Uses LocalStack
      - production   # Uses real AWS
```

## Daily Commands

### Virtual Environment

```bash
# Activate virtual environment (do this first every day)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate   # Windows

# Deactivate when done
deactivate
```

### Local Development

```bash
# Start LocalStack
docker-compose up -d

# Build for local
sam build --parameter-overrides Environment=local
# Or: make sam-build-local

# Start SAM local
sam local start-api --docker-network tax-app-network --parameter-overrides Environment=local
# Or: make sam-start

# Test endpoint
curl -X POST http://localhost:3000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"SecurePass123!"}'
```

### Production Deployment

```bash
# Build for production
sam build --parameter-overrides Environment=production
# Or: make sam-build-prod

# Deploy to AWS
sam deploy --guided --parameter-overrides Environment=production
```

## First-Time Setup

### 0. Create and Activate Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate   # Windows

# Your prompt should show (venv) prefix
```

### 1. Install Dependencies

```bash
pip install -r user_registration/requirements.txt
pip install -r user_registration/tests/requirements-dev.txt
```

### 2. Start LocalStack

```bash
docker-compose up -d
sleep 15  # Wait for LocalStack to be ready
```

### 3. Create DynamoDB Table

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

## Makefile Commands

```bash
make help                  # Show all available commands
make localstack-start      # Start LocalStack
make localstack-stop       # Stop LocalStack
make localstack-status     # Check LocalStack health
make sam-build-local       # Build for local development
make sam-build-prod        # Build for production
make sam-start             # Start SAM local API
make test                  # Run all tests
make view-db-simple        # View DynamoDB table contents
make clean                 # Clean up everything
```

## Testing

```bash
# Run all tests
pytest user_registration/tests/ -v

# Run specific test types
pytest user_registration/tests/test_*_unit.py        # Unit tests only
pytest user_registration/tests/test_*_property.py    # Property-based tests only
pytest user_registration/tests/test_*_integration.py # Integration tests only

# Run with coverage
pytest user_registration/tests/ --cov=user_registration --cov-report=html
```

## Viewing LocalStack Data

```bash
# View DynamoDB table (simple format)
make view-db-simple

# View DynamoDB table (full JSON)
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws dynamodb scan \
  --table-name UsersTable \
  --endpoint-url http://localhost:4566 \
  --region us-east-1
```

## Troubleshooting

### Lambda Times Out (502 Error)

1. Check LocalStack is running: `docker ps | grep localstack`
2. Verify you're using `Environment=local` parameter
3. Ensure `--docker-network tax-app-network` flag is used
4. Check LocalStack logs: `docker logs tax-app-localstack`

### Table Not Found Error

Create the table:
```bash
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws dynamodb create-table \
  --table-name UsersTable \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:4566 \
  --region us-east-1
```

### Code Changes Not Reflected

Rebuild SAM:
```bash
sam build --parameter-overrides Environment=local
# Then restart SAM (Ctrl+C and run sam local start-api again)
```

## API Endpoints

### User Registration

**Endpoint:** `POST /register`

**Local:** `http://localhost:3000/register`  
**Production:** `https://{api-id}.execute-api.{region}.amazonaws.com/Prod/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePass123!"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

**Success Response (201):**
```json
{
  "message": "User registered successfully",
  "email": "user@example.com"
}
```

**Error Responses:**
- `400` - Validation error (invalid email, weak password, etc.)
- `409` - User already exists
- `500` - Internal server error

### User Login

**Endpoint:** `POST /login`

**Local:** `http://localhost:3000/login`  
**Production:** `https://{api-id}.execute-api.{region}.amazonaws.com/Prod/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200):**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**
- `400` - Validation error (missing fields)
- `401` - Invalid credentials
- `500` - Internal server error

### Logout (Client-Side Only)

**Important:** There is **no server-side logout endpoint**. Logout is handled entirely on the client side.

**How to logout:**
1. Delete the JWT token from your client's storage (localStorage, sessionStorage, memory, etc.)
2. Redirect the user to the login page or public area
3. No server request needed

**Why client-side logout?**  
Since JWTs are stateless tokens, the server doesn't maintain session state. A server-side logout endpoint would add complexity without providing real security benefits. Token expiration provides automatic security by limiting the token's lifetime.

## File Structure

```
.
├── user_registration/          # Lambda function code
│   ├── app.py                 # Lambda handler
│   ├── validator.py           # Input validation
│   ├── password_hasher.py     # Password hashing (bcrypt)
│   ├── user_repository.py     # DynamoDB operations
│   ├── response_formatter.py  # API response formatting
│   └── tests/                 # Test files
├── template.yaml              # SAM template (with Environment parameter)
├── docker-compose.yml         # LocalStack configuration
├── Makefile                   # Convenience commands
├── README.md                  # Full documentation
├── LOCALSTACK_SAM_SETUP.md   # Detailed LocalStack setup guide
└── QUICK_REFERENCE.md        # This file
```

## Key Concepts

### Environment Parameter

The `Environment` parameter in `template.yaml` controls the Lambda's behavior:

- **`Environment=local`**: Sets `AWS_ENDPOINT_URL=http://172.18.0.1:4566` (LocalStack)
- **`Environment=production`**: Doesn't set `AWS_ENDPOINT_URL` (uses real AWS)

### Docker Networking

- LocalStack runs in Docker container `tax-app-localstack`
- SAM Lambda containers connect via Docker network `tax-app-network`
- Gateway IP `172.18.0.1` allows SAM containers to reach LocalStack

### Why `172.18.0.1:4566`?

This is the Docker bridge gateway IP that SAM Lambda containers can reach. Other approaches don't work:
- ❌ `localhost:4566` - Wrong context (Lambda container's localhost)
- ❌ `host.docker.internal:4566` - DNS resolution issues
- ❌ `tax-app-localstack:4566` - Not resolvable from SAM containers
- ✅ `172.18.0.1:4566` - Docker bridge gateway (works!)

## Additional Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [LocalStack Documentation](https://docs.localstack.cloud/)
- [Full Setup Guide](./LOCALSTACK_SAM_SETUP.md)
- [Environment Variables Guide](./ENV_VARS_EXPLAINED.md)
