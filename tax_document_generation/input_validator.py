"""
Input validator for tax document generation.

This module validates user-supplied form data for tax document generation,
including checking for required fields, validating data types, and verifying
field formats (SSN, dates, numeric values, etc.).

Requirements: 2.1, 2.2, 2.3
"""

import re
import logging
from typing import Dict, Any, List

from exceptions import ValidationError
from address_normalizer import normalize_address_fields


logger = logging.getLogger(__name__)


# SSN/TIN pattern: XXX-XX-XXXX or XX-XXXXXXX
SSN_PATTERN = re.compile(r'^\d{3}-\d{2}-\d{4}$')
TIN_PATTERN = re.compile(r'^\d{2}-\d{7}$')

# Date pattern: YYYY-MM-DD
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# ZIP code pattern: XXXXX or XXXXX-XXXX
ZIP_PATTERN = re.compile(r'^\d{5}(-\d{4})?$')

# Phone pattern: Flexible format supporting international and various formats
# Allows: +1 (555) 123-4567, 555-123-4567, (555) 123-4567, +44 20 1234 5678, etc.
PHONE_PATTERN = re.compile(r'^\+?[\d\s\-\(\)]+$')


# Required fields for Form 1040
FORM_1040_REQUIRED_FIELDS = {
    'firstName': str,
    'lastName': str,
    'ssn': str,
    'filingStatus': str,
    'income': (int, float),
}

# Required fields for Form 1099-DIV
FORM_1099_DIV_REQUIRED_FIELDS = {
    # Payer information
    'payerName': str,
    'payerTIN': str,
    
    # Recipient information
    'recipientTIN': str,
    'recipientName': str,
    
    # At least one dividend amount must be present
    'totalOrdinaryDividends': (int, float),
}

# Optional fields for Form 1099-DIV
FORM_1099_DIV_OPTIONAL_FIELDS = {
    # Payer address
    'payerStreetAddress': str,
    'payerCity': str,
    'payerState': str,
    'payerCountry': str,
    'payerZip': str,
    'payerPhone': str,  # Legacy field name
    'payerTelephoneNumber': str,  # New field name
    
    # Recipient address
    'recipientStreetAddress': str,
    'recipientCity': str,
    'recipientState': str,
    'recipientCountry': str,
    'recipientZip': str,
    
    # Account and year
    'accountNumber': str,
    'calendarYear': str,
    
    # Box 1: Dividends
    'qualifiedDividends': (int, float),
    
    # Box 2: Capital gains
    'totalCapitalGainDistributions': (int, float),
    'unrecapturedSection1250Gain': (int, float),
    'section1202Gain': (int, float),
    'collectibles28Gain': (int, float),
    'section897OrdinaryDividends': (int, float),
    'section897CapitalGain': (int, float),
    
    # Box 3-7
    'nondividendDistributions': (int, float),
    'federalIncomeTaxWithheld': (int, float),
    'section199ADividends': (int, float),
    'investmentExpenses': (int, float),
    'foreignTaxPaid': (int, float),
    
    # Box 8-13
    'foreignCountry': str,
    'cashLiquidationDistributions': (int, float),
    'noncashLiquidationDistributions': (int, float),
    'fatcaFilingRequirement': bool,
    'exemptInterestDividends': (int, float),
    'specifiedPrivateActivityBondInterest': (int, float),
    
    # Box 14-16: State information (first state)
    'state': str,
    'stateIdentificationNumber': str,
    'stateTaxWithheld': (int, float),
    
    # Box 14-16: State information (second state)
    'state2': str,
    'stateIdentificationNumber2': str,
    'stateTaxWithheld2': (int, float),
}

# Required fields for Form 1099 (generic)
FORM_1099_REQUIRED_FIELDS = {
    'firstName': str,
    'lastName': str,
    'ssn': str,
    'income': (int, float),
}

