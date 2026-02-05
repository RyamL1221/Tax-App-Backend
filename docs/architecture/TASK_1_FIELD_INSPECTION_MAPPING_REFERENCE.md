# Task 1: PDF Field Inspection and Mapping Reference

## Overview

This document provides the results of the PDF field inspection for the 1099-DIV template, identifying all available fields and documenting the exact PDF field names needed for the comprehensive schema update.

**Date**: Generated during Task 1 execution  
**PDF Template**: `samples/1099-DIV.pdf`  
**Inspection Tool**: `tax_document_generation/inspect_pdf_fields.py`

## Inspection Summary

- **Total Fields Found**: 140 fields
- **Total Pages**: 4 pages
- **Form Copies**: Base (CopyA), Copy1, Copy2, CopyB
- **Field Distribution**:
  - Base (CopyA): 36 fields
  - Copy1: 35 fields
  - Copy2: 35 fields
  - CopyB: 34 fields

## Current vs. Comprehensive Mapping

### Currently Mapped Fields (25 fields)

The current `canonical_div_1099.py` includes:

1. **Calendar Year**: calendarYear
2. **Payer Information** (4 fields): payerName, payerStreetAddress, payerCity, payerTIN
3. **Recipient Information** (3 fields): recipientName, recipientStreetAddress, recipientTIN
4. **Dividend Fields** (13 fields): Boxes 1a-13
5. **State Tax** (3 fields): state, stateIdentificationNumber, stateTaxWithheld (first state only)
6. **Account Number**: accountNumber

### New Fields to Add (15+ fields)

Based on the requirements and PDF inspection, the following fields need to be added:

#### 1. Payer Address Components (NOT FOUND - Combined Field)

**Analysis**: The PDF inspection reveals that the payer address is stored in a **single combined field** `f2_2[0]` (76pt height), not separate fields for street, city, state, zip, etc.

- **Current Field**: `f2_2[0]` - Large text field (242.1 x 76.0 pt) for complete payer address
- **Nearby Text**: "PAYER'S name, street address, city or town, state or province, country, ZIP or foreign postal code"

**Conclusion**: The payer address components (payerState, payerCountry, payerZip, payerTelephoneNumber) **cannot be mapped to separate PDF fields** because they don't exist as separate fields in the PDF template. The PDF uses a single multi-line text field for the entire payer address block.

#### 2. Recipient Address Components (NOT FOUND - Combined Fields)

**Analysis**: Similar to payer address, the recipient address uses **three combined fields**:

- **f2_5[0]**: Recipient name (26pt height)
- **f2_6[0]**: Street address including apt. no. (26pt height)
- **f2_7[0]**: City, state, ZIP combined (26pt height)

**Nearby Text for f2_7**: "City or town, state or province, country, and ZIP or foreign postal code"

**Conclusion**: The recipient address components (recipientCity, recipientState, recipientCountry, recipientZip) **cannot be mapped to separate PDF fields**. The PDF uses combined fields where city, state, and ZIP are entered together in field `f2_7[0]`.

#### 3. Second State Tax Fields (FOUND - Available)

**Analysis**: The PDF has TWO rows for state tax information in Boxes 14-16:

**First State (Row 1)** - Already mapped:
- Box 14 (State): `f2_27[0]` - 36.0 x 14.0 pt
- Box 15 (State ID): `f2_28[0]` - 36.0 x 12.0 pt  
- Box 16 (Tax Withheld): `f2_29[0]` - 64.8 x 14.0 pt
- Box 16 (continued): `f2_30[0]` - 64.8 x 12.0 pt

**Second State (Row 2)** - NEW FIELDS TO MAP:
- Box 14 (State 2): `f2_31[0]` - 89.8 x 12.0 pt
- Box 16 (Tax Withheld 2): `f2_32[0]` - 89.8 x 12.0 pt

**Note**: There appears to be NO separate field for State ID Number (Box 15) for the second state. The PDF structure shows:
- `f2_31[0]`: Positioned at (406.0, 336.0) - likely for state tax withheld amount
- `f2_32[0]`: Positioned at (406.0, 348.0) - likely for additional state info

## Detailed Field Analysis

### LeftCol Fields (Payer and Recipient Information)

#### Copy1 LeftCol Structure:

| Field Name | Position | Dimensions | Purpose | Notes |
|------------|----------|------------|---------|-------|
| `f2_2[0]` | (52.4, 56.0) | 242.1 x 76.0 | Payer name, street, city, state, ZIP | **Combined multi-line field** |
| `f2_3[0]` | (50.4, 142.0) | 122.4 x 38.0 | Payer TIN | Already mapped |
| `f2_4[0]` | (172.8, 142.0) | 122.4 x 38.0 | Recipient TIN | Already mapped |
| `f2_5[0]` | (52.4, 190.0) | 242.1 x 26.0 | Recipient name | Already mapped |
| `f2_6[0]` | (52.4, 226.0) | 242.1 x 26.0 | Recipient street address | Already mapped |
| `f2_7[0]` | (52.4, 262.0) | 242.1 x 26.0 | Recipient city, state, ZIP | **Combined field** |
| `f2_8[0]` | (50.4, 334.0) | 244.8 x 26.0 | Account number | Already mapped |

