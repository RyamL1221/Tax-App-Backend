"""
JWT Validator Module

This module validates JWT tokens for authentication.
"""

import jwt
from typing import Dict, Any
from datetime import datetime

from exceptions import AuthenticationError


def validate_jwt(token: str, secret: str) -> Dict[str, Any]:
    """
    Validate JWT token and return payload.
    
    Args:
        token: JWT token string
        secret: Secret key for validation
        
    Returns:
        dict: JWT payload containing userId and email
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        # Decode and validate JWT
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        
        # Validate required claims
        if 'userId' not in payload:
            raise AuthenticationError("JWT token missing userId claim")
        
        if 'email' not in payload:
            raise AuthenticationError("JWT token missing email claim")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("JWT token has expired")
    except jwt.InvalidSignatureError:
        raise AuthenticationError("Invalid JWT signature")
    except jwt.DecodeError:
        raise AuthenticationError("Invalid JWT token format")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid JWT token: {str(e)}")
