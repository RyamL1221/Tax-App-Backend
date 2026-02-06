"""
Address normalization for tax document generation.

This module provides functions to normalize address fields, supporting both
legacy combined address format ("City, State ZIP") and new separate format
(city, state, and ZIP as separate fields).

Requirements: 6.1, 6.2
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple


logger = logging.getLogger(__name__)


# Pattern to match combined address format: "City, State ZIP"
# Examples: "New York, NY 10001", "Los Angeles, CA 90001-1234"
COMBINED_ADDRESS_PATTERN = re.compile(
    r'^(.+?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$'
)


def normalize_address_fields(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize address fields to support both old and new formats.
    
    This function handles backward compatibility by parsing combined address
    formats and extracting separate components. It supports both payer and
    recipient address fields.
    
    Old format: payerCity = "New York, NY 10001"
    New format: payerCity = "New York", payerState = "NY", payerZip = "10001"
    
    Args:
        form_data: Raw form data from API request
        
    Returns:
        Normalized form data with separate address components
        
    Requirements:
        - 6.1: Support existing API requests with current field names
        - 6.2: Support new field names alongside old field names
        
    Examples:
        >>> data = {"payerCity": "New York, NY 10001"}
        >>> normalized = normalize_address_fields(data)
        >>> normalized["payerCity"]
        'New York'
        >>> normalized["payerState"]
        'NY'
        >>> normalized["payerZip"]
        '10001'
        
        >>> data = {"payerCity": "New York", "payerState": "NY", "payerZip": "10001"}
        >>> normalized = normalize_address_fields(data)
        >>> normalized["payerCity"]
        'New York'
    """
    normalized = form_data.copy()
    
    # Normalize payer address fields
    normalized = _normalize_address_group(
        normalized,
        city_field="payerCity",
        state_field="payerState",
        zip_field="payerZip"
    )
    
    # Normalize recipient address fields
    normalized = _normalize_address_group(
        normalized,
        city_field="recipientCity",
        state_field="recipientState",
        zip_field="recipientZip"
    )
    
    return normalized


def _normalize_address_group(
    form_data: Dict[str, Any],
    city_field: str,
    state_field: str,
    zip_field: str
) -> Dict[str, Any]:
    """
    Normalize a group of address fields (city, state, ZIP).
    
    Args:
        form_data: Form data dictionary
        city_field: Name of the city field (e.g., "payerCity")
        state_field: Name of the state field (e.g., "payerState")
        zip_field: Name of the ZIP field (e.g., "payerZip")
        
    Returns:
        Form data with normalized address fields
    """
    # Check if city field exists and contains combined format
    if city_field not in form_data:
        return form_data
    
    city_value = form_data[city_field]
    
    # Only process string values
    if not isinstance(city_value, str):
        return form_data
    
    # Try to parse combined address format
    parsed = parse_combined_address(city_value)
    
    if parsed is not None:
        city, state, zip_code = parsed
        
        # Log deprecation warning
        logger.warning(
            f"Deprecated field format detected: {city_field} contains combined address "
            f"'{city_value}'. Please use separate {city_field}, {state_field}, and "
            f"{zip_field} fields. Combined format will be removed in a future version."
        )
        
        # Only set if not already provided (explicit values take precedence)
        if state_field not in form_data:
            form_data[state_field] = state
            logger.debug(f"Extracted {state_field} = '{state}' from combined address")
        
        if zip_field not in form_data:
            form_data[zip_field] = zip_code
            logger.debug(f"Extracted {zip_field} = '{zip_code}' from combined address")
        
        # Update city to just the city name
        form_data[city_field] = city
        logger.debug(f"Normalized {city_field} = '{city}' from combined address")
    
    return form_data


def parse_combined_address(address: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse combined address format into separate components.
    
    Parses addresses in the format "City, State ZIP" where:
    - City can contain spaces and multiple words
    - State is a 2-letter code
    - ZIP is 5 digits or 5+4 format (XXXXX-XXXX)
    
    Args:
        address: Combined address string
        
    Returns:
        Tuple of (city, state, zip_code) if parsing succeeds, None otherwise
        
    Examples:
        >>> parse_combined_address("New York, NY 10001")
        ('New York', 'NY', '10001')
        
        >>> parse_combined_address("Los Angeles, CA 90001-1234")
        ('Los Angeles', 'CA', '90001-1234')
        
        >>> parse_combined_address("San Francisco, CA")
        None
        
        >>> parse_combined_address("New York")
        None
    """
    if not isinstance(address, str):
        return None
    
    # Try to match the combined address pattern
    match = COMBINED_ADDRESS_PATTERN.match(address.strip())
    
    if match:
        city = match.group(1).strip()
        state = match.group(2).strip()
        zip_code = match.group(3).strip()
        return (city, state, zip_code)
    
    return None
