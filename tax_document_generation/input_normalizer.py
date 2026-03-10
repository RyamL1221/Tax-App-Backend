"""
Input normalization for flexible form data formatting.

This module provides normalization functions that transform flexible input
formats into standardized formats required for PDF generation. It operates
between validation and field mapping to ensure backward compatibility while
providing a better developer experience.

Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.2, 4.1-4.5, 7.1-7.5, 8.1-8.2
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import logging

from field_mappings.field_metadata import FIELD_METADATA

logger = logging.getLogger()


@dataclass
class NormalizationResult:
    """
    Result of input normalization operation.
    
    Attributes:
        normalized_data: Form data with normalized values
        changes: List of (field_name, original_value, normalized_value) tuples
    
    Requirements: 4.1, 4.2, 4.3
    """
    normalized_data: Dict[str, Any]
    changes: List[Tuple[str, str, str]]


def normalize_decimal_field(value: Any) -> str:
    """
    Normalize a decimal/currency field to two decimal places.
    
    This function accepts flexible input formats (integers, floats, strings)
    and converts them to a standardized string format with exactly two
    decimal places. Values are rounded to two decimal places if necessary.
    
    Args:
        value: Input value (string, int, or float)
        
    Returns:
        String with exactly two decimal places (e.g., "1000.00")
        
    Examples:
        >>> normalize_decimal_field("1000")
        "1000.00"
        >>> normalize_decimal_field(1000)
        "1000.00"
        >>> normalize_decimal_field("1000.5")
        "1000.50"
        >>> normalize_decimal_field("1000.123")
        "1000.12"
        >>> normalize_decimal_field("1000.00")
        "1000.00"
        
    Raises:
        ValueError: If value cannot be converted to a decimal
        
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    try:
        # Convert to float first to handle all numeric types
        if isinstance(value, str):
            # Remove any whitespace
            value = value.strip()
        
        numeric_value = float(value)
        
        # Format to exactly two decimal places
        # This handles rounding automatically
        return f"{numeric_value:.2f}"
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Cannot normalize decimal value '{value}': {str(e)}")


def normalize_tin_field(value: str, tin_type: str) -> str:
    """
    Normalize a TIN field by adding hyphens if missing.
    
    This function accepts TINs with or without hyphens and ensures they
    are formatted correctly according to the specified type (SSN or EIN).
    
    Args:
        value: TIN value (9 digits, with or without hyphens)
        tin_type: "SSN" or "EIN"
        
    Returns:
        Formatted TIN with hyphens
        
    Examples:
        >>> normalize_tin_field("123456789", "EIN")
        "12-3456789"
        >>> normalize_tin_field("12-3456789", "EIN")
        "12-3456789"
        >>> normalize_tin_field("987654321", "SSN")
        "987-65-4321"
        >>> normalize_tin_field("987-65-4321", "SSN")
        "987-65-4321"
        
    Raises:
        ValueError: If TIN format is invalid or tin_type is unknown
        
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    try:
        # Remove any existing hyphens and whitespace
        clean_tin = value.replace("-", "").replace(" ", "").strip()
        
        # Validate that we have exactly 9 digits
        if not clean_tin.isdigit() or len(clean_tin) != 9:
            raise ValueError(f"TIN must be exactly 9 digits, got: {value}")
        
        # Format based on type
        if tin_type == "EIN":
            # EIN format: XX-XXXXXXX
            return f"{clean_tin[:2]}-{clean_tin[2:]}"
        elif tin_type == "SSN":
            # SSN format: XXX-XX-XXXX
            return f"{clean_tin[:3]}-{clean_tin[3:5]}-{clean_tin[5:]}"
        else:
            raise ValueError(f"Unknown TIN type: {tin_type}. Must be 'SSN' or 'EIN'")
            
    except (AttributeError, IndexError) as e:
        raise ValueError(f"Cannot normalize TIN value '{value}': {str(e)}")


def normalize_form_data(
    form_data: Dict[str, Any],
    document_type: str
) -> NormalizationResult:
    """
    Normalize form data based on field metadata.
    
    This function iterates through all fields in the form data and applies
    normalization rules based on the field metadata configuration. It tracks
    all changes made during normalization for logging purposes.
    
    Args:
        form_data: Validated form data from request
        document_type: Type of document (e.g., "1099-DIV")
        
    Returns:
        NormalizationResult with normalized data and change log
        
    Raises:
        ValueError: If normalization fails for a field
        
    Requirements: 1.1-1.5, 2.1-2.5, 3.1, 3.2, 4.1, 4.2, 4.3, 7.1, 7.2, 8.1, 8.2
    """
    # Create a copy of form data to avoid modifying the original
    normalized_data = form_data.copy()
    changes: List[Tuple[str, str, str]] = []
    
    # Iterate through all fields in the form data
    for field_name, field_value in form_data.items():
        # Skip None values
        if field_value is None:
            continue
        
        # Get metadata for this field
        metadata = FIELD_METADATA.get(field_name)
        if not metadata:
            # Field not in metadata, skip normalization
            continue
        
        # Get normalization type
        normalization_type = metadata.get("normalization_type")
        if not normalization_type:
            # No normalization needed for this field
            continue
        
        try:
            # Apply normalization based on type
            if normalization_type == "decimal":
                normalized_value = normalize_decimal_field(field_value)
                
                # Only record change if value actually changed
                if str(field_value) != normalized_value:
                    changes.append((field_name, str(field_value), normalized_value))
                    normalized_data[field_name] = normalized_value
                    
            elif normalization_type == "tin":
                tin_format = metadata.get("tin_format")
                if not tin_format:
                    logger.warning(f"Field {field_name} has normalization_type='tin' but no tin_format specified")
                    continue
                
                normalized_value = normalize_tin_field(str(field_value), tin_format)
                
                # Only record change if value actually changed
                if str(field_value) != normalized_value:
                    changes.append((field_name, str(field_value), normalized_value))
                    normalized_data[field_name] = normalized_value
                    
        except ValueError as e:
            # Log the error and re-raise with more context
            logger.error(f"Failed to normalize field {field_name}: {str(e)}")
            raise ValueError(f"Normalization failed for field {field_name}: {str(e)}")
    
    return NormalizationResult(
        normalized_data=normalized_data,
        changes=changes
    )
