"""
Main Lambda Handler for Tax Document Generation

This module implements the main Lambda handler that orchestrates the entire
document generation workflow.
"""

import os
import sys
import uuid
import time
from typing import Dict

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

from models import GenerationRequest
from jwt_validator import validate_jwt
from input_validator import validate_form_data
from template_retriever import get_template
from document_generator import generate_document
from output_persister import store_output
from job_repository import create_job, update_job_completed, update_job_failed
from response_formatter import success_response, error_response
from logger import log_error, log_success, log_info
from exceptions import (
    AuthenticationError,
    ValidationError,
    TemplateNotFoundError,
    GenerationError,
    S3Error
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
    start_time = time.time()
    job_id = None
    
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
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Construct template key
        template_key = f"templates/irs/{document_type}.pdf"
        
        # Create PENDING job record
        create_job(job_table_name, job_id, user_id, document_type, template_key)
        log_info(f"Created job {job_id} with PENDING status")
        
        # Validate form data
        validate_form_data(document_type, form_data)
        log_info(f"Validated form data for job {job_id}")
        
        # Retrieve template from S3
        template = get_template(templates_bucket, document_type)
        log_info(f"Retrieved template for document type {document_type}")
        
        # Generate document
        generated_document = generate_document(template, form_data, document_type)
        log_info(f"Generated document for job {job_id}")
        
        # Store output to S3
        output_key = store_output(outputs_bucket, user_id, job_id, generated_document, document_type)
        log_info(f"Stored output to {output_key}")
        
        # Update job to COMPLETED
        completed_job = update_job_completed(job_table_name, job_id, output_key)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        log_success(job_id, duration_ms, {
            'documentType': document_type,
            'userId': user_id
        })
        
        # Return success response
        return success_response(completed_job)
        
    except AuthenticationError as e:
        error_msg = str(e)
        if job_id:
            update_job_failed(job_table_name, job_id, error_msg)
            log_error(job_id, e)
        return error_response(401, "AuthenticationError", error_msg)
        
    except ValidationError as e:
        error_msg = str(e)
        if job_id:
            update_job_failed(job_table_name, job_id, error_msg)
            log_error(job_id, e)
        return error_response(400, "ValidationError", error_msg)
        
    except TemplateNotFoundError as e:
        error_msg = str(e)
        if job_id:
            update_job_failed(job_table_name, job_id, error_msg)
            log_error(job_id, e)
        return error_response(404, "TemplateNotFoundError", error_msg)
        
    except GenerationError as e:
        error_msg = "An error occurred during document generation"
        if job_id:
            update_job_failed(job_table_name, job_id, str(e))
            log_error(job_id, e)
        return error_response(500, "GenerationError", error_msg)
        
    except S3Error as e:
        error_msg = "An error occurred while storing the document"
        if job_id:
            update_job_failed(job_table_name, job_id, str(e))
            log_error(job_id, e)
        return error_response(500, "InternalError", error_msg)
        
    except Exception as e:
        error_msg = "An unexpected error occurred"
        if job_id:
            try:
                update_job_failed(job_table_name, job_id, str(e))
            except:
                pass  # Don't fail if we can't update the job
            log_error(job_id, e)
        return error_response(500, "InternalError", error_msg)
