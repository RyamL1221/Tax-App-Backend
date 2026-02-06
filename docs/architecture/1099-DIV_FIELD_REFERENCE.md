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
| payerState | - | | string | payer |
| payerCountry | - | | string | payer |
| payerZip | - | | string | payer |
| payerTelephoneNumber | - | | string | payer |
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
| state2 | 14 | | string | taxes |
| stateIdentificationNumber2 | 15 | | string | taxes |
| stateTaxWithheld2 | 16 | | decimal | taxes |
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
- **Multi-Copy:** This field appears on all four copies of the form (CopyA, Copy1, Copy2, CopyB) to ensure IRS compliance.
- **Field Flags:** The CopyA calendar year field has a READ-ONLY flag set in the PDF template, which is automatically cleared by the document generator before filling.
- **Rendering:** Calendar year fields are very small (28.8×10.0 points) and use a minimum font size of 5.0pt for proper rendering.

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
- **Example:** `"New York"`
- **Description:** The payer's city or town.
- **Note:** This field can be used separately (new format) or combined with state and ZIP in the old format ("City, State ZIP"). The system supports both formats for backward compatibility.

#### payerState
- **Required:** No
- **Data Type:** string (2 characters)
- **Validation:** Two-letter state code (e.g., "NY", "CA")
- **Example:** `"NY"`
- **Description:** The payer's state or province (two-letter abbreviation).

#### payerCountry
- **Required:** No
- **Data Type:** string (max 50 characters)
- **Example:** `"Canada"`
- **Description:** The payer's country if not USA.

#### payerZip
- **Required:** No
- **Data Type:** string (max 10 characters)
- **Validation:** Format XXXXX or XXXXX-XXXX
- **Example:** `"10001"` or `"10001-1234"`
- **Description:** The payer's ZIP or foreign postal code.

#### payerTelephoneNumber
- **Required:** No
- **Data Type:** string (max 20 characters)
- **Validation:** Phone number format (flexible)
- **Example:** `"(555) 123-4567"`
- **Description:** The payer's contact telephone number.

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

The 1099-DIV form supports reporting state tax information for up to **two states**. Use the first set of fields (state, stateIdentificationNumber, stateTaxWithheld) for the primary state, and the second set (state2, stateIdentificationNumber2, stateTaxWithheld2) for an additional state if applicable.

#### state (Box 14)
- **Required:** No
- **Data Type:** string (2 characters)
- **Validation:** Two-letter state code
- **Example:** `"NY"`
- **Description:** State abbreviation (first state).

#### stateIdentificationNumber (Box 15)
- **Required:** No
- **Data Type:** string (max 20 characters)
- **Example:** `"12-3456789"`
- **Description:** State identification number (first state).

#### stateTaxWithheld (Box 16)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"50.00"`
- **Description:** State tax withheld (first state).

#### state2 (Box 14, Row 2)
- **Required:** No
- **Data Type:** string (2 characters)
- **Validation:** Two-letter state code
- **Example:** `"CA"`
- **Description:** State abbreviation (second state). Use this field when reporting tax information for a second state.

#### stateIdentificationNumber2 (Box 15, Row 2)
- **Required:** No
- **Data Type:** string (max 20 characters)
- **Example:** `"98-7654321"`
- **Description:** State identification number (second state). Use this field when reporting tax information for a second state.

#### stateTaxWithheld2 (Box 16, Row 2)
- **Required:** No
- **Data Type:** decimal
- **Example:** `"25.00"`
- **Description:** State tax withheld (second state). Use this field when reporting tax information for a second state.

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
    "payerCity": "New York",
    "payerState": "NY",
    "payerZip": "10001",
    "payerTelephoneNumber": "(555) 123-4567",
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
    "stateIdentificationNumber": "12-3456789",
    "stateTaxWithheld": "50.00",
    "state2": "CA",
    "stateIdentificationNumber2": "98-7654321",
    "stateTaxWithheld2": "25.00",
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
- The form generates four copies automatically (CopyA for IRS, Copy1 for recipient, Copy2 for state, CopyB for payer)
- The calendar year field appears on all four copies to ensure IRS compliance
- Field names use camelCase convention for consistency
- Payer fields are prefixed with "payer"
- Recipient fields are prefixed with "recipient"

## Backward Compatibility

### Address Field Formats

The system supports both old and new address field formats for backward compatibility:

**Old Format (Combined):**
```json
{
  "payerCity": "New York, NY 10001"
}
```

**New Format (Separate):**
```json
{
  "payerCity": "New York",
  "payerState": "NY",
  "payerZip": "10001"
}
```

Both formats are accepted. When using the old combined format, the system will automatically parse the city, state, and ZIP components. However, the new separate format is recommended for clarity and validation.

