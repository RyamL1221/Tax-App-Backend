#!/bin/bash

echo "🚀 Starting Tax App Backend Development Environment"
echo "=================================================="

# Start LocalStack
echo "📦 Starting LocalStack..."
make localstack-start

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack to be ready..."
sleep 10

# Check LocalStack status
echo "✅ Checking LocalStack status..."
make localstack-status

# Load environment variables
echo "🔧 Loading environment variables..."
source .env.local

# Build SAM application
echo "🔨 Building SAM application..."
sam build

echo ""
echo "=================================================="
echo "✅ Setup complete!"
echo ""
echo "To start the API Gateway, run:"
echo "  sam local start-api --docker-network tax-app-network"
echo ""
echo "Then test with:"
echo "  curl -X POST http://localhost:3000/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@example.com\",\"name\":\"Test User\",\"password\":\"SecurePass123!\"}'"
echo ""
echo "To stop LocalStack when done:"
echo "  make localstack-stop"
echo "=================================================="
