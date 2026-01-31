"""
Request validator for user registration endpoint.

This module provides validation functions for registration data including
email format (RFC 5322), password strength, and name validation.
"""

import re
from email_validator import validate_email as validate_email_format, EmailNotValidError


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_email(email: str) -> bool:
    """
    Validates email format against RFC 5322.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid
        
    Raises:
        ValidationError: If email format is invalid
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email must be a non-empty string")
    
    try:
        # email-validator library validates against RFC 5322
        validate_email_format(email, check_deliverability=False)
        return True
    except EmailNotValidError as e:
        raise ValidationError(f"Invalid email format: {str(e)}")


def validate_password_strength(password: str) -> bool:
    """
    Validates password meets strength requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        
    Returns:
        True if password meets all requirements
        
    Raises:
        ValidationError: If password fails strength requirements
    """
    if not password or not isinstance(password, str):
        raise ValidationError("Password must be a non-empty string")
    
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit")
    
    # Special characters: any non-alphanumeric character
    if not re.search(r'[^A-Za-z0-9]', password):
        raise ValidationError("Password must contain at least one special character")
    
    return True


def validate_name(name: str) -> bool:
    """
    Validates name is non-empty after trimming whitespace.
    
    Args:
        name: Name to validate
        
    Returns:
        True if name is valid
        
    Raises:
        ValidationError: If name is empty or only whitespace
    """
    if not isinstance(name, str):
        raise ValidationError("Name must be a string")
    
    if not name.strip():
        raise ValidationError("Name must be a non-empty string after trimming whitespace")
    
    return True


def validate_registration_data(email: str, name: str, password: str) -> None:
    """
    Validates registration data by orchestrating all validation functions.
    
    Args:
        email: User's email address
        name: User's name
        password: User's password
        
    Raises:
        ValidationError: If any validation rule fails
    """
    # Validate in order: email, name, password
    # This ensures consistent error reporting
    validate_email(email)
    validate_name(name)
    validate_password_strength(password)
