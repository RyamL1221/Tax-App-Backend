#!/bin/bash

# Helper script to view reset tokens from DynamoDB (shows hashes, not plaintext)

echo "Reset tokens in DynamoDB (hashed):"
echo "===================================="
echo ""

AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws dynamodb scan \
  --table-name ResetTokens \
  --endpoint-url http://localhost:4566 \
  --region us-east-1 \
  --output table

echo ""
echo "⚠️  Note: These are HASHED tokens, not the plaintext tokens."
echo "    You need the plaintext token from your SAM terminal output."
echo ""
echo "    Look for lines containing '[DEV ONLY]' in the terminal where"
echo "    you ran 'sam local start-api'"
