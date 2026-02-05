"""
Address Combiner Module for Tax Document Generation

This module provides functions to combine individual address components into
formatted multi-line strings suitable for PDF form fields. The IRS 1099-DIV
form uses single multi-line text fields for complete address blocks, requiring
all address components to be concatenated before PDF generation.

Key Functions:
- combine_payer_address(): Combines payer address components into IRS-compliant format
- combine_recipient_address(): Combines recipient city/state/ZIP components
- combine_address_fields(): Processes form data to create combined address fields

Requirements Addressed:
- 4.1: Address combination logic in separate module
- 4.3: Recipient address combination function
- 9.1: Separate module for reusability and maintainability

Usage:
    from address_combiner import combine_address_fields
    
    # Process form data to combine address components
    form_data = {
        "payerName": "Example Corp",
        "payerStreetAddress": "123 Main St",
        "payerCity": "New York",
        "payerState": "NY",
        "payerZip": "10001"
    }
    
    # Combine address fields
    form_data = combine_address_fields(form_data)
    
    # Result includes:
    # form_data["payerAddressBlock"] = "Example Corp\\n123 Main St\\nNew York, NY 10001"
"""

import logging
from typing import Any, Dict, Optional

# Configure logger
logger = logging.getLogger(__name__)

def combine_payer_address(
    payer_name: Optional[str] = None,
    payer_street_address: Optional[str] = None,
    payer_city: Optional[str] = None,
    payer_state: Optional[str] = None,
    payer_zip: Optional[str] = None,
    payer_country: Optional[str] = None,
    payer_telephone_number: Optional[str] = None
) -> str:
    """
    Combine payer address components into IRS-compliant multi-line format.
    
    This function takes individual payer address components and combines them into
    a single multi-line string suitable for the 1099-DIV PDF field f2_2. The format
    follows IRS specifications for payer address blocks.
    
    Format:
        {payerName}
        {payerStreetAddress}
        {payerCity}, {payerState} {payerZip}
        {payerCountry}
        {payerTelephoneNumber}
    
    Empty or None components are omitted to avoid blank lines in the PDF.
    The city/state/ZIP line is formatted with proper punctuation and spacing.
    
    Args:
        payer_name: Payer's name (typically required, but function handles None)
        payer_street_address: Street address (e.g., "123 Main Street")
        payer_city: City name (e.g., "New York")
        payer_state: Two-letter state code (e.g., "NY")
        payer_zip: ZIP or postal code (e.g., "10001" or "10001-1234")
        payer_country: Country name (e.g., "USA", "Canada") - omit for USA
        payer_telephone_number: Phone number (e.g., "(555) 123-4567")
        
    Returns:
        Formatted multi-line address string with empty components omitted.
        Returns empty string if no components are provided.
        
    Examples:
        >>> combine_payer_address(
        ...     payer_name="Example Investment Corp",
        ...     payer_street_address="123 Wall Street",
        ...     payer_city="New York",
        ...     payer_state="NY",
        ...     payer_zip="10005",
        ...     payer_telephone_number="(555) 123-4567"
        ... )
        'Example Investment Corp\\n123 Wall Street\\nNew York, NY 10005\\n(555) 123-4567'
        
        >>> combine_payer_address(
        ...     payer_name="Example Corp",
        ...     payer_city="Boston",
        ...     payer_state="MA"
        ... )
        'Example Corp\\nBoston, MA'
        
        >>> combine_payer_address(
        ...     payer_name="International Corp",
        ...     payer_street_address="456 Main St",
        ...     payer_city="Toronto",
        ...     payer_state="ON",
        ...     payer_zip="M5H 2N2",
        ...     payer_country="Canada"
        ... )
        'International Corp\\n456 Main St\\nToronto, ON M5H 2N2\\nCanada'
    
    Requirements:
        - 1.2: All payer address components are combined into a single multi-line string
        - 1.3: The combined address block is formatted according to IRS specifications
        - 1.5: Each address component appears on its own line in the PDF
        - 1.6: Empty/missing components are omitted from the combined address (no blank lines)
        - 4.1: Function takes individual address components as parameters
        - 4.2: Follows IRS formatting guidelines for payer address blocks
    """
    # Build address line by line, skipping empty/None components
    address_lines = []
    
    # Line 1: Payer name
    if payer_name:
        address_lines.append(payer_name)
    else:
        # Log warning if payer name is missing (it's typically required)
        logger.warning("Payer name is missing in address combination")
    
    # Line 2: Street address
    if payer_street_address:
        address_lines.append(payer_street_address)
    
    # Line 3: City, State ZIP (combined on one line with proper formatting)
    # Format: "City, State ZIP" (comma only between city and state)
    # If state is missing: "City ZIP" (no comma)
    city_state_zip_line = []
    
    if payer_city:
        city_state_zip_line.append(payer_city)
    
    # Add comma only if we have both city and state
    if payer_city and payer_state:
        # Format: "City, State ZIP"
        state_zip_parts = [payer_state]
        if payer_zip:
            state_zip_parts.append(payer_zip)
        city_state_zip_line.append(", " + " ".join(state_zip_parts))
    elif payer_state:
        # Format: "State ZIP" (no city)
        state_zip_parts = [payer_state]
        if payer_zip:
            state_zip_parts.append(payer_zip)
        city_state_zip_line.append(" ".join(state_zip_parts))
    elif payer_zip:
        # Format: "City ZIP" or just "ZIP" (no state)
        city_state_zip_line.append(" " + payer_zip if payer_city else payer_zip)
    
    # Join the parts (will be just one string due to our formatting above)
    if city_state_zip_line:
        address_lines.append("".join(city_state_zip_line))
    
    # Line 4: Country (if provided and not USA)
    if payer_country and payer_country.upper() not in ["USA", "US", "UNITED STATES"]:
        address_lines.append(payer_country)
    
    # Line 5: Telephone number
    if payer_telephone_number:
        address_lines.append(payer_telephone_number)
    
    # Join all lines with newline characters
    combined_address = "\n".join(address_lines)
    
    logger.debug(f"Combined payer address: {len(address_lines)} lines")
    
    return combined_address


