# Form 1099-DIV Field Reference

## Overview

This document describes all fields supported by the 1099-DIV tax document generation API.

## Required Fields

These fields MUST be present in every 1099-DIV request:

| Field Name | Type | Format | Description | Example |
|------------|------|--------|-------------|---------|
| `payerName` | string | Non-empty | Name of the payer (investment company) | "Vanguard Investments" |
| `payerTIN` | string | XX-XXXXXXX | Payer's Tax Identification Number (EIN) | "23-1945930" |
| `recipientTIN` | string | XXX-XX-XXXX | Recipient's Tax Identification Number (SSN) | "123-45-6789" |
| `recipientName` | string | Non-empty | Name of the recipient (taxpayer) | "John Doe" |
| `totalOrdinaryDividends` | number | >= 0 | Box 1a: Total ordinary dividends | 5000.00 |

## Optional Payer Information Fields

| Field Name | Type | Format | Description | Example |
|------------|------|--------|-------------|---------|
| `payerStreetAddress` | string | Any | Payer's street address | "100 Vanguard Blvd" |
| `payerCity` | string | Any | Payer's city | "Malvern" |
| `payerState` | string | 2-letter code | Payer's state (US state/territory) | "PA" |
| `payerCountry` | string | Any | Payer's country | "USA" |
| `payerZip` | string | XXXXX or XXXXX-XXXX | Payer's ZIP code | "19355" or "19355-1234" |
| `payerPhone` | string | XXX-XXX-XXXX | Payer's phone number | "800-662-7447" |

## Optional Recipient Information Fields

| Field Name | Type | Format | Description | Example |
|------------|------|--------|-------------|---------|
| `recipientStreetAddress` | string | Any | Recipient's street address | "456 Main St, Apt 2B" |
| `recipientCity` | string | Any | Recipient's city | "Boston" |
| `recipientState` | string | 2-letter code | Recipient's state (US state/territory) | "MA" |
| `recipientCountry` | string | Any | Recipient's country | "USA" |
| `recipientZip` | string | XXXXX or XXXXX-XXXX | Recipient's ZIP code | "02101" |

## Optional Account and Year Fields

| Field Name | Type | Format | Description | Example |
|------------|------|--------|-------------|---------|
| `accountNumber` | string | Any | Account number | "12345678" |
| `calendarYear` | string | YYYY | Tax year (1900-2100) | "2025" |

## Optional Dividend Fields (Box 1-2)

| Field Name | Type | Format | Description | Example |
|------------|------|--------|-------------|---------|
| `qualifiedDividends` | number | >= 0 | Box 1b: Qualified dividends | 3000.00 |
| `totalCapitalGainDistributions` | number | >= 0 | Box 2a: Total capital gain distributions | 1500.00 |
| `unrecapturedSection1250Gain` | number | >= 0 | Box 2b: Unrecaptured Section 1250 gain | 0 |
| `section1202Gain` | number | >= 0 | Box 2c: Section 1202 gain | 0 |
| `collectibles28Gain` | number | >= 0 | Box 2d: Collectibles (28%) gain | 0 |
| `section897OrdinaryDividends` | number | >= 0 | Box 2e: Section 897 ordinary dividends | 0 |
| `section897CapitalGain` | number | >= 0 | Box 2f: Section 897 capital gain | 0 |

## Optional Distribution and Tax Fields (Box 3-7)

| Field Name | Type | Format | Description | Example |
|------------|------|--------|-------------|---------|
| `nondividendDistributions` | number | >= 0 | Box 3: Nondividend distributions | 0 |
| `federalIncomeTaxWithheld` | number | >= 0 | Box 4: Federal income tax withheld | 500.00 |
| `section199ADividends` | number | >= 0 | Box 5: Section 199A dividends | 2000.00 |
| `investmentExpenses` | number | >= 0 | Box 6: Investment expenses | 50.00 |
| `foreignTaxPaid` | number | >= 0 | Box 7: Foreign tax paid | 0 |

## Optional Foreign and Liquidation Fields (Box 8-13)

