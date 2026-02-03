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

Requirements: 1.2, 1.4, 5.4
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
    "payerTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",
    
    # Optional payer address fields
    "payerStreetAddress": "topmostSubform[0].Copy1[0].LeftCol[0].f2_3[0]",
    "payerCity": "topmostSubform[0].Copy1[0].LeftCol[0].f2_4[0]",
    "payerState": "topmostSubform[0].Copy1[0].LeftCol[0].f2_5[0]",
    "payerZip": "topmostSubform[0].Copy1[0].LeftCol[0].f2_6[0]",
    "payerCountry": "topmostSubform[0].Copy1[0].LeftCol[0].f2_33[0]",
    "payerPhone": "topmostSubform[0].Copy1[0].LeftCol[0].f2_34[0]",
    
    # =========================================================================
    # Recipient Information Fields
    # =========================================================================
    # Required recipient fields
    "recipientTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",
    "recipientName": "topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]",
    
    # Optional recipient address fields
    "recipientStreetAddress": "topmostSubform[0].Copy1[0].RghtCol[0].f2_32[0]",
    "recipientCity": "topmostSubform[0].Copy1[0].RghtCol[0].f2_35[0]",
    "recipientState": "topmostSubform[0].Copy1[0].RghtCol[0].f2_36[0]",
    "recipientZip": "topmostSubform[0].Copy1[0].RghtCol[0].f2_37[0]",
    "recipientCountry": "topmostSubform[0].Copy1[0].RghtCol[0].f2_38[0]",
    
    # =========================================================================
    # Account Number Field
    # =========================================================================
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
