# 1099-DIV Field Reference

## Overview

This document provides a comprehensive reference for all fields in the IRS Form 1099-DIV API. Use this guide to understand which fields are required, their data types, validation rules, and example values.

## Quick Reference Table

| API Field Name | IRS Box | Required | Data Type | Section |
|---------------|---------|----------|-----------|---------|
| calendarYear | - | ✓ | string | metadata |
| payerName | - | ✓ | string | payer |
| payerTIN | - | ✓ | string | payer |
| payerStreetAddress | - | | string | payer |
| payerCity | - | | string | payer |
| payerCountry | - | | string | payer |
| payerPhone | - | | string | payer |
| recipientName | - | ✓ | string | recipient |
| recipientTIN | - | ✓ | string | recipient |
| recipientStreetAddress | - | | string | recipient |
| recipientCity | - | | string | recipient |
| recipientState | - | | string | recipient |
| recipientZip | - | | string | recipient |
| recipientCountry | - | | string | recipient |
| totalOrdinaryDividends | 1a | ✓ | decimal | dividends |
| qualifiedDividends | 1b | | decimal | dividends |
| totalCapitalGainDistributions | 2a | | decimal | capital_gains |
| unrecapturedSection1250Gain | 2b | | decimal | capital_gains |
| section1202Gain | 2c | | decimal | capital_gains |
| collectibles28Gain | 2d | | decimal | capital_gains |
| section897OrdinaryDividends | 2e | | decimal | capital_gains |
| section897CapitalGain | 2f | | decimal | capital_gains |
| nondividendDistributions | 3 | | decimal | distributions |
| federalIncomeTaxWithheld | 4 | | decimal | taxes |
| section199ADividends | 5 | | decimal | other |
| investmentExpenses | 6 | | decimal | other |
| foreignTaxPaid | 7 | | decimal | taxes |
| foreignCountry | 8 | | string | other |
| cashLiquidationDistributions | 9 | | decimal | distributions |
| noncashLiquidationDistributions | 10 | | decimal | distributions |
| fatcaFilingRequirement | 11 | | boolean | other |
| exemptInterestDividends | 12 | | decimal | other |
| specifiedPrivateActivityBondInterest | 13 | | decimal | other |
| state | 14 | | string | taxes |
| stateIdentificationNumber | 15 | | string | taxes |
| stateTaxWithheld | 16 | | decimal | taxes |
| accountNumber | - | | string | account |

## Required Fields

The following fields MUST be present in all 1099-DIV form submissions:

1. **calendarYear** - Tax year for the form
2. **payerName** - Name of the payer
3. **payerTIN** - Payer's Tax Identification Number
4. **recipientName** - Name of the recipient
5. **recipientTIN** - Recipient's Tax Identification Number
6. **totalOrdinaryDividends** - Total ordinary dividends (Box 1a)

## Optional Fields

All other fields are optional and may be omitted if not applicable.

## Field Descriptions

### Metadata Fields

#### calendarYear
- **Required:** Yes
- **Data Type:** string (4 digits)
- **Validation:** Must be a 4-digit year (e.g., "2024")
- **Example:** `"2024"`
- **Description:** The tax year for which this form is being filed.

### Payer Information

#### payerName
- **Required:** Yes
- **Data Type:** string (max 100 characters)
- **Example:** `"Example Corporation"`
- **Description:** The legal name of the company or individual making the dividend payments.

#### payerTIN
- **Required:** Yes
- **Data Type:** string (EIN format)
- **Validation:** Format XX-XXXXXXX (9 digits with optional hyphen)
- **Example:** `"12-3456789"`
- **Description:** The payer's Employer Identification Number (EIN) or Social Security Number (SSN).

#### payerStreetAddress
- **Required:** No
- **Data Type:** string (max 100 characters)
- **Example:** `"123 Main Street"`
- **Description:** The payer's street address.

#### payerCity
- **Required:** No
- **Data Type:** string (max 100 characters)
- **Example:** `"New York, NY 10001"`
- **Description:** The payer's city, state, and ZIP code (combined field).

#### payerCountry
- **Required:** No
- **Data Type:** string (max 50 characters)
- **Example:** `"Canada"`
- **Description:** The payer's country if not USA.

#### payerPhone
- **Required:** No
- **Data Type:** string (max 20 characters)
- **Validation:** Phone number format (flexible)
- **Example:** `"(555) 123-4567"`
- **Description:** The payer's contact phone number.

### Recipient Information

#### recipientName
- **Required:** Yes
- **Data Type:** string (max 100 characters)
- **Example:** `"John Doe"`
- **Description:** The legal name of the taxpayer receiving the dividends.

#### recipientTIN
- **Required:** Yes
- **Data Type:** string (SSN format)
- **Validation:** Format XXX-XX-XXXX (9 digits with optional hyphens)
- **Example:** `"123-45-6789"`
- **Description:** The recipient's Social Security Number (SSN) or Employer Identification Number (EIN).

#### recipientStreetAddress
- **Required:** No
- **Data Type:** string (max 100 characters)
- **Example:** `"456 Oak Avenue"`
- **Description:** The recipient's street address.

#### recipientCity
- **Required:** No
- **Data Type:** string (max 50 characters)
- **Example:** `"Los Angeles"`
- **Description:** The recipient's city.

#### recipientState
- **Required:** No
- **Data Type:** string (2 characters)
- **Validation:** Two-letter state code
- **Example:** `"CA"`
- **Description:** The recipient's state (two-letter abbreviation).

