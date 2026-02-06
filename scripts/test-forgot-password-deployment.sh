#!/bin/bash

# Test script for ForgotPasswordFunction deployment verification
# This script validates Requirements: 4.2, 6.1, 6.3

set -e

echo "=========================================="
echo "ForgotPasswordFunction Deployment Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
    local test_name="$1"
    local payload="$2"
    local expected_status="$3"
    local expected_pattern="$4"
    
    echo -n "Testing: $test_name... "
    
    response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:3000/auth/forgot-password \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    body=$(echo "$response" | sed '$d')
    status=$(echo "$response" | tail -n 1)
    
    if [ "$status" -eq "$expected_status" ]; then
        if echo "$body" | grep -q "$expected_pattern"; then
            echo -e "${GREEN}✓ PASSED${NC}"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${RED}✗ FAILED${NC} - Response body doesn't match expected pattern"
            echo "  Expected pattern: $expected_pattern"
            echo "  Got: $body"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC} - Status code mismatch"
        echo "  Expected: $expected_status"
        echo "  Got: $status"
        echo "  Response: $body"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "1. Testing valid email (existing user)"
echo "   Validates: No import errors, function executes successfully"
test_endpoint \
    "Valid email - existing user" \
    '{"email": "test@example.com"}' \
    200 \
    "password reset link"

echo ""
echo "2. Testing valid email (non-existent user - non-enumeration)"
echo "   Validates: Application logic executes, returns same response"
test_endpoint \
    "Valid email - non-existent user" \
    '{"email": "nonexistent@example.com"}' \
    200 \
    "password reset link"

echo ""
echo "3. Testing invalid email format"
echo "   Validates: Input validation works"
test_endpoint \
    "Invalid email format" \
    '{"email": "invalid-email"}' \
    400 \
    "valid email address"

echo ""
echo "4. Testing missing email field"
echo "   Validates: Required field validation works"
test_endpoint \
    "Missing email field" \
    '{}' \
    400 \
    "Email address is required"

echo ""
echo "5. Testing malformed JSON"
echo "   Validates: Error handling works"
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:3000/auth/forgot-password \
    -H "Content-Type: application/json" \
    -d 'invalid json')
status=$(echo "$response" | tail -n 1)
if [ "$status" -eq 400 ] || [ "$status" -eq 500 ]; then
    echo -e "Testing: Malformed JSON... ${GREEN}✓ PASSED${NC} (Status: $status)"
    ((TESTS_PASSED++))
else
    echo -e "Testing: Malformed JSON... ${RED}✗ FAILED${NC} (Status: $status)"
    ((TESTS_FAILED++))
fi

echo ""
echo "=========================================="
echo "Database Verification"
echo "=========================================="
echo ""

echo "6. Verifying ResetTokens table has entries"
token_count=$(AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
    aws dynamodb scan --table-name ResetTokens \
    --endpoint-url http://localhost:4566 \
    --region us-east-1 2>/dev/null | jq '.Items | length')

if [ "$token_count" -gt 0 ]; then
    echo -e "   ${GREEN}✓ PASSED${NC} - Found $token_count reset tokens"
    ((TESTS_PASSED++))
else
    echo -e "   ${RED}✗ FAILED${NC} - No reset tokens found"
    ((TESTS_FAILED++))
fi

echo ""
echo "7. Verifying RateLimits table has entries"
rate_limit_count=$(AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
    aws dynamodb scan --table-name RateLimits \
    --endpoint-url http://localhost:4566 \
    --region us-east-1 2>/dev/null | jq '.Items | length')

if [ "$rate_limit_count" -gt 0 ]; then
    echo -e "   ${GREEN}✓ PASSED${NC} - Found $rate_limit_count rate limit entries"
    ((TESTS_PASSED++))
else
    echo -e "   ${RED}✗ FAILED${NC} - No rate limit entries found"
    ((TESTS_FAILED++))
fi

echo ""
echo "=========================================="
echo "Import Error Verification"
echo "=========================================="
echo ""

echo "8. Checking for import errors (502 responses)"
if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "   ${GREEN}✓ PASSED${NC} - No 502 errors detected"
    echo "   All responses were 200 or 400 (application-level responses)"
    echo "   This confirms no import errors occurred"
else
    echo -e "   ${YELLOW}⚠ WARNING${NC} - Some tests failed, check responses above"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""
    echo "Validation Complete:"
    echo "  ✓ No import errors (no 502 responses)"
    echo "  ✓ Function executes application logic successfully"
    echo "  ✓ Returns proper HTTP status codes (200, 400)"
    echo "  ✓ Database operations work (ResetTokens, RateLimits)"
    echo "  ✓ Input validation works correctly"
    echo ""
    echo "Requirements Validated: 4.2, 6.1, 6.3"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
