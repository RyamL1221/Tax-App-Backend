"""
Response Formatter Module

This module handles formatting API Gateway responses for the tax document generation feature.
"""

import json
from typing import Dict


def get_cors_headers() -> Dict[str, str]:
    """
    Get CORS headers for API responses.
    
    Returns:
        dict: CORS headers
    """
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }


def success_response(job_record: Dict) -> Dict:
    """
    Format a successful generation response.
    
    Args:
        job_record: Completed job record from DynamoDB
        
    Returns:
        dict: API Gateway response format
    """
    response_body = {
        'jobId': job_record['jobId'],
        'userId': job_record['userId'],
        'status': job_record['status'],
        'outputKey': job_record.get('outputKey'),
        'documentType': job_record['documentType'],
        'createdAt': job_record['createdAt'],
        'completedAt': job_record.get('completedAt')
    }
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps(response_body)
    }


def error_response(status_code: int, error_type: str, message: str) -> Dict:
    """
    Format an error response.
    
    Args:
        status_code: HTTP status code (400, 401, 404, 500, etc.)
        error_type: Error type identifier (e.g., "ValidationError", "AuthenticationError")
        message: Human-readable error message
        
    Returns:
        dict: API Gateway response format
    """
    response_body = {
        'error': error_type,
        'message': message
    }
    
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(response_body)
    }
