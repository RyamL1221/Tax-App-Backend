"""
Response formatter for password recovery endpoints.

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
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST,OPTIONS"
    }


def forgot_password_success_response() -> Dict[str, Any]:
    """
    Returns 200 success response for forgot password requests.
    
    Uses a generic message to prevent account enumeration.
    The same message is returned whether the email exists or not.
    
    Returns:
        API Gateway proxy response with 200 status code
        
    Example:
        >>> response = forgot_password_success_response()
        >>> response["statusCode"]
        200
    """
    return {
        "statusCode": 200,
        "headers": _get_cors_headers(),
        "body": json.dumps({
            "message": "If an account exists with that email, a password reset link has been sent."
        })
    }


def reset_password_success_response() -> Dict[str, Any]:
    """
    Returns 200 success response for reset password requests.
    
    Returns:
        API Gateway proxy response with 200 status code
        
    Example:
        >>> response = reset_password_success_response()
        >>> response["statusCode"]
        200
    """
    return {
        "statusCode": 200,
        "headers": _get_cors_headers(),
        "body": json.dumps({
            "message": "Password has been successfully reset."
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
            "error": "ValidationError",
            "message": message
        })
    }


def rate_limit_error_response(retry_after: int) -> Dict[str, Any]:
    """
    Returns 429 rate limit exceeded response.
    
    Args:
        retry_after: Seconds until next request is allowed
        
    Returns:
        API Gateway proxy response with 429 status code and Retry-After header
        
    Example:
        >>> response = rate_limit_error_response(300)
        >>> response["statusCode"]
        429
        >>> response["headers"]["Retry-After"]
        '300'
    """
    headers = _get_cors_headers()
    headers["Retry-After"] = str(retry_after)
    
    return {
        "statusCode": 429,
        "headers": headers,
        "body": json.dumps({
            "error": "RateLimitExceeded",
            "message": "Too many requests. Please try again later."
        })
    }


def invalid_token_error_response() -> Dict[str, Any]:
    """
    Returns 401 invalid token response.
    
    Used when a reset token is invalid, expired, or already used.
    
    Returns:
        API Gateway proxy response with 401 status code
        
    Example:
        >>> response = invalid_token_error_response()
        >>> response["statusCode"]
        401
    """
    return {
        "statusCode": 401,
        "headers": _get_cors_headers(),
        "body": json.dumps({
            "error": "InvalidToken",
            "message": "The reset token is invalid, expired, or has already been used."
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
            "error": "InternalError",
            "message": "An unexpected error occurred. Please try again later."
        })
    }