# Required fields for Form W2
FORM_W2_REQUIRED_FIELDS = {
    'firstName': str,
    'lastName': str,
    'ssn': str,
    'income': (int, float),
}

# Valid filing statuses for Form 1040
VALID_FILING_STATUSES = ['single', 'married_filing_jointly', 'married_filing_separately', 
                          'head_of_household', 'qualifying_widow']

# Valid US state codes
VALID_STATE_CODES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC', 'PR', 'VI', 'GU', 'AS', 'MP'
]


# Document type to required fields mapping
DOCUMENT_TYPE_FIELDS = {
    '1040': FORM_1040_REQUIRED_FIELDS,
    '1099': FORM_1099_REQUIRED_FIELDS,
    '1099-DIV': FORM_1099_DIV_REQUIRED_FIELDS,
    'W2': FORM_W2_REQUIRED_FIELDS,
}


def validate_form_data(document_type: str, form_data: dict) -> None:
    """
    Validates form data for a specific document type.
    
    This function checks that all required fields are present, validates field
    data types, and verifies field formats (SSN, dates, numeric values, etc.).
    
    Before validation, address fields are normalized to support both legacy
    combined format ("City, State ZIP") and new separate format (city, state,
    and ZIP as separate fields).
    
    Args:
        document_type: The IRS form type (e.g., "1040")
        form_data: Dictionary of form field values
        
    Raises:
        ValidationError: If validation fails with details about missing/invalid fields
        
    Requirements:
        - 2.1: Validates that all required form fields are present
        - 2.2: Verifies that field values conform to expected data types and formats
        - 2.3: Raises ValidationError with descriptive messages for failures
        - 6.1: Support existing API requests with current field names
        - 6.2: Support new field names alongside old field names
        
    Examples:
        >>> validate_form_data('1040', {
        ...     'firstName': 'John',
        ...     'lastName': 'Doe',
        ...     'ssn': '123-45-6789',
        ...     'filingStatus': 'single',
        ...     'income': 75000
        ... })
        # No exception raised - validation passed
        
        >>> validate_form_data('1040', {'firstName': 'John'})
        ValidationError: Missing required field: lastName
    """
    # Validate document type is supported
    if document_type not in DOCUMENT_TYPE_FIELDS:
        logger.warning(f"Unsupported document type: {document_type}")
        raise ValidationError(f"Unsupported document type: {document_type}")
    
    # Validate form_data is a dictionary
    if not isinstance(form_data, dict):
        logger.warning("Form data is not a dictionary")
        raise ValidationError("Form data must be a dictionary")
    
    # Normalize address fields to support both old and new formats (Requirements 6.1, 6.2)
    # This extracts separate address components from combined format if present
    # and returns a normalized dictionary
    form_data = normalize_address_fields(form_data)
    
    # Get required fields for this document type
    required_fields = DOCUMENT_TYPE_FIELDS[document_type]
    
    # Get optional fields if this is 1099-DIV
    optional_fields = {}
    if document_type == '1099-DIV':
        optional_fields = FORM_1099_DIV_OPTIONAL_FIELDS
    
    # Check for required fields (Requirement 2.1)
    _validate_required_fields(form_data, required_fields)
    
    # Validate field data types and formats (Requirement 2.2)
    _validate_field_types_and_formats(document_type, form_data, required_fields, optional_fields)
    
    logger.debug(f"Form data validation passed for document type: {document_type}")


