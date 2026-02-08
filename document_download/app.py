"""
Main Lambda Handler for Document Download

This module implements the Lambda handler for downloading generated tax documents.
"""

import os
import sys
import logging
from typing import Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from jwt_validator import validate_jwt
from job_repository import get_job
from document_retriever import get_document
from response_formatter import pdf_response, error_response
from exceptions import (
    AuthenticationError,
    AuthorizationError,
    JobNotFoundError,
    DocumentNotFoundError,
    DocumentGenerationFailedError,
    DatabaseError,
    S3Error
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle document download requests.
    
    Args:
        event: API Gateway event with path parameters and headers
        context: Lambda context
        
    Returns:
        API Gateway response with PDF binary or error
    """
    job_id = None
    
    try:
        # Get environment variables
        jwt_secret = os.environ.get('JWT_SECRET_KEY')
        job_table_name = os.environ.get('JOB_TABLE_NAME')
        outputs_bucket = os.environ.get('OUTPUTS_BUCKET')
        
        if not all([jwt_secret, job_table_name, outputs_bucket]):
            raise Exception("Missing required environment variables")
        
        # Extract jobId from path parameters
        path_params = event.get('pathParameters', {})
        if not path_params or 'jobId' not in path_params:
            return error_response(400, "BadRequest", "Missing jobId parameter")
        
        job_id = path_params['jobId']
        logger.info(f"Processing download request for job {job_id}")
        
        # Extract and validate JWT token
        auth_header = event.get('headers', {}).get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise AuthenticationError("Missing or invalid Authorization header")
        
        token = auth_header.replace('Bearer ', '')
        jwt_payload = validate_jwt(token, jwt_secret)
        jwt_user_id = jwt_payload.get('userId')
        
        if not jwt_user_id:
            raise AuthenticationError("JWT token missing userId claim")
        
        logger.info(f"Authenticated user {jwt_user_id}")
        
        # Retrieve job record from DynamoDB
        job = get_job(job_table_name, job_id)
        logger.info(f"Retrieved job {job_id} with status {job.get('status')}")
        
        # Verify authorization: job.userId must match JWT userId
        job_user_id = job.get('userId')
        if job_user_id != jwt_user_id:
            logger.warning(f"Authorization failed: job userId {job_user_id} != JWT userId {jwt_user_id}")
            raise AuthorizationError("You do not have permission to access this document")
        
        logger.info(f"Authorization successful for user {jwt_user_id}")
        
        # Check job status
        job_status = job.get('status')
        
        if job_status == 'FAILED':
            error_message = job.get('errorMessage', 'Unknown error')
            logger.warning(f"Job {job_id} failed: {error_message}")
            raise DocumentGenerationFailedError("Document generation failed. Please try generating the document again.")
        
        if job_status != 'COMPLETED':
            # Job is PENDING or RUNNING - document not ready yet
            logger.info(f"Job {job_id} not completed yet (status: {job_status})")
            raise DocumentNotFoundError("Document not found")
        
        # Get output key from job
        output_key = job.get('outputKey')
        if not output_key:
            logger.error(f"Job {job_id} is COMPLETED but missing outputKey")
            raise DocumentNotFoundError("Document not found")
        
        # Retrieve document from S3
        logger.info(f"Retrieving document from S3: {output_key}")
        pdf_bytes = get_document(outputs_bucket, output_key)
        
        # Extract filename from output key
        # Format: outputs/{userId}/{jobId}/form-{documentType}.pdf
        filename = output_key.split('/')[-1]
        
        # Log successful download
        logger.info(f"Document download successful", extra={
            'jobId': job_id,
            'userId': jwt_user_id,
            'documentType': job.get('documentType'),
            'documentSize': len(pdf_bytes)
        })
        
        # Return PDF response
        return pdf_response(pdf_bytes, filename)
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed for job {job_id}: {str(e)}")
        return error_response(401, "AuthenticationError", str(e))
        
    except AuthorizationError as e:
        logger.warning(f"Authorization failed for job {job_id}: {str(e)}")
        return error_response(403, "AuthorizationError", str(e))
        
    except JobNotFoundError as e:
        logger.info(f"Job not found: {job_id}")
        return error_response(404, "NotFoundError", "Document not found")
        
    except DocumentNotFoundError as e:
        logger.info(f"Document not found for job {job_id}")
        return error_response(404, "NotFoundError", "Document not found")
        
    except DocumentGenerationFailedError as e:
        logger.warning(f"Document generation failed for job {job_id}")
        return error_response(400, "DocumentGenerationFailed", str(e))
        
    except DatabaseError as e:
        logger.error(f"Database error for job {job_id}: {str(e)}", exc_info=True)
        return error_response(500, "InternalError", "An unexpected error occurred")
        
    except S3Error as e:
        logger.error(f"S3 error for job {job_id}: {str(e)}", exc_info=True)
        return error_response(500, "InternalError", "An unexpected error occurred")
        
    except Exception as e:
        logger.error(f"Unexpected error for job {job_id}: {str(e)}", exc_info=True)
        return error_response(500, "InternalError", "An unexpected error occurred")
