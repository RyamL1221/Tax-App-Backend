"""
DynamoDB repository for user data persistence.

This module handles user data storage in DynamoDB with duplicate detection
and error handling for the user registration endpoint.
"""

import os
from datetime import datetime, timezone
from typing import Dict

import boto3
from botocore.exceptions import ClientError


class DuplicateUserError(Exception):
    """Raised when attempting to create a user with an existing email."""
    pass


class UserNotFoundError(Exception):
    """Raised when a user with the given email does not exist."""
    pass


class DatabaseError(Exception):
    """Raised when a database operation fails."""
    pass


def create_user(email: str, name: str, password_hash: str) -> Dict[str, str]:
    """
    Creates a new user in DynamoDB.
    
    This function stores user data in DynamoDB with a conditional check to prevent
    duplicate emails. The email serves as the partition key.
    
    Args:
        email: User's email address (used as partition key)
        name: User's display name
        password_hash: Bcrypt hash of the user's password
        
    Returns:
        Dictionary containing the created user data (without password hash):
        {
            "email": "user@example.com",
            "name": "John Doe",
            "created_at": "2024-01-15T10:30:00Z"
        }
        
    Raises:
        DuplicateUserError: If a user with the given email already exists
        DatabaseError: If the database operation fails for any other reason
        
    Examples:
        >>> user = create_user("user@example.com", "John Doe", "$2b$12$...")
        >>> user["email"]
        'user@example.com'
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
    
    # Generate ISO 8601 timestamp
    created_at = datetime.now(timezone.utc).isoformat()
    
    # Prepare item for DynamoDB
    item = {
        'email': {'S': email},
        'name': {'S': name},
        'password_hash': {'S': password_hash},
        'created_at': {'S': created_at}
    }
    
    try:
        # Put item with conditional check for duplicate email
        # attribute_not_exists(email) ensures the email doesn't already exist
        dynamodb.put_item(
            TableName=table_name,
            Item=item,
            ConditionExpression='attribute_not_exists(email)'
        )
        
        # Return user data without password hash
        return {
            'email': email,
            'name': name,
            'created_at': created_at
        }
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        
        # Handle duplicate email (conditional check failed)
        if error_code == 'ConditionalCheckFailedException':
            raise DuplicateUserError(f"User with email {email} already exists")
        
        # Handle other DynamoDB errors
        error_message = e.response.get('Error', {}).get('Message', str(e))
        raise DatabaseError(f"Failed to create user: {error_message}") from e
    
    except Exception as e:
        # Handle unexpected errors
        raise DatabaseError(f"Unexpected error creating user: {str(e)}") from e


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
        
        # Return complete user data including password_hash
        return {
            'email': item['email']['S'],
            'name': item['name']['S'],
            'password_hash': item['password_hash']['S'],
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
