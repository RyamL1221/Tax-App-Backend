"""
Field metadata configuration for IRS Form 1099-DIV.

This module provides comprehensive metadata for each field including
required/optional status, IRS box numbers, descriptions, and validation rules.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3, 10.3, 10.4
"""

from typing import TypedDict, Optional, Dict


class FieldMetadata(TypedDict):
    """
    Metadata for a single 1099-DIV form field.
    
    This TypedDict defines the structure for field metadata, providing
    comprehensive information about each field's requirements, validation
    rules, and documentation.
    
    Attributes:
        required: Whether the field is required by IRS regulations.
                 Required fields must be present in all form submissions.
        
        irs_box: IRS box number (e.g., "1a", "2a") or None for non-box fields.
                Box numbers correspond to the official IRS form layout.
        
        description: Human-readable description of the field's purpose.
                    Used for API documentation and developer reference.
        
        section: Logical grouping of the field. Valid values:
                - "metadata": Form-level metadata (calendar year)
                - "payer": Payer information fields
                - "recipient": Recipient information fields
                - "dividends": Dividend-related boxes (Box 1)
                - "capital_gains": Capital gain boxes (Box 2)
                - "distributions": Distribution boxes (Box 3, 9, 10)
                - "taxes": Tax withholding boxes (Box 4, 7, 14-16)
                - "other": Other boxes (Box 5, 6, 8, 11, 12, 13)
                - "account": Account number field
        
        data_type: Expected data type for the field. Valid values:
                  - "string": Text data
                  - "decimal": Numeric data with decimal places
                  - "boolean": True/False or checkbox data
        
        max_length: Maximum length for string fields. None for numeric fields.
                   Used for validation and UI constraints.
        
        validation_pattern: Regular expression pattern for validation.
                          None if no specific pattern is required.
                          Used to validate field format before submission.
        
        example_value: Example of a valid value for this field.
                      Used in API documentation and testing.
        
        normalization_type: Type of normalization to apply. Valid values:
                           - "decimal": Normalize to two decimal places
                           - "tin": Normalize TIN format (add hyphens)
                           - None: No normalization needed
        
        tin_format: Format for TIN normalization. Valid values:
                   - "SSN": Social Security Number (XXX-XX-XXXX)
                   - "EIN": Employer Identification Number (XX-XXXXXXX)
                   - None: Not a TIN field
    
    Requirements: 2.1, 2.2, 2.3, 5.1, 5.2, 5.3
    """
    required: bool
    irs_box: Optional[str]
    description: str
    section: str
    data_type: str
    max_length: Optional[int]
    validation_pattern: Optional[str]
    example_value: str
    normalization_type: Optional[str]
    tin_format: Optional[str]


