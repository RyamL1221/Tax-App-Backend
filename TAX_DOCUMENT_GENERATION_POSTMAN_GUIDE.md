# Tax Document Generation - Postman Testing Guide

## Prerequisites

1. **LocalStack running**:
   ```bash
   docker-compose up -d
   ```

2. **Initialize LocalStack resources**:
   ```bash
   ./init-localstack.sh
   ```

3. **Upload the 1099-DIV template to S3**:
   ```bash
   export AWS_ACCESS_KEY_ID=test
   export AWS_SECRET_ACCESS_KEY=test
   export AWS_DEFAULT_REGION=us-east-1
   
   # Upload as 1099-DIV.pdf (matches the document type)
   aws s3 cp 1099-DIV.pdf s3://tax-app-documents/templates/irs/1099-DIV.pdf --endpoint-url http://localhost:4566
   ```

4. **Build and start SAM**:
   ```bash
   sam build && sam local start-api --docker-network tax-app-network --warm-containers EAGER
   ```

## Important: Document Type and PDF Filename

- **Document Type in API**: Use `1099-DIV` (matches your PDF)
- **PDF Filename in S3**: Must be `1099-DIV.pdf` (matches the document type)
- **Your source PDF**: `1099-DIV.pdf` (upload with same name)

The system constructs the S3 key as: `templates/irs/{documentType}.pdf`

## Postman Setup

1. **Import Collection**:
   - Open Postman
   - Click "Import"
   - Select `postman_collection.json`
   - Collection will appear as "Tax App API"

2. **Collection Variables**:
   - The collection has a variable `jwt_token` that automatically stores your JWT token
   - No manual configuration needed!

## Testing Workflow

### Step 1: Register a User

Navigate to: **User Registration** → **Successful Registration**

Request body:
```json
{
  "email": "john.doe@example.com",
  "name": "John Doe",
  "password": "SecurePass123!"
}
```

Click **Send**

Expected response (201):
```json
{
  "message": "User registered successfully",
  "email": "john.doe@example.com"
}
```

### Step 2: Login

Navigate to: **User Login** → **Successful Login**

Request body:
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!"
}
```

Click **Send**

Expected response (200):
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Important**: The JWT token is automatically saved to the collection variable `{{jwt_token}}`. You'll see this in the Postman Console.

### Step 3: Generate Tax Document

Navigate to: **Tax Document Generation** → **Generate 1099-DIV - Complete Form**

The Authorization header is automatically set to: `Bearer {{jwt_token}}`

Request body:
```json
{
  "documentType": "1099-DIV",
  "formData": {
    "payerName": "Vanguard Investments",
    "payerStreetAddress": "100 Vanguard Blvd",
    "payerCity": "Malvern",
    "payerState": "PA",
    "payerCountry": "USA",
    "payerZip": "19355",
    "payerPhone": "800-662-7447",
    "payerTIN": "23-1945930",
    "recipientTIN": "123-45-6789",
    "recipientName": "John Doe",
    "recipientStreetAddress": "456 Main St, Apt 2B",
    "recipientCity": "Boston",
    "recipientState": "MA",
    "recipientCountry": "USA",
    "recipientZip": "02101",
    "accountNumber": "12345678",
    "calendarYear": "2025",
    "totalOrdinaryDividends": 5000.00,
    "qualifiedDividends": 3000.00,
    "totalCapitalGainDistributions": 1500.00,
    "federalIncomeTaxWithheld": 500.00,
    "section199ADividends": 2000.00
  }
}
```

Click **Send**

Expected response (200):
```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "john.doe@example.com",
  "documentType": "1099-DIV",
  "status": "COMPLETED",
  "createdAt": "2026-02-02T12:00:00.000Z",
  "completedAt": "2026-02-02T12:00:01.234Z",
  "outputKey": "outputs/john.doe@example.com/550e8400-e29b-41d4-a716-446655440000/1099-DIV.pdf",
  "templateKey": "templates/irs/1099-DIV.pdf"
}
```

## Available Test Cases

### Valid Requests

1. **Generate 1099-DIV - Complete Form**
   - Full 1099-DIV form with payer, recipient, and dividend details
   - Includes address, phone, TIN, dividends, capital gains, and tax withholding

2. **Generate 1099-DIV - Minimal Required Fields**
   - Only the required fields: payerName, payerTIN, recipientTIN, recipientName, totalOrdinaryDividends
   - Tests minimum viable form submission

3. **Generate 1099-DIV - With Foreign Tax**
   - Includes foreign tax paid and foreign country
   - Tests international dividend scenarios

### Error Test Cases

1. **Missing Required Field (payerName)**
   - Expected: 400 ValidationError
   - Message: "Missing required field: payerName"

2. **Invalid TIN Format**
   - Expected: 400 ValidationError
   - TIN without proper format: "123456789"
   - Message: "TIN must be in format XX-XXXXXXX"

3. **Invalid JWT Token**
   - Expected: 401 AuthenticationError
   - Uses hardcoded invalid token
   - Message: "Invalid JWT token"

4. **Missing Authorization Header**
   - Expected: 401 AuthenticationError
   - No Authorization header sent
   - Message: "Missing or invalid Authorization header"

5. **Template Not Found**
   - Expected: 404 TemplateNotFoundError
   - Requests document type "1040" which doesn't exist
   - Message: "Template not found for document type: 1040"

## Verifying Generated Documents

To check if the document was actually created in S3:

```bash
# List all generated documents
aws s3 ls s3://tax-app-documents/outputs/ --recursive --endpoint-url http://localhost:4566

