"""
Request validator for user login endpoint.

This module provides validation functions for login data including
email format (RFC 5322) and password presence validation.

Note: Login validation is simpler than registration validation. We only check
format/presence, not strength requirements, since the password was already
validated during registration.
"""

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


def validate_password_present(password: str) -> bool:
    """
    Validates password is non-empty.
    
    For login, we only check that a password is provided, not its strength,
    since password strength was already validated during registration.
    
    Args:
        password: Password to validate
        
    Returns:
        True if password is present
        
    Raises:
        ValidationError: If password is empty or not a string
    """
    if not isinstance(password, str):
        raise ValidationError("Password must be a string")
    
    if not password:
        raise ValidationError("Password must be a non-empty string")
    
    return True


def validate_login_data(email: str, password: str) -> None:
    """
    Validates login request data.
    
    Args:
        email: User's email address
        password: User's password
        
    Raises:
        ValidationError: If any validation rule fails
    """
    # Validate in order: email, password
    # This ensures consistent error reporting
    validate_email(email)
    validate_password_present(password)
