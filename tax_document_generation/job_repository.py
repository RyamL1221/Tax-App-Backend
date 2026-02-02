"""
Job Repository Module

This module manages job records in DynamoDB for tracking document generation requests.
"""

import boto3
from datetime import datetime
from typing import Dict
from botocore.exceptions import ClientError


def create_job(table_name: str, job_id: str, user_id: str, document_type: str, template_key: str) -> Dict:
    """
    Creates a new job record with PENDING status.
    
    Args:
        table_name: DynamoDB table name
        job_id: Unique job identifier
        user_id: User identifier
        document_type: The IRS form type (e.g., "1040")
        template_key: S3 key of the input template
        
    Returns:
        dict: Created job record
        
    Raises:
        Exception: If DynamoDB operation fails
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    now = datetime.utcnow().isoformat() + 'Z'
    
    item = {
        'jobId': job_id,
        'userId': user_id,
        'documentType': document_type,
        'status': 'PENDING',
        'createdAt': now,
        'updatedAt': now,
        'templateKey': template_key
    }
    
    try:
        table.put_item(Item=item)
        return item
    except ClientError as e:
        raise Exception(f"Failed to create job record: {str(e)}")


def update_job_running(table_name: str, job_id: str) -> None:
    """
    Updates job status to RUNNING.
    
    Args:
        table_name: DynamoDB table name
        job_id: Unique job identifier
        
    Raises:
        Exception: If DynamoDB operation fails
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    now = datetime.utcnow().isoformat() + 'Z'
    
    try:
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, updatedAt = :updated',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'RUNNING',
                ':updated': now
            }
        )
    except ClientError as e:
        raise Exception(f"Failed to update job to RUNNING: {str(e)}")


def update_job_completed(table_name: str, job_id: str, output_key: str) -> Dict:
    """
    Updates job status to COMPLETED with output location.
    
    Args:
        table_name: DynamoDB table name
        job_id: Unique job identifier
        output_key: S3 key where output was stored
        
    Returns:
        dict: Updated job record
        
    Raises:
        Exception: If DynamoDB operation fails
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    now = datetime.utcnow().isoformat() + 'Z'
    
    try:
        response = table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, outputKey = :output, completedAt = :completed, updatedAt = :updated',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':output': output_key,
                ':completed': now,
                ':updated': now
            },
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes', {})
    except ClientError as e:
        raise Exception(f"Failed to update job to COMPLETED: {str(e)}")


def update_job_failed(table_name: str, job_id: str, error_message: str) -> Dict:
    """
    Updates job status to FAILED with error details.
    
    Args:
        table_name: DynamoDB table name
        job_id: Unique job identifier
        error_message: Description of the failure
        
    Returns:
        dict: Updated job record
        
    Raises:
        Exception: If DynamoDB operation fails
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    now = datetime.utcnow().isoformat() + 'Z'
    
    try:
        response = table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, errorMessage = :error, updatedAt = :updated',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'FAILED',
                ':error': error_message,
                ':updated': now
            },
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes', {})
    except ClientError as e:
        raise Exception(f"Failed to update job to FAILED: {str(e)}")


def get_job(table_name: str, job_id: str) -> Dict:
    """
    Retrieves a job record by job ID.
    
    Args:
        table_name: DynamoDB table name
        job_id: Unique job identifier
        
    Returns:
        dict: Job record
        
    Raises:
        Exception: If DynamoDB operation fails or job not found
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    try:
        response = table.get_item(Key={'jobId': job_id})
        if 'Item' not in response:
            raise Exception(f"Job {job_id} not found")
        return response['Item']
    except ClientError as e:
        raise Exception(f"Failed to get job record: {str(e)}")
