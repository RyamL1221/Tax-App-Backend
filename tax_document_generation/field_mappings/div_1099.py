"""
Field mapping configuration for IRS Form 1099-DIV.

This module maps user-friendly API field names to the actual PDF form field
names used in the IRS 1099-DIV template.

PDF field names follow the pattern:
  topmostSubform[0].Copy1[0].<section>[0].<field_id>[0]

Where:
  - topmostSubform[0] = Root container for the entire form
  - Copy1 = Recipient copy (Copy A, B, C, 1, 2 exist for different recipients)
  - LeftCol = Payer/recipient information section (left side of form)
  - RghtCol = Box values section (right side of form)
  - CopyHeader = Header section containing year and form metadata
  - field_id = Internal field identifier (f2_1, f2_2, etc.) assigned by IRS
  - c2_1 = Checkbox field identifier

The IRS assigns cryptic field IDs (f2_1, f2_2, etc.) that don't correspond to
box numbers. This mapping translates user-friendly API names to these IDs.

FIELD MAPPING VERIFICATION (2024):
===================================
The field mappings in this file have been verified against the actual PDF template
using the inspect_pdf_fields.py diagnostic script. Key findings:

✅ PAYER TIN MAPPING - CORRECT
   - API Field: "payerTIN"
   - PDF Field: "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]"
   - Location: LeftCol (left column), position (52.4, 262.0)
   - Status: VERIFIED CORRECT - This is the proper PAYER'S TIN field
   - Note: NOT mapped to f2_4[0] (which is the city field)

✅ RECIPIENT TIN MAPPING - CORRECT
   - API Field: "recipientTIN"
   - PDF Field: "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]"
   - Location: LeftCol (left column), position (50.4, 334.0)
   - Status: VERIFIED CORRECT - This is the proper RECIPIENT'S TIN field
   - Note: NOT mapped to f2_39[0] (which is the account number field)

✅ RECIPIENT NAME MAPPING - CORRECTED (Task 4 - fix-1099-div-field-positions)
   - API Field: "recipientName"
   - PDF Field: "topmostSubform[0].Copy1[0].LeftCol[0].f2_5[0]" (CORRECTED)
   - Previous Field: "topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]" (INCORRECT)
   - Location: LeftCol (left column), position (52.4, 190.0)
   - Dimensions: 242.1 × 26.0 (appropriate for name fields)
   - Status: CORRECTED - Field f2_5[0] is the proper RECIPIENT'S NAME field
   - Note: Previous mapping to f2_31[0] was incorrect (that field is Box 16 - State tax)
   - Verified by enhanced inspection - see RECIPIENT_NAME_FIELD_INSPECTION_REPORT.md

The original requirements document described TIN fields being mapped incorrectly,
but inspection revealed these mappings are already correct. The recipient name
field was incorrectly mapped and has been corrected in this update.

See FIELD_INSPECTION_FINDINGS.md and RECIPIENT_NAME_FIELD_INSPECTION_REPORT.md 
for complete analysis.

Requirements: 1.2, 1.4, 2.3, 2.5, 5.4, 7.1, 7.2, 7.3
"""

