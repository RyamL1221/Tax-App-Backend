#!/bin/bash

# Set dummy AWS credentials for LocalStack (it doesn't validate them)
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Print statement
echo "Attempting to create DynamoDB Tables"

# Create DynamoDB Users table
aws dynamodb create-table \
    --table-name Users \
    --attribute-definitions \
        AttributeName=email,AttributeType=S \
    --key-schema \
        AttributeName=email,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "Users table created"

# Create DynamoDB ResetTokens table
aws dynamodb create-table \
    --table-name ResetTokens \
    --attribute-definitions \
        AttributeName=token_hash,AttributeType=S \
    --key-schema \
        AttributeName=token_hash,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "ResetTokens table created"

# Create DynamoDB RateLimits table
aws dynamodb create-table \
    --table-name RateLimits \
    --attribute-definitions \
        AttributeName=identifier,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema \
        AttributeName=identifier,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "RateLimits table created"

# Enable TTL on ResetTokens table
aws dynamodb update-time-to-live \
    --table-name ResetTokens \
    --time-to-live-specification "Enabled=true, AttributeName=ttl" \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "TTL enabled on ResetTokens table"

# Enable TTL on RateLimits table
aws dynamodb update-time-to-live \
    --table-name RateLimits \
    --time-to-live-specification "Enabled=true, AttributeName=ttl" \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "TTL enabled on RateLimits table"

# Print statement
echo "Listing tables to verify creation"

# List tables to verify
aws dynamodb list-tables --region us-east-1 --endpoint-url http://localhost:4566