# Download a specific document
aws s3 cp s3://tax-app-documents/outputs/john.doe@example.com/JOB-ID-HERE/1099-DIV.pdf ./output.pdf --endpoint-url http://localhost:4566
```

## Checking Job Status in DynamoDB

```bash
# Scan all jobs
aws dynamodb scan \
  --table-name TaxDocumentJobs \
  --endpoint-url http://localhost:4566

# Get specific job by ID
aws dynamodb get-item \
  --table-name TaxDocumentJobs \
  --key '{"jobId": {"S": "YOUR-JOB-ID-HERE"}}' \
  --endpoint-url http://localhost:4566
```

## Troubleshooting

### Issue: 401 AuthenticationError even with valid token

**Solution**: Make sure you ran the login request first. The token is automatically saved, but only after a successful login.

### Issue: 404 Template not found

**Solution**: Verify the template was uploaded to S3 with the correct name:
```bash
aws s3 ls s3://tax-app-documents/templates/irs/ --endpoint-url http://localhost:4566
```

You should see `1099-DIV.pdf` in the list.

### Issue: Token expired

**Solution**: JWT tokens expire after 1 hour. Simply run the login request again to get a fresh token.

### Issue: SAM not responding

**Solution**: Check if SAM is running:
```bash
# Check running containers
docker ps

# View SAM logs
docker logs -f $(docker ps -q --filter ancestor=public.ecr.aws/sam/emulation-python3.14)
```

## Tips

1. **Use Postman Console**: Open the console (View → Show Postman Console) to see detailed request/response logs and the JWT token being saved.

2. **Collection Variables**: You can manually view/edit the `jwt_token` variable by clicking on the collection name → Variables tab.

3. **Environment Variables**: If you want to test against different environments (e.g., production), create a Postman environment with different base URLs.

4. **Test Scripts**: The login request has a test script that automatically saves the JWT token. You can add similar scripts to other requests if needed.

## Quick Reference

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| `/register` | POST | No | Create new user account |
| `/login` | POST | No | Get JWT token |
| `/Prod/generate` | POST | Yes (JWT) | Generate tax document |

## Form Data Fields for 1099

| Field | Type | Required | Format | Example |
|-------|------|----------|--------|---------|
| firstName | string | Yes | Non-empty | "John" |
| lastName | string | Yes | Non-empty | "Doe" |
| ssn | string | Yes | XXX-XX-XXXX | "123-45-6789" |
| income | number | Yes | Non-negative (int or float) | 5000 |

## Form Data Fields for 1040

| Field | Type | Required | Format | Example |
|-------|------|----------|--------|---------|
| firstName | string | Yes | Non-empty | "John" |
| lastName | string | Yes | Non-empty | "Doe" |
| ssn | string | Yes | XXX-XX-XXXX | "123-45-6789" |
| filingStatus | string | Yes | One of: single, married_filing_jointly, married_filing_separately, head_of_household, qualifying_widow | "single" |
| income | number | Yes | Non-negative (int or float) | 75000 |

## Form Data Fields for W2

| Field | Type | Required | Format | Example |
|-------|------|----------|--------|---------|
| firstName | string | Yes | Non-empty | "John" |
| lastName | string | Yes | Non-empty | "Doe" |
| ssn | string | Yes | XXX-XX-XXXX | "123-45-6789" |
| income | number | Yes | Non-negative (int or float) | 50000 |

## Next Steps

After successfully testing with Postman, you can:

1. Add more document types (upload more PDFs to S3)
2. Test with different form data combinations
3. Implement a frontend that calls these APIs
4. Add more validation rules
5. Implement document retrieval endpoints
