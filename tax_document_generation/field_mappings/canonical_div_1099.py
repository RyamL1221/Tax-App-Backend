"""
Canonical field mapping configuration for IRS Form 1099-DIV.

This module provides the standardized, well-documented mapping structure
organized by official IRS box numbers. This is the authoritative source
for all 1099-DIV field mappings.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4
"""

from typing import Dict

# Canonical mapping from API field names to PDF field names
# Organized by IRS form structure for clarity and maintainability
CANONICAL_FIELD_MAPPING: Dict[str, str] = {
    # =========================================================================
    # Calendar Year
    # =========================================================================
    "calendarYear": "topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]",
    
    # =========================================================================
    # Payer Information (LeftCol)
    # =========================================================================
    "payerName": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",
    "payerStreetAddress": "topmostSubform[0].Copy1[0].LeftCol[0].f2_3[0]",
    "payerCity": "topmostSubform[0].Copy1[0].LeftCol[0].f2_4[0]",
    "payerTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",
    
    # =========================================================================
    # Recipient Information (LeftCol)
    # =========================================================================
    "recipientName": "topmostSubform[0].Copy1[0].LeftCol[0].f2_5[0]",
    "recipientStreetAddress": "topmostSubform[0].Copy1[0].LeftCol[0].f2_6[0]",
    "recipientTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",
    
    # =========================================================================
    # Box 1: Dividends (RghtCol)
    # =========================================================================
    "totalOrdinaryDividends": "topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]",  # Box 1a
    "qualifiedDividends": "topmostSubform[0].Copy1[0].RghtCol[0].f2_10[0]",  # Box 1b
    
    # =========================================================================
    # Box 2: Capital Gains (RghtCol)
    # =========================================================================
    "totalCapitalGainDistributions": "topmostSubform[0].Copy1[0].RghtCol[0].Box2a_ReadOrder[0].f2_11[0]",  # Box 2a
    "unrecapturedSection1250Gain": "topmostSubform[0].Copy1[0].RghtCol[0].f2_12[0]",  # Box 2b
    "section1202Gain": "topmostSubform[0].Copy1[0].RghtCol[0].Box2c_ReadOrder[0].f2_13[0]",  # Box 2c
    "collectibles28Gain": "topmostSubform[0].Copy1[0].RghtCol[0].f2_14[0]",  # Box 2d
    "section897OrdinaryDividends": "topmostSubform[0].Copy1[0].RghtCol[0].Box2e_ReadOrder[0].f2_15[0]",  # Box 2e
    "section897CapitalGain": "topmostSubform[0].Copy1[0].RghtCol[0].f2_16[0]",  # Box 2f
    
    # =========================================================================
    # Box 3-7: Distributions and Taxes (RghtCol)
    # =========================================================================
    "nondividendDistributions": "topmostSubform[0].Copy1[0].RghtCol[0].Box3_ReadOrder[0].f2_17[0]",  # Box 3
    "federalIncomeTaxWithheld": "topmostSubform[0].Copy1[0].RghtCol[0].f2_18[0]",  # Box 4
    "section199ADividends": "topmostSubform[0].Copy1[0].RghtCol[0].Box5_ReadOrder[0].f2_19[0]",  # Box 5
    "investmentExpenses": "topmostSubform[0].Copy1[0].RghtCol[0].f2_20[0]",  # Box 6
    "foreignTaxPaid": "topmostSubform[0].Copy1[0].RghtCol[0].Box7_ReadOrder[0].f2_21[0]",  # Box 7
    
    # =========================================================================
    # Box 8-13: Foreign and Liquidation (RghtCol)
    # =========================================================================
    "foreignCountry": "topmostSubform[0].Copy1[0].RghtCol[0].f2_22[0]",  # Box 8
    "cashLiquidationDistributions": "topmostSubform[0].Copy1[0].RghtCol[0].Box9_ReadOrder[0].f2_23[0]",  # Box 9
    "noncashLiquidationDistributions": "topmostSubform[0].Copy1[0].RghtCol[0].f2_24[0]",  # Box 10
    "fatcaFilingRequirement": "topmostSubform[0].Copy1[0].RghtCol[0].TagCorrectingSubform[0].c2_3[0]",  # Box 11
    "exemptInterestDividends": "topmostSubform[0].Copy1[0].RghtCol[0].Box12_ReadOrder[0].f2_25[0]",  # Box 12
    "specifiedPrivateActivityBondInterest": "topmostSubform[0].Copy1[0].RghtCol[0].f2_26[0]",  # Box 13
    
    # =========================================================================
    # Box 14-16: State Tax (RghtCol)
    # =========================================================================
    "state": "topmostSubform[0].Copy1[0].RghtCol[0].Box14_ReadOrder[0].f2_27[0]",  # Box 14
    "stateIdentificationNumber": "topmostSubform[0].Copy1[0].RghtCol[0].Box14_ReadOrder[0].f2_28[0]",  # Box 15
    "stateTaxWithheld": "topmostSubform[0].Copy1[0].RghtCol[0].Box15_ReadOrder[0].f2_29[0]",  # Box 16
    
    # =========================================================================
    # Account Number (RghtCol)
    # =========================================================================
    "accountNumber": "topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]",
}
