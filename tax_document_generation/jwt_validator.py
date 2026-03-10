"""
JWT validation module for tax document generation.

This module provides JWT (JSON Web Token) validation functionality
for authenticating users and extracting user identity from tokens.
It validates token signatures, checks expiration, and extracts the
userId claim for use in document generation and storage operations.
"""

import jwt
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError, DecodeError
from exceptions import AuthenticationError


def validate_jwt(token: str, secret: str) -> dict:
    """
    Validates a JWT token and returns the decoded payload.
    
    Validates the token's signature using the provided secret key and checks
    that the token has not expired. Returns the decoded payload containing
    the userId and other claims if valid.
    
    Args:
        token: JWT token string to verify (format: header.payload.signature)
        secret: Secret key used to sign the JWT (must match the key used during generation)
        
    Returns:
        dict: Decoded JWT payload containing userId and other claims
        
    Raises:
        AuthenticationError: If token is invalid, expired, or malformed
        
    Example:
        >>> payload = validate_jwt(token, secret_key)
        >>> user_id = payload['userId']
        >>> print(f"Authenticated user: {user_id}")
        
    Requirements: 8.1, 8.2, 8.3
    
    Note:
        - Uses HS256 algorithm for signature verification
        - Automatically checks token expiration
        - Does not modify the token or payload
        - Extracts userId from token claims for user identification
    """
    # Validate inputs
    if not token or not isinstance(token, str):
        raise AuthenticationError("Token must be a non-empty string")
    
    if not secret or not isinstance(secret, str):
        raise AuthenticationError("Secret key must be a non-empty string")
    
    # Decode and verify the JWT token
    # jwt.decode automatically verifies:
    # 1. Signature validity using the secret key
    # 2. Token expiration (exp claim)
    # 3. Token format and structure
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"]
        )
        
        # Verify that userId claim exists in the payload
        if 'userId' not in payload:
            raise AuthenticationError("Token payload missing required 'userId' claim")
        
        return payload
        
    except InvalidSignatureError as e:
        # Token signature is invalid or was signed with a different key
        raise AuthenticationError(f"Invalid token signature: {str(e)}")
    except ExpiredSignatureError as e:
        # Token has expired
        raise AuthenticationError(f"Token has expired: {str(e)}")
    except DecodeError as e:
        # Token format is invalid or cannot be decoded
        raise AuthenticationError(f"Invalid token format: {str(e)}")
    except AuthenticationError:
        # Re-raise our custom AuthenticationError as-is
        raise
    except Exception as e:
        # Catch any other unexpected errors
        raise AuthenticationError(f"Token validation failed: {str(e)}")
