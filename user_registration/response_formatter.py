"""
Response formatter for user registration endpoint.

This module provides functions to format HTTP responses with consistent structure,
appropriate status codes, CORS headers, and JSON content type for the Lambda function.
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
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }


def success_response(email: str) -> Dict[str, Any]:
    """
    Returns a 201 success response for successful user registration.
    
    Args:
        email: The email address of the successfully registered user
        
    Returns:
        API Gateway proxy response dictionary with:
        - statusCode: 201
        - headers: CORS headers and Content-Type
        - body: JSON string with success message and email
        
    Examples:
        >>> response = success_response("user@example.com")
        >>> response["statusCode"]
        201
        >>> "user@example.com" in response["body"]
        True
    """
    return {
        'statusCode': 201,
        'headers': _get_cors_headers(),
        'body': json.dumps({
            'message': 'User registered successfully',
            'email': email
        })
    }


def validation_error_response(message: str) -> Dict[str, Any]:
    """
    Returns a 400 validation error response.
    
    Args:
        message: Descriptive error message explaining the validation failure
        
    Returns:
        API Gateway proxy response dictionary with:
        - statusCode: 400
        - headers: CORS headers and Content-Type
        - body: JSON string with error message
        
    Examples:
        >>> response = validation_error_response("Invalid email format")
        >>> response["statusCode"]
        400
    """
    return {
        'statusCode': 400,
        'headers': _get_cors_headers(),
        'body': json.dumps({
            'error': f'Validation failed: {message}'
        })
    }


def duplicate_user_response() -> Dict[str, Any]:
    """
    Returns a 409 conflict response for duplicate email attempts.
    
    Returns:
        API Gateway proxy response dictionary with:
        - statusCode: 409
        - headers: CORS headers and Content-Type
        - body: JSON string with error message
        
    Examples:
        >>> response = duplicate_user_response()
        >>> response["statusCode"]
        409
    """
    return {
        'statusCode': 409,
        'headers': _get_cors_headers(),
        'body': json.dumps({
            'error': 'Email already registered'
        })
    }


def internal_error_response() -> Dict[str, Any]:
    """
    Returns a 500 internal server error response.
    
    Returns:
        API Gateway proxy response dictionary with:
        - statusCode: 500
        - headers: CORS headers and Content-Type
        - body: JSON string with generic error message
        
    Examples:
        >>> response = internal_error_response()
        >>> response["statusCode"]
        500
    """
    return {
        'statusCode': 500,
        'headers': _get_cors_headers(),
        'body': json.dumps({
            'error': 'Internal server error'
        })
    }
