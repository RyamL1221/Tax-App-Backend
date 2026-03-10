# AWS SES Setup Guide for Password Recovery

This guide provides comprehensive instructions for setting up AWS Simple Email Service (SES) for the password recovery feature in the Tax-App-Backend project.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Email/Domain Verification](#emaildomain-verification)
4. [Moving from Sandbox to Production](#moving-from-sandbox-to-production)
5. [Email Authentication (SPF, DKIM, DMARC)](#email-authentication-spf-dkim-dmarc)
6. [IAM Permissions](#iam-permissions)
7. [Environment Configuration](#environment-configuration)
8. [Testing Email Sending](#testing-email-sending)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)

## Overview

AWS SES is used to send password reset emails to users. The system supports two environments:

- **Local Development (LocalStack)**: Uses LocalStack SES emulation for testing
- **Production (AWS SES)**: Uses real AWS SES for sending emails

### Key Features

- Email verification for sender addresses
- Sandbox mode for testing (limited recipients)
- Production mode for unrestricted sending
- Email authentication (SPF, DKIM, DMARC) for deliverability
- Retry logic with exponential backoff
- Comprehensive logging and monitoring

## Prerequisites

Before setting up SES, ensure you have:

- AWS account with appropriate permissions
- AWS CLI installed and configured
- Access to DNS settings for your domain (for domain verification)
- Email client access for email verification

## Email/Domain Verification

SES requires verification of sender email addresses or domains before sending emails.

### Option 1: Email Address Verification (Quickest)

Use this for testing or if you don't own a domain.

#### Step 1: Verify Email Address in AWS Console

1. Open the AWS SES Console: https://console.aws.amazon.com/ses/
2. Navigate to **Configuration** → **Verified identities**
3. Click **Create identity**
4. Select **Email address**
5. Enter your sender email (e.g., `noreply@yourdomain.com`)
6. Click **Create identity**

#### Step 2: Check Verification Email

1. Check the inbox of the email address you entered
2. Look for an email from Amazon SES with subject "Amazon SES Email Address Verification Request"
3. Click the verification link in the email
4. You should see a confirmation page: "Congratulations! You've successfully verified..."

#### Step 3: Verify Status in Console

1. Return to the SES Console → **Verified identities**
2. Your email should show status: **Verified** (green checkmark)
3. Note: Verification may take a few minutes

#### Using AWS CLI

```bash
# Verify email address
aws ses verify-email-identity --email-address noreply@yourdomain.com --region us-east-1

# Check verification status
aws ses get-identity-verification-attributes \
  --identities noreply@yourdomain.com \
  --region us-east-1
```

### Option 2: Domain Verification (Recommended for Production)

Use this for production to send from any email address at your domain.

#### Step 1: Verify Domain in AWS Console

1. Open the AWS SES Console: https://console.aws.amazon.com/ses/
2. Navigate to **Configuration** → **Verified identities**
3. Click **Create identity**
4. Select **Domain**
5. Enter your domain (e.g., `yourdomain.com`)
6. Check **Assign a default configuration set** (optional)
7. Click **Create identity**

#### Step 2: Add DNS Records

AWS will provide DNS records to add to your domain:

**CNAME Records for Verification:**
```
Name: _amazonses.yourdomain.com
Type: CNAME
Value: [provided by AWS, e.g., abc123.dkim.amazonses.com]
```

**How to add DNS records:**

**Using Route 53 (if your domain is hosted on AWS):**
1. SES Console will show a button: **Publish DNS records to Route 53**
2. Click the button to automatically add records
3. Verification happens automatically

**Using Other DNS Providers (GoDaddy, Namecheap, Cloudflare, etc.):**
1. Copy the CNAME record details from SES Console
2. Log in to your DNS provider
3. Navigate to DNS management for your domain
4. Add a new CNAME record with the provided name and value
5. Save changes

#### Step 3: Wait for Verification

- DNS propagation can take 5 minutes to 48 hours
- Check status in SES Console → **Verified identities**
- Status will change from **Pending** to **Verified**

#### Using AWS CLI

```bash
# Verify domain
aws ses verify-domain-identity --domain yourdomain.com --region us-east-1

# Check verification status
aws ses get-identity-verification-attributes \
  --identities yourdomain.com \
  --region us-east-1
```

### Verification Best Practices

- **Use domain verification for production** - Allows sending from any email at your domain
- **Verify multiple email addresses for testing** - Useful in sandbox mode
- **Keep verification emails** - Save them for reference
- **Monitor verification status** - Set up CloudWatch alarms for verification failures

## Moving from Sandbox to Production

New AWS accounts start in **SES Sandbox mode** with restrictions.

### Sandbox Mode Restrictions

- Can only send to verified email addresses
- Maximum 200 emails per 24 hours
- Maximum 1 email per second
- Cannot send to unverified recipients

### Production Mode Benefits

- Can send to any email address
- Higher sending limits (starts at 50,000 emails per 24 hours)
- Higher sending rate (starts at 14 emails per second)
- Can request limit increases

### Requesting Production Access

#### Step 1: Open Support Case

1. Open AWS SES Console: https://console.aws.amazon.com/ses/
2. Click **Account dashboard** in left sidebar
3. Under **Sending statistics**, click **Request production access**
4. Fill out the form:

**Use case description (example):**
```
We are building a tax document management application that requires
password reset email functionality. Users will request password resets
through our web application, and we will send them secure reset links
via email.

Expected sending volume: 1,000-5,000 emails per month
Email types: Transactional (password reset notifications only)
Bounce/complaint handling: We monitor bounce and complaint rates and
maintain email list hygiene.
```

**Mail type:** Select **Transactional**

**Website URL:** Your application URL

**Use case description:** Explain your use case (see example above)

**Additional information:**
- Describe how you handle bounces and complaints
- Explain your email list management
- Mention compliance with anti-spam laws

#### Step 2: Wait for Approval

- AWS typically responds within 24 hours
- You may receive follow-up questions
- Check your AWS account email for updates

#### Step 3: Verify Production Access

```bash
# Check account sending limits
aws ses get-send-quota --region us-east-1
```

**Output:**
```json
{
    "Max24HourSend": 50000.0,
    "MaxSendRate": 14.0,
    "SentLast24Hours": 0.0
}
```

- `Max24HourSend`: Maximum emails per 24 hours
- `MaxSendRate`: Maximum emails per second
- `SentLast24Hours`: Emails sent in last 24 hours

### Production Access Best Practices

- **Request production access early** - Can take 24-48 hours
- **Provide detailed use case** - Increases approval chances
- **Start with conservative estimates** - You can request increases later
- **Monitor sending limits** - Set up CloudWatch alarms

## Email Authentication (SPF, DKIM, DMARC)

Email authentication improves deliverability and prevents spoofing.

### Why Email Authentication Matters

- **Improves deliverability** - Emails less likely to be marked as spam
- **Builds sender reputation** - ISPs trust authenticated emails
- **Prevents spoofing** - Protects your domain from impersonation
- **Required by many ISPs** - Gmail, Yahoo, etc. require authentication

### DKIM (DomainKeys Identified Mail)

DKIM adds a digital signature to your emails.

#### Enable DKIM in SES

**Using AWS Console:**

1. Open SES Console → **Configuration** → **Verified identities**
2. Click your verified domain
3. Navigate to **Authentication** tab
4. Under **DKI**, click **Edit**
5. Check **Enabled**
6. Click **Save changes**

**AWS provides 3 CNAME records to add to DNS:**

```
Name: abc123._domainkey.yourdomain.com
Type: CNAME
Value: abc123.dkim.amazonses.com

Name: def456._domainkey.yourdomain.com
Type: CNAME
Value: def456.dkim.amazonses.com

Name: ghi789._domainkey.yourdomain.com
Type: CNAME
Value: ghi789.dkim.amazonses.com
```

#### Add DKIM Records to DNS

**Using Route 53:**
- Click **Publish DNS records to Route 53** in SES Console

**Using Other DNS Providers:**
- Add all 3 CNAME records to your DNS settings
- Wait for DNS propagation (5 minutes to 48 hours)

#### Verify DKIM Status

```bash
# Check DKIM status
aws ses get-identity-dkim-attributes \
  --identities yourdomain.com \
  --region us-east-1
```

**Expected output:**
```json
{
    "DkimAttributes": {
        "yourdomain.com": {
            "DkimEnabled": true,
            "DkimVerificationStatus": "Success",
            "DkimTokens": ["abc123", "def456", "ghi789"]
        }
    }
}
```

### SPF (Sender Policy Framework)

SPF specifies which mail servers can send email for your domain.

#### Add SPF Record to DNS

**Record details:**
```
Name: yourdomain.com (or @ for root domain)
Type: TXT
Value: "v=spf1 include:amazonses.com ~all"
```

**If you already have an SPF record:**
```
# Before
v=spf1 include:_spf.google.com ~all

# After (add amazonses.com)
v=spf1 include:_spf.google.com include:amazonses.com ~all
```

**SPF Record Explanation:**
- `v=spf1` - SPF version 1
- `include:amazonses.com` - Allow Amazon SES to send
- `~all` - Soft fail for other servers (recommended)

#### Verify SPF Record

```bash
# Check SPF record (macOS/Linux)
dig TXT yourdomain.com +short

# Check SPF record (Windows)
nslookup -type=TXT yourdomain.com
```

### DMARC (Domain-based Message Authentication)

DMARC builds on SPF and DKIM to provide reporting and policy enforcement.

#### Add DMARC Record to DNS

**Basic DMARC record:**
```
Name: _dmarc.yourdomain.com
Type: TXT
Value: "v=DMARC1; p=none; rua=mailto:dmarc-reports@yourdomain.com"
```

**DMARC Record Explanation:**
- `v=DMARC1` - DMARC version 1
- `p=none` - Policy (none = monitor only, quarantine = spam folder, reject = block)
- `rua=mailto:...` - Email address for aggregate reports

**Recommended DMARC progression:**
1. Start with `p=none` to monitor
2. After 1-2 weeks, change to `p=quarantine`
3. After another 1-2 weeks, change to `p=reject`

**Production DMARC record:**
```
v=DMARC1; p=reject; rua=mailto:dmarc-reports@yourdomain.com; ruf=mailto:dmarc-forensics@yourdomain.com; pct=100; adkim=s; aspf=s
```

#### Verify DMARC Record

```bash
# Check DMARC record (macOS/Linux)
dig TXT _dmarc.yourdomain.com +short

# Check DMARC record (Windows)
nslookup -type=TXT _dmarc.yourdomain.com
```

### Email Authentication Checklist

- [ ] DKIM enabled in SES Console
- [ ] 3 DKIM CNAME records added to DNS
- [ ] DKIM verification status: Success
- [ ] SPF TXT record added to DNS
- [ ] SPF record includes `include:amazonses.com`
- [ ] DMARC TXT record added to DNS
- [ ] DMARC policy starts at `p=none`
- [ ] DMARC reports email address configured

### Testing Email Authentication

Use these tools to verify your email authentication:

- **MXToolbox**: https://mxtoolbox.com/SuperTool.aspx
- **DMARC Analyzer**: https://www.dmarcanalyzer.com/
- **Mail Tester**: https://www.mail-tester.com/

**How to test:**
1. Send a test email from your application
2. Forward the received email to checker@mail-tester.com
3. View your score and authentication results
4. Fix any issues identified

## IAM Permissions

Lambda functions need IAM permissions to send emails via SES.

### Required IAM Permissions

The Lambda execution role needs these SES permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            "Resource": "*"
        }
    ]
}
```

### Permissions in SAM Template

The `template.yaml` already includes SES permissions:

```yaml
ForgotPasswordFunction:
  Type: AWS::Serverless::Function
  Properties:
    # ... other properties ...
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref ResetTokens
      - DynamoDBCrudPolicy:
          TableName: !Ref RateLimits
      - Statement:
          - Effect: Allow
            Action:
              - ses:SendEmail
              - ses:SendRawEmail
            Resource: '*'
```

### Verifying IAM Permissions

```bash
# Get Lambda function configuration
aws lambda get-function-configuration \
  --function-name tax-app-backend-ForgotPasswordFunction-ABC123 \
  --region us-east-1

# Get IAM role ARN from output, then check role policies
aws iam list-attached-role-policies \
  --role-name tax-app-backend-ForgotPasswordFunctionRole-ABC123

# Get inline policies
aws iam list-role-policies \
  --role-name tax-app-backend-ForgotPasswordFunctionRole-ABC123
```

### Least Privilege Principle

For production, restrict SES permissions to specific sender addresses:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            "Resource": "arn:aws:ses:us-east-1:123456789012:identity/noreply@yourdomain.com"
        }
    ]
}
```

## Environment Configuration

Configure environment variables for SES integration.

### Required Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `FROM_EMAIL` | Verified sender email address | `noreply@yourdomain.com` | Yes |
| `SES_REGION` | AWS region for SES | `us-east-1` | Yes |
| `BASE_URL` | Frontend base URL for reset links | `https://app.yourdomain.com` | Yes |
| `AWS_ENDPOINT_URL` | LocalStack endpoint (local only) | `http://172.18.0.1:4566` | No |
| `CONFIGURATION_SET_NAME` | SES configuration set (optional) | `password-reset-emails` | No |

### Local Development Configuration

**File: `.env.local`**

```bash
# LocalStack SES configuration
AWS_ENDPOINT_URL=http://172.18.0.1:4566
FROM_EMAIL=noreply@example.com
SES_REGION=us-east-1
BASE_URL=http://localhost:3000
```

**File: `env.json`**

```json
{
  "ForgotPasswordFunction": {
    "FROM_EMAIL": "noreply@example.com",
    "SES_REGION": "us-east-1",
    "BASE_URL": "http://localhost:3000",
    "AWS_ENDPOINT_URL": "http://172.18.0.1:4566"
  }
}
```

### Production Configuration

**File: `template.yaml`**

```yaml
ForgotPasswordFunction:
  Type: AWS::Serverless::Function
  Properties:
    Environment:
      Variables:
        FROM_EMAIL: noreply@yourdomain.com
        SES_REGION: us-east-1
        BASE_URL: https://app.yourdomain.com
        # AWS_ENDPOINT_URL not set in production
```

### Configuration Best Practices

- **Use verified sender email** - Must be verified in SES
- **Match SES region** - Use the region where you verified your email/domain
- **Use HTTPS in production** - BASE_URL should use HTTPS
- **Don't commit secrets** - Use AWS Secrets Manager for sensitive data
- **Test configuration** - Verify environment variables are set correctly

## Testing Email Sending

Test email sending in both local and production environments.

### Testing with LocalStack (Local Development)

#### Step 1: Start LocalStack

```bash
# Start LocalStack with SES
docker-compose up -d

# Verify LocalStack is running
docker ps | grep localstack
```

#### Step 2: Verify Sender Email in LocalStack

```bash
# Verify email in LocalStack
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws ses verify-email-identity \
  --email-address noreply@example.com \
  --endpoint-url http://localhost:4566 \
  --region us-east-1

# Check verification status
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws ses get-identity-verification-attributes \
  --identities noreply@example.com \
  --endpoint-url http://localhost:4566 \
  --region us-east-1
```

#### Step 3: Start SAM Local

```bash
# Build for local
sam build

# Start SAM local API
sam local start-api --docker-network tax-app-network --env-vars env.json
```

#### Step 4: Test Forgot Password Endpoint

```bash
# Send password reset request
curl -X POST http://localhost:3000/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

#### Step 5: Check LocalStack Logs

```bash
# View LocalStack logs
docker logs tax-app-localstack -f

# Look for SES email send events
```

**Note:** LocalStack doesn't actually send emails. It logs the email send request.

### Testing with Real AWS SES

#### Step 1: Verify Sender Email

```bash
# Verify email in AWS SES
aws ses verify-email-identity \
  --email-address noreply@yourdomain.com \
  --region us-east-1

# Wait for verification email and click link
```

#### Step 2: Deploy to AWS

```bash
# Build for production
sam build --parameter-overrides Environment=production

# Deploy
sam deploy --parameter-overrides Environment=production
```

#### Step 3: Test Production Endpoint

```bash
# Get API URL from deployment outputs
API_URL="https://abc123.execute-api.us-east-1.amazonaws.com/Prod"

# Send password reset request
curl -X POST $API_URL/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-verified-email@example.com"
  }'
```

**Note:** In sandbox mode, recipient email must also be verified.

#### Step 4: Check Email Inbox

1. Check the inbox of the recipient email
2. Look for password reset email
3. Verify email content and reset link
4. Click reset link to test complete flow

#### Step 5: Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/tax-app-backend-ForgotPasswordFunction-ABC123 --follow

# Look for:
# - "Email sent successfully. MessageId: ..."
# - "Reset email sent successfully to: use***@example.com"
```

### Testing Checklist

- [ ] LocalStack SES integration works
- [ ] Sender email verified in AWS SES
- [ ] Production deployment successful
- [ ] Password reset email received
- [ ] Email content correct (reset link, expiration)
- [ ] Reset link works
- [ ] CloudWatch logs show success
- [ ] No errors in Lambda logs

## Monitoring and Logging

Monitor email delivery and track metrics.

### CloudWatch Metrics

SES automatically publishes metrics to CloudWatch:

**Key Metrics:**
- `Send` - Number of emails sent
- `Delivery` - Number of emails delivered
- `Bounce` - Number of bounced emails
- `Complaint` - Number of spam complaints
- `Reject` - Number of rejected emails

**View metrics in AWS Console:**
1. Open CloudWatch Console: https://console.aws.amazon.com/cloudwatch/
2. Navigate to **Metrics** → **All metrics**
3. Select **SES**
4. View metrics by email address or domain

### CloudWatch Alarms

Set up alarms for email delivery issues:

#### High Bounce Rate Alarm

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name ses-high-bounce-rate \
  --alarm-description "Alert when bounce rate exceeds 5%" \
  --metric-name Reputation.BounceRate \
  --namespace AWS/SES \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 0.05 \
  --comparison-operator GreaterThanThreshold \
  --region us-east-1
```

#### High Complaint Rate Alarm

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name ses-high-complaint-rate \
  --alarm-description "Alert when complaint rate exceeds 0.1%" \
  --metric-name Reputation.ComplaintRate \
  --namespace AWS/SES \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 0.001 \
  --comparison-operator GreaterThanThreshold \
  --region us-east-1
```

#### Email Send Failures Alarm

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name ses-send-failures \
  --alarm-description "Alert when email sends fail" \
  --metric-name Reject \
  --namespace AWS/SES \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --region us-east-1
```

### Lambda Logging

The EmailService logs comprehensive information:

**Log Levels:**
- `INFO` - Successful operations
- `WARNING` - Retries, transient errors
- `ERROR` - Permanent failures

**Example logs:**

```
INFO: Email sent successfully. MessageId: 0102018d1234abcd-12345678-1234-1234-1234-123456789abc-000000
INFO: Reset email sent successfully to: use***@example.com
WARNING: Transient error Throttling, retrying in 1.23s (attempt 1/3)
ERROR: Permanent SES error: MessageRejected
```

### CloudWatch Insights Queries

Query Lambda logs for email metrics:

**Count successful email sends:**
```
fields @timestamp, @message
| filter @message like /Email sent successfully/
| stats count() as EmailsSent by bin(5m)
```

**Count email failures:**
```
fields @timestamp, @message
| filter @message like /Failed to send reset email/
| stats count() as EmailsFailed by bin(5m)
```

**Track retry attempts:**
```
fields @timestamp, @message
| filter @message like /retrying in/
| parse @message /retrying in * \(attempt (?<attempt>\d+)/
| stats count() as Retries by attempt
```

### SES Reputation Dashboard

Monitor your sender reputation:

1. Open SES Console → **Account dashboard**
2. View **Reputation metrics**:
   - Bounce rate (should be < 5%)
   - Complaint rate (should be < 0.1%)
3. View **Sending statistics**:
   - Emails sent
   - Delivery rate
   - Bounce rate
   - Complaint rate

### Monitoring Best Practices

- **Set up CloudWatch alarms** - Get notified of issues
- **Monitor bounce rate** - Keep below 5%
- **Monitor complaint rate** - Keep below 0.1%
- **Review logs regularly** - Check for patterns
- **Track MessageIds** - Useful for debugging
- **Use CloudWatch Insights** - Query logs for metrics

## Common Issues and Troubleshooting

### Issue 1: Email Not Verified

**Symptoms:**
- Error: "Email address is not verified"
- Error: "MessageRejected"

**Solution:**
```bash
# Verify email address
aws ses verify-email-identity \
  --email-address noreply@yourdomain.com \
  --region us-east-1

# Check verification status
aws ses get-identity-verification-attributes \
  --identities noreply@yourdomain.com \
  --region us-east-1
```

### Issue 2: Sandbox Mode Restrictions

**Symptoms:**
- Error: "Email address is not verified" (for recipient)
- Can only send to specific email addresses

**Solution:**
- Verify recipient email addresses in sandbox mode
- Request production access (see [Moving from Sandbox to Production](#moving-from-sandbox-to-production))

### Issue 3: Throttling Errors

**Symptoms:**
- Error: "Throttling"
- Error: "Maximum sending rate exceeded"

**Solution:**
- EmailService automatically retries with exponential backoff
- Check sending limits: `aws ses get-send-quota --region us-east-1`
- Request limit increase if needed

### Issue 4: Invalid Endpoint

**Symptoms:**
- Error: "Could not connect to the endpoint URL"
- Timeout errors

**Solution:**
```bash
# Check AWS_ENDPOINT_URL environment variable
# Local: should be http://172.18.0.1:4566
# Production: should not be set

# Verify in Lambda
aws lambda get-function-configuration \
  --function-name ForgotPasswordFunction \
  --region us-east-1 \
  --query 'Environment.Variables'
```

### Issue 5: Missing IAM Permissions

**Symptoms:**
- Error: "User is not authorized to perform: ses:SendEmail"
- Error: "AccessDenied"

**Solution:**
- Check Lambda execution role has SES permissions
- See [IAM Permissions](#iam-permissions) section

### Issue 6: Email Goes to Spam

**Symptoms:**
- Email delivered but in spam folder
- Low deliverability

**Solution:**
- Set up DKIM, SPF, DMARC (see [Email Authentication](#email-authentication-spf-dkim-dmarc))
- Warm up your sending reputation (start with low volume)
- Use a verified domain (not just email address)
- Avoid spam trigger words in email content

### Issue 7: High Bounce Rate

**Symptoms:**
- CloudWatch alarm: High bounce rate
- SES reputation dashboard shows high bounce rate

**Solution:**
- Remove invalid email addresses from your list
- Implement email validation before sending
- Monitor bounce notifications
- Keep bounce rate below 5%

### Issue 8: Configuration Set Not Found

**Symptoms:**
- Error: "ConfigurationSetDoesNotExist"

**Solution:**
```bash
# List configuration sets
aws ses list-configuration-sets --region us-east-1

# Create configuration set if needed
aws ses create-configuration-set \
  --configuration-set Name=password-reset-emails \
  --region us-east-1

# Or remove CONFIGURATION_SET_NAME environment variable
```

### Debugging Checklist

When troubleshooting email issues:

- [ ] Check sender email is verified in SES
- [ ] Check recipient email is verified (sandbox mode only)
- [ ] Check AWS_ENDPOINT_URL is correct for environment
- [ ] Check Lambda has SES IAM permissions
- [ ] Check CloudWatch logs for error details
- [ ] Check SES sending limits
- [ ] Check SES reputation metrics
- [ ] Test with mail-tester.com
- [ ] Verify DKIM, SPF, DMARC records

### Getting Help

If you're still experiencing issues:

1. **Check AWS Service Health Dashboard**: https://status.aws.amazon.com/
2. **Review SES Developer Guide**: https://docs.aws.amazon.com/ses/
3. **Open AWS Support Case**: https://console.aws.amazon.com/support/
4. **Check CloudWatch Logs**: Look for detailed error messages
5. **Test with AWS CLI**: Isolate the issue

## Summary

### Quick Setup Checklist

- [ ] Verify sender email/domain in SES
- [ ] Request production access (if needed)
- [ ] Set up DKIM, SPF, DMARC
- [ ] Configure IAM permissions in template.yaml
- [ ] Set environment variables (FROM_EMAIL, SES_REGION, BASE_URL)
- [ ] Test with LocalStack
- [ ] Deploy to AWS
- [ ] Test production email sending
- [ ] Set up CloudWatch alarms
- [ ] Monitor bounce and complaint rates

### Key Takeaways

- **Email verification is required** - Verify sender email/domain before sending
- **Start in sandbox mode** - Request production access when ready
- **Email authentication improves deliverability** - Set up DKIM, SPF, DMARC
- **Monitor your reputation** - Keep bounce rate < 5%, complaint rate < 0.1%
- **Use CloudWatch for monitoring** - Set up alarms and review logs
- **Test thoroughly** - Test in both local and production environments

### Related Documentation

- [Password Recovery Testing Guide](PASSWORD_RECOVERY_TESTING.md)
- [LocalStack SAM Setup](LOCALSTACK_SAM_SETUP.md)
- [Quick Reference Guide](QUICK_REFERENCE.md)
- [AWS SES Developer Guide](https://docs.aws.amazon.com/ses/)

## Appendix: Useful Commands

### SES Management

```bash
# Verify email address
aws ses verify-email-identity --email-address EMAIL --region REGION

# Verify domain
aws ses verify-domain-identity --domain DOMAIN --region REGION

# Check verification status
aws ses get-identity-verification-attributes --identities EMAIL_OR_DOMAIN --region REGION

# Get sending limits
aws ses get-send-quota --region REGION

# List verified identities
aws ses list-identities --region REGION

# Get DKIM attributes
aws ses get-identity-dkim-attributes --identities DOMAIN --region REGION

# Send test email
aws ses send-email \
  --from noreply@yourdomain.com \
  --to recipient@example.com \
  --subject "Test Email" \
  --text "This is a test email" \
  --region us-east-1
```

### CloudWatch Logs

```bash
# Tail Lambda logs
aws logs tail /aws/lambda/FUNCTION_NAME --follow

# Query logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/FUNCTION_NAME \
  --filter-pattern "Email sent successfully" \
  --region us-east-1
```

### LocalStack SES

```bash
# Verify email in LocalStack
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws ses verify-email-identity \
  --email-address EMAIL \
  --endpoint-url http://localhost:4566 \
  --region us-east-1

# List verified emails in LocalStack
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws ses list-identities \
  --endpoint-url http://localhost:4566 \
  --region us-east-1
```
