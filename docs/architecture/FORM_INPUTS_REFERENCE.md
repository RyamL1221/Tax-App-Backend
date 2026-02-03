# Tax Document Generation - Form Inputs Reference

## Overview

The tax document generation API accepts form data that varies by document type. All requests follow this structure:

```json
{
  "documentType": "string",
  "formData": {
    // Fields vary by document type
  }
}
```

## Supported Document Types

The system currently supports three document types:
- `1099` - Form 1099 (various types including DIV, INT, MISC, etc.)
- `1040` - Individual Income Tax Return
- `W2` - Wage and Tax Statement

## Form Fields by Document Type

### 1099 Forms

**Document Type**: `1099`

**Required Fields**:
```json
{
  "documentType": "1099",
  "formData": {
    "firstName": "string",      // Non-empty string
    "lastName": "string",       // Non-empty string
    "ssn": "string",           // Format: XXX-XX-XXXX
    "income": number           // Non-negative number (int or float)
  }
}
```

**Example**:
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

**Validation Rules**:
- `firstName`: Must be non-empty after trimming whitespace
- `lastName`: Must be non-empty after trimming whitespace
- `ssn`: Must match pattern `\d{3}-\d{2}-\d{4}` (e.g., "123-45-6789")
- `income`: Must be >= 0, can be integer or float

---

### 1040 Forms

**Document Type**: `1040`

**Required Fields**:
```json
{
  "documentType": "1040",
  "formData": {
    "firstName": "string",      // Non-empty string
    "lastName": "string",       // Non-empty string
    "ssn": "string",           // Format: XXX-XX-XXXX
    "filingStatus": "string",  // One of the valid statuses
    "income": number           // Non-negative number (int or float)
  }
}
```

**Valid Filing Statuses**:
- `single`
- `married_filing_jointly`
- `married_filing_separately`
- `head_of_household`
- `qualifying_widow`

**Example**:
```json
{
  "documentType": "1040",
  "formData": {
    "firstName": "Jane",
    "lastName": "Smith",
    "ssn": "987-65-4321",
    "filingStatus": "married_filing_jointly",
    "income": 125000
  }
}
```

**Validation Rules**:
- `firstName`: Must be non-empty after trimming whitespace
- `lastName`: Must be non-empty after trimming whitespace
- `ssn`: Must match pattern `\d{3}-\d{2}-\d{4}` (e.g., "987-65-4321")
- `filingStatus`: Must be one of the valid filing statuses listed above
- `income`: Must be >= 0, can be integer or float

---

### W2 Forms

**Document Type**: `W2`

**Required Fields**:
```json
{
  "documentType": "W2",
  "formData": {
    "firstName": "string",      // Non-empty string
    "lastName": "string",       // Non-empty string
    "ssn": "string",           // Format: XXX-XX-XXXX
    "income": number           // Non-negative number (int or float)
  }
}
```

**Example**:
```json
{
  "documentType": "W2",
  "formData": {
    "firstName": "Bob",
    "lastName": "Johnson",
    "ssn": "555-66-7777",
    "income": 75000
  }
}
```

**Validation Rules**:
- `firstName`: Must be non-empty after trimming whitespace
- `lastName`: Must be non-empty after trimming whitespace
- `ssn`: Must match pattern `\d{3}-\d{2}-\d{4}` (e.g., "555-66-7777")
- `income`: Must be >= 0, can be integer or float

---

## Common Validation Rules

### SSN Format
- **Pattern**: `XXX-XX-XXXX` where X is a digit
- **Valid**: "123-45-6789", "987-65-4321"
- **Invalid**: "12345678", "123456789", "123-456-789"

### Name Fields (firstName, lastName)
- Must be strings
- Cannot be empty or only whitespace
- Whitespace is trimmed before validation

### Income Field
- Must be a number (integer or float)
- Must be non-negative (>= 0)
- Can be 0
- Examples: 0, 100, 5000.50, 125000

## Error Responses

### Missing Required Field
```json
{
  "error": "ValidationError",
  "message": "Missing required field: ssn"
}
```

### Invalid Field Type
```json
{
  "error": "ValidationError",
  "message": "Field 'income' must be of type int or float"
}
```

### Invalid SSN Format
```json
{
  "error": "ValidationError",
  "message": "SSN must be in format XXX-XX-XXXX"
}
```

### Invalid Filing Status
```json
{
  "error": "ValidationError",
  "message": "Filing status must be one of: single, married_filing_jointly, married_filing_separately, head_of_household, qualifying_widow"
}
```

### Negative Income
```json
{
  "error": "ValidationError",
  "message": "Income must be a non-negative number"
}
```

### Empty Name Field
```json
{
  "error": "ValidationError",
  "message": "Field 'firstName' must be a non-empty string"
}
```

## Important Notes

### Document Type vs PDF Filename

The `documentType` in your API request must match the PDF filename in S3:

- API Request: `"documentType": "1099"`
- S3 Path: `s3://tax-app-documents/templates/irs/1099.pdf`

If you have a PDF named `1099-DIV.pdf`, you need to either:
1. Rename it to `1099.pdf` when uploading to S3, OR
2. Use `"documentType": "1099-DIV"` in your API request (but this requires updating the validator)

### Generic Field Names

The current implementation uses generic field names like `income` for all document types. This means:

- For 1099-DIV: Use `income` (not `dividends` or `qualifiedDividends`)
- For 1099-INT: Use `income` (not `interest`)
- For 1099-MISC: Use `income` (not `miscellaneous`)

The actual PDF template determines how the `income` value is displayed on the form.

### Optional Fields

Currently, all fields listed above are **required**. The system does not support optional fields yet. If you need to add optional fields (like spouse information for married filing jointly), you would need to update the validator.

## Testing Tips

1. **Start with valid data**: Use the examples provided above
2. **Test one validation at a time**: Change one field to test specific validation rules
3. **Check error messages**: They tell you exactly what's wrong
4. **Verify SSN format**: Most common mistake is forgetting the dashes
5. **Use realistic values**: While the system accepts any non-negative number for income, use realistic values for testing

## Quick Reference Table

| Document Type | firstName | lastName | ssn | filingStatus | income |
|---------------|-----------|----------|-----|--------------|--------|
| 1099 | ✓ Required | ✓ Required | ✓ Required | ✗ Not used | ✓ Required |
| 1040 | ✓ Required | ✓ Required | ✓ Required | ✓ Required | ✓ Required |
| W2 | ✓ Required | ✓ Required | ✓ Required | ✗ Not used | ✓ Required |

Legend:
- ✓ Required: Field must be present and valid
- ✗ Not used: Field is not used for this document type