# Comprehensive metadata for all 1099-DIV fields
FIELD_METADATA: Dict[str, FieldMetadata] = {
    # =========================================================================
    # Calendar Year
    # =========================================================================
    "calendarYear": {
        "required": True,
        "irs_box": None,
        "description": "Tax year for the form (e.g., 2024)",
        "section": "metadata",
        "data_type": "string",
        "max_length": 4,
        "validation_pattern": r"^\d{4}$",
        "example_value": "2024",
        "normalization_type": None,
        "tin_format": None
    },
    
    # =========================================================================
    # VOIDED and CORRECTED Checkboxes
    # =========================================================================
    "voided": {
        "required": False,
        "irs_box": None,
        "description": "VOIDED checkbox - indicates form should be disregarded",
        "section": "header",
        "data_type": "boolean",
        "max_length": None,
        "validation_pattern": None,
        "example_value": "true",
        "normalization_type": None,
        "tin_format": None
    },
    "corrected": {
        "required": False,
        "irs_box": None,
        "description": "CORRECTED checkbox - indicates form replaces previously filed form",
        "section": "header",
        "data_type": "boolean",
        "max_length": None,
        "validation_pattern": None,
        "example_value": "true",
        "normalization_type": None,
        "tin_format": None
    },
    
    # =========================================================================
    # Payer Information
    # =========================================================================
    "payerName": {
        "required": True,
        "irs_box": None,
        "description": "Name of the payer (company or individual)",
        "section": "payer",
        "data_type": "string",
        "max_length": 100,
        "validation_pattern": None,
        "example_value": "Example Corporation",
        "normalization_type": None,
        "tin_format": None
    },
    "payerAddressBlock": {
        "required": False,
        "irs_box": None,
        "description": "Combined payer address block (auto-generated from individual address components)",
        "section": "payer",
        "data_type": "string",
        "max_length": 500,
        "validation_pattern": None,
        "example_value": "Example Corporation\n123 Main Street\nNew York, NY 10001\n(555) 123-4567",
        "normalization_type": None,
        "tin_format": None
    },
    "payerTIN": {
        "required": True,
        "irs_box": None,
        "description": "Payer's Tax Identification Number (EIN or SSN)",
        "section": "payer",
        "data_type": "string",
        "max_length": 11,
        "validation_pattern": r"^\d{2}-?\d{7}$",
        "example_value": "12-3456789",
        "normalization_type": "tin",
        "tin_format": "EIN"
    },
    "payerStreetAddress": {
        "required": False,
        "irs_box": None,
        "description": "Payer's street address",
        "section": "payer",
        "data_type": "string",
        "max_length": 100,
        "validation_pattern": None,
        "example_value": "123 Main Street",
        "normalization_type": None,
        "tin_format": None
    },
    "payerCity": {
        "required": False,
        "irs_box": None,
        "description": "Payer's city, state, and ZIP code (combined field)",
        "section": "payer",
        "data_type": "string",
        "max_length": 100,
        "validation_pattern": None,
        "example_value": "New York, NY 10001",
        "normalization_type": None,
        "tin_format": None
    },
    "payerState": {
        "required": False,
        "irs_box": None,
        "description": "Payer's state or province (two-letter code)",
        "section": "payer",
        "data_type": "string",
        "max_length": 2,
        "validation_pattern": r"^[A-Z]{2}$",
        "example_value": "NY",
        "normalization_type": None,
        "tin_format": None
    },
    "payerCountry": {
        "required": False,
        "irs_box": None,
        "description": "Payer's country (if not USA)",
        "section": "payer",
        "data_type": "string",
        "max_length": 50,
        "validation_pattern": None,
        "example_value": "Canada",
        "normalization_type": None,
        "tin_format": None
    },
    "payerZip": {
        "required": False,
        "irs_box": None,
        "description": "Payer's ZIP or foreign postal code",
        "section": "payer",
        "data_type": "string",
        "max_length": 10,
        "validation_pattern": r"^\d{5}(-\d{4})?$",
        "example_value": "10001",
        "normalization_type": None,
        "tin_format": None
    },
    "payerTelephoneNumber": {
        "required": False,
        "irs_box": None,
        "description": "Payer's telephone number",
        "section": "payer",
        "data_type": "string",
        "max_length": 20,
        "validation_pattern": r"^\+?[\d\s\-\(\)]+$",
        "example_value": "(555) 123-4567",
        "normalization_type": None,
        "tin_format": None
    },
    
    # =========================================================================
    # Recipient Information
    # =========================================================================
    "recipientName": {
        "required": True,
        "irs_box": None,
        "description": "Name of the recipient (taxpayer)",
        "section": "recipient",
        "data_type": "string",
        "max_length": 100,
        "validation_pattern": None,
        "example_value": "John Doe",
        "normalization_type": None,
        "tin_format": None
    },
    "recipientTIN": {
        "required": True,
        "irs_box": None,
        "description": "Recipient's Tax Identification Number (SSN or EIN)",
        "section": "recipient",
        "data_type": "string",
        "max_length": 11,
        "validation_pattern": r"^\d{3}-?\d{2}-?\d{4}$",
        "example_value": "123-45-6789",
        "normalization_type": "tin",
        "tin_format": "SSN"
    },
    "recipientStreetAddress": {
        "required": False,
        "irs_box": None,
        "description": "Recipient's street address",
        "section": "recipient",
        "data_type": "string",
        "max_length": 100,
        "validation_pattern": None,
        "example_value": "456 Oak Avenue",
        "normalization_type": None,
        "tin_format": None
    },
    "recipientCityStateZip": {
        "required": False,
        "irs_box": None,
        "description": "Combined recipient city/state/ZIP (auto-generated from individual address components)",
        "section": "recipient",
        "data_type": "string",
        "max_length": 100,
        "validation_pattern": None,
        "example_value": "Los Angeles, CA 90001",
        "normalization_type": None,
        "tin_format": None
    },
    "recipientCity": {
        "required": False,
        "irs_box": None,
        "description": "Recipient's city or town",
        "section": "recipient",
        "data_type": "string",
        "max_length": 50,
        "validation_pattern": None,
        "example_value": "Los Angeles",
        "normalization_type": None,
        "tin_format": None
    },
    "recipientState": {
        "required": False,
        "irs_box": None,
        "description": "Recipient's state or province (two-letter code)",
        "section": "recipient",
        "data_type": "string",
        "max_length": 2,
        "validation_pattern": r"^[A-Z]{2}$",
        "example_value": "CA",
        "normalization_type": None,
        "tin_format": None
    },
    "recipientCountry": {
        "required": False,
        "irs_box": None,
        "description": "Recipient's country (if not USA)",
        "section": "recipient",
        "data_type": "string",
        "max_length": 50,
        "validation_pattern": None,
        "example_value": "Canada",
        "normalization_type": None,
        "tin_format": None
    },
    "recipientZip": {
        "required": False,
        "irs_box": None,
        "description": "Recipient's ZIP or foreign postal code",
        "section": "recipient",
        "data_type": "string",
        "max_length": 10,
        "validation_pattern": r"^\d{5}(-\d{4})?$",
        "example_value": "90001",
        "normalization_type": None,
        "tin_format": None
    },
    
    # =========================================================================
    # Box 1: Dividends
    # =========================================================================
    "totalOrdinaryDividends": {
        "required": True,
        "irs_box": "1a",
        "description": "Total ordinary dividends",
        "section": "dividends",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "1000.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "qualifiedDividends": {
        "required": False,
        "irs_box": "1b",
        "description": "Qualified dividends (subset of Box 1a)",
        "section": "dividends",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "800.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    
    # =========================================================================
    # Box 2: Capital Gains
    # =========================================================================
    "totalCapitalGainDistributions": {
        "required": False,
        "irs_box": "2a",
        "description": "Total capital gain distributions",
        "section": "capital_gains",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "500.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "unrecapturedSection1250Gain": {
        "required": False,
        "irs_box": "2b",
        "description": "Unrecaptured Section 1250 gain",
        "section": "capital_gains",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "100.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "section1202Gain": {
        "required": False,
        "irs_box": "2c",
        "description": "Section 1202 gain",
        "section": "capital_gains",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "50.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "collectibles28Gain": {
        "required": False,
        "irs_box": "2d",
        "description": "Collectibles (28%) gain",
        "section": "capital_gains",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "25.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "section897OrdinaryDividends": {
        "required": False,
        "irs_box": "2e",
        "description": "Section 897 ordinary dividends",
        "section": "capital_gains",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "75.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "section897CapitalGain": {
        "required": False,
        "irs_box": "2f",
        "description": "Section 897 capital gain",
        "section": "capital_gains",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "60.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    
    # =========================================================================
    # Box 3-7: Distributions and Taxes
    # =========================================================================
    "nondividendDistributions": {
        "required": False,
        "irs_box": "3",
        "description": "Nondividend distributions",
        "section": "distributions",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "200.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "federalIncomeTaxWithheld": {
        "required": False,
        "irs_box": "4",
        "description": "Federal income tax withheld",
        "section": "taxes",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "150.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "section199ADividends": {
        "required": False,
        "irs_box": "5",
        "description": "Section 199A dividends",
        "section": "other",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "300.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "investmentExpenses": {
        "required": False,
        "irs_box": "6",
        "description": "Investment expenses",
        "section": "other",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "50.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "foreignTaxPaid": {
        "required": False,
        "irs_box": "7",
        "description": "Foreign tax paid",
        "section": "taxes",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "75.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    
    # =========================================================================
    # Box 8-13: Foreign and Liquidation
    # =========================================================================
    "foreignCountry": {
        "required": False,
        "irs_box": "8",
        "description": "Foreign country or U.S. possession",
        "section": "other",
        "data_type": "string",
        "max_length": 50,
        "validation_pattern": None,
        "example_value": "United Kingdom",
        "normalization_type": None,
        "tin_format": None
    },
    "cashLiquidationDistributions": {
        "required": False,
        "irs_box": "9",
        "description": "Cash liquidation distributions",
        "section": "distributions",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "1000.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "noncashLiquidationDistributions": {
        "required": False,
        "irs_box": "10",
        "description": "Noncash liquidation distributions",
        "section": "distributions",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "500.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "fatcaFilingRequirement": {
        "required": False,
        "irs_box": "11",
        "description": "FATCA filing requirement (checkbox)",
        "section": "other",
        "data_type": "boolean",
        "max_length": None,
        "validation_pattern": None,
        "example_value": "true",
        "normalization_type": None,
        "tin_format": None
    },
    "secondTinNotification": {
        "required": False,
        "irs_box": None,
        "description": "2nd TIN not. checkbox - indicates IRS notified payer twice that recipient provided incorrect TIN",
        "section": "header",
        "data_type": "boolean",
        "max_length": None,
        "validation_pattern": None,
        "example_value": "true",
        "normalization_type": None,
        "tin_format": None
    },
    "exemptInterestDividends": {
        "required": False,
        "irs_box": "12",
        "description": "Exempt-interest dividends",
        "section": "other",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "250.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    "specifiedPrivateActivityBondInterest": {
        "required": False,
        "irs_box": "13",
        "description": "Specified private activity bond interest dividends",
        "section": "other",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "100.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    
    # =========================================================================
    # Box 14-16: State Tax
    # =========================================================================
    "state": {
        "required": False,
        "irs_box": "14",
        "description": "State (two-letter code)",
        "section": "taxes",
        "data_type": "string",
        "max_length": 2,
        "validation_pattern": r"^[A-Z]{2}$",
        "example_value": "NY",
        "normalization_type": None,
        "tin_format": None
    },
    "stateIdentificationNumber": {
        "required": False,
        "irs_box": "15",
        "description": "State identification number",
        "section": "taxes",
        "data_type": "string",
        "max_length": 20,
        "validation_pattern": None,
        "example_value": "12-3456789",
        "normalization_type": None,
        "tin_format": None
    },
    "stateTaxWithheld": {
        "required": False,
        "irs_box": "16",
        "description": "State tax withheld",
        "section": "taxes",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "50.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    
    # =========================================================================
    # Box 14-16: Second State Tax (Multi-State Reporting)
    # =========================================================================
    "state2": {
        "required": False,
        "irs_box": "14",
        "description": "Second state (two-letter code)",
        "section": "taxes",
        "data_type": "string",
        "max_length": 2,
        "validation_pattern": r"^[A-Z]{2}$",
        "example_value": "CA",
        "normalization_type": None,
        "tin_format": None
    },
    "stateIdentificationNumber2": {
        "required": False,
        "irs_box": "15",
        "description": "Second state identification number",
        "section": "taxes",
        "data_type": "string",
        "max_length": 20,
        "validation_pattern": None,
        "example_value": "98-7654321",
        "normalization_type": None,
        "tin_format": None
    },
    "stateTaxWithheld2": {
        "required": False,
        "irs_box": "16",
        "description": "Second state tax withheld",
        "section": "taxes",
        "data_type": "decimal",
        "max_length": None,
        "validation_pattern": r"^\d+(\.\d{2})?$",
        "example_value": "25.00",
        "normalization_type": "decimal",
        "tin_format": None
    },
    
    # =========================================================================
    # Account Number
    # =========================================================================
    "accountNumber": {
        "required": False,
        "irs_box": None,
        "description": "Account number (optional)",
        "section": "account",
        "data_type": "string",
        "max_length": 20,
        "validation_pattern": None,
        "example_value": "1234567890",
        "normalization_type": None,
        "tin_format": None
    },
}