def _validate_required_fields(form_data: Dict[str, Any], required_fields: Dict[str, Any]) -> None:
    """
    Validates that all required fields are present in form data.
    
    Args:
        form_data: Dictionary of form field values
        required_fields: Dictionary mapping field names to expected types
        
    Raises:
        ValidationError: If any required field is missing
        
    Requirement: 2.1
    """
    missing_fields: List[str] = []
    
    for field_name in required_fields.keys():
        if field_name not in form_data:
            missing_fields.append(field_name)
    
    if missing_fields:
        error_msg = f"Missing required field{'s' if len(missing_fields) > 1 else ''}: {', '.join(missing_fields)}"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _validate_field_types_and_formats(document_type: str, form_data: Dict[str, Any], 
                                      required_fields: Dict[str, Any],
                                      optional_fields: Dict[str, Any] = None) -> None:
    """
    Validates field data types and formats.
    
    Args:
        document_type: The IRS form type (e.g., "1040")
        form_data: Dictionary of form field values
        required_fields: Dictionary mapping field names to expected types
        optional_fields: Dictionary mapping optional field names to expected types
        
    Raises:
        ValidationError: If any field has invalid type or format
        
    Requirement: 2.2
    """
    if optional_fields is None:
        optional_fields = {}
    
    # Combine required and optional fields for validation
    all_fields = {**required_fields, **optional_fields}
    
    for field_name, expected_type in all_fields.items():
        if field_name not in form_data:
            # Skip optional fields that aren't present
            if field_name in optional_fields:
                continue
            # Required fields already checked in _validate_required_fields
            continue
        
        field_value = form_data[field_name]
        
        # Check data type
        if not isinstance(field_value, expected_type):
            error_msg = f"Field '{field_name}' must be of type {_format_type_name(expected_type)}"
            logger.info(error_msg)
            raise ValidationError(error_msg)
        
        # Perform format-specific validations
        if field_name in ['ssn', 'recipientTIN'] and isinstance(field_value, str):
            _validate_ssn_format(field_value)
        elif field_name == 'payerTIN' and isinstance(field_value, str):
            _validate_tin_format(field_value)
        elif field_name == 'filingStatus':
            _validate_filing_status(field_value)
        elif field_name in ['income', 'totalOrdinaryDividends', 'qualifiedDividends',
                           'totalCapitalGainDistributions', 'unrecapturedSection1250Gain',
                           'section1202Gain', 'collectibles28Gain', 'section897OrdinaryDividends',
                           'section897CapitalGain', 'nondividendDistributions', 'federalIncomeTaxWithheld',
                           'section199ADividends', 'investmentExpenses', 'foreignTaxPaid',
                           'cashLiquidationDistributions', 'noncashLiquidationDistributions',
                           'exemptInterestDividends', 'specifiedPrivateActivityBondInterest', 
                           'stateTaxWithheld', 'stateTaxWithheld2']:
            _validate_amount(field_name, field_value)
        elif field_name in ['firstName', 'lastName', 'payerName', 'recipientName']:
            _validate_name_field(field_name, field_value)
        elif field_name in ['payerZip', 'recipientZip']:
            _validate_zip_code(field_value)
        elif field_name in ['payerPhone', 'payerTelephoneNumber']:
            _validate_phone_number(field_value)
        elif field_name in ['state', 'payerState', 'recipientState', 'state2']:
            _validate_state_code(field_value)
        elif field_name == 'calendarYear':
            _validate_year(field_value)