def combine_recipient_address(
    recipient_city: Optional[str] = None,
    recipient_state: Optional[str] = None,
    recipient_zip: Optional[str] = None,
    recipient_country: Optional[str] = None
) -> str:
    """
    Combine recipient address components for city/state/ZIP field.
    
    This function takes recipient city, state, ZIP, and country components and
    combines them into a formatted string suitable for the 1099-DIV PDF field f2_7.
    The format follows IRS specifications for recipient address information.
    
    Format:
        {recipientCity}, {recipientState} {recipientZip}
        {recipientCountry}
    
    The city/state/ZIP are combined on the first line with proper punctuation.
    If a country is provided and it's not "USA", it appears on a second line.
    Empty or None components are omitted to avoid blank lines.
    
    Args:
        recipient_city: City name (e.g., "Los Angeles")
        recipient_state: Two-letter state code (e.g., "CA")
        recipient_zip: ZIP or postal code (e.g., "90001" or "90001-1234")
        recipient_country: Country name (e.g., "USA", "Canada") - omit for USA
        
    Returns:
        Formatted address string (single or multi-line) with empty components omitted.
        Returns empty string if no components are provided.
        
    Examples:
        >>> combine_recipient_address(
        ...     recipient_city="Los Angeles",
        ...     recipient_state="CA",
        ...     recipient_zip="90001"
        ... )
        'Los Angeles, CA 90001'
        
        >>> combine_recipient_address(
        ...     recipient_city="Boston",
        ...     recipient_state="MA"
        ... )
        'Boston, MA'
        
        >>> combine_recipient_address(
        ...     recipient_city="Toronto",
        ...     recipient_state="ON",
        ...     recipient_zip="M5H 2N2",
        ...     recipient_country="Canada"
        ... )
        'Toronto, ON M5H 2N2\\nCanada'
        
        >>> combine_recipient_address(
        ...     recipient_zip="10001"
        ... )
        '10001'
        
        >>> combine_recipient_address()
        ''
    
    Requirements:
        - 3.1: Recipient address components are combined into field f2_7
        - 3.3: Combined recipient address follows same formatting rules as payer address
        - 3.4: Empty/missing recipient components are omitted (no blank lines)
        - 4.3: Function takes city, state, ZIP, country as parameters
        - 4.4: Returns formatted single-line or multi-line string
    """
    # Build address line by line
    address_lines = []
    
    # Line 1: City, State ZIP (combined on one line with proper formatting)
    # Format: "City, State ZIP" (comma only between city and state)
    # If state is missing: "City ZIP" (no comma)
    city_state_zip_line = []
    
    if recipient_city:
        city_state_zip_line.append(recipient_city)
    
    # Add comma only if we have both city and state
    if recipient_city and recipient_state:
        # Format: "City, State ZIP"
        state_zip_parts = [recipient_state]
        if recipient_zip:
            state_zip_parts.append(recipient_zip)
        city_state_zip_line.append(", " + " ".join(state_zip_parts))
    elif recipient_state:
        # Format: "State ZIP" (no city)
        state_zip_parts = [recipient_state]
        if recipient_zip:
            state_zip_parts.append(recipient_zip)
        city_state_zip_line.append(" ".join(state_zip_parts))
    elif recipient_zip:
        # Format: "City ZIP" or just "ZIP" (no state)
        city_state_zip_line.append(" " + recipient_zip if recipient_city else recipient_zip)
    
    # Join the parts (will be just one string due to our formatting above)
    if city_state_zip_line:
        address_lines.append("".join(city_state_zip_line))
    
    # Line 2: Country (if provided and not USA)
    if recipient_country and recipient_country.upper() not in ["USA", "US", "UNITED STATES"]:
        address_lines.append(recipient_country)
    
    # Join all lines with newline characters
    combined_address = "\n".join(address_lines)
    
    logger.debug(f"Combined recipient address: {len(address_lines)} lines")
    
    return combined_address


