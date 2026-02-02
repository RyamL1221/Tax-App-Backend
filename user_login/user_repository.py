"""
DynamoDB repository for user data retrieval.

This module handles user data retrieval from DynamoDB for the login endpoint.
It shares the same table structure as the registration endpoint.
"""

import os
from typing import Dict

import boto3
from botocore.exceptions import ClientError


class UserNotFoundError(Exception):
    """Raised when a user with the given email does not exist."""
    pass


class DatabaseError(Exception):
    """Raised when a database operation fails."""
    pass


def get_user_by_email(email: str) -> Dict[str, str]:
    """
    Retrieves a user from DynamoDB by email.
    
    This function queries DynamoDB using the email as the partition key
    and returns the complete user data including the password hash for
    authentication purposes.
    
    Args:
        email: User's email address (partition key)
        
    Returns:
        Dictionary containing user data:
        {
            "email": "user@example.com",
            "name": "John Doe",
            "password_hash": "$2b$12...",
            "session_version": 0,
            "created_at": "2024-01-15T10:30:00Z"
        }
        
    Raises:
        UserNotFoundError: If no user with the given email exists
        DatabaseError: If the database operation fails
        
    Examples:
        >>> user = get_user_by_email("user@example.com")
        >>> user["email"]
        'user@example.com'
        >>> "password_hash" in user
        True
    """
    # Get table name from environment variable
    table_name = os.environ.get('USER_TABLE_NAME')
    if not table_name:
        raise DatabaseError("USER_TABLE_NAME environment variable not set")
    
    # Create DynamoDB client with region (default to us-east-1 for testing)
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Configure endpoint for LocalStack if AWS_ENDPOINT_URL is set
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
    
    # Debug logging
    import logging
    logger = logging.getLogger()
    logger.info(f"DynamoDB Config - Region: {region}, Endpoint: {endpoint_url}, Table: {table_name}")
    
    if endpoint_url:
        dynamodb = boto3.client('dynamodb', region_name=region, endpoint_url=endpoint_url)
    else:
        dynamodb = boto3.client('dynamodb', region_name=region)
    
    try:
        # Get item from DynamoDB using email as partition key
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                'email': {'S': email}
            }
        )
        
        # Check if item exists
        if 'Item' not in response:
            raise UserNotFoundError(f"User with email {email} not found")
        
        # Extract item data
        item = response['Item']
        
        # Return complete user data including password_hash and session_version
        return {
            'email': item['email']['S'],
            'name': item['name']['S'],
            'password_hash': item['password_hash']['S'],
            'session_version': int(item.get('session_version', {}).get('N', '0')),
            'created_at': item['created_at']['S']
        }
        
    except UserNotFoundError:
        # Re-raise UserNotFoundError as-is
        raise
        
    except ClientError as e:
        # Handle DynamoDB client errors
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        raise DatabaseError(f"Failed to retrieve user: {error_message}") from e
    
    except Exception as e:
        # Handle unexpected errors
        raise DatabaseError(f"Unexpected error retrieving user: {str(e)}") from e
