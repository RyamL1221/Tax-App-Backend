"""
JWT verification module for protected endpoints.

This module provides JWT (JSON Web Token) verification functionality
for validating authentication tokens, including signature verification,
expiration checking, and claim extraction.
"""

import jwt
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError, DecodeError


def verify_jwt_token(token: str, secret_key: str) -> dict:
    """
    Verifies a JWT authentication token and extracts its payload.
    
    Validates the token's signature using the provided secret key and checks
    that the token has not expired. Returns the decoded payload if valid.
    
    Args:
        token: JWT token string to verify (format: header.payload.signature)
        secret_key: Secret key used to sign the JWT (must match the key used during generation)
        
    Returns:
        Dictionary containing the decoded JWT payload with claims (email, iat, exp)
        
    Raises:
        InvalidSignatureError: If the token signature is invalid or was signed with a different key
        ExpiredSignatureError: If the token has expired (exp claim is in the past)
        DecodeError: If the token format is invalid or cannot be decoded
        ValueError: If token or secret_key is empty
        
    Example:
        >>> # Assuming a valid token was generated
        >>> payload = verify_jwt_token(token, secret_key)
        >>> email = payload['email']
        >>> print(f"Authenticated user: {email}")
        
    Note:
        - Uses HS256 algorithm for signature verification
        - Automatically checks token expiration
        - Does not modify the token or payload
        - For logout endpoints, format validation without verification is sufficient
    """
    # Validate inputs
    if not token or not isinstance(token, str):
        raise ValueError("Token must be a non-empty string")
    
    if not secret_key or not isinstance(secret_key, str):
        raise ValueError("Secret key must be a non-empty string")
    
    # Decode and verify the JWT token
    # jwt.decode automatically verifies:
    # 1. Signature validity using the secret key
    # 2. Token expiration (exp claim)
    # 3. Token format and structure
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=["HS256"]
        )
        return payload
    except InvalidSignatureError:
        # Token signature is invalid or was signed with a different key
        raise
    except ExpiredSignatureError:
        # Token has expired
        raise
    except DecodeError:
        # Token format is invalid or cannot be decoded
        raise
