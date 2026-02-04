# 1099-DIV Field Inspection Analysis

## Inspection Date
Task 2 of debug-1099-div-field-mappings spec

## Summary
Ran `inspect_pdf_fields.py` on `samples/1099-DIV.pdf` to identify correct PDF field names for:
- Payer TIN (currently incorrectly mapped)
- Recipient TIN (currently incorrectly mapped)
- Recipient Name (currently not working)

## PDF Structure
- **Total Fields**: 140 fields
- **Total Pages**: 4 pages
- **Copies**: CopyA (Page 2), Copy1 (Page 3), CopyB (Page 4), Copy2 (Page 6)

## Current Mappings (from div_1099.py)
```python
"payerName": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",
"payerTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",
"payerCity": "topmostSubform[0].Copy1[0].LeftCol[0].f2_4[0]",

"recipientTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",
"recipientName": "topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]",
"accountNumber": "topmostSubform[0].Copy1[0].RghtCol[0].f2_39[0]",
```

## Field Analysis - Copy1 (Page 3) LeftCol

Based on field positions (y-coordinate indicates vertical position on form):

| Field Name | Y Position | Height | Likely Purpose |
|------------|-----------|--------|----------------|
| f2_2[0] | 56.0 | 76.0 | **Payer Name** (large field) ✓ CORRECT |
| f2_3[0] | 142.0 | 38.0 | **Payer Street Address** ✓ CORRECT |
| f2_4[0] | 142.0 | 38.0 | **Payer City/State** (same row as f2_3) ✓ CORRECT |
| f2_5[0] | 190.0 | 26.0 | **Payer State** ✓ CORRECT |
| f2_6[0] | 226.0 | 26.0 | **Payer ZIP** ✓ CORRECT |
| f2_7[0] | 262.0 | 26.0 | **Payer TIN** ✓ CORRECT |
| f2_8[0] | 334.0 | 26.0 | **Recipient TIN** ✓ CORRECT |

## Field Analysis - Copy1 (Page 3) RghtCol

Based on field positions:

| Field Name | Y Position | Height | Likely Purpose |
|------------|-----------|--------|----------------|
| f2_9[0] | 60.0 | 12.0 | Box 1a - Total Ordinary Dividends ✓ |
| f2_10[0] | 96.0 | 12.0 | Box 1b - Qualified Dividends ✓ |
| ... | ... | ... | (other box fields) |
| f2_31[0] | 336.0 | 12.0 | **Box 16 - State Tax Withheld (line 1)** |
| f2_32[0] | 348.0 | 12.0 | **Box 16 - State Tax Withheld (line 2)** |

## Critical Finding: Missing f2_39 Field

**ISSUE**: The current mapping shows `accountNumber` mapped to `f2_39[0]`, but **f2_39 does not exist** in the PDF!

The highest field number in RghtCol is `f2_32[0]`. There is no `f2_33`, `f2_34`, `f2_35`, `f2_36`, `f2_37`, `f2_38`, or `f2_39` in the RghtCol.

## Analysis of Current Mappings

### 1. Payer TIN Mapping
**Current**: `f2_7[0]` in LeftCol  
**Status**: ✓ **CORRECT**  
**Position**: y=262.0 (below ZIP code field)  
**Conclusion**: The current mapping appears to be correct based on field position.

### 2. Recipient TIN Mapping
**Current**: `f2_8[0]` in LeftCol  
**Status**: ✓ **CORRECT**  
**Position**: y=334.0 (below Payer TIN)  
**Conclusion**: The current mapping appears to be correct based on field position.

### 3. Recipient Name Mapping
**Current**: `f2_31[0]` in RghtCol  
**Status**: ❌ **INCORRECT**  
**Position**: y=336.0 in RghtCol (Box 16 area - state tax withheld)  
**Issue**: This field is in the wrong section (RghtCol instead of LeftCol) and wrong position (bottom of form in tax boxes area)

### 4. Account Number Mapping
**Current**: `f2_39[0]` in RghtCol  
**Status**: ❌ **FIELD DOES NOT EXIST**  
**Issue**: There is no f2_39 field in the PDF

## Hypothesis: Recipient Name Location

Looking at the LeftCol fields, there's a gap in the field sequence:
- f2_2 = Payer Name (y=56.0)
- f2_3 = Payer Street (y=142.0)
- f2_4 = Payer City (y=142.0)
- f2_5 = Payer State (y=190.0)
- f2_6 = Payer ZIP (y=226.0)
- f2_7 = Payer TIN (y=262.0)
- f2_8 = Recipient TIN (y=334.0)

**Missing**: Where is the Recipient Name field?

Possible locations:
1. Between f2_7 and f2_8 (but no field exists there in the output)
2. The field might not exist in this PDF template
3. The field might be on a different page or section

## Verification Needed

To resolve the discrepancies, we need to:

1. **Visually inspect the PDF** to see where "RECIPIENT'S name" label appears
2. **Check if recipient name field exists** in the LeftCol between TIN fields
3. **Verify the account number field location** (if it exists)
4. **Check other copies** (CopyA, CopyB, Copy2) for consistency

## Field Naming Pattern Across Copies

All three copies (Copy1, CopyB, Copy2) have identical field structures:
- Copy1: `topmostSubform[0].Copy1[0].LeftCol[0].f2_X[0]`
- CopyB: `topmostSubform[0].CopyB[0].LeftCol[0].f2_X[0]`
- Copy2: `topmostSubform[0].Copy2[0].LeftCol[0].f2_X[0]`
- CopyA: `topmostSubform[0].CopyA[0].LeftCol[0].f1_X[0]` (uses f1_ prefix!)

**Note**: CopyA uses `f1_` prefix while other copies use `f2_` prefix.

## Next Steps

1. Open the PDF in a viewer and visually locate:
   - Recipient Name field label and its position
   - Account Number field label and its position
2. Cross-reference visual positions with field coordinates
3. Update field mappings based on visual verification
4. Test the corrected mappings with actual form generation
