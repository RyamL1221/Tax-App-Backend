"""
Output Persister Module

This module handles storing generated tax documents to S3.
"""

import boto3
import os
from botocore.exceptions import ClientError
from exceptions import S3Error


def store_output(bucket: str, user_id: str, job_id: str, document: bytes, document_type: str) -> str:
    """
    Stores a generated document to S3.
    
    Args:
        bucket: S3 bucket name
        user_id: User identifier
        job_id: Unique job identifier
        document: Generated document content (PDF bytes)
        document_type: The IRS form type (e.g., "1040")
        
    Returns:
        str: S3 object key where document was stored
        
    Raises:
        S3Error: If S3 operation fails
    """
    # Construct S3 key following the pattern: outputs/{user_id}/{job_id}/form-{document_type}.pdf
    s3_key = f"outputs/{user_id}/{job_id}/form-{document_type}.pdf"
    
    try:
        # Create S3 client with endpoint URL if specified (for LocalStack)
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        if endpoint_url:
            s3_client = boto3.client('s3', endpoint_url=endpoint_url)
        else:
            s3_client = boto3.client('s3')
        
        # Store the document
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=document,
            ContentType='application/pdf',
            Metadata={
                'userId': user_id,
                'jobId': job_id,
                'documentType': document_type
            }
        )
        
        return s3_key
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        raise S3Error(f"Failed to store document to S3: {error_code} - {error_message}")
    except Exception as e:
        raise S3Error(f"Failed to store document to S3: {str(e)}")
