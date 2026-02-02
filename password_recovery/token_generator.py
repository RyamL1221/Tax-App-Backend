"""
Token generator for password recovery.

This module generates cryptographically secure reset tokens using
secrets.token_bytes for high entropy, encodes them as URL-safe base64
for email transmission, and hashes them with SHA-256 for secure storage.
"""

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Tuple


class TokenGenerator:
    """Generates cryptographically secure reset tokens for password recovery."""
    
    def generate_reset_token(self, user_email: str) -> Tuple[str, str, datetime]:
        """
        Generates a secure reset token for the given user.
        
        Args:
            user_email: The email address of the user
            
        Returns:
            tuple containing:
            - plaintext_token: Base64-encoded token to send to user
            - token_hash: SHA-256 hash to store in database
            - expiration: Expiration timestamp (1 hour from now)
            
        The token is generated using secrets.token_bytes(32) for
        cryptographic security (256-bit entropy).
        
        Examples:
            >>> generator = TokenGenerator()
            >>> plaintext, hash_val, exp = generator.generate_reset_token("user@example.com")
            >>> len(base64.urlsafe_b64decode(plaintext))
            32
            >>> len(hash_val)
            64
        """
        # Generate 32 bytes (256 bits) of cryptographically secure random data
        token_bytes = secrets.token_bytes(32)
        
        # Encode as URL-safe base64 for email transmission
        # URL-safe base64 uses - and _ instead of + and / for URL compatibility
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        
        # Hash the token with SHA-256 for secure storage
        # We store only the hash, never the plaintext token
        token_hash = hashlib.sha256(token_bytes).hexdigest()
        
        # Set expiration to 1 hour from now (UTC)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        return plaintext_token, token_hash, expiration
