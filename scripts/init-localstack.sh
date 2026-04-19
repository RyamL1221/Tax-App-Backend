#!/bin/bash

# Set dummy AWS credentials for LocalStack (it doesn't validate them)
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Stack name prefix for resource names (matches samconfig.toml stack_name)
STACK_NAME="${STACK_NAME:-tax-app-backend-dev}"

# Print statement
echo "Creating DynamoDB Tables with prefix: ${STACK_NAME}"

# Create DynamoDB Users table
aws dynamodb create-table \
    --table-name "${STACK_NAME}-Users" \
    --attribute-definitions \
        AttributeName=email,AttributeType=S \
    --key-schema \
        AttributeName=email,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "${STACK_NAME}-Users table created"

# Create DynamoDB ResetTokens table
aws dynamodb create-table \
    --table-name "${STACK_NAME}-ResetTokens" \
    --attribute-definitions \
        AttributeName=token_hash,AttributeType=S \
    --key-schema \
        AttributeName=token_hash,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "${STACK_NAME}-ResetTokens table created"

# Create DynamoDB RateLimits table
aws dynamodb create-table \
    --table-name "${STACK_NAME}-RateLimits" \
    --attribute-definitions \
        AttributeName=identifier,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema \
        AttributeName=identifier,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "${STACK_NAME}-RateLimits table created"

# Enable TTL on ResetTokens table
aws dynamodb update-time-to-live \
    --table-name "${STACK_NAME}-ResetTokens" \
    --time-to-live-specification "Enabled=true, AttributeName=ttl" \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "TTL enabled on ResetTokens table"

# Enable TTL on RateLimits table
aws dynamodb update-time-to-live \
    --table-name "${STACK_NAME}-RateLimits" \
    --time-to-live-specification "Enabled=true, AttributeName=ttl" \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "TTL enabled on RateLimits table"

# Create DynamoDB TaxDocumentJobs table
aws dynamodb create-table \
    --table-name "${STACK_NAME}-TaxDocumentJobs" \
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

echo "${STACK_NAME}-TaxDocumentJobs table created"

# Create DynamoDB ImportJobs table
aws dynamodb create-table \
    --table-name "${STACK_NAME}-ImportJobs" \
    --attribute-definitions \
        AttributeName=importJobId,AttributeType=S \
        AttributeName=userId,AttributeType=S \
    --key-schema \
        AttributeName=importJobId,KeyType=HASH \
    --global-secondary-indexes \
        "[{\"IndexName\":\"UserIdIndex\",\"KeySchema\":[{\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "${STACK_NAME}-ImportJobs table created"

# Create DynamoDB ImportJobRows table
aws dynamodb create-table \
    --table-name "${STACK_NAME}-ImportJobRows" \
    --attribute-definitions \
        AttributeName=importJobId,AttributeType=S \
        AttributeName=rowNumber,AttributeType=N \
    --key-schema \
        AttributeName=importJobId,KeyType=HASH \
        AttributeName=rowNumber,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "${STACK_NAME}-ImportJobRows table created"

# Create S3 bucket for tax documents
BUCKET_NAME="${STACK_NAME}-documents"
echo "Creating S3 bucket: ${BUCKET_NAME}"

aws s3 mb "s3://${BUCKET_NAME}" \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "S3 bucket ${BUCKET_NAME} created"

# Create folder structure in S3 bucket
aws s3api put-object \
    --bucket "${BUCKET_NAME}" \
    --key templates/irs/ \
    --region us-east-1 \
    --endpoint-url http://localhost:4566

echo "Created templates/irs/ folder in S3 bucket"

aws s3api put-object \
    --bucket "${BUCKET_NAME}" \
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

aws s3 cp ./samples/1099-DIV.pdf "s3://${BUCKET_NAME}/templates/irs/1099-DIV.pdf" \
    --endpoint-url http://localhost:4566

echo "1099-DIV template uploaded successfully"

# List S3 buckets to verify
echo "Listing S3 buckets to verify creation"
aws s3 ls --endpoint-url http://localhost:4566

# Verify template upload
echo "Verifying template upload"
aws s3 ls "s3://${BUCKET_NAME}/templates/irs/" --endpoint-url http://localhost:4566
