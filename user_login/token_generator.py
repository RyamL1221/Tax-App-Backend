"""
Token generation module for user login.

This module provides JWT (JSON Web Token) authentication token generation
using cryptographically signed tokens with the HS256 algorithm.
"""

import jwt
import time


def generate_jwt_token(email: str, secret_key: str, session_version: int = 0) -> str:
    """
    Generates a JWT authentication token.
    
    Creates a cryptographically signed JWT token containing the user's email,
    session version, and expiration information. The token is self-contained
    and stateless, with session version enabling server-side invalidation.
    
    Args:
        email: User's email address to include in token payload
        secret_key: Secret key for signing the JWT (must be at least 32 characters)
        session_version: Current session version for the user (default: 0)
        
    Returns:
        JWT token string in format: header.payload.signature
        
    Raises:
        ValueError: If email is empty or secret_key is less than 32 characters
        
    Example:
        >>> token = generate_jwt_token("user@example.com", "a" * 32, 1)
        >>> len(token.split('.'))
        3
        >>> import jwt
        >>> payload = jwt.decode(token, "a" * 32, algorithms=["HS256"])
        >>> payload['email']
        'user@example.com'
        >>> payload['session_version']
        1
        
    Note:
        - Token expires 24 hours after issuance
        - Uses HS256 (HMAC with SHA-256) algorithm
        - Payload includes: email, session_version, iat (issued at), exp (expiration)
        - Session version enables invalidation of all tokens issued before password reset
    """
    # Validate inputs
    if not email or not isinstance(email, str):
        raise ValueError("Email must be a non-empty string")
    
    if not secret_key or not isinstance(secret_key, str):
        raise ValueError("Secret key must be a non-empty string")
    
    if len(secret_key) < 32:
        raise ValueError("JWT secret key must be at least 32 characters")
    
    # Generate timestamps
    issued_at = int(time.time())
    expiration = issued_at + 86400  # 24 hours in seconds
    
    # Create payload with required claims
    payload = {
        "email": email,
        "session_version": session_version,
        "iat": issued_at,
        "exp": expiration
    }
    
    # Generate and return JWT token using HS256 algorithm
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    
    return token
