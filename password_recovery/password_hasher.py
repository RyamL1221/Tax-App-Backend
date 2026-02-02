"""
Password hasher for password recovery.

This module handles secure password hashing using bcrypt with a work factor of 12.
"""

import logging
import bcrypt


logger = logging.getLogger(__name__)


class PasswordHasher:
    """
    Password hasher using bcrypt.
    
    Provides secure password hashing and verification using bcrypt with
    a work factor of 12 for security.
    """
    
    # Work factor for bcrypt (number of rounds)
    # 12 rounds provides a good balance between security and performance
    WORK_FACTOR = 12
    
    def hash_password(self, plaintext_password: str) -> str:
        """
        Hashes a password using bcrypt.
        
        Args:
            plaintext_password: The password to hash
            
        Returns:
            Bcrypt hash string
            
        Uses work factor of 12 for security.
        
        Note: Bcrypt has a 72-byte limit. Passwords longer than 72 bytes
        when encoded as UTF-8 will be truncated.
        
        Examples:
            >>> hasher = PasswordHasher()
            >>> hashed = hasher.hash_password("MySecurePassword123!")
            >>> print(f"Hashed password: {hashed}")
        """
        try:
            # Convert password to bytes
            password_bytes = plaintext_password.encode('utf-8')
            
            # Bcrypt has a 72-byte limit, truncate if necessary
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
                logger.debug("Password truncated to 72 bytes for bcrypt")
            
            # Generate salt and hash
            salt = bcrypt.gensalt(rounds=self.WORK_FACTOR)
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Return as string
            hashed_str = hashed.decode('utf-8')
            
            logger.debug("Password hashed successfully")
            return hashed_str
            
        except Exception as e:
            logger.error(f"Error hashing password: {type(e).__name__}")
            # Don't log the actual password for security
            raise
    
    def verify_password(self, plaintext_password: str, hashed_password: str) -> bool:
        """
        Verifies a password against a hash.
        
        Args:
            plaintext_password: Password to verify
            hashed_password: Stored bcrypt hash
            
        Returns:
            True if password matches
            
        Note: Bcrypt has a 72-byte limit. Passwords longer than 72 bytes
        when encoded as UTF-8 will be truncated for verification.
            
        Examples:
            >>> hasher = PasswordHasher()
            >>> hashed = hasher.hash_password("MyPassword123!")
            >>> is_valid = hasher.verify_password("MyPassword123!", hashed)
            >>> print(f"Password valid: {is_valid}")
        """
        try:
            # Convert to bytes
            password_bytes = plaintext_password.encode('utf-8')
            
            # Bcrypt has a 72-byte limit, truncate if necessary
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
                logger.debug("Password truncated to 72 bytes for bcrypt verification")
            
            hashed_bytes = hashed_password.encode('utf-8')
            
            # Verify password
            is_valid = bcrypt.checkpw(password_bytes, hashed_bytes)
            
            logger.debug(f"Password verification: {'success' if is_valid else 'failed'}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying password: {type(e).__name__}")
            # On error, reject the password for security
            return False
    
    def get_work_factor(self) -> int:
        """
        Gets the current work factor.
        
        Returns:
            The bcrypt work factor (number of rounds)
            
        Examples:
            >>> hasher = PasswordHasher()
            >>> work_factor = hasher.get_work_factor()
            >>> print(f"Work factor: {work_factor}")
        """
        return self.WORK_FACTOR