def combine_address_fields(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process form data to combine address components into PDF-ready fields.
    
    This function orchestrates the address combination process for both payer and
    recipient addresses. It extracts individual address components from the form data,
    combines them into multi-line blocks suitable for PDF fields, adds the combined
    fields to the form data, and removes the individual component fields (which are
    API-only and not directly mapped to PDF fields).
    
    Processing Steps:
        1. Extract payer address components from form_data
        2. Call combine_payer_address() to create payerAddressBlock
        3. Extract recipient address components from form_data
        4. Call combine_recipient_address() to create recipientCityStateZip
        5. Add combined fields to form_data
        6. Remove individual component fields (API-only fields)
        7. Keep fields that have their own PDF mappings (payerName, recipientName, recipientStreetAddress)
    
    Args:
        form_data: Dictionary with API field names and values. Expected to contain
                   address component fields like payerCity, payerState, payerZip, etc.
                   This dictionary is modified in place.
        
    Returns:
        Modified form_data dictionary with:
        - payerAddressBlock: Combined payer address (if components exist)
        - recipientCityStateZip: Combined recipient address (if components exist)
        - Individual component fields removed
        - Other fields preserved unchanged
        
    Examples:
        >>> form_data = {
        ...     "payerName": "Example Corp",
        ...     "payerStreetAddress": "123 Main St",
        ...     "payerCity": "New York",
        ...     "payerState": "NY",
        ...     "payerZip": "10001",
        ...     "payerTelephoneNumber": "(555) 123-4567",
        ...     "recipientName": "John Doe",
        ...     "recipientStreetAddress": "456 Oak Ave",
        ...     "recipientCity": "Los Angeles",
        ...     "recipientState": "CA",
        ...     "recipientZip": "90001"
        ... }
        >>> result = combine_address_fields(form_data)
        >>> "payerAddressBlock" in result
        True
        >>> "recipientCityStateZip" in result
        True
        >>> "payerCity" in result  # Individual component removed
        False
        >>> "payerName" in result  # Kept (has its own PDF field)
        True
        
        >>> # Handles missing components gracefully
        >>> form_data = {"payerName": "Example Corp"}
        >>> result = combine_address_fields(form_data)
        >>> result["payerAddressBlock"]
        'Example Corp'
    
    Field Handling:
        Fields that are COMBINED and REMOVED:
        - Payer: payerStreetAddress, payerCity, payerState, payerZip, 
                 payerCountry, payerTelephoneNumber
        - Recipient: recipientCity, recipientState, recipientZip, recipientCountry
        
        Fields that are KEPT (have their own PDF mappings):
        - payerName (maps to f2_2 for backward compatibility)
        - recipientName (maps to f2_5)
        - recipientStreetAddress (maps to f2_6)
    
    Requirements:
        - 1.2: All payer address components are combined into a single multi-line string
        - 1.4: The combined address is filled into PDF field f2_2 for all copies
        - 3.1: Recipient address components are combined into field f2_7
        - 5.1: Modify generate_document() to combine address fields before field mapping
        - 5.2: After address normalization, combine payer address components into payerAddressBlock
        - 5.3: After address normalization, combine recipient address components into recipientCityStateZip
    """
    logger.info("Starting address field combination")
    
    # Step 1: Extract payer address components from form_data
    payer_name = form_data.get("payerName")
    payer_street_address = form_data.get("payerStreetAddress")
    payer_city = form_data.get("payerCity")
    payer_state = form_data.get("payerState")
    payer_zip = form_data.get("payerZip")
    payer_country = form_data.get("payerCountry")
    payer_telephone_number = form_data.get("payerTelephoneNumber")
    
    # Step 2: Combine payer address components
    payer_address_block = combine_payer_address(
        payer_name=payer_name,
        payer_street_address=payer_street_address,
        payer_city=payer_city,
        payer_state=payer_state,
        payer_zip=payer_zip,
        payer_country=payer_country,
        payer_telephone_number=payer_telephone_number
    )
    
    # Step 3: Extract recipient address components from form_data
    recipient_city = form_data.get("recipientCity")
    recipient_state = form_data.get("recipientState")
    recipient_zip = form_data.get("recipientZip")
    recipient_country = form_data.get("recipientCountry")
    
    # Step 4: Combine recipient address components
    recipient_city_state_zip = combine_recipient_address(
        recipient_city=recipient_city,
        recipient_state=recipient_state,
        recipient_zip=recipient_zip,
        recipient_country=recipient_country
    )
    
    # Step 5: Add combined fields to form_data if components exist
    if payer_address_block:
        form_data["payerAddressBlock"] = payer_address_block
        logger.info(f"Added payerAddressBlock with {len(payer_address_block.split(chr(10)))} lines")
    
    if recipient_city_state_zip:
        form_data["recipientCityStateZip"] = recipient_city_state_zip
        logger.info(f"Added recipientCityStateZip: {recipient_city_state_zip[:50]}...")
    
    # Step 6: Remove individual component fields from form_data
    # These are API-only fields that are not directly mapped to PDF fields
    payer_components_to_remove = [
        "payerStreetAddress",
        "payerCity",
        "payerState",
        "payerZip",
        "payerCountry",
        "payerTelephoneNumber"
    ]
    
    recipient_components_to_remove = [
        "recipientCity",
        "recipientState",
        "recipientZip",
        "recipientCountry"
    ]
    
    removed_count = 0
    for field in payer_components_to_remove + recipient_components_to_remove:
        if field in form_data:
            del form_data[field]
            removed_count += 1
    
    logger.info(f"Removed {removed_count} individual address component fields")
    
    # Step 7: Keep fields that have their own PDF mappings
    # - payerName: kept for backward compatibility (maps to f2_2)
    # - recipientName: kept (maps to f2_5)
    # - recipientStreetAddress: kept (maps to f2_6)
    # These fields are NOT removed from form_data
    
    logger.info("Address field combination complete")
    
    return form_data