| Field Name | Type | Format | Description | Example |
|------------|------|--------|-------------|---------|
| `foreignCountry` | string | Any | Box 8: Foreign country or U.S. possession | "Canada" |
| `cashLiquidationDistributions` | number | >= 0 | Box 9: Cash liquidation distributions | 0 |
| `noncashLiquidationDistributions` | number | >= 0 | Box 10: Noncash liquidation distributions | 0 |
| `fatcaFilingRequirement` | boolean | true/false | Box 11: FATCA filing requirement | false |
| `exemptInterestDividends` | number | >= 0 | Box 12: Exempt-interest dividends | 0 |
| `specifiedPrivateActivityBondInterest` | number | >= 0 | Box 13: Specified private activity bond interest dividends | 0 |

## Optional State Tax Fields (Box 14-16)

| Field Name | Type | Format | Description | Example |
|------------|------|--------|-------------|---------|
| `state` | string | 2-letter code | Box 14: State | "MA" |
| `stateIdentificationNumber` | string | Any | Box 15: State identification number | "123456789" |
| `stateTaxWithheld` | number | >= 0 | Box 16: State tax withheld | 250.00 |

## Complete Example

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
    "unrecapturedSection1250Gain": 0,
    "section1202Gain": 0,
    "collectibles28Gain": 0,
    "section897OrdinaryDividends": 0,
    "section897CapitalGain": 0,
    "nondividendDistributions": 0,
    "federalIncomeTaxWithheld": 500.00,
    "section199ADividends": 2000.00,
    "investmentExpenses": 50.00,
    "foreignTaxPaid": 0,
    "foreignCountry": "",
    "cashLiquidationDistributions": 0,
    "noncashLiquidationDistributions": 0,
    "fatcaFilingRequirement": false,
    "exemptInterestDividends": 0,
    "specifiedPrivateActivityBondInterest": 0,
    "state": "MA",
    "stateIdentificationNumber": "123456789",
    "stateTaxWithheld": 250.00
  }
}
```

## Minimal Example

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "payerName": "Fidelity Investments",
    "payerTIN": "04-3232190",
    "recipientTIN": "987-65-4321",
    "recipientName": "Jane Smith",
    "totalOrdinaryDividends": 1250.50
  }
}
```

## Validation Rules

### Format Validations

- **TIN (payerTIN)**: Must match pattern `XX-XXXXXXX` (e.g., "23-1945930")
- **SSN (recipientTIN)**: Must match pattern `XXX-XX-XXXX` (e.g., "123-45-6789")
- **ZIP Code**: Must match pattern `XXXXX` or `XXXXX-XXXX` (e.g., "02101" or "02101-1234")
- **Phone**: Must match pattern `XXX-XXX-XXXX` (e.g., "800-662-7447")
- **State**: Must be a valid 2-letter US state/territory code (e.g., "MA", "CA", "NY")
- **Year**: Must be a 4-digit year between 1900 and 2100 (e.g., "2025")

### Value Validations

- **All monetary amounts**: Must be non-negative numbers (>= 0)
- **Name fields**: Must be non-empty strings after trimming whitespace
- **Boolean fields**: Must be `true` or `false`

### Common Validation Errors

```json
// Missing required field
{
  "error": "ValidationError",
  "message": "Missing required field: payerName"
}

// Invalid TIN format
{
  "error": "ValidationError",
  "message": "TIN must be in format XX-XXXXXXX"
}

// Invalid SSN format
{
  "error": "ValidationError",
  "message": "SSN must be in format XXX-XX-XXXX"
}

// Negative amount
{
  "error": "ValidationError",
  "message": "Field 'totalOrdinaryDividends' must be a non-negative number"
}

// Invalid state code
{
  "error": "ValidationError",
  "message": "State must be a valid US state/territory code"
}
```

## Valid US State/Territory Codes

AL, AK, AZ, AR, CA, CO, CT, DE, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NY, NC, ND, OH, OK, OR, PA, RI, SC, SD, TN, TX, UT, VT, VA, WA, WV, WI, WY, DC, PR, VI, GU, AS, MP

## Tips for Testing

1. **Start with minimal fields**: Test with only the 5 required fields first
2. **Add fields incrementally**: Add optional fields one at a time to test validation
3. **Test format validations**: Try invalid formats for TIN, SSN, ZIP, phone, etc.
4. **Test negative amounts**: Verify that negative numbers are rejected
5. **Test empty strings**: Verify that empty name fields are rejected
6. **Test invalid state codes**: Try "XX" or "ZZ" to test state validation
