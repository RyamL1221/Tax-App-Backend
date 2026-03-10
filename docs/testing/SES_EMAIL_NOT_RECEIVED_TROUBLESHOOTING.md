# SES Email Not Received - Troubleshooting Guide

## Issue Summary

**Problem**: User tested the forgot password endpoint but did not receive the password reset email.

**Root Cause**: AWS SES account is in Sandbox mode, which restricts email sending to only verified email addresses.

## Diagnosis

### SES Account Status

```bash
$ aws ses get-send-quota --region us-east-1
{
    "Max24HourSend": 200.0,
    "MaxSendRate": 1.0,
    "SentLast24Hours": 0.0
}
```

**Analysis**:
- `Max24HourSend: 200.0` indicates the account is in **Sandbox mode**
- In Sandbox mode, emails can only be sent to verified email addresses
- Both the sender (FROM_EMAIL) and recipient must be verified

## Solution Options

### Option 1: Verify Recipient Email Address (Quick Fix for Testing)

This is the fastest solution for testing purposes.

#### Step 1: Verify the Recipient Email

```bash
# Replace with the email address you want to test with
aws ses verify-email-identity \
  --email-address your-test-email@example.com \
  --region us-east-1
```

#### Step 2: Check Your Email Inbox

1. Check the inbox of the email address you just verified
2. Look for an email from Amazon SES with subject: "Amazon SES Email Address Verification Request"
3. Click the verification link in the email
4. You should see a confirmation page: "Congratulations! You've successfully verified..."

#### Step 3: Verify the Verification Status

```bash
aws ses get-identity-verification-attributes \
  --identities your-test-email@example.com \
  --region us-east-1
```

**Expected output**:
```json
{
    "VerificationAttributes": {
        "your-test-email@example.com": {
            "VerificationStatus": "Success"
        }
    }
}
```

#### Step 4: Test Again

```bash
# Test the forgot password endpoint again
curl -X POST https://your-api-url/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-test-email@example.com"
  }'
```

#### Step 5: Check Email Inbox

You should now receive the password reset email within a few seconds.

### Option 2: Request Production Access (Recommended for Production)

This removes the restriction and allows sending to any email address.

#### Step 1: Open AWS SES Console

1. Go to: https://console.aws.amazon.com/ses/
2. Click **Account dashboard** in the left sidebar
3. Under **Sending statistics**, click **Request production access**

#### Step 2: Fill Out the Request Form

**Use case description (example)**:
```
We are building a tax document management application that requires
password reset email functionality. Users will request password resets
through our web application, and we will send them secure reset links
via email.

Expected sending volume: 1,000-5,000 emails per month
Email types: Transactional (password reset notifications only)
Bounce/complaint handling: We monitor bounce and complaint rates and
maintain email list hygiene through automated processes.
```

**Form fields**:
- **Mail type**: Select "Transactional"
- **Website URL**: Your application URL
- **Use case description**: Explain your use case (see example above)
- **Additional information**:
  - Describe how you handle bounces and complaints
  - Explain your email list management
  - Mention compliance with anti-spam laws (CAN-SPAM, GDPR)

#### Step 3: Submit and Wait for Approval

- AWS typically responds within 24 hours
- You may receive follow-up questions
- Check your AWS account email for updates

#### Step 4: Verify Production Access

```bash
# Check sending limits after approval
aws ses get-send-quota --region us-east-1
```

**Expected output after approval**:
```json
{
    "Max24HourSend": 50000.0,
    "MaxSendRate": 14.0,
    "SentLast24Hours": 0.0
}
```

- `Max24HourSend: 50000.0` indicates Production mode
- You can now send to any email address

## Verification Checklist

Before testing, ensure:

