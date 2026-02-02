# Manual Token Retrieval Guide

## The Issue

When running SAM locally with `sam local start-api`, Lambda logs appear in the **SAM terminal output**, not in LocalStack logs. This means the `[DEV ONLY]` token logs will show up in your SAM terminal.

## How to Get the Reset Token

### Method 1: Check SAM Terminal Output (Recommended)

1. **Call the forgot-password endpoint**:
   ```bash
   curl -X POST http://localhost:3000/forgot-password \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com"}'
   ```

2. **Look at your SAM terminal** (where you ran `sam local start-api`)

3. **Find the `[DEV ONLY]` lines**:
   ```
   [INFO] 2026-02-02T02:05:23.456Z ... Generated reset token for email: test@example.com
   [INFO] 2026-02-02T02:05:23.457Z ... [DEV ONLY] Reset token for test@example.com: YWJjMTIzZGVmNDU2...
   [INFO] 2026-02-02T02:05:23.458Z ... [DEV ONLY] Reset link: http://localhost:3000/reset-password?token=YWJjMTIzZGVmNDU2...
   ```

4. **Copy the token** (the long base64-encoded string)

### Method 2: Use the Test Script

```bash
./test-forgot-password.sh
```

Then check your SAM terminal for the `[DEV ONLY]` logs.

### Method 3: Query DynamoDB Directly (Advanced)

You can see the token **hash** (not the plaintext token) in DynamoDB:

```bash
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws dynamodb scan \
  --table-name ResetTokens \
  --endpoint-url http://localhost:4566 \
  --region us-east-1
```

**Note**: This shows the hashed token, not the plaintext token you need for testing.

## Why This Happens

- **SAM Local**: Runs Lambda functions in Docker containers on your machine
- **Lambda Logs**: Go to the SAM terminal (stdout), not to LocalStack
- **LocalStack Logs**: Only contain LocalStack service logs (DynamoDB, SES, etc.)

## Testing the Reset Password Endpoint

Once you have the token from the SAM terminal:

```bash
curl -X POST http://localhost:3000/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_TOKEN_HERE",
    "new_password": "NewSecurePassword123!"
  }'
```

## Troubleshooting

### No [DEV ONLY] Logs Appearing

**Check 1**: Verify the user exists
```bash
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws dynamodb get-item \
  --table-name Users \
  --key '{"email": {"S": "test@example.com"}}' \
  --endpoint-url http://localhost:4566 \
  --region us-east-1
```

If no user exists, create one:
```bash
curl -X POST http://localhost:3000/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

**Check 2**: Verify AWS_ENDPOINT_URL is set

The dev logging only works when `AWS_ENDPOINT_URL` contains "localstack" or "localhost". Check your `env.json`:

```json
{
  "ForgotPasswordFunction": {
    "AWS_ENDPOINT_URL": "http://172.18.0.1:4566",
    ...
  }
}
```

**Check 3**: Rebuild SAM

```bash
sam build
# Then restart: sam local start-api --env-vars env.json --docker-network tax-app-network
```

### Rate Limit Errors

If you get "Too many requests", clear the rate limit table:

```bash
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws dynamodb delete-table --table-name RateLimits \
  --endpoint-url http://localhost:4566 --region us-east-1

./init-localstack.sh  # Recreate tables
```

## Production Behavior

In production (real AWS), the `[DEV ONLY]` logging is automatically disabled because:
- `AWS_ENDPOINT_URL` is not set in production Lambda functions
- The condition `if 'localstack' in aws_endpoint.lower()` will be false
- Tokens are never logged (security best practice)