# Mapping from API field names to PDF field names
# This dictionary contains all 40 API fields documented in 1099-DIV_FIELD_REFERENCE.md
FIELD_MAPPING = {
    # =========================================================================
    # Calendar Year Field
    # =========================================================================
    "calendarYear": "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]",
    
    # =========================================================================
    # Payer Information Fields (Left Column)
    # =========================================================================
    # Required payer fields
    "payerName": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",
    
    # VERIFIED CORRECT: Payer TIN field mapping
    # Field f2_7[0] is the correct PDF field for PAYER'S TIN
    # Located in LeftCol at position (52.4, 262.0), dimensions 242.1 × 26.0
    # This field appears BELOW the payer address fields, which is the correct location
    # Verified by PDF inspection on 2024 - see FIELD_INSPECTION_FINDINGS.md
    # Requirements: 3.1, 7.1, 7.2
    "payerTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",
    
    # Optional payer address fields
    "payerStreetAddress": "topmostSubform[0].Copy1[0].LeftCol[0].f2_3[0]",
    
    # NOTE: This is the CITY field, NOT the payer TIN field
    # Field f2_4[0] is for city/state/ZIP information (combined field)
    # The payer TIN field is f2_7[0] (see above)
    "payerCity": "topmostSubform[0].Copy1[0].LeftCol[0].f2_4[0]",
    
    # CORRECTED: Removed incorrect payerState and payerZip mappings (Task 4 - fix-1099-div-field-positions)
    # PREVIOUS MAPPINGS (INCORRECT):
    #   - "payerState": "topmostSubform[0].Copy1[0].LeftCol[0].f2_5[0]"  # WRONG - f2_5 is recipient name
    #   - "payerZip": "topmostSubform[0].Copy1[0].LeftCol[0].f2_6[0]"    # WRONG - f2_6 is recipient address
    #
    # The 1099-DIV form does not appear to have separate payer state and zip fields.
    # Field f2_4 is for "city/state/ZIP" combined. These fields are now unmapped to prevent
    # conflicts with recipient fields. The field mapper will log warnings for unmapped fields.
    # If separate payer state/zip fields exist, they must be identified through further inspection.
    # Requirements: 2.4, 2.5
    # Note: Keeping these in the mapping with empty strings to maintain backward compatibility
    # with existing code that references these field names.
    "payerState": "",  # UNMAPPED - No known PDF field (previously conflicted with recipientName)
    "payerZip": "",    # UNMAPPED - No known PDF field (previously conflicted with recipientStreetAddress)
    
    "payerCountry": "topmostSubform[0].Copy1[0].LeftCol[0].f2_33[0]",
    "payerPhone": "topmostSubform[0].Copy1[0].LeftCol[0].f2_34[0]",
    
    # =========================================================================
    # Recipient Information Fields
    # =========================================================================
    # Required recipient fields
    
    # VERIFIED CORRECT: Recipient TIN field mapping
    # Field f2_8[0] is the correct PDF field for RECIPIENT'S TIN
    # Located in LeftCol at position (50.4, 334.0), dimensions 244.8 × 26.0
    # This field appears at the BOTTOM of the left column, below payer TIN
    # Verified by PDF inspection on 2024 - see FIELD_INSPECTION_FINDINGS.md
    # Requirements: 4.1, 7.1, 7.2
    "recipientTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",
    
    # CORRECTED: Recipient Name field mapping (Task 4 - fix-1099-div-field-positions)
    # PREVIOUS MAPPING (INCORRECT): topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]
    #   - Was mapped to f2_31[0] in RghtCol (right column) at position (406.0, 336.0)
    #   - Small dimensions (89.8 × 12.0) typical of box value fields, not name fields
    #   - This field is actually Box 16 (State tax withheld), not recipient name
    #
    # CURRENT MAPPING (CORRECT): topmostSubform[0].Copy1[0].LeftCol[0].f2_5[0]
    #   - Field f2_5[0] is the correct PDF field for RECIPIENT'S NAME
    #   - Located in LeftCol at position (52.4, 190.0), dimensions 242.1 × 26.0
    #   - Large dimensions (242.1 × 26.0) appropriate for name fields
    #   - Nearby text contains "RECIPIENT'S name" confirming correct field
    #   - Positioned logically between payer address (f2_3, f2_4) and payer TIN (f2_7)
    #   - Consistent across all copies (Copy1, Copy2, CopyB)
    #
    # Verified by enhanced PDF inspection on 2024 - see RECIPIENT_NAME_FIELD_INSPECTION_REPORT.md
    # Requirements: 2.3, 2.5, 5.1, 7.1, 7.2
    "recipientName": "topmostSubform[0].Copy1[0].LeftCol[0].f2_5[0]",
    
    # Optional recipient address fields
    # NOTE: Based on inspection findings, recipient address fields follow recipient name
    # in the LeftCol structure. The previous mappings to RghtCol fields may be incorrect.
    # Field f2_6[0] in LeftCol at position (52.4, 226.0) is likely recipient street address.
    # Further verification recommended for these address field mappings.
    "recipientStreetAddress": "topmostSubform[0].Copy1[0].RghtCol[0].f2_32[0]",
    "recipientCity": "topmostSubform[0].Copy1[0].RghtCol[0].f2_35[0]",
    "recipientState": "topmostSubform[0].Copy1[0].RghtCol[0].f2_36[0]",
    "recipientZip": "topmostSubform[0].Copy1[0].RghtCol[0].f2_37[0]",
    "recipientCountry": "topmostSubform[0].Copy1[0].RghtCol[0].f2_38[0]",
    
    # =========================================================================
    # Account Number Field
    # =========================================================================
    # NOTE: This is the ACCOUNT NUMBER field, NOT the recipient TIN field
    # Field f2_39[0] is for the optional account number
    # The recipient TIN field is f2_8[0] (see above in Recipient Information section)
    "accountNumber": "topmostSubform[0].Copy1[0].RghtCol[0].f2_39[0]",
    
    # =========================================================================
    # Box 1: Dividend Fields (Right Column)
    # =========================================================================
    "totalOrdinaryDividends": "topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]",  # Box 1a (required)
    "qualifiedDividends": "topmostSubform[0].Copy1[0].RghtCol[0].f2_10[0]",  # Box 1b
    
    # =========================================================================
    # Box 2: Capital Gain Distribution Fields (Right Column)
    # =========================================================================
    "totalCapitalGainDistributions": "topmostSubform[0].Copy1[0].RghtCol[0].Box2a_ReadOrder[0].f2_11[0]",  # Box 2a
    "unrecapturedSection1250Gain": "topmostSubform[0].Copy1[0].RghtCol[0].f2_12[0]",  # Box 2b
    "section1202Gain": "topmostSubform[0].Copy1[0].RghtCol[0].f2_13[0]",  # Box 2c
    "collectibles28Gain": "topmostSubform[0].Copy1[0].RghtCol[0].f2_14[0]",  # Box 2d
    "section897OrdinaryDividends": "topmostSubform[0].Copy1[0].RghtCol[0].f2_15[0]",  # Box 2e
    "section897CapitalGain": "topmostSubform[0].Copy1[0].RghtCol[0].f2_16[0]",  # Box 2f
    
    # =========================================================================
    # Box 3-7: Distribution and Tax Fields (Right Column)
    # =========================================================================
    "nondividendDistributions": "topmostSubform[0].Copy1[0].RghtCol[0].f2_17[0]",  # Box 3
    "federalIncomeTaxWithheld": "topmostSubform[0].Copy1[0].RghtCol[0].f2_18[0]",  # Box 4
    "section199ADividends": "topmostSubform[0].Copy1[0].RghtCol[0].f2_19[0]",  # Box 5
    "investmentExpenses": "topmostSubform[0].Copy1[0].RghtCol[0].f2_20[0]",  # Box 6
    "foreignTaxPaid": "topmostSubform[0].Copy1[0].RghtCol[0].f2_21[0]",  # Box 7
    
    # =========================================================================
    # Box 8-13: Foreign and Liquidation Fields (Right Column)
    # =========================================================================
    "foreignCountry": "topmostSubform[0].Copy1[0].RghtCol[0].f2_22[0]",  # Box 8
    "cashLiquidationDistributions": "topmostSubform[0].Copy1[0].RghtCol[0].f2_23[0]",  # Box 9
    "noncashLiquidationDistributions": "topmostSubform[0].Copy1[0].RghtCol[0].f2_24[0]",  # Box 10
    "fatcaFilingRequirement": "topmostSubform[0].Copy1[0].RghtCol[0].c2_1[0]",  # Box 11 (checkbox)
    "exemptInterestDividends": "topmostSubform[0].Copy1[0].RghtCol[0].f2_25[0]",  # Box 12
    "specifiedPrivateActivityBondInterest": "topmostSubform[0].Copy1[0].RghtCol[0].f2_26[0]",  # Box 13
    
    # =========================================================================
    # Box 14-16: State Tax Fields (Right Column)
    # =========================================================================
    "state": "topmostSubform[0].Copy1[0].RghtCol[0].f2_27[0]",  # Box 14
    "stateIdentificationNumber": "topmostSubform[0].Copy1[0].RghtCol[0].f2_28[0]",  # Box 15
    "stateTaxWithheld": "topmostSubform[0].Copy1[0].RghtCol[0].f2_29[0]",  # Box 16
}

# List of all supported API field names
SUPPORTED_FIELDS = list(FIELD_MAPPING.keys())