**Key Finding**: The PDF template does NOT have separate fields for:
- Payer state, country, ZIP, telephone
- Recipient city, state, country, ZIP

These are all combined into larger multi-line text fields.

### RghtCol Fields (Boxes 14-16 State Tax)

#### Current Mapping (First State):

```python
"state": "topmostSubform[0].Copy1[0].RghtCol[0].Box14_ReadOrder[0].f2_27[0]",
"stateIdentificationNumber": "topmostSubform[0].Copy1[0].RghtCol[0].Box14_ReadOrder[0].f2_28[0]",
"stateTaxWithheld": "topmostSubform[0].Copy1[0].RghtCol[0].Box15_ReadOrder[0].f2_29[0]",
```

**Issue**: The current mapping has an inconsistency:
- `stateIdentificationNumber` is mapped to `Box14_ReadOrder[0].f2_28[0]` (should be Box15)
- `stateTaxWithheld` is mapped to `Box15_ReadOrder[0].f2_29[0]` (should be Box16)

#### Proposed Mapping (Second State):

Based on the field positions and nearby text analysis:

```python
# Second state fields (Row 2 of Boxes 14-16)
"state2": "topmostSubform[0].Copy1[0].RghtCol[0].Box14_ReadOrder[0].f2_28[0]",  # Second row, Box 14
"stateTaxWithheld2": "topmostSubform[0].Copy1[0].RghtCol[0].Box15_ReadOrder[0].f2_30[0]",  # Second row, Box 16
```

**Note**: There does NOT appear to be a separate field for `stateIdentificationNumber2`. The PDF may only support state ID for the first state.

## Field Name Patterns

### XFA Path Structure

All fields follow this pattern:
```
topmostSubform[0].<CopyName>[0].<Section>[0].<OptionalGroup>[0].<FieldID>[0]
```

Where:
- **CopyName**: `CopyA`, `Copy1`, `Copy2`, `CopyB`
- **Section**: `CopyHeader`, `LeftCol`, `RghtCol`
- **OptionalGroup**: `CalendarYear`, `Box2a_ReadOrder`, `Box14_ReadOrder`, etc.
- **FieldID**: `f1_1`, `f2_1`, `c2_1` (text fields start with `f`, checkboxes with `c`)

### Copy Differences

- **CopyA (Base)**: Uses `f1_` prefix for field IDs
- **Copy1, Copy2, CopyB**: Use `f2_` prefix for field IDs
- **Checkboxes**: Use `c1_` or `c2_` prefix

## Recommendations

### 1. Address Field Strategy

Since the PDF template does NOT have separate fields for address components, we have two options:

**Option A: Keep Combined Format (Recommended)**
- Continue using combined address fields as currently implemented
- Document that users should provide complete address strings
- Example: `payerCity: "New York, NY 10001"`

**Option B: Parse and Combine**
- Accept separate address components in API
- Combine them before filling the PDF
- Example: Combine `payerCity`, `payerState`, `payerZip` into single string for `f2_2[0]`

**Recommendation**: Use **Option B** for better API usability while maintaining PDF compatibility.

### 2. Second State Mapping

Add support for second state tax reporting:

```python
"state2": "topmostSubform[0].Copy1[0].RghtCol[0].Box14_ReadOrder[0].f2_28[0]",
"stateTaxWithheld2": "topmostSubform[0].Copy1[0].RghtCol[0].Box15_ReadOrder[0].f2_30[0]",
```

**Note**: Skip `stateIdentificationNumber2` as the PDF doesn't appear to have a dedicated field for it.

### 3. Fix Current Mapping Issues

The current mapping has Box14/Box15 inconsistencies that should be corrected:

**Current (Incorrect)**:
```python
"stateIdentificationNumber": "...Box14_ReadOrder[0].f2_28[0]",  # Wrong box group
"stateTaxWithheld": "...Box15_ReadOrder[0].f2_29[0]",  # Wrong box group
```

**Should Be**:
```python
"stateIdentificationNumber": "...Box15_ReadOrder[0].f2_28[0]",  # Box 15
"stateTaxWithheld": "...Box16_ReadOrder[0].f2_29[0]",  # Box 16
```

## New Fields Summary

### Fields That CAN Be Added:

1. **state2**: Second state name (Box 14, row 2)
2. **stateTaxWithheld2**: Second state tax withheld (Box 16, row 2)

### Fields That CANNOT Be Added (No PDF Fields):

