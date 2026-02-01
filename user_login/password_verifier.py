"""
Password verification module for user login.

This module provides secure password verification using bcrypt's constant-time
comparison to prevent timing attacks.
"""

import bcrypt


class InvalidCredentialsError(Exception):
    """Raised when password verification fails."""
    pass


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a password against a bcrypt hash.
    
    Uses bcrypt.checkpw() which provides constant-time comparison to prevent
    timing attacks. This is critical for security as it ensures that attackers
    cannot determine if a password is partially correct by measuring response times.
    
    Args:
        password: Plaintext password to verify
        password_hash: Bcrypt hash to verify against (should start with $2b$12$)
        
    Returns:
        True if password matches hash
        
    Raises:
        InvalidCredentialsError: If verification fails (password doesn't match)
        
    Example:
        >>> password = "SecurePass123!"
        >>> password_hash = "$2b$12$..."  # bcrypt hash
        >>> verify_password(password, password_hash)
        True
    """
    try:
        # Convert strings to bytes for bcrypt verification
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        
        # Use bcrypt.checkpw for constant-time comparison
        # This prevents timing attacks by always taking the same amount of time
        # regardless of where the password differs from the hash
        is_valid = bcrypt.checkpw(password_bytes, hash_bytes)
        
        if not is_valid:
            raise InvalidCredentialsError("Password does not match")
        
        return True
        
    except InvalidCredentialsError:
        # Re-raise our custom exception
        raise
    except Exception as e:
        # Handle any bcrypt errors (e.g., invalid hash format)
        # Wrap in InvalidCredentialsError to maintain consistent error handling
        raise InvalidCredentialsError(f"Password verification failed: {str(e)}")
