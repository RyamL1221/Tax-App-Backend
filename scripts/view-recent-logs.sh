#!/bin/bash

# View recent LocalStack logs with focus on password recovery

echo "Recent LocalStack logs (last 50 lines):"
echo "========================================"
echo ""

docker logs tax-app-localstack 2>&1 | tail -50

echo ""
echo "========================================"
echo ""
echo "To see only DEV ONLY token logs:"
echo "  docker logs tax-app-localstack 2>&1 | grep 'DEV ONLY'"
echo ""
echo "To follow logs in real-time:"
echo "  docker logs -f tax-app-localstack"
