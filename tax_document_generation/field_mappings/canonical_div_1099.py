"""
Canonical field mapping configuration for IRS Form 1099-DIV.

This module provides the standardized, well-documented mapping structure
organized by official IRS box numbers. This is the authoritative source
for all 1099-DIV field mappings.

Address Field Handling:
- Payer address components are combined into `payerAddressBlock` before PDF generation
- Recipient city/state/ZIP are combined into `recipientCityStateZip` before PDF generation
- Individual component mappings are kept for backward compatibility
- The address_combiner module handles the combination logic

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
    # VOIDED and CORRECTED Checkboxes (CopyHeader)
    # These checkboxes appear at the top of each copy to indicate form status
    # Note: CopyB only has CORRECTED checkbox (no VOIDED)
    # =========================================================================
    "voided": "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[0]",  # VOIDED checkbox
    "corrected": "topmostSubform[0].Copy1[0].CopyHeader[0].c2_1[1]",  # CORRECTED checkbox
    
    # =========================================================================
    # Payer Information (LeftCol)
    # Combined Address Field:
    #   - payerAddressBlock: Auto-generated combined field containing all payer
    #     address components (name, street, city, state, zip, country, telephone)
    #     formatted as a multi-line string. This is the primary field used for
    #     PDF generation.
    # Individual Component Fields:
    #   - Kept for backward compatibility with existing API contracts
    #   - These are combined into payerAddressBlock by address_combiner module
    #   - If payerAddressBlock exists, it takes precedence over individual components
    # =========================================================================
    "payerAddressBlock": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",  # Combined multi-line address
    "payerName": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",  # Backward compatibility
    "payerStreetAddress": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",  # Backward compatibility
    "payerCity": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",  # Backward compatibility
    "payerState": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",  # Backward compatibility
    "payerCountry": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",  # Backward compatibility
    "payerZip": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",  # Backward compatibility
    "payerTelephoneNumber": "topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",  # Backward compatibility
    "payerTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_3[0]",
    
    # =========================================================================
    # Recipient Information (LeftCol)
    # Combined Address Field:
    #   - recipientCityStateZip: Auto-generated combined field containing recipient
    #     city, state, ZIP, and country formatted as a single or multi-line string.
    #     This is the primary field used for PDF generation.
    # Individual Component Fields:
    #   - Kept for backward compatibility with existing API contracts
    #   - These are combined into recipientCityStateZip by address_combiner module
    #   - If recipientCityStateZip exists, it takes precedence over individual components
    # Note: recipientName and recipientStreetAddress remain separate (they have their own PDF fields)
    # =========================================================================
    "recipientTIN": "topmostSubform[0].Copy1[0].LeftCol[0].f2_4[0]",
    "recipientName": "topmostSubform[0].Copy1[0].LeftCol[0].f2_5[0]",
    "recipientStreetAddress": "topmostSubform[0].Copy1[0].LeftCol[0].f2_6[0]",
    "recipientCityStateZip": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",  # Combined city/state/ZIP
    "recipientCity": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",  # Backward compatibility
    "recipientState": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",  # Backward compatibility
    "recipientCountry": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",  # Backward compatibility
    "recipientZip": "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",  # Backward compatibility
    
    # =========================================================================
    # Account Number (LeftCol)
    # =========================================================================
    "accountNumber": "topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",
    
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
    "secondTinNotification": "topmostSubform[0].CopyA[0].LeftCol[0].c1_4[0]",  # 2nd TIN not. checkbox (CopyA only)
    "exemptInterestDividends": "topmostSubform[0].Copy1[0].RghtCol[0].Box12_ReadOrder[0].f2_25[0]",  # Box 12
    "specifiedPrivateActivityBondInterest": "topmostSubform[0].Copy1[0].RghtCol[0].f2_26[0]",  # Box 13
    
    # =========================================================================
    # Box 14-16: State Tax (RghtCol)
    # Two rows for reporting up to two states
    # =========================================================================
    "state": "topmostSubform[0].Copy1[0].RghtCol[0].Box14_ReadOrder[0].f2_27[0]",  # Box 14 Row 1
    "stateIdentificationNumber": "topmostSubform[0].Copy1[0].RghtCol[0].Box15_ReadOrder[0].f2_29[0]",  # Box 15 Row 1
    "stateTaxWithheld": "topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]",  # Box 16 Row 1
    "state2": "topmostSubform[0].Copy1[0].RghtCol[0].Box14_ReadOrder[0].f2_28[0]",  # Box 14 Row 2
    "stateIdentificationNumber2": "topmostSubform[0].Copy1[0].RghtCol[0].Box15_ReadOrder[0].f2_30[0]",  # Box 15 Row 2
    "stateTaxWithheld2": "topmostSubform[0].Copy1[0].RghtCol[0].f2_32[0]",  # Box 16 Row 2
}
