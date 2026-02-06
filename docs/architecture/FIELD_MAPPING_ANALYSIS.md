# 1099-DIV Field Mapping Analysis

## Inspection Results Summary

**Date:** 2024
**PDF Analyzed:** samples/SAMPLE-1099-DIV-MULTI-COPY.pdf
**Total Fields Found:** 140 fields across 4 pages
**Pages:** CopyA (Page 2), Copy1 (Page 3), CopyB (Page 4), Copy2 (Page 6)

## Field Layout Analysis

### Left Column Fields (Payer/Recipient Information)

Based on the inspection, the LeftCol fields follow this pattern on Copy1:

| Field Name | Y Position | Height | Purpose (Inferred from Position) |
|------------|-----------|--------|----------------------------------|
| f2_2[0] | 56.0 | 76.0 | **PAYER'S name** (large field) |
| f2_3[0] | 142.0 | 38.0 | **Street address** (left half) |
| f2_4[0] | 142.0 | 38.0 | **City/State/ZIP** (right half) |
| f2_5[0] | 190.0 | 26.0 | **Unknown field** |
| f2_6[0] | 226.0 | 26.0 | **Unknown field** |
| f2_7[0] | 262.0 | 26.0 | **PAYER'S TIN** |
| f2_8[0] | 334.0 | 26.0 | **RECIPIENT'S TIN** |

### Right Column Fields (Box Values)

The RghtCol fields on Copy1 include:

| Field Name | Y Position | Height | Purpose (Inferred from Position) |
|------------|-----------|--------|----------------------------------|
| f2_9[0] | 60.0 | 12.0 | Box 1a - Total ordinary dividends |
| f2_10[0] | 96.0 | 12.0 | Box 1b - Qualified dividends |
| f2_11[0] | 120.0 | 12.0 | Box 2a - Total capital gain |
| ... | ... | ... | ... |
| f2_31[0] | 336.0 | 12.0 | **Box 16 or Account Number?** |
| f2_32[0] | 348.0 | 12.0 | **Unknown field** |

## Current Mapping Analysis

### Current Mappings (from div_1099.py)

```python
"payerTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",
"recipientTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",
"recipientName": "topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]",
```

### Field Position Verification

**Payer TIN (f2_7[0]):**
- Location: LeftCol, y=262.0
- Dimensions: 242.1 x 26.0
- ✅ **CORRECT** - This is in the left column at the appropriate position for payer TIN

**Recipient TIN (f2_8[0]):**
- Location: LeftCol, y=334.0
- Dimensions: 244.8 x 26.0
- ✅ **CORRECT** - This is in the left column at the bottom, appropriate for recipient TIN

**Recipient Name (f2_31[0]):**
- Location: RghtCol, y=336.0
- Dimensions: 89.8 x 12.0
- ⚠️ **QUESTIONABLE** - This is in the RIGHT column at the bottom
- This appears to be Box 16 (state tax withheld) or account number area
- Recipient name should likely be in the LEFT column

## Problem Identification

Based on the IRS 1099-DIV form structure, the recipient's name should appear in the LEFT column, not the right column. Looking at the LeftCol fields:

- **f2_2[0]** (y=56.0, height=76.0) - This is the PAYER'S name (large field at top)
- **f2_5[0]** (y=190.0, height=26.0) - Could this be recipient name?
- **f2_6[0]** (y=226.0, height=26.0) - Could this be recipient street address?

However, the typical 1099-DIV layout has:
1. Payer's name, street address, city/state/ZIP
2. Payer's TIN
3. Recipient's TIN
4. Recipient's name, street address, city/state/ZIP
5. Account number (optional)

## Recommended Investigation

To properly identify the recipient name field, we need to:

1. **Check the actual IRS 1099-DIV PDF template** to see the visual labels
2. **Look at field f2_5[0] and f2_6[0]** - these might be recipient name/address
3. **Verify f2_31[0] and f2_32[0]** - these are likely account number or state tax fields

## Multi-Copy Verification

All three copies (Copy1, Copy2, CopyB) have identical field structures:
- ✅ Copy1: f2_7[0] (payer TIN), f2_8[0] (recipient TIN), f2_31[0] (?)
- ✅ Copy2: f2_7[0] (payer TIN), f2_8[0] (recipient TIN), f2_31[0] (?)
- ✅ CopyB: f2_7[0] (payer TIN), f2_8[0] (recipient TIN), f2_31[0] (?)

The field naming is consistent across all copies, which is good for the multi-copy generation logic.

## Conclusion

**Current Status:**
- ✅ Payer TIN mapping appears CORRECT (f2_7[0])
- ✅ Recipient TIN mapping appears CORRECT (f2_8[0])
- ⚠️ Recipient Name mapping is QUESTIONABLE (f2_31[0] is in wrong column)

**Next Steps:**
1. Visually inspect the actual PDF template to see field labels
2. Test filling f2_5[0] and f2_6[0] to see if they are recipient name/address
3. Verify what f2_31[0] and f2_32[0] actually represent on the form
4. Update mappings based on visual confirmation

## Additional Notes

The inspection script highlighted fields containing "TIN" keyword:
- Found checkbox fields with "TIN" in the name: `TagCorrectingSubform[0].c2_3[0]`
- These are "CORRECTED" checkboxes, not TIN input fields
- The actual TIN fields (f2_7, f2_8) don't have "TIN" in their names

This confirms that PDF field names are cryptic and don't match their visual labels.
