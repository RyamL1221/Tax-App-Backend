"""
Response formatter for user login endpoint.

This module provides functions to format HTTP responses with consistent
structure, including success and error responses with appropriate status
codes and CORS headers.
"""

import json
from typing import Dict, Any


def _get_cors_headers() -> Dict[str, str]:
    """
    Returns standard CORS headers for all responses.
    
    Returns:
        Dictionary of CORS headers
    """
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "POST,OPTIONS"
    }


def success_response(email: str, token: str) -> Dict[str, Any]:
    """
    Returns 200 success response with authentication token.
    
    Args:
        email: User's email address
        token: Generated authentication token
        
    Returns:
        API Gateway proxy response with 200 status code
        
    Example:
        >>> response = success_response("user@example.com", "abc123...")
        >>> response["statusCode"]
        200
        >>> "token" in json.loads(response["body"])
        True
    """
    return {
        "statusCode": 200,
        "headers": _get_cors_headers(),
        "body": json.dumps({
            "message": "Login successful",
            "email": email,
            "token": token
        })
    }


def validation_error_response(message: str) -> Dict[str, Any]:
    """
    Returns 400 validation error response.
    
    Args:
        message: Descriptive error message
        
    Returns:
        API Gateway proxy response with 400 status code
        
    Example:
        >>> response = validation_error_response("Invalid email format")
        >>> response["statusCode"]
        400
    """
    return {
        "statusCode": 400,
        "headers": _get_cors_headers(),
        "body": json.dumps({
            "error": f"Validation failed: {message}"
        })
    }


def authentication_error_response() -> Dict[str, Any]:
    """
    Returns 401 authentication failed response with generic message.
    
    Uses a generic error message to prevent user enumeration attacks.
    The same message is returned whether the email doesn't exist or
    the password is incorrect.
    
    Returns:
        API Gateway proxy response with 401 status code
        
    Example:
        >>> response = authentication_error_response()
        >>> response["statusCode"]
        401
        >>> "Invalid credentials" in response["body"]
        True
    """
    return {
        "statusCode": 401,
        "headers": _get_cors_headers(),
        "body": json.dumps({
            "error": "Invalid credentials"
        })
    }


def internal_error_response() -> Dict[str, Any]:
    """
    Returns 500 internal server error response.
    
    Returns a generic error message without revealing internal details.
    
    Returns:
        API Gateway proxy response with 500 status code
        
    Example:
        >>> response = internal_error_response()
        >>> response["statusCode"]
        500
    """
    return {
        "statusCode": 500,
        "headers": _get_cors_headers(),
        "body": json.dumps({
            "error": "Internal server error"
        })
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Returns error response with given status code.
    
    Generic error response function for custom error cases.
    
    Args:
        status_code: HTTP status code
        message: Error message
        
    Returns:
        API Gateway proxy response with specified status code
        
    Example:
        >>> response = error_response(403, "Forbidden")
        >>> response["statusCode"]
        403
    """
    return {
        "statusCode": status_code,
        "headers": _get_cors_headers(),
        "body": json.dumps({
            "error": message
        })
    }
