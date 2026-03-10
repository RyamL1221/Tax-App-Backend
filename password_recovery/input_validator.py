"""
Input validator for password recovery.

This module validates and sanitizes API inputs for the password recovery
endpoints, including email format validation and password strength validation.
"""

import re
import logging
from typing import Optional, Tuple


logger = logging.getLogger(__name__)


class InputValidator:
    """Validates and sanitizes API inputs for password recovery."""
    
    # Email regex pattern (RFC 5322 simplified)
    # Matches most common email formats: local-part@domain
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    
    def validate_forgot_password_input(self, body: dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates /forgot-password request body.
        
        Returns:
            tuple containing:
            - is_valid: True if input is valid
            - email: Normalized email address (if valid)
            - error_message: Error description (if invalid)
            
        Checks:
        - Email field is present
        - Email matches valid format (regex)
        - Email is normalized (lowercase, trimmed)
        
        Examples:
            >>> validator = InputValidator()
            >>> is_valid, email, error = validator.validate_forgot_password_input({"email": "user@example.com"})
            >>> if is_valid:
            ...     print(f"Valid email: {email}")
            ... else:
            ...     print(f"Invalid: {error}")
        """
        # Check if body is a dictionary
        if not isinstance(body, dict):
            logger.warning("Request body is not a dictionary")
            return False, None, "Invalid request format"
        
        # Check 1: Email field is present
        if 'email' not in body:
            logger.info("Email field missing from request")
            return False, None, "Email address is required"
        
        email = body['email']
        
        # Check if email is a string
        if not isinstance(email, str):
            logger.warning("Email field is not a string")
            return False, None, "Email address must be a string"
        
        # Normalize email: trim whitespace and convert to lowercase
        email = email.strip().lower()
        
        # Check if email is empty after trimming
        if not email:
            logger.info("Email field is empty after trimming")
            return False, None, "Email address is required"
        
        # Check 2: Email matches valid format (regex)
        if not self.EMAIL_PATTERN.match(email):
            logger.info(f"Invalid email format: {email}")
            return False, None, "Please provide a valid email address"
        
        # All checks passed
        logger.debug(f"Email validation passed: {email}")
        return True, email, None
    
    def validate_reset_password_input(self, body: dict) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Validates /reset-password request body.
        
        Returns:
            tuple containing:
            - is_valid: True if input is valid
            - token: Reset token (if valid)
            - new_password: New password (if valid)
            - error_message: Error description (if invalid)
            
        Checks:
        - Token field is present and non-empty
        - new_password field is present
        - Password meets minimum requirements:
          * At least 8 characters
          * Contains uppercase and lowercase
          * Contains at least one digit
          * Contains at least one special character
        
        Examples:
            >>> validator = InputValidator()
            >>> is_valid, token, password, error = validator.validate_reset_password_input({
            ...     "token": "abc123",
            ...     "new_password": "SecurePass123!"
            ... })
            >>> if is_valid:
            ...     print("Valid input")
            ... else:
            ...     print(f"Invalid: {error}")
        """
        # Check if body is a dictionary
        if not isinstance(body, dict):
            logger.warning("Request body is not a dictionary")
            return False, None, None, "Invalid request format"
        
        # Check 1: Token field is present
        if 'token' not in body:
            logger.info("Token field missing from request")
            return False, None, None, "Reset token is required"
        
        # Check 2: new_password field is present
        if 'new_password' not in body:
            logger.info("new_password field missing from request")
            return False, None, None, "New password is required"
        
        token = body['token']
        
        # Check if token is a string
        if not isinstance(token, str):
            logger.warning("Token field is not a string")
            return False, None, None, "Reset token must be a string"
        
        # Trim whitespace from token
        token = token.strip()
        
        # Check if token is empty after trimming
        if not token:
            logger.info("Token field is empty after trimming")
            return False, None, None, "Reset token is required"
        
        new_password = body['new_password']
        
        # Check if password is a string
        if not isinstance(new_password, str):
            logger.warning("new_password field is not a string")
            return False, None, None, "New password must be a string"
        
        # Check 3: Password meets minimum requirements
        is_valid_password, password_error = self._validate_password_strength(new_password)
        if not is_valid_password:
            logger.info(f"Password validation failed: {password_error}")
            return False, None, None, password_error
        
        # All checks passed
        logger.debug("Reset password input validation passed")
        return True, token, new_password, None
    
    def _validate_password_strength(self, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validates password strength requirements.
        
        Args:
            password: The password to validate
            
        Returns:
            tuple containing:
            - is_valid: True if password meets requirements
            - error_message: Error description (if invalid)
            
        Requirements:
        - At least 8 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains at least one digit
        - Contains at least one special character
        """
        # Check minimum length
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for digit
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        # Check for special character
        # Special characters: any non-alphanumeric character
        if not re.search(r'[^a-zA-Z0-9]', password):
            return False, "Password must contain at least one special character"
        
        # All requirements met
        return True, None
