# Password Recovery Testing Guide (LocalStack)

## Overview

When testing the password recovery endpoints locally with LocalStack, emails are not actually sent. Instead, the plaintext reset token is logged to the console for testing purposes.

## Prerequisites

1. LocalStack must be running: `docker-compose up -d`
2. SAM application must be built: `sam build`
3. SAM local API must be running: `sam local start-api --env-vars env.json --docker-network tax-app-network`

## Testing Workflow

### Option 1: Using the Test Script (Recommended)

```bash
./test-forgot-password.sh
```

This script will:
1. Call the `/forgot-password` endpoint with a test email
2. Wait for logs to flush
3. Extract and display the reset token

### Option 2: Manual Testing

#### Step 1: Call Forgot Password Endpoint

```bash
curl -X POST http://localhost:3000/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Expected response:
```json
{
  "message": "If an account exists with this email, a password reset link has been sent."
}
```

#### Step 2: Extract Token from Logs

```bash
./get-reset-token.sh
```

This will search the LocalStack logs and display the most recent reset token.

#### Step 3: Use Token to Reset Password

```bash
curl -X POST http://localhost:3000/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_TOKEN_HERE",
    "new_password": "NewSecurePassword123!"
  }'
```

### Option 3: Using Postman

1. Import `postman_collection.json`
2. Navigate to **Password Recovery** folder
3. Run **Forgot Password - Existing User** request
4. Run `./get-reset-token.sh` in terminal to get the token
5. Copy the token to **Reset Password - Valid Token** request
6. Run the reset password request

## How It Works

### Development-Only Token Logging

The `forgot_password_handler.py` includes special logging that only activates in local development:

```python
# DEV ONLY: Log plaintext token for local testing
aws_endpoint = os.environ.get('AWS_ENDPOINT_URL', '')
if 'localstack' in aws_endpoint.lower() or 'localhost' in aws_endpoint.lower():
    logger.info(f"[DEV ONLY] Reset token for {email}: {plaintext_token}")
```

**Important**: When running `sam local start-api`, Lambda logs appear in the **SAM terminal output**, not in LocalStack logs.

### Where to Find the Token

After calling the forgot-password endpoint, check your **SAM terminal** (where you ran `sam local start-api`) for output like:

```
[INFO] 2026-02-02T02:05:23.456Z ... Generated reset token for email: test@example.com
[INFO] 2026-02-02T02:05:23.457Z ... [DEV ONLY] Reset token for test@example.com: YWJjMTIzZGVmNDU2...
[INFO] 2026-02-02T02:05:23.458Z ... [DEV ONLY] Reset link: http://localhost:3000/reset-password?token=YWJjMTIzZGVmNDU2...
```

Copy the token from this output.

### Token Extraction Script

The `get-reset-token.sh` script searches LocalStack logs, but since SAM runs locally, you need to check the SAM terminal output instead. See [MANUAL_TOKEN_RETRIEVAL.md](./MANUAL_TOKEN_RETRIEVAL.md) for detailed instructions.

## Troubleshooting

### No Token Found in Logs

If `get-reset-token.sh` returns "No reset token found":

1. **Check if user exists**: The token is only generated for existing users
   ```bash
   # Create a test user first
   curl -X POST http://localhost:3000/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "TestPassword123!"
     }'
   ```

2. **Check LocalStack logs directly**:
   ```bash
   docker logs tax-app-localstack 2>&1 | grep "DEV ONLY"
   ```

3. **Verify environment variables**: Check that `AWS_ENDPOINT_URL` is set in `env.json`

### SES MessageRejected Error

This is expected in LocalStack's free tier. The error message:
```
SES error sending reset email: MessageRejected
```

This is normal and doesn't affect testing. The token is still generated and logged before the email attempt.

### Rate Limiting

The forgot-password endpoint has rate limiting (5 requests per 15 minutes per IP). If you hit the limit:

```json
{
  "error": "Too many requests. Please try again later.",
  "retry_after": 900
}
```

Wait for the retry period or clear the RateLimits table:
```bash
aws dynamodb delete-table --table-name RateLimits --endpoint-url=http://localhost:4566
./init-localstack.sh  # Recreate the table
```

## Security Notes

⚠️ **IMPORTANT**: The development-only logging is automatically disabled in production environments. Never manually log tokens in production code.

The logging only activates when:
- `AWS_ENDPOINT_URL` contains "localstack" or "localhost"
- This environment variable is only set in local development (`env.json`)
- Production Lambda functions don't have this variable set

## Testing Checklist

- [ ] User registration works
- [ ] Forgot password returns success for existing user
- [ ] Token can be extracted from logs
- [ ] Reset password works with valid token
- [ ] Reset password fails with invalid token
- [ ] Reset password fails with expired token (wait 1 hour)
- [ ] Reset password fails with reused token
- [ ] Rate limiting works (try 6 requests quickly)
- [ ] Non-enumeration works (same response for non-existent user)
