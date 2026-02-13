"""
Response Formatter Module

This module formats API Gateway responses for document downloads.
"""

import json
import base64
import os
from typing import Dict, Any


def _get_allowed_origin() -> str:
    """
    Get the allowed CORS origin from environment variable.
    
    Returns:
        str: Allowed origin, defaults to '*' if not set
    """
    return os.environ.get('CORS_ALLOWED_ORIGIN', '*')


def pdf_response(pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Format successful PDF download response.
    
    Args:
        pdf_bytes: PDF document content
        filename: Filename for Content-Disposition header
        
    Returns:
        dict: API Gateway response with binary PDF
    """
    allowed_origin = _get_allowed_origin()
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Access-Control-Allow-Origin': allowed_origin,
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': base64.b64encode(pdf_bytes).decode('utf-8'),
        'isBase64Encoded': True
    }


def error_response(status_code: int, error_type: str, message: str) -> Dict[str, Any]:
    """
    Format error response.
    
    Args:
        status_code: HTTP status code
        error_type: Error type identifier
        message: User-friendly error message
        
    Returns:
        dict: API Gateway response with error JSON
    """
    allowed_origin = _get_allowed_origin()
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': allowed_origin,
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps({
            'error': error_type,
            'message': message
        })
    }
