# Tax-App-Backend

This will serve as the backend for the tax app.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
  - [User Registration Endpoint](#user-registration-endpoint)

## Quick Start

### Local Development with LocalStack

```bash
# 0. Activate virtual environment (if not already activated)
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 1. Start LocalStack
docker-compose up -d

# 2. Create DynamoDB table (first time only)
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:4566 \
  --region us-east-1

# 3. Build and start SAM
sam build --parameter-overrides Environment=local
sam local start-api --docker-network tax-app-network --env-vars env.json --parameter-overrides Environment=local

# 4. Test at http://localhost:3000/register
```

### Production Deployment

```bash
# 1. Build for production
sam build --parameter-overrides Environment=production

# 2. Deploy to AWS
sam deploy --guided --parameter-overrides Environment=production
```

**Key Concept:** The `Environment` parameter automatically configures the app for local (LocalStack) or production (AWS) - no code changes needed!

## Overview

The Tax-App-Backend is a serverless application built with AWS SAM (Serverless Application Model). It provides REST API endpoints for user management and tax-related operations.

### Features

- **User Registration**: Secure user registration with email validation, password strength requirements, and bcrypt password hashing
- **User Authentication**: JWT-based stateless authentication for secure API access
- **Client-Side Logout**: Simple logout by discarding JWT tokens on the client side
- **DynamoDB Storage**: Persistent user data storage with duplicate email detection
- **CORS Support**: Cross-origin resource sharing enabled for web applications
- **Comprehensive Logging**: Request tracking and error logging for monitoring and debugging

### Authentication and Logout

This application uses **JWT (JSON Web Token) based authentication** for a stateless, scalable authentication system.

#### How Authentication Works

1. **Registration**: Users register via the `/register` endpoint with email, name, and password
2. **Login**: Users authenticate via the `/login` endpoint and receive a JWT token
3. **Protected Requests**: Include the JWT token in the `Authorization` header for protected endpoints
4. **Logout**: Handled entirely on the client side (see below)

#### Client-Side Logout

**Important:** This system does **not** have a server-side logout endpoint. Logout is handled entirely on the client side.

**How to implement logout in your client application:**

1. **Delete the JWT token** from your client's storage (localStorage, sessionStorage, memory, etc.)
2. **Redirect the user** to the login page or public area of your application
3. **No server request needed** - simply discard the token

**Why client-side logout?**

Since JWTs are stateless tokens, the server doesn't maintain session state. Once a JWT is issued, it remains valid until it expires. A server-side logout endpoint would add complexity without providing real security benefits, as:
- The server cannot "revoke" a JWT that's already been issued (without adding a token blacklist, which defeats the purpose of stateless authentication)
- Clients can simply stop sending the token to achieve the same effect as logout
- Token expiration provides automatic security by limiting the token's lifetime

**Security considerations:**

- Set appropriate token expiration times (e.g., 1 hour, 24 hours) based on your security requirements
- Use HTTPS to prevent token interception
- Store tokens securely on the client (avoid localStorage for sensitive applications; prefer httpOnly cookies or memory storage)
- Clear tokens immediately when the user logs out

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.14** or compatible version
- **AWS SAM CLI** - [Install the AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- **AWS CLI** - [Install the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Docker** (optional, for local testing) - [Install Docker](https://docs.docker.com/get-docker/)
- **AWS Account** with appropriate permissions to create Lambda functions, API Gateway, and DynamoDB tables

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd tax-app-backend
```

### 2. Set Up Python Virtual Environment (Recommended)

Using a virtual environment isolates project dependencies from your system Python:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Your prompt should now show (venv) prefix
```

**Note:** You'll need to activate the virtual environment every time you start a new terminal session.

### 3. Install Dependencies

With the virtual environment activated, install the dependencies:

```bash
pip install -r user_registration/requirements.txt
```

For development and testing, also install the test dependencies:

```bash
pip install -r user_registration/tests/requirements-dev.txt
```

## Running Tests

The project includes both unit tests and property-based tests to ensure correctness.

### Run All Tests

```bash
pytest user_registration/tests/
```

### Run Tests with Verbose Output

```bash
pytest user_registration/tests/ -v
```

### Run Specific Test Files

```bash
# Run only unit tests
pytest user_registration/tests/test_*_unit.py

# Run only property-based tests
pytest user_registration/tests/test_*_property.py

# Run integration tests
pytest user_registration/tests/test_lambda_handler_integration.py
```

### Run Tests with Coverage

```bash
pytest user_registration/tests/ --cov=user_registration --cov-report=html
```

## Local Development

### Using LocalStack for Local AWS Emulation

LocalStack allows you to develop and test AWS applications locally without connecting to real AWS services.

#### Prerequisites

- **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** - Usually included with Docker Desktop
- **awscli-local** - Install with `pip install awscli-local`

#### Quick Start with LocalStack

```bash
# Complete setup (install dependencies + start LocalStack)
make setup

# Or step by step:
make install              # Install Python dependencies
make localstack-start     # Start LocalStack in Docker
make localstack-init      # Initialize DynamoDB table
```

#### Daily Development Workflow

**First Time Setup** (run once):
```bash
make setup
```

**Every Day After** (when you start working):
```bash
# Check if LocalStack is running
make localstack-status

# If not running, start it
make localstack-start

# Run your tests
make test
```

**When You're Done** (optional):
```bash
make localstack-stop
```

**Note:** You can also use `docker-compose up -d` instead of `make localstack-start` if you prefer.

#### Available Make Commands

```bash
make help                 # Show all available commands
make localstack-start     # Start LocalStack
make localstack-stop      # Stop LocalStack
make localstack-logs      # View LocalStack logs
make localstack-status    # Check LocalStack health
make test                 # Run tests with moto (no LocalStack needed)
make test-local           # Run tests against LocalStack
make deploy-local         # Deploy to LocalStack using SAM
make clean                # Clean up and stop LocalStack
```

#### Using LocalStack

Once LocalStack is running, you can interact with it using the AWS CLI with the `--endpoint-url` flag or using `awslocal`:

```bash
# List DynamoDB tables
awslocal dynamodb list-tables --region us-east-1

# Scan the users table
awslocal dynamodb scan --table-name Users --region us-east-1

# Test the endpoint (after deploying)
curl -X POST http://localhost:4566/restapis/*/Prod/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "SecurePass123!"
  }'
```

#### Environment Variables for LocalStack

Use `.env.local` for LocalStack development:

```bash
# Load LocalStack environment
source .env.local

# Or export manually
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export USER_TABLE_NAME=Users
```

### Build the SAM Application

Before running locally or deploying, build the application:

```bash
# For local development with LocalStack
sam build --parameter-overrides Environment=local

# For production deployment to AWS
sam build --parameter-overrides Environment=production

# Or use Makefile shortcuts:
make sam-build-local   # Build for local development
make sam-build-prod    # Build for production
```

**Important:** The `Environment` parameter controls whether the Lambda connects to LocalStack (local) or real AWS (production). This allows the same code to work in both environments without manual changes.

### Run Locally

#### Option 1: With LocalStack (Recommended for Full Testing)

This connects SAM to LocalStack so your Lambda can access the DynamoDB table:

```bash
# 1. Make sure LocalStack is running
make localstack-start

# 2. Build the SAM application for local development
sam build --parameter-overrides Environment=local

# 3. Start SAM with LocalStack connection
sam local start-api --docker-network tax-app-network --env-vars env.json --parameter-overrides Environment=local

# Or use the Makefile shortcut (does steps 2-3):
make sam-start
```

The API will be available at `http://localhost:3000`

**What's happening:**
- `--parameter-overrides Environment=local` tells SAM to use LocalStack endpoint
- `--env-vars env.json` loads environment variables into Lambda containers
- `--docker-network tax-app-network` connects SAM to LocalStack's Docker network
- Lambda automatically connects to LocalStack's DynamoDB at `http://host.docker.internal:4566`
- No manual configuration changes needed!

#### Option 2: Without LocalStack (Quick Testing)

For quick testing without database persistence:

```bash
sam build
sam local start-api
```

**Note:** This won't connect to DynamoDB, so registration will fail with database errors.

### Test Local Endpoint

```bash
curl -X POST http://localhost:3000/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "SecurePass123!"
  }'
```

## Deployment

### Environment Parameter System

This project uses CloudFormation parameters to automatically configure the application for local development or production deployment. **No manual code changes are needed!**

**How it works:**
- `Environment=local`: Lambda connects to LocalStack at `http://172.18.0.1:4566`
- `Environment=production`: Lambda connects to real AWS DynamoDB

### First-Time Deployment

For the first deployment, use the guided deployment process:

```bash
# 1. Build for production
sam build --parameter-overrides Environment=production

# 2. Deploy with guided setup
sam deploy --guided --parameter-overrides Environment=production
```

You will be prompted to provide:
- **Stack Name**: Name for your CloudFormation stack (e.g., `tax-app-backend`)
- **AWS Region**: Region to deploy to (e.g., `us-east-1`)
- **Confirm changes before deploy**: Choose `Y` to review changes
- **Allow SAM CLI IAM role creation**: Choose `Y` to allow SAM to create IAM roles
- **Save arguments to configuration file**: Choose `Y` to save settings for future deployments

### Subsequent Deployments

After the initial guided deployment, you can deploy with:

```bash
sam build --parameter-overrides Environment=production
sam deploy --parameter-overrides Environment=production

# Or use the Makefile shortcut:
make sam-build-prod
sam deploy --parameter-overrides Environment=production
```

### Deployment Outputs

After successful deployment, SAM will output important information:

- **UserRegistrationApi**: The API Gateway endpoint URL for the registration endpoint
- **UsersTableName**: The DynamoDB table name
- **UserRegistrationFunction**: The Lambda function ARN

Example output:
```
Outputs:
UserRegistrationApi: https://abc123xyz.execute-api.us-east-1.amazonaws.com/Prod/register/
UsersTableName: Users
UserRegistrationFunction: arn:aws:lambda:us-east-1:123456789012:function:tax-app-backend-UserRegistrationFunction-ABC123
```

## API Documentation

### Available Endpoints

This API provides the following endpoints:

- **POST /register** - Register a new user account
- **POST /login** - Authenticate and receive a JWT token

**Note:** There is no `/logout` endpoint. Logout is handled on the client side by discarding the JWT token. See the [Authentication and Logout](#authentication-and-logout) section for details.

### User Registration Endpoint

Register a new user with email, name, and password.

#### Endpoint

```
POST https://<api-id>.execute-api.<region>.amazonaws.com/Prod/register
```

Replace `<api-id>` and `<region>` with your actual API Gateway ID and AWS region from the deployment outputs.

#### Request Format

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePass123!"
}
```

**Field Requirements:**

- **email** (required): Valid email address following RFC 5322 format
- **name** (required): Non-empty string (whitespace-only names are rejected)
- **password** (required): Must meet the following requirements:
  - Minimum 8 characters
  - At least one uppercase letter (A-Z)
  - At least one lowercase letter (a-z)
  - At least one digit (0-9)
  - At least one special character (e.g., !@#$%^&*)

#### Response Format

**Success Response (201 Created):**

```json
{
  "message": "User registered successfully",
  "email": "user@example.com"
}
```

**Validation Error (400 Bad Request):**

```json
{
  "error": "Validation failed: Invalid email format"
}
```

```json
{
  "error": "Validation failed: Password must be at least 8 characters and contain uppercase, lowercase, digit, and special character"
}
```

```json
{
  "error": "Missing required fields: email, password"
}
```

**Duplicate Email Error (409 Conflict):**

```json
{
  "error": "Email already registered"
}
```

**Internal Server Error (500):**

```json
{
  "error": "Internal server error"
}
```

#### Example Requests

**Successful Registration:**

```bash
curl -X POST https://abc123xyz.execute-api.us-east-1.amazonaws.com/Prod/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "name": "John Doe",
    "password": "MySecure123!"
  }'
```

Response:
```json
{
  "message": "User registered successfully",
  "email": "john.doe@example.com"
}
```

**Invalid Email:**

```bash
curl -X POST https://abc123xyz.execute-api.us-east-1.amazonaws.com/Prod/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email",
    "name": "John Doe",
    "password": "MySecure123!"
  }'
```

Response:
```json
{
  "error": "Validation failed: Invalid email format"
}
```

**Weak Password:**

```bash
curl -X POST https://abc123xyz.execute-api.us-east-1.amazonaws.com/Prod/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "name": "John Doe",
    "password": "weak"
  }'
```

Response:
```json
{
  "error": "Validation failed: Password must be at least 8 characters and contain uppercase, lowercase, digit, and special character"
}
```

**Duplicate Email:**

```bash
# First registration succeeds
curl -X POST https://abc123xyz.execute-api.us-east-1.amazonaws.com/Prod/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "name": "John Doe",
    "password": "MySecure123!"
  }'

