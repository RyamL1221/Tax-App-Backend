"""
Main Lambda Handler for Tax Document Generation

This module implements the main Lambda handler that orchestrates the entire
document generation workflow by delegating to generation_service.py.
"""

import os
import sys
from typing import Dict

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

from models import GenerationRequest
from jwt_validator import validate_jwt
from generation_service import generate_single_document, GenerationResult
from job_repository import get_job
from response_formatter import success_response, error_response
from logger import log_info
from exceptions import (
    AuthenticationError,
    ValidationError,
)


def lambda_handler(event: Dict, context) -> Dict:
    """
    Main Lambda handler for tax document generation.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        dict: API Gateway response
    """
    # Handle OPTIONS requests for CORS preflight
    http_method = event.get('httpMethod', '')
    if http_method == 'OPTIONS':
        cors_origin = os.environ.get('CORS_ALLOWED_ORIGIN', '*')
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': cors_origin,
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': ''
        }
    
    try:
        # Get environment variables
        templates_bucket = os.environ.get('TEMPLATES_BUCKET')
        outputs_bucket = os.environ.get('OUTPUTS_BUCKET')
        job_table_name = os.environ.get('JOB_TABLE_NAME')
        jwt_secret = os.environ.get('JWT_SECRET_KEY')
        
        if not all([templates_bucket, outputs_bucket, job_table_name, jwt_secret]):
            raise Exception("Missing required environment variables")
        
        # Extract and validate JWT token
        auth_header = event.get('headers', {}).get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise AuthenticationError("Missing or invalid Authorization header")
        
        token = auth_header.replace('Bearer ', '')
        jwt_payload = validate_jwt(token, jwt_secret)
        user_id = jwt_payload.get('userId')
        
        if not user_id:
            raise AuthenticationError("JWT token missing userId claim")
        
        log_info(f"Processing request for user {user_id}")
        
        # Parse request
        request = GenerationRequest.from_api_event(event)
        document_type = request.document_type
        form_data = request.form_data
        
        # Delegate to generation service
        result = generate_single_document(
            user_id=user_id,
            document_type=document_type,
            form_data=form_data,
            templates_bucket=templates_bucket,
            outputs_bucket=outputs_bucket,
            job_table_name=job_table_name,
        )
        
        # Map GenerationResult back to HTTP response
        if result.status == "COMPLETED":
            # Fetch the full job record for the success response
            completed_job = get_job(job_table_name, result.job_id)
            return success_response(completed_job)
        else:
            # Map error_type to HTTP status code and response
            return _error_result_to_response(result)
        
    except AuthenticationError as e:
        return error_response(401, "AuthenticationError", str(e))
        
    except ValidationError as e:
        return error_response(400, "ValidationError", str(e))
        
    except Exception as e:
        return error_response(500, "InternalError", "An unexpected error occurred")


def _error_result_to_response(result: GenerationResult) -> Dict:
    """
    Map a failed GenerationResult to the appropriate HTTP error response.
    
    Preserves the same HTTP status codes and error messages as the
    pre-refactor handler.
    
    Args:
        result: GenerationResult with status="FAILED"
        
    Returns:
        dict: API Gateway error response
    """
    error_type = result.error_type
    error_message = result.error_message
    
    if error_type == "ValidationError":
        return error_response(400, "ValidationError", error_message)
    elif error_type == "TemplateNotFoundError":
        return error_response(404, "TemplateNotFoundError", error_message)
    elif error_type == "GenerationError":
        return error_response(500, "GenerationError", error_message)
    elif error_type == "S3Error":
        return error_response(500, "InternalError", error_message)
    else:
        # InternalError or unknown
        return error_response(500, "InternalError", error_message)
