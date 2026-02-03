#!/bin/bash

# Test script for reset-password endpoint
# Usage: ./test-reset-password.sh <token>

if [ -z "$1" ]; then
    echo "Usage: ./test-reset-password.sh <token>"
    echo ""
    echo "Example:"
    echo "  ./test-reset-password.sh akujcAnUs4b4OUo-mFljwhNw3R4tjf-C5tVsk_gzQRw="
    echo ""
    echo "Get a token by running: ./test-forgot-password.sh"
    echo "Then check your SAM terminal for the [DEV ONLY] token line"
    exit 1
fi

TOKEN="$1"

echo "Testing reset-password endpoint..."
echo "Token: $TOKEN"
echo ""

curl -X POST http://localhost:3000/reset-password \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN\",
    \"new_password\": \"NewSecurePassword123!\"
  }"

echo ""
echo ""
echo "If successful, you can now login with:"
echo "  Email: test@example.com"
echo "  Password: NewSecurePassword123!"
