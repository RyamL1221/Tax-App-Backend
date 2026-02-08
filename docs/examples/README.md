# API Request Examples

This directory contains example JSON payloads for the Tax Document Generation API.

## Available Examples

### Standard Format Examples

These examples use the traditional format with pre-formatted values:

- **1099-DIV-minimal-example.json**: Minimal required fields only
  - Decimal values: Pre-formatted with two decimal places (e.g., `1000.00`)
  - TINs: Pre-formatted with hyphens (e.g., `"12-3456789"`, `"123-45-6789"`)

- **1099-DIV-typical-example.json**: Common use case with typical fields
  - Includes payer/recipient addresses
  - Includes common optional fields
  - All values pre-formatted

- **1099-DIV-complete-example.json**: All available fields
  - Demonstrates all optional fields
  - Includes checkboxes (voided, corrected, FATCA, secondTinNotification)
  - All values pre-formatted

### Flexible Format Example

- **1099-DIV-flexible-format-example.json**: Demonstrates flexible input formatting
  - Decimal values: Can be integers, floats, or strings (e.g., `1000`, `"800.5"`, `"150"`)
  - TINs: Can be with or without hyphens (e.g., `"123456789"` or `"12-3456789"`)
  - System automatically normalizes to required format

## Flexible Input Formatting

As of the flexible input formatting feature, the API accepts multiple formats for decimal and TIN fields:

### Decimal/Currency Fields

All 16 decimal fields support flexible formatting:

**Accepted Formats:**
- Integer: `1000` → Normalized to `"1000.00"`
- Float: `1000.5` → Normalized to `"1000.50"`
- String (no decimals): `"1000"` → Normalized to `"1000.00"`
- String (one decimal): `"1000.5"` → Normalized to `"1000.50"`
- String (two decimals): `"1000.00"` → Unchanged
- String (excess decimals): `"1000.123"` → Rounded to `"1000.12"`

**Decimal Fields:**
1. `totalOrdinaryDividends` (required)
2. `qualifiedDividends`
3. `totalCapitalGainDistributions`
4. `unrecapturedSection1250Gain`
5. `section1202Gain`
6. `collectibles28Gain`
7. `section897OrdinaryDividends`
8. `section897CapitalGain`
9. `nondividendDistributions`
10. `federalIncomeTaxWithheld`
11. `section199ADividends`
12. `investmentExpenses`
13. `foreignTaxPaid`
14. `cashLiquidationDistributions`
15. `noncashLiquidationDistributions`
16. `exemptInterestDividends`
17. `specifiedPrivateActivityBondInterest`
18. `stateTaxWithheld`
19. `stateTaxWithheld2`

### TIN Fields

Both TIN fields support flexible formatting:

**Payer TIN (EIN format):**
- Without hyphens: `"123456789"` → Normalized to `"12-3456789"`
- With hyphens: `"12-3456789"` → Unchanged

**Recipient TIN (SSN or EIN format):**
- Without hyphens (SSN): `"987654321"` → Normalized to `"987-65-4321"`
- With hyphens (SSN): `"987-65-4321"` → Unchanged
- With hyphens (EIN): `"12-3456789"` → Unchanged

## Backward Compatibility

All existing payloads continue to work without modification. The normalization layer operates transparently:

- Pre-formatted values (e.g., `"1000.00"`, `"12-3456789"`) are accepted and used as-is
- Flexible formats (e.g., `1000`, `"123456789"`) are automatically normalized
- No changes to JSON schema or field names
- No breaking changes to API contract

## Usage

### cURL Example (Flexible Format)

```bash
curl -X POST https://api.example.com/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d @docs/examples/1099-DIV-flexible-format-example.json
```

### cURL Example (Standard Format)

```bash
curl -X POST https://api.example.com/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d @docs/examples/1099-DIV-typical-example.json
```

## Normalization Logging

When flexible formats are used, the system logs normalization changes:

```json
{
  "level": "INFO",
  "message": "Normalized 3 fields for job abc-123",
  "context": {}
}
{
  "level": "INFO",
  "message": "  totalOrdinaryDividends: 1000 -> 1000.00",
  "context": {}
}
{
  "level": "INFO",
  "message": "  payerTIN: ***-**-6789 -> ***-**-6789",
  "context": {}
}
```

Note: Sensitive data (TINs) are masked in logs, showing only the last 4 digits.

## Field Reference

For complete field documentation, see:
- [1099-DIV Field Reference](../architecture/1099-DIV_FIELD_REFERENCE.md)
- [API Documentation](../development/FRONTEND_API_DOCUMENTATION.md)
