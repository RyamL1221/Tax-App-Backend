#!/bin/bash

# Set dummy AWS credentials for LocalStack (it doesn't validate them)
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Print statement
echo "Attempting to create DynamoDB Table"

# Create DynamoDB table
aws dynamodb create-table \
    --table-name Users \
    --attribute-definitions \
        AttributeName=email,AttributeType=S \
    --key-schema \
        AttributeName=email,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

# Print statement
echo "Listing tables to verify creation"

# List tables to verify
aws dynamodb list-tables --region us-east-1 --endpoint-url http://localhost:4566