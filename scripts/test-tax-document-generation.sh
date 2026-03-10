#!/bin/bash

# Test script for tax document generation endpoint
# This script tests the /generate endpoint with LocalStack

set -e

echo "=== Tax Document Generation Test Script ==="
echo ""

# Configuration
API_URL="${API_URL:-http://localhost:3000}"
ENDPOINT="${API_URL}/Prod/generate"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Generate JWT token for testing
generate_jwt() {
    local user_id="$1"
    local secret="local-dev-secret-key-min-32-chars-long-for-security"
    
    # Use Python to generate JWT
    python3 << EOF
import jwt
from datetime import datetime, timedelta

payload = {
    "userId": "$user_id",
    "exp": datetime.utcnow() + timedelta(hours=1)
}
token = jwt.encode(payload, "$secret", algorithm="HS256")
print(token)
EOF
}

# Test 1: Valid document generation request
test_valid_request() {
    print_info "Test 1: Valid document generation request"
    
    JWT_TOKEN=$(generate_jwt "test-user-123")
    
    RESPONSE=$(curl -s -X POST "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d '{
            "documentType": "1040",
            "formData": {
                "firstName": "John",
                "lastName": "Doe",
                "ssn": "123-45-6789",
                "filingStatus": "single",
                "income": 75000
            }
        }')
    
    if echo "$RESPONSE" | grep -q '"jobId"'; then
        print_success "Valid request succeeded"
        echo "Response: $RESPONSE"
    else
        print_error "Valid request failed"
        echo "Response: $RESPONSE"
        return 1
    fi
    
    echo ""
}

# Test 2: Missing required field
test_missing_field() {
    print_info "Test 2: Missing required field (should fail)"
    
    JWT_TOKEN=$(generate_jwt "test-user-456")
    
    RESPONSE=$(curl -s -X POST "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d '{
            "documentType": "1040",
            "formData": {
                "firstName": "Jane",
                "lastName": "Smith"
            }
        }')
    
    if echo "$RESPONSE" | grep -q '"error".*"ValidationError"'; then
        print_success "Missing field validation works"
        echo "Response: $RESPONSE"
    else
        print_error "Missing field validation failed"
        echo "Response: $RESPONSE"
        return 1
    fi
    
    echo ""
}

# Test 3: Invalid JWT token
test_invalid_jwt() {
    print_info "Test 3: Invalid JWT token (should fail)"
    
    RESPONSE=$(curl -s -X POST "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer invalid-token-here" \
        -d '{
            "documentType": "1040",
            "formData": {
                "firstName": "Bob",
                "lastName": "Johnson",
                "ssn": "987-65-4321",
                "filingStatus": "single",
                "income": 50000
            }
        }')
    
    if echo "$RESPONSE" | grep -q '"error".*"AuthenticationError"'; then
        print_success "JWT validation works"
        echo "Response: $RESPONSE"
    else
        print_error "JWT validation failed"
        echo "Response: $RESPONSE"
        return 1
    fi
    
    echo ""
}

# Test 4: Invalid SSN format
test_invalid_ssn() {
    print_info "Test 4: Invalid SSN format (should fail)"
    
    JWT_TOKEN=$(generate_jwt "test-user-789")
    
    RESPONSE=$(curl -s -X POST "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d '{
            "documentType": "1040",
            "formData": {
                "firstName": "Alice",
                "lastName": "Williams",
                "ssn": "12345678",
                "filingStatus": "single",
                "income": 60000
            }
        }')
    
    if echo "$RESPONSE" | grep -q '"error".*"ValidationError"'; then
        print_success "SSN format validation works"
        echo "Response: $RESPONSE"
    else
        print_error "SSN format validation failed"
        echo "Response: $RESPONSE"
        return 1
    fi
    
    echo ""
}

# Run all tests
main() {
    echo "Testing endpoint: $ENDPOINT"
    echo ""
    
    # Check if PyJWT is installed
    if ! python3 -c "import jwt" 2>/dev/null; then
        print_error "PyJWT is not installed. Install with: pip install PyJWT"
        exit 1
    fi
    
    # Run tests
    test_valid_request || exit 1
    test_missing_field || exit 1
    test_invalid_jwt || exit 1
    test_invalid_ssn || exit 1
    
    echo ""
    print_success "All tests passed!"
}

main