1. **payerState**: No separate field (combined in f2_2)
2. **payerCountry**: No separate field (combined in f2_2)
3. **payerZip**: No separate field (combined in f2_2)
4. **payerTelephoneNumber**: No separate field (combined in f2_2)
5. **recipientCity**: No separate field (combined in f2_7)
6. **recipientState**: No separate field (combined in f2_7)
7. **recipientCountry**: No separate field (combined in f2_7)
8. **recipientZip**: No separate field (combined in f2_7)
9. **stateIdentificationNumber2**: No separate field for second state

### Alternative Approach: Virtual Fields

We can still accept these fields in the API and combine them before PDF generation:

```python
# API accepts separate fields
{
  "payerCity": "New York",
  "payerState": "NY",
  "payerZip": "10001"
}

# System combines them for PDF field f2_2[0]
"New York, NY 10001"
```

This provides a better API experience while working within PDF constraints.

## Complete Field Reference

### Copy1 (Primary Copy) - All Fields

#### CopyHeader:
- `f2_1[0]`: Calendar Year ✓ Mapped

#### LeftCol:
- `f2_2[0]`: Payer name, address (combined) ✓ Mapped (as payerName, payerStreetAddress, payerCity)
- `f2_3[0]`: Payer TIN ✓ Mapped
- `f2_4[0]`: Recipient TIN ✓ Mapped
- `f2_5[0]`: Recipient name ✓ Mapped
- `f2_6[0]`: Recipient street address ✓ Mapped
- `f2_7[0]`: Recipient city, state, ZIP (combined) ⚠️ Partially mapped (needs update)
- `f2_8[0]`: Account number ✓ Mapped

#### RghtCol:
- `f2_9[0]`: Box 1a - Total ordinary dividends ✓ Mapped
- `f2_10[0]`: Box 1b - Qualified dividends ✓ Mapped
- `f2_11[0]`: Box 2a - Total capital gain distributions ✓ Mapped
- `f2_12[0]`: Box 2b - Unrecaptured section 1250 gain ✓ Mapped
- `f2_13[0]`: Box 2c - Section 1202 gain ✓ Mapped
- `f2_14[0]`: Box 2d - Collectibles (28%) gain ✓ Mapped
- `f2_15[0]`: Box 2e - Section 897 ordinary dividends ✓ Mapped
- `f2_16[0]`: Box 2f - Section 897 capital gain ✓ Mapped
- `f2_17[0]`: Box 3 - Nondividend distributions ✓ Mapped
- `f2_18[0]`: Box 4 - Federal income tax withheld ✓ Mapped
- `f2_19[0]`: Box 5 - Section 199A dividends ✓ Mapped
- `f2_20[0]`: Box 6 - Investment expenses ✓ Mapped
- `f2_21[0]`: Box 7 - Foreign tax paid ✓ Mapped
- `f2_22[0]`: Box 8 - Foreign country ✓ Mapped
- `f2_23[0]`: Box 9 - Cash liquidation distributions ✓ Mapped
- `f2_24[0]`: Box 10 - Noncash liquidation distributions ✓ Mapped
- `c2_3[0]`: Box 11 - FATCA filing requirement (checkbox) ✓ Mapped
- `f2_25[0]`: Box 12 - Exempt-interest dividends ✓ Mapped
- `f2_26[0]`: Box 13 - Specified private activity bond interest ✓ Mapped
- `f2_27[0]`: Box 14 - State (row 1) ✓ Mapped
- `f2_28[0]`: Box 14 - State (row 2) OR Box 15 - State ID (row 1) ⚠️ Needs clarification
- `f2_29[0]`: Box 16 - State tax withheld (row 1) ✓ Mapped
- `f2_30[0]`: Box 16 - State tax withheld (row 2) ❌ Not mapped
- `f2_31[0]`: Additional field (purpose unclear) ✓ Mapped as accountNumber
- `f2_32[0]`: Additional field (purpose unclear) ❌ Not mapped

## Next Steps

1. **Clarify PDF Field Usage**: Manually inspect the PDF to determine the exact purpose of fields `f2_27` through `f2_32` in the state tax section
2. **Update Canonical Mapping**: Add second state fields based on clarified field purposes
3. **Implement Address Parsing**: Create functions to combine separate address components into combined PDF fields
4. **Update Field Metadata**: Add metadata for new virtual fields (address components)
5. **Update Documentation**: Reflect the combined field approach in API documentation

## Conclusion

The PDF inspection reveals that the 1099-DIV template uses **combined address fields** rather than separate fields for each address component. This means:

- **Can Add**: Second state tax fields (state2, stateTaxWithheld2)
- **Cannot Add as Separate PDF Fields**: Individual address components (city, state, ZIP, country, telephone)
- **Solution**: Accept separate address components in API, combine them before PDF generation

This approach provides the best user experience while working within the constraints of the PDF template structure.
