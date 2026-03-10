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

# Create DynamoDB TaxDocumentJobs table
aws dynamodb create-table \
    --table-name TaxDocumentJobs \
    --attribute-definitions \
        AttributeName=jobId,AttributeType=S \
        AttributeName=userId,AttributeType=S \
    --key-schema \
        AttributeName=jobId,KeyType=HASH \
    --global-secondary-indexes \
        "[{\"IndexName\":\"UserIdIndex\",\"KeySchema\":[{\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "TaxDocumentJobs table created"

# Create S3 bucket for tax documents
echo "Creating S3 bucket for tax documents"

aws s3 mb s3://tax-app-documents \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "S3 bucket tax-app-documents created"

# Create folder structure in S3 bucket
aws s3api put-object \
    --bucket tax-app-documents \
    --key templates/irs/ \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "Created templates/irs/ folder in S3 bucket"

aws s3api put-object \
    --bucket tax-app-documents \
    --key outputs/ \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "Created outputs/ folder in S3 bucket"

# Print statement
echo "Listing tables to verify creation"

# List tables to verify
aws dynamodb list-tables --region us-east-1 --endpoint-url http://localhost:4566

# Upload 1099-DIV template to S3
echo "Uploading 1099-DIV template to S3"

aws s3 cp ./samples/1099-DIV.pdf s3://tax-app-documents/templates/irs/1099-DIV.pdf \
    --endpoint-url http://localhost:4566

echo "1099-DIV template uploaded successfully"

# List S3 buckets to verify
echo "Listing S3 buckets to verify creation"
aws s3 ls --endpoint-url http://localhost:4566

# Verify template upload
echo "Verifying template upload"
aws s3 ls s3://tax-app-documents/templates/irs/ --endpoint-url http://localhost:4566