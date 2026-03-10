#!/bin/bash

# Helper script to extract the most recent password reset token from LocalStack logs

echo "Searching for password reset token in LocalStack logs..."
echo ""

# Try to extract token from [DEV ONLY] log line first (new format)
TOKEN=$(docker logs tax-app-localstack 2>&1 | grep "\[DEV ONLY\] Reset token for" | tail -1 | grep -o "[A-Za-z0-9+/=]\{32,\}" | head -1)

# Fallback: try to extract from reset link pattern (old format)
if [ -z "$TOKEN" ]; then
    TOKEN=$(docker logs tax-app-localstack 2>&1 | grep -o "http://[^'\"[:space:]]*/reset-password?token=[^'\"[:space:]]*" | tail -1 | sed 's/.*token=//')
fi

if [ -z "$TOKEN" ]; then
    echo "No reset token found in logs."
    echo ""
    echo "Make sure you've called the /forgot-password endpoint first."
    echo "You can also check the full logs with: docker logs tax-app-localstack"
else
    echo "Most recent reset token:"
    echo ""
    echo "$TOKEN"
    echo ""
    echo "Full reset link:"
    echo "http://localhost:3000/auth/reset-password?token=$TOKEN"
    echo ""
    echo "Use this token in your Postman request or copy it to test the reset-password endpoint."
fi
