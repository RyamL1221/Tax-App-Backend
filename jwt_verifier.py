"""
JWT verification module for protected endpoints.

This module provides JWT (JSON Web Token) verification functionality
for validating authentication tokens, including signature verification,
expiration checking, session version validation, and claim extraction.
"""

import jwt
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError, DecodeError
from typing import Optional, Callable


class SessionVersionMismatchError(Exception):
    """Raised when JWT session version doesn't match current user session version."""
    pass


def verify_jwt_token(
    token: str, 
    secret_key: str,
    get_session_version: Optional[Callable[[str], int]] = None
) -> dict:
    """
    Verifies a JWT authentication token and extracts its payload.
    
    Validates the token's signature using the provided secret key, checks
    that the token has not expired, and optionally validates the session
    version against the current user's session version. Returns the decoded
    payload if valid.
    
    Args:
        token: JWT token string to verify (format: header.payload.signature)
        secret_key: Secret key used to sign the JWT (must match the key used during generation)
        get_session_version: Optional callable that takes an email and returns the current
                           session version for that user. If provided, session version
                           validation will be performed.
        
    Returns:
        Dictionary containing the decoded JWT payload with claims 
        (email, session_version, iat, exp)
        
    Raises:
        InvalidSignatureError: If the token signature is invalid or was signed with a different key
        ExpiredSignatureError: If the token has expired (exp claim is in the past)
        DecodeError: If the token format is invalid or cannot be decoded
        ValueError: If token or secret_key is empty
        SessionVersionMismatchError: If session version in token doesn't match current version
        
    Example:
        >>> # Without session version validation
        >>> payload = verify_jwt_token(token, secret_key)
        >>> email = payload['email']
        >>> print(f"Authenticated user: {email}")
        
        >>> # With session version validation
        >>> def get_user_session_version(email: str) -> int:
        ...     return user_repository.get_session_version(email)
        >>> payload = verify_jwt_token(token, secret_key, get_user_session_version)
        
    Note:
        - Uses HS256 algorithm for signature verification
        - Automatically checks token expiration
        - Does not modify the token or payload
        - Session version validation is optional but recommended for protected endpoints
        - If session version validation fails, SessionVersionMismatchError is raised
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
        
        # If session version validation is enabled, check it
        if get_session_version is not None:
            email = payload.get('email')
            token_session_version = payload.get('session_version', 0)
            
            if email:
                current_session_version = get_session_version(email)
                
                # If token's session version is less than current, it's invalid
                if token_session_version < current_session_version:
                    raise SessionVersionMismatchError(
                        f"Token session version {token_session_version} is less than "
                        f"current session version {current_session_version}. "
                        f"Token was issued before password reset."
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
    except SessionVersionMismatchError:
        # Session version mismatch - re-raise as-is
        raise