#### recipientZip
- **Required:** No
- **Data Type:** string (5 or 9 digits)
- **Validation:** Format XXXXX or XXXXX-XXXX
- **Example:** `"90001"`
- **Description:** The recipient's ZIP code.

#### recipientCountry
- **Required:** No
- **Data Type:** string (max 50 characters)
- **Example:** `"Mexico"`
- **Description:** The recipient's country if not USA.

### Box 1: Dividends

#### totalOrdinaryDividends (Box 1a)
- **Required:** Yes
- **Data Type:** decimal
- **Validation:** Numeric value with up to 2 decimal places
- **Example:** `"1000.00"`
- **Description:** Total ordinary dividends paid to the recipient.

#### qualifiedDividends (Box 1b)
- **Required:** No
- **Data Type:** decimal
- **Validation:** Numeric value with up to 2 decimal places
- **Example:** `"800.00"`
- **Description:** Qualified dividends (subset of Box 1a) eligible for lower tax rates.

### Box 2: Capital Gains

#### totalCapitalGainDistributions (Box 2a)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"500.00"`
- **Description:** Total capital gain distributions.

#### unrecapturedSection1250Gain (Box 2b)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"100.00"`
- **Description:** Unrecaptured Section 1250 gain.

#### section1202Gain (Box 2c)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"50.00"`
- **Description:** Section 1202 gain.

#### collectibles28Gain (Box 2d)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"25.00"`
- **Description:** Collectibles (28%) gain.

#### section897OrdinaryDividends (Box 2e)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"75.00"`
- **Description:** Section 897 ordinary dividends.

#### section897CapitalGain (Box 2f)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"60.00"`
- **Description:** Section 897 capital gain.

### Box 3-7: Distributions and Taxes

#### nondividendDistributions (Box 3)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"200.00"`
- **Description:** Nondividend distributions (return of capital).

#### federalIncomeTaxWithheld (Box 4)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"150.00"`
- **Description:** Federal income tax withheld.

#### section199ADividends (Box 5)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"300.00"`
- **Description:** Section 199A dividends.

#### investmentExpenses (Box 6)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"50.00"`
- **Description:** Investment expenses.

#### foreignTaxPaid (Box 7)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"75.00"`
- **Description:** Foreign tax paid.

### Box 8-13: Foreign and Liquidation

#### foreignCountry (Box 8)
- **Required:** No
- **Data Type:** string (max 50 characters)
- **Example:** `"United Kingdom"`
- **Description:** Foreign country or U.S. possession.

#### cashLiquidationDistributions (Box 9)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"1000.00"`
- **Description:** Cash liquidation distributions.

#### noncashLiquidationDistributions (Box 10)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"500.00"`
- **Description:** Noncash liquidation distributions.

#### fatcaFilingRequirement (Box 11)
- **Required:** No
- **Data Type:** boolean
- **Example:** `true`
- **Description:** FATCA filing requirement checkbox.

#### exemptInterestDividends (Box 12)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"250.00"`
- **Description:** Exempt-interest dividends.

#### specifiedPrivateActivityBondInterest (Box 13)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"100.00"`
- **Description:** Specified private activity bond interest dividends.

### Box 14-16: State Tax

#### state (Box 14)
- **Required:** No
- **Data Type:** string (2 characters)
- **Validation:** Two-letter state code
- **Example:** `"NY"`
- **Description:** State abbreviation.

#### stateIdentificationNumber (Box 15)
- **Required:** No
- **Data Type:** string (max 20 characters)
- **Example:** `"12-3456789"`
- **Description:** State identification number.

#### stateTaxWithheld (Box 16)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"50.00"`
- **Description:** State tax withheld.

### Account Information

#### accountNumber
- **Required:** No
- **Data Type:** string (max 20 characters)
- **Example:** `"1234567890"`
- **Description:** Optional account number for the recipient.

## Example API Requests

### Minimal Request (Required Fields Only)

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
  }
}
```

### Complete Request (With Optional Fields)

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "payerStreetAddress": "123 Main Street",
    "payerCity": "New York, NY 10001",
    "payerPhone": "(555) 123-4567",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "recipientStreetAddress": "456 Oak Avenue",
    "recipientCity": "Los Angeles",
    "recipientState": "CA",
    "recipientZip": "90001",
    "totalOrdinaryDividends": "1000.00",
    "qualifiedDividends": "800.00",
    "totalCapitalGainDistributions": "500.00",
    "federalIncomeTaxWithheld": "150.00",
    "section199ADividends": "300.00",
    "foreignTaxPaid": "75.00",
    "foreignCountry": "United Kingdom",
    "state": "NY",
    "stateTaxWithheld": "50.00",
    "accountNumber": "1234567890"
  }
}
```

## Validation Rules

### String Fields
- Must not exceed maximum length
- Special characters are allowed unless otherwise specified
- Empty strings are not allowed for required fields

### Decimal Fields
- Must be numeric values
- Up to 2 decimal places recommended
- Negative values are not allowed
- Format: `"1000.00"` (as string in JSON)

### Boolean Fields
- Accepted values: `true`, `false`
- Used for checkbox fields (e.g., FATCA filing requirement)

### TIN Fields
- Payer TIN: EIN format (XX-XXXXXXX)
- Recipient TIN: SSN format (XXX-XX-XXXX)
- Hyphens are optional but recommended

### State Codes
- Must be valid two-letter U.S. state abbreviations
- Uppercase letters only

## Notes

- All monetary values should be provided as strings with 2 decimal places
- The form generates three copies automatically (Copy A, Copy B, Copy C)
- Field names use camelCase convention for consistency
- Payer fields are prefixed with "payer"
- Recipient fields are prefixed with "recipient"
