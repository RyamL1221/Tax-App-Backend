#!/bin/bash

# Script to completely restart SAM local with fresh Lambda containers
# This ensures no cached containers are reused

echo "=== Restarting SAM Local with Fresh Containers ==="
echo ""

# Step 1: Stop any running SAM processes
echo "Step 1: Checking for running SAM processes..."
SAM_PIDS=$(ps aux | grep "sam local start-api" | grep -v grep | awk '{print $2}')
if [ -n "$SAM_PIDS" ]; then
    echo "Found SAM processes: $SAM_PIDS"
    echo "Please stop SAM local (Ctrl+C in the SAM terminal) and run this script again."
    exit 1
else
    echo "✓ No SAM processes running"
fi

# Step 2: Remove ALL Lambda containers
echo ""
echo "Step 2: Removing all Lambda containers..."
LAMBDA_CONTAINERS=$(docker ps -a | grep -E 'lambci|public.ecr.aws/lambda|rapid' | awk '{print $1}')
if [ -n "$LAMBDA_CONTAINERS" ]; then
    echo "Found Lambda containers:"
    docker ps -a | grep -E 'lambci|public.ecr.aws/lambda|rapid'
    echo ""
    echo "Removing containers..."
    echo "$LAMBDA_CONTAINERS" | xargs docker rm -f
    echo "✓ Lambda containers removed"
else
    echo "✓ No Lambda containers found"
fi

# Step 3: Clean build directory
echo ""
echo "Step 3: Cleaning build directory..."
rm -rf .aws-sam/build
echo "✓ Build directory cleaned"

# Step 4: Rebuild
echo ""
echo "Step 4: Building SAM application..."
sam build
if [ $? -ne 0 ]; then
    echo "✗ Build failed!"
    exit 1
fi
echo "✓ Build successful"

# Step 5: Instructions for restart
echo ""
echo "=== Ready to Restart ==="
echo ""
echo "Now run SAM local with:"
echo "  sam local start-api --env-vars env.json --docker-network tax-app-network"
echo ""
echo "After SAM starts, test the reset-password endpoint:"
echo "  1. Get a fresh token: ./test-forgot-password.sh"
echo "  2. Look for [DEV ONLY] token in SAM terminal output"
echo "  3. Test reset: ./test-reset-password.sh <token>"
echo ""
