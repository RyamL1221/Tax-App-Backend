#!/bin/bash

# Test script for LocalStack user registration endpoint

echo "Testing User Registration Endpoint on LocalStack"
echo "================================================"

# Set LocalStack endpoint
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Test 1: Create DynamoDB table
echo -e "\n1. Creating DynamoDB table..."
awslocal dynamodb create-table \
    --table-name Users \
    --attribute-definitions AttributeName=email,AttributeType=S \
    --key-schema AttributeName=email,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 2>/dev/null || echo "Table already exists"

# Test 2: List tables
echo -e "\n2. Listing DynamoDB tables..."
awslocal dynamodb list-tables --region us-east-1

# Test 3: Test user registration (if Lambda is deployed)
echo -e "\n3. Testing user registration..."
curl -X POST http://localhost:4566/restapis/*/Prod/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "SecurePass123!"
  }' 2>/dev/null || echo "Lambda not deployed yet. Deploy with 'make deploy-local'"

# Test 4: Check if user was created in DynamoDB
echo -e "\n4. Checking DynamoDB for created user..."
awslocal dynamodb scan --table-name Users --region us-east-1

echo -e "\n================================================"
echo "LocalStack testing complete!"
