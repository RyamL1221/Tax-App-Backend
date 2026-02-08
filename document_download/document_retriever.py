"""
Document Retriever Module

This module retrieves PDF documents from S3.
"""

import boto3
import os
from botocore.exceptions import ClientError

from exceptions import DocumentNotFoundError, S3Error


def get_document(bucket: str, s3_key: str) -> bytes:
    """
    Retrieve document from S3.
    
    Args:
        bucket: S3 bucket name
        s3_key: S3 object key
        
    Returns:
        bytes: PDF document content
        
    Raises:
        DocumentNotFoundError: If S3 object doesn't exist
        S3Error: If S3 operation fails
    """
    try:
        # Get AWS endpoint URL if configured (for LocalStack)
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        
        # Connect to S3
        if endpoint_url:
            s3 = boto3.client('s3', endpoint_url=endpoint_url)
        else:
            s3 = boto3.client('s3')
        
        # Retrieve document
        response = s3.get_object(Bucket=bucket, Key=s3_key)
        
        # Read binary content
        pdf_bytes = response['Body'].read()
        
        return pdf_bytes
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        
        # Check if object doesn't exist
        if error_code in ['NoSuchKey', '404', 'NotFound']:
            raise DocumentNotFoundError(f"Document not found: {s3_key}")
        
        # Other S3 errors
        raise S3Error(f"S3 error ({error_code}): {str(e)}")
        
    except Exception as e:
        # Wrap unexpected errors
        raise S3Error(f"Failed to retrieve document: {str(e)}")
