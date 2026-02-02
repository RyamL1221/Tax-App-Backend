"""
Token validator for password recovery.

This module validates reset tokens by checking their existence in the database,
verifying they haven't expired, and ensuring they haven't been used.
"""

import base64
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from user_repository import get_reset_token, DatabaseError


logger = logging.getLogger(__name__)


class TokenValidator:
    """Validates reset tokens for password recovery."""
    
    def _get_token_hash(self, plaintext_token: str) -> str:
        """
        Computes the SHA-256 hash of a token.
        
        Args:
            plaintext_token: The token submitted by the user (base64-encoded)
            
        Returns:
            SHA-256 hash of the token
            
        Raises:
            ValueError: If token cannot be decoded
        """
        try:
            # Decode from base64 to get the original bytes
            token_bytes = base64.urlsafe_b64decode(plaintext_token)
            # Hash the token bytes with SHA-256
            return hashlib.sha256(token_bytes).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to decode token: {str(e)}")
            raise ValueError("Invalid token format")
    
    def validate_token(self, plaintext_token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates a reset token.
        
        Args:
            plaintext_token: The token submitted by the user (base64-encoded)
            
        Returns:
            tuple containing:
            - is_valid: True if token is valid, not expired, and not used
            - user_email: Email of the user (if valid)
            - error_message: Error description (if invalid)
            
        Validation checks:
        1. Token hash exists in database
        2. Token has not expired
        3. Token has not been used (used_at is None)
        
        Examples:
            >>> validator = TokenValidator()
            >>> is_valid, email, error = validator.validate_token("valid_token_here")
            >>> if is_valid:
            ...     print(f"Token valid for {email}")
            ... else:
            ...     print(f"Token invalid: {error}")
        """
        try:
            # Hash the submitted token to look it up in the database
            token_hash = self._get_token_hash(plaintext_token)
        except ValueError as e:
            return False, None, str(e)
        
        try:
            token_data = get_reset_token(token_hash)
            
            # Check 1: Token hash exists in database
            if token_data is None:
                logger.info(f"Token not found in database: {token_hash[:8]}...")
                return False, None, "Invalid or expired reset token"
            
            # Extract token data
            email = token_data['email']
            expiration_str = token_data['expiration']
            used_at = token_data.get('used_at')
            
            # Check 2: Token has not been used
            if used_at is not None:
                logger.info(f"Token already used for {email}")
                return False, None, "This reset token has already been used"
            
            # Check 3: Token has not expired
            # Parse the expiration timestamp (ISO 8601 format)
            try:
                expiration = datetime.fromisoformat(expiration_str)
                # Ensure expiration is timezone-aware (UTC)
                if expiration.tzinfo is None:
                    expiration = expiration.replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.error(f"Failed to parse expiration timestamp: {str(e)}")
                return False, None, "Invalid token data"
            
            # Compare with current time (UTC)
            current_time = datetime.now(timezone.utc)
            if current_time > expiration:
                logger.info(f"Token expired for {email} (expired at {expiration_str})")
                return False, None, "The reset token has expired"
            
            # All checks passed - token is valid
            logger.info(f"Token validated successfully for {email}")
            return True, email, None
            
        except DatabaseError as e:
            # Database errors should be logged but not expose details to the user
            logger.error(f"Database error during token validation: {str(e)}")
            return False, None, "An error occurred while validating the token"
        
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error during token validation: {str(e)}")
            return False, None, "An error occurred while validating the token"
