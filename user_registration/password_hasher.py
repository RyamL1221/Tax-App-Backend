"""
Password hashing module using bcrypt.

This module provides secure password hashing functionality using the bcrypt
algorithm with a work factor of 12 for the user registration endpoint.
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt with a work factor of 12.
    
    Args:
        password: Plaintext password string to hash
        
    Returns:
        Bcrypt hash as a UTF-8 string suitable for DynamoDB storage
        
    Raises:
        Exception: If hashing fails due to encoding or bcrypt errors
        
    Examples:
        >>> hash_result = hash_password("SecurePass123!")
        >>> hash_result.startswith("$2b$12$")
        True
    """
    try:
        # Encode the password string to bytes (required by bcrypt)
        password_bytes = password.encode('utf-8')
        
        # Generate salt and hash with work factor of 12
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password_bytes, salt)
        
        # Decode the hash bytes back to UTF-8 string for DynamoDB storage
        return password_hash.decode('utf-8')
    except Exception as e:
        # Re-raise with context about the hashing operation
        raise Exception(f"Password hashing failed: {str(e)}") from e