- [ ] Sender email (FROM_EMAIL) is verified in SES
- [ ] Recipient email is verified (Sandbox mode only)
- [ ] SES account status checked (Sandbox vs Production)
- [ ] Lambda has SES IAM permissions
- [ ] Environment variables are set correctly (FROM_EMAIL, SES_REGION, BASE_URL)
- [ ] AWS_ENDPOINT_URL is NOT set in production Lambda

## Common Mistakes

### Mistake 1: Only Verified Sender, Not Recipient

**Problem**: Verified the sender email but forgot to verify the recipient email in Sandbox mode.

**Solution**: Verify both sender AND recipient emails in Sandbox mode.

### Mistake 2: Clicked Wrong Verification Link

**Problem**: Received multiple verification emails and clicked an old/expired link.

**Solution**: Request a new verification email and click the latest link.

### Mistake 3: Wrong AWS Region

**Problem**: Verified email in us-east-1 but Lambda is configured for us-west-2.

**Solution**: Verify email in the same region as your Lambda function (check SES_REGION environment variable).

### Mistake 4: Verification Email in Spam

**Problem**: Verification email from Amazon SES went to spam folder.

**Solution**: Check spam/junk folder for emails from "no-reply-aws@amazon.com".

## Checking CloudWatch Logs

To see what happened during the email send attempt:

```bash
# Get your Lambda function name
aws lambda list-functions --query 'Functions[?contains(FunctionName, `ForgotPassword`)].FunctionName'

# Tail the logs
aws logs tail /aws/lambda/your-function-name --follow
```

**Look for these log messages**:

**Success**:
```
INFO: Email sent successfully to: use***@example.com. MessageId: 0102018d...
INFO: Reset email sent successfully to: use***@example.com. MessageId: 0102018d...
```

**Failure (Unverified Recipient)**:
```
ERROR: Permanent SES error: MessageRejected
ERROR: Failed to send reset email to: use***@example.com
```

**Failure (Unverified Sender)**:
```
ERROR: Permanent SES error: MailFromDomainNotVerified
ERROR: Failed to send reset email to: use***@example.com
```

## Testing Workflow

### Complete Testing Workflow for Sandbox Mode

1. **Verify sender email**:
   ```bash
   aws ses verify-email-identity --email-address noreply@yourdomain.com --region us-east-1
   ```

2. **Verify recipient email** (your test email):
   ```bash
   aws ses verify-email-identity --email-address your-test-email@example.com --region us-east-1
   ```

3. **Check both verification emails and click links**

4. **Verify both are verified**:
   ```bash
   aws ses list-identities --region us-east-1
   ```

5. **Test the endpoint**:
   ```bash
   curl -X POST https://your-api-url/auth/forgot-password \
     -H "Content-Type: application/json" \
     -d '{"email": "your-test-email@example.com"}'
   ```

6. **Check CloudWatch logs**:
   ```bash
   aws logs tail /aws/lambda/your-function-name --follow
   ```

7. **Check email inbox** for password reset email

## Next Steps

### For Testing (Sandbox Mode)

1. Verify your test email address in SES
2. Click the verification link
3. Test the forgot password endpoint again
4. You should receive the email

### For Production

1. Request production access from AWS SES
2. Wait for approval (typically 24 hours)
3. Once approved, you can send to any email address
4. Set up email authentication (DKIM, SPF, DMARC) for better deliverability

## Related Documentation

- [SES Setup Guide](../development/SES_SETUP_GUIDE.md) - Complete SES configuration guide
- [Password Recovery Testing](PASSWORD_RECOVERY_TESTING.md) - Testing guide for password recovery
- [LocalStack SAM Setup](../development/LOCALSTACK_SAM_SETUP.md) - Local development setup

## Summary

**The issue**: AWS SES Sandbox mode restricts email sending to verified addresses only.

**The solution**: 
- **Quick fix**: Verify the recipient email address in SES
- **Long-term**: Request production access to send to any email address

**Key takeaway**: In Sandbox mode, both sender AND recipient emails must be verified in SES before emails can be delivered.
