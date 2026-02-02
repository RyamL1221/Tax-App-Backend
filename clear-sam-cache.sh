#!/bin/bash

# Script to clear SAM local cache and Docker containers

echo "Clearing SAM cache..."
echo ""

# Stop any running SAM containers
echo "1. Stopping SAM Lambda containers..."
docker ps | grep 'lambci\|public.ecr.aws/lambda' | awk '{print $1}' | xargs -r docker stop 2>/dev/null

# Remove SAM containers
echo "2. Removing SAM Lambda containers..."
docker ps -a | grep 'lambci\|public.ecr.aws/lambda' | awk '{print $1}' | xargs -r docker rm 2>/dev/null

# Clean build directory
echo "3. Cleaning build directory..."
rm -rf .aws-sam/build

echo ""
echo "✅ Cache cleared!"
echo ""
echo "Next steps:"
echo "  1. sam build"
echo "  2. sam local start-api --env-vars env.json --docker-network tax-app-network"
