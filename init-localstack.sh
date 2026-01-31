#!/bin/bash

echo "Initializing LocalStack resources..."

# Wait for LocalStack to be ready
sleep 5

# Create DynamoDB table
awslocal dynamodb create-table \
    --table-name UsersTable \
    --attribute-definitions \
        AttributeName=email,AttributeType=S \
    --key-schema \
        AttributeName=email,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

echo "DynamoDB table 'UsersTable' created successfully"

# List tables to verify
awslocal dynamodb list-tables --region us-east-1

echo "LocalStack initialization complete!"
