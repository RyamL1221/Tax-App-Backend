#!/bin/bash

# Test script for forgot-password endpoint with token extraction

echo "Testing forgot-password endpoint..."
echo ""

# Call the forgot-password endpoint
curl -X POST http://localhost:3000/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

echo ""
echo ""
echo "✅ Request sent successfully!"
echo ""
echo "📋 To get the reset token:"
echo "   Look in your SAM terminal output for lines containing '[DEV ONLY]'"
echo "   The token will be logged there immediately after the request."
echo ""
echo "   Example output:"
echo "   [INFO] [DEV ONLY] Reset token for test@example.com: abc123..."
echo "   [INFO] [DEV ONLY] Reset link: http://localhost:3000/reset-password?token=abc123..."
echo ""
echo "💡 Tip: The token is the long base64-encoded string after 'token='"
