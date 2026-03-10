"""
Template retriever module for fetching IRS templates from S3.

This module provides functionality to retrieve IRS tax form templates from the
Template_Store (S3 bucket). Templates are stored under the `templates/irs/` prefix
and are identified by document type (e.g., "1040" for Form 1040).

Requirements: 3.1, 3.3
"""

import boto3
import os
from botocore.exceptions import ClientError
from exceptions import TemplateNotFoundError, S3Error


def get_template(bucket: str, document_type: str) -> bytes:
    """
    Retrieves an IRS template from S3.
    
    This function constructs the S3 key using the pattern `templates/irs/{document_type}.pdf`
    and fetches the template file from the specified S3 bucket. It handles S3 errors
    appropriately, distinguishing between missing templates and other S3 failures.
    
    Args:
        bucket: S3 bucket name where templates are stored
        document_type: The IRS form type (e.g., "1040", "1099", "W2")
        
    Returns:
        bytes: Template file content as raw bytes
        
    Raises:
        TemplateNotFoundError: If the template does not exist in S3 (NoSuchKey error)
        S3Error: If any other S3 operation fails (permissions, network, etc.)
        
    Requirements:
        - 3.1: Construct S3 key using pattern `templates/irs/{documentType}`
        - 3.3: Raise TemplateNotFoundError if template doesn't exist
        
    Example:
        >>> template_bytes = get_template("my-bucket", "1040")
        >>> # template_bytes contains the PDF file content
    """
    # Construct S3 key following the pattern templates/irs/{document_type}.pdf
    s3_key = f"templates/irs/{document_type}.pdf"
    
    # Create S3 client with endpoint URL if specified (for LocalStack)
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
    if endpoint_url:
        s3_client = boto3.client('s3', endpoint_url=endpoint_url)
    else:
        s3_client = boto3.client('s3')
    
    try:
        # Fetch the template from S3
        response = s3_client.get_object(Bucket=bucket, Key=s3_key)
        
        # Read and return the template content as bytes
        template_content = response['Body'].read()
        return template_content
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        
        # Handle NoSuchKey error - template doesn't exist
        if error_code == 'NoSuchKey':
            raise TemplateNotFoundError(
                f"IRS template for document type '{document_type}' not found"
            )
        
        # Handle all other S3 errors
        error_message = e.response.get('Error', {}).get('Message', str(e))
        raise S3Error(
            f"Failed to retrieve template from S3: {error_message}"
        )
    
    except Exception as e:
        # Handle any unexpected errors
        raise S3Error(
            f"Unexpected error while retrieving template: {str(e)}"
        )