**Deprecation Notice:** The combined address format is deprecated and will be removed in a future version. A deprecation warning will be logged when the old format is detected. Please migrate to the new separate format.

## Multi-State Tax Reporting

The 1099-DIV form supports reporting state tax information for up to **two states**. This is useful when dividends are subject to tax withholding in multiple states.

### Structure

- **First State:** Use `state`, `stateIdentificationNumber`, `stateTaxWithheld`
- **Second State:** Use `state2`, `stateIdentificationNumber2`, `stateTaxWithheld2`

### Example: Multi-State Reporting

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00",
    
    "state": "NY",
    "stateIdentificationNumber": "12-3456789",
    "stateTaxWithheld": "50.00",
    
    "state2": "CA",
    "stateIdentificationNumber2": "98-7654321",
    "stateTaxWithheld2": "25.00"
  }
}
```

### Important Notes

- The association between state name, state ID number, and tax withheld is maintained for each state
- If only one state is applicable, only use the first set of fields (without the "2" suffix)
- Both states are optional - you can omit state tax information entirely if not applicable
- Each state's fields should be provided together (state, ID, and tax withheld)


## PDF Field Flags and Rendering

### Field Flags

Some fields in the IRS 1099-DIV PDF template have special flags that affect how they can be modified:

#### READ-ONLY Flag

- **Affected Fields:** CopyA calendar year field (`topmostSubform[0].CopyA[0].CopyHeader[0].CalendarYear[0].f1_1[0]`)
- **Flag Value:** Bit 0 of the field_flags bitmask
- **Impact:** Prevents modification of the field value
- **Solution:** The document generator automatically detects and clears READ-ONLY flags before filling fields

#### HIDDEN Flag

- **Flag Value:** Bit 1 of the field_flags bitmask
- **Impact:** Makes the field invisible in PDF viewers
- **Solution:** The document generator automatically detects and clears HIDDEN flags if present

### Small Field Rendering

Some fields in the 1099-DIV form are very small and require special handling:

#### Calendar Year Fields

- **Dimensions:** 28.8×10.0 points (very small)
- **Font Size:** Minimum 5.0pt, maximum 7.0pt
- **Rendering Strategy:** Uses SmallField configuration with adaptive font sizing
- **Fallback:** If text doesn't fit at calculated size, reduces font size in 1pt increments (up to 3 attempts)

### Field Flag Handling Process

The document generator follows this process for all fields:

1. **Flag Detection:** Check field_flags bitmask for READ-ONLY and HIDDEN flags
2. **Flag Clearing:** Clear problematic flags using bitwise operations
3. **Widget Update:** Call widget.update() to apply flag changes
4. **Field Filling:** Proceed with normal field filling process
5. **Logging:** Log all flag operations for debugging

### Diagnostic Tools

For debugging field flag issues, use the inspection script:

```bash
python tax_document_generation/inspect_calendar_year_fields.py
```

This script provides:
- Field names and dimensions
- Field flag values and status
- READ-ONLY and HIDDEN flag detection
- Actionable diagnostic information

### Technical Details

#### Field Flag Bitmask

```python
# PyMuPDF field flag bit positions
FIELD_FLAG_READONLY = 1 << 0   # Bit 0: Read-only
FIELD_FLAG_HIDDEN = 1 << 1     # Bit 1: Hidden
FIELD_FLAG_REQUIRED = 1 << 2   # Bit 2: Required
FIELD_FLAG_NOEXPORT = 1 << 3   # Bit 3: No export
```

#### Clearing Flags

```python
# Clear READ-ONLY flag (bit 0)
widget.field_flags = widget.field_flags & ~(1 << 0)
widget.update()

# Clear HIDDEN flag (bit 1)
widget.field_flags = widget.field_flags & ~(1 << 1)
widget.update()
```

### Known Issues and Solutions

#### Issue: Calendar Year Not Visible

**Symptoms:**
- Calendar year field appears empty in generated PDF
- Field exists in PDF but has no visible value

**Root Cause:**
- CopyA calendar year field has READ-ONLY flag set
- Small field dimensions (28.8×10.0 points) require special font sizing

**Solution:**
- Document generator automatically clears READ-ONLY flag
- Uses SmallField configuration with 5.0pt minimum font size
- Applies adaptive font sizing with fallback

**Verification:**
```bash
# Generate test PDF
python tax_document_generation/generate_calendar_year_test_pdf.py

# Verify calendar year appears on all 4 copies
python tax_document_generation/verify_debug_pdf.py
```

## Related Documentation

- [Field Mapping Corrections](FIELD_MAPPING_CORRECTIONS.md) - History of field mapping fixes
- [Field Inspection Findings](FIELD_INSPECTION_FINDINGS.md) - Detailed field analysis
- [Migration Guide](MIGRATION_GUIDE_FIELD_STANDARDIZATION.md) - Field standardization migration