def _validate_ssn_format(ssn: str) -> None:
    """
    Validates SSN format (XXX-XX-XXXX).
    
    Args:
        ssn: Social Security Number string
        
    Raises:
        ValidationError: If SSN format is invalid
    """
    if not SSN_PATTERN.match(ssn):
        error_msg = "SSN must be in format XXX-XX-XXXX"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _validate_tin_format(tin: str) -> None:
    """
    Validates TIN format (XX-XXXXXXX for EIN).
    
    Args:
        tin: Taxpayer Identification Number string
        
    Raises:
        ValidationError: If TIN format is invalid
    """
    if not TIN_PATTERN.match(tin):
        error_msg = "TIN must be in format XX-XXXXXXX"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _validate_zip_code(zip_code: str) -> None:
    """
    Validates ZIP code format (XXXXX or XXXXX-XXXX).
    
    Args:
        zip_code: ZIP code string
        
    Raises:
        ValidationError: If ZIP code format is invalid
    """
    if not ZIP_PATTERN.match(zip_code):
        error_msg = "ZIP code must be in format XXXXX or XXXXX-XXXX"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _validate_phone_number(phone: str) -> None:
    """
    Validates phone number format.
    
    Accepts various formats including:
    - (555) 123-4567
    - 555-123-4567
    - +1 (555) 123-4567
    - +44 20 1234 5678
    
    Args:
        phone: Phone number string
        
    Raises:
        ValidationError: If phone number format is invalid
    """
    if not PHONE_PATTERN.match(phone):
        error_msg = "Phone number must contain only digits, spaces, hyphens, parentheses, and optional leading +"
        logger.info(error_msg)
        raise ValidationError(error_msg)
    
    # Additional validation: must have at least 10 digits
    digits_only = ''.join(c for c in phone if c.isdigit())
    if len(digits_only) < 10:
        error_msg = "Phone number must contain at least 10 digits"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _validate_state_code(state: str) -> None:
    """
    Validates state code is a valid US state/territory abbreviation.
    
    State codes must be exactly 2 uppercase letters (e.g., 'NY', 'CA').
    Lowercase codes are not accepted.
    
    Args:
        state: State code string
        
    Raises:
        ValidationError: If state code is invalid or not uppercase
    """
    # Check format first (must be 2 uppercase letters)
    if not re.match(r'^[A-Z]{2}$', state):
        error_msg = f"State code must be exactly 2 uppercase letters (e.g., 'NY', 'CA')"
        logger.info(error_msg)
        raise ValidationError(error_msg)
    
    # Then check if it's a valid state/territory
    if state not in VALID_STATE_CODES:
        error_msg = f"State must be a valid US state/territory code"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _validate_year(year: str) -> None:
    """
    Validates year format (YYYY).
    
    Args:
        year: Year string
        
    Raises:
        ValidationError: If year format is invalid
    """
    if not year.isdigit() or len(year) != 4:
        error_msg = "Calendar year must be a 4-digit year (e.g., 2025)"
        logger.info(error_msg)
        raise ValidationError(error_msg)
    
    year_int = int(year)
    if year_int < 1900 or year_int > 2100:
        error_msg = "Calendar year must be between 1900 and 2100"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _validate_filing_status(filing_status: str) -> None:
    """
    Validates filing status is one of the valid options.
    
    Args:
        filing_status: Filing status string
        
    Raises:
        ValidationError: If filing status is invalid
    """
    if filing_status not in VALID_FILING_STATUSES:
        error_msg = f"Filing status must be one of: {', '.join(VALID_FILING_STATUSES)}"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _validate_income(income: float) -> None:
    """
    Validates income is a non-negative number.
    
    Args:
        income: Income value (int or float)
        
    Raises:
        ValidationError: If income is negative
    """
    if income < 0:
        error_msg = "Income must be a non-negative number"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _validate_amount(field_name: str, amount: float) -> None:
    """
    Validates monetary amount is a non-negative number.
    
    Args:
        field_name: Name of the field (for error messages)
        amount: Amount value (int or float)
        
    Raises:
        ValidationError: If amount is negative
    """
    if amount < 0:
        error_msg = f"Field '{field_name}' must be a non-negative number"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _validate_name_field(field_name: str, value: str) -> None:
    """
    Validates name fields are non-empty after trimming.
    
    Args:
        field_name: Name of the field (for error messages)
        value: Field value
        
    Raises:
        ValidationError: If name is empty or only whitespace
    """
    if not value.strip():
        error_msg = f"Field '{field_name}' must be a non-empty string"
        logger.info(error_msg)
        raise ValidationError(error_msg)


def _format_type_name(expected_type: Any) -> str:
    """
    Formats type name for error messages.
    
    Args:
        expected_type: Type or tuple of types
        
    Returns:
        Formatted type name string
    """
    if isinstance(expected_type, tuple):
        type_names = [t.__name__ for t in expected_type]
        return ' or '.join(type_names)
    else:
        return expected_type.__name__