# Second registration with same email fails
curl -X POST https://abc123xyz.execute-api.us-east-1.amazonaws.com/Prod/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "name": "Jane Doe",
    "password": "AnotherPass456!"
  }'
```

Response:
```json
{
  "error": "Email already registered"
}
```

#### Security Features

- **Password Hashing**: Passwords are hashed using bcrypt with a work factor of 12 before storage
- **No Plaintext Storage**: Plaintext passwords are never stored in the database
- **Duplicate Detection**: Email uniqueness is enforced at the database level
- **Input Validation**: All inputs are validated before processing
- **CORS Support**: Cross-origin requests are supported with appropriate headers
- **Secure Logging**: Passwords and password hashes are never logged

#### CORS Headers

All responses include the following CORS headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token
Access-Control-Allow-Methods: GET,POST,OPTIONS
```

## Troubleshooting

### Common Issues

**Issue: SAM build fails**
- Ensure Python 3.14 is installed and available in your PATH
- Check that all dependencies in `requirements.txt` are installable

**Issue: Tests fail with DynamoDB errors**
- Ensure `moto` is installed for mocking AWS services
- Check that environment variables are set correctly in tests

**Issue: Deployment fails with IAM permissions**
- Ensure your AWS credentials have permissions to create Lambda functions, API Gateway, and DynamoDB tables
- Check the AWS CloudFormation console for detailed error messages

**Issue: API returns 500 errors**
- Check CloudWatch Logs for the Lambda function
- Verify the DynamoDB table exists and the Lambda has permissions
- Ensure the `USER_TABLE_NAME` environment variable is set correctly

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
