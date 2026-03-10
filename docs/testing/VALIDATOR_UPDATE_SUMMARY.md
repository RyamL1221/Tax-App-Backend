# Validator Update Summary

## Changes Made

Updated the tax document generation system to properly support Form 1099-DIV with all official IRS fields.

### 1. Updated Input Validator (`tax_document_generation/input_validator.py`)

**Added Support For:**
- Document type `1099-DIV` with specific field requirements
- 5 required fields for 1099-DIV
- 40+ optional fields for complete 1099-DIV forms
- New validation patterns for TIN, ZIP, phone, state codes, and year

**New Validation Patterns:**
- `TIN_PATTERN`: XX-XXXXXXX (for Employer Identification Numbers)
- `ZIP_PATTERN`: XXXXX or XXXXX-XXXX
- `PHONE_PATTERN`: XXX-XXX-XXXX
- Valid US state/territory codes (50 states + DC, PR, VI, GU, AS, MP)

**New Validation Functions:**
- `_validate_tin_format()`: Validates payer TIN format
- `_validate_zip_code()`: Validates ZIP code format
- `_validate_phone_number()`: Validates phone number format
- `_validate_state_code()`: Validates US state/territory codes
- `_validate_year()`: Validates calendar year (1900-2100)
- `_validate_amount()`: Validates monetary amounts (non-negative)

### 2. Updated Postman Collection (`postman_collection.json`)

**Replaced Test Cases:**
- Old: Generic 1099 with firstName, lastName, ssn, income
- New: Proper 1099-DIV with payer, recipient, and dividend fields

**New Test Requests:**
1. **Generate 1099-DIV - Complete Form**: Full form with all major fields
2. **Generate 1099-DIV - Minimal Required Fields**: Only 5 required fields
3. **Generate 1099-DIV - With Foreign Tax**: International dividend scenario
4. **Missing Required Field (payerName)**: Tests validation
5. **Invalid TIN Format**: Tests TIN format validation
6. **Invalid JWT Token**: Tests authentication
7. **Missing Authorization Header**: Tests auth requirement
8. **Template Not Found**: Tests 404 error handling

### 3. Updated Documentation

**Created/Updated Files:**
- `1099-DIV_FIELD_REFERENCE.md`: Complete field reference with all 45+ fields
- `TAX_DOCUMENT_GENERATION_POSTMAN_GUIDE.md`: Updated with 1099-DIV examples
- `FORM_INPUTS_REFERENCE.md`: Updated with correct information

## Required Fields for 1099-DIV

```json
{
  "payerName": "string (non-empty)",
  "payerTIN": "string (format: XX-XXXXXXX)",
  "recipientTIN": "string (format: XXX-XX-XXXX)",
  "recipientName": "string (non-empty)",
  "totalOrdinaryDividends": "number (>= 0)"
}
```

## Optional Field Categories

1. **Payer Address** (6 fields): street, city, state, country, zip, phone
2. **Recipient Address** (5 fields): street, city, state, country, zip
3. **Account Info** (2 fields): accountNumber, calendarYear
4. **Dividends** (7 fields): qualified dividends, capital gains, various Section gains
5. **Distributions & Tax** (5 fields): nondividend distributions, withholding, expenses
6. **Foreign & Liquidation** (6 fields): foreign tax, liquidations, FATCA
7. **State Tax** (3 fields): state, state ID, state tax withheld

## Setup Instructions

### 1. Upload PDF to S3

```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

aws s3 cp 1099-DIV.pdf s3://tax-app-documents/templates/irs/1099-DIV.pdf --endpoint-url http://localhost:4566
```

### 2. Import Postman Collection

- Open Postman
- Import `postman_collection.json`
- Collection includes automatic JWT token management

### 3. Test Workflow

1. **Register**: User Registration → Successful Registration
2. **Login**: User Login → Successful Login (JWT auto-saved)
3. **Generate**: Tax Document Generation → Generate 1099-DIV - Complete Form

## Example API Request

```json
POST /Prod/generate
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
  "documentType": "1099-DIV",
  "formData": {
    "payerName": "Vanguard Investments",
    "payerTIN": "23-1945930",
    "recipientTIN": "123-45-6789",
    "recipientName": "John Doe",
    "totalOrdinaryDividends": 5000.00,
    "qualifiedDividends": 3000.00
  }
}
```

## Example API Response

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

## Validation Examples

### Valid Formats

- **TIN**: "23-1945930", "04-3232190"
- **SSN**: "123-45-6789", "987-65-4321"
- **ZIP**: "02101", "19355-1234"
- **Phone**: "800-662-7447", "617-555-0100"
- **State**: "MA", "CA", "NY", "DC", "PR"
- **Year**: "2025", "2024", "2023"

### Invalid Formats (Will Be Rejected)

- **TIN**: "123456789" (no dashes), "1-2345678" (wrong format)
- **SSN**: "12345678" (no dashes), "123456789" (too many digits)
- **ZIP**: "123" (too short), "ABCDE" (not numeric)
- **Phone**: "8006627447" (no dashes), "800.662.7447" (wrong separator)
- **State**: "XX" (invalid), "Massachusetts" (full name not allowed)
- **Year**: "25" (2 digits), "3000" (out of range)

## Breaking Changes

### Before (Old Validator)
```json
{
  "documentType": "1099",
  "formData": {
    "firstName": "John",
    "lastName": "Doe",
    "ssn": "123-45-6789",
    "income": 5000
  }
}
```

### After (New Validator)
```json
{
  "documentType": "1099-DIV",
  "formData": {
    "payerName": "Vanguard Investments",
    "payerTIN": "23-1945930",
    "recipientTIN": "123-45-6789",
    "recipientName": "John Doe",
    "totalOrdinaryDividends": 5000.00
  }
}
```

## Migration Notes

- The old generic `1099` document type still works with the old fields
- The new `1099-DIV` document type requires the new fields
- Both document types are supported simultaneously
- No changes needed to existing `1040` or `W2` document types

## Testing Checklist

- [ ] Upload 1099-DIV.pdf to S3
- [ ] Import updated Postman collection
- [ ] Test user registration
- [ ] Test user login (verify JWT token is saved)
- [ ] Test complete 1099-DIV form generation
- [ ] Test minimal 1099-DIV form (5 required fields only)
- [ ] Test validation errors (missing fields, invalid formats)
- [ ] Test authentication errors (invalid/missing JWT)
- [ ] Verify generated PDF in S3
- [ ] Verify job record in DynamoDB

## Next Steps

1. **Test the updated validator** with Postman
2. **Verify PDF generation** works with the new fields
3. **Update document generator** if needed to map fields to PDF form
4. **Add more document types** (1099-INT, 1099-MISC, etc.) using the same pattern
5. **Add field-level validation** (e.g., qualified dividends <= total dividends)
