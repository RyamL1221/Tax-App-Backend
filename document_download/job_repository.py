"""
Job Repository Module

This module retrieves job records from DynamoDB.
"""

import boto3
import os
from typing import Dict, Any
from botocore.exceptions import ClientError

from exceptions import JobNotFoundError, DatabaseError


def get_job(table_name: str, job_id: str) -> Dict[str, Any]:
    """
    Retrieve job record from DynamoDB.
    
    Args:
        table_name: DynamoDB table name
        job_id: Job identifier
        
    Returns:
        dict: Job record with userId, status, outputKey, etc.
        
    Raises:
        JobNotFoundError: If job doesn't exist
        DatabaseError: If DynamoDB operation fails
    """
    try:
        # Get AWS endpoint URL if configured (for LocalStack)
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        
        # Connect to DynamoDB
        if endpoint_url:
            dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
        else:
            dynamodb = boto3.resource('dynamodb')
        
        table = dynamodb.Table(table_name)
        
        # Retrieve job record
        response = table.get_item(Key={'jobId': job_id})
        
        # Check if job exists
        if 'Item' not in response:
            raise JobNotFoundError(f"Job {job_id} not found")
        
        return response['Item']
        
    except JobNotFoundError:
        # Re-raise JobNotFoundError
        raise
    except ClientError as e:
        # Wrap DynamoDB errors
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        raise DatabaseError(f"DynamoDB error ({error_code}): {str(e)}")
    except Exception as e:
        # Wrap unexpected errors
        raise DatabaseError(f"Failed to retrieve job: {str(e)}")
