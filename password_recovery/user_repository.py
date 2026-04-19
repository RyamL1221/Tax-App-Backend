"""
DynamoDB repository for password recovery operations.

This module handles reset token storage and retrieval in DynamoDB,
including atomic token invalidation and session version management.
"""

import os
from datetime import datetime, timezone
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError


class DatabaseError(Exception):
    """Raised when a database operation fails."""
    pass


class TokenAlreadyUsedError(Exception):
    """Raised when attempting to mark an already-used token as used."""
    pass


def store_reset_token(email: str, token_hash: str, expiration: datetime) -> bool:
    """
    Stores a password reset token hash for a user.
    
    Creates/updates a reset_token item in DynamoDB with:
    - token_hash (partition key)
    - email
    - expiration (ISO 8601 timestamp)
    - used_at (initially None)
    - created_at (ISO 8601 timestamp)
    
    Args:
        email: User's email address
        token_hash: SHA-256 hash of the reset token
        expiration: Token expiration timestamp
        
    Returns:
        True if token was stored successfully
        
    Raises:
        DatabaseError: If the database operation fails
        
    Examples:
        >>> from datetime import datetime, timedelta, timezone
        >>> exp = datetime.now(timezone.utc) + timedelta(hours=1)
        >>> store_reset_token("user@example.com", "abc123hash", exp)
        True
    """
    # Get table name from environment variable
    table_name = os.environ.get('RESET_TOKENS_TABLE_NAME')
    if not table_name:
        raise DatabaseError("RESET_TOKENS_TABLE_NAME environment variable not set")
    
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
    
    # Generate ISO 8601 timestamp for created_at
    created_at = datetime.now(timezone.utc).isoformat()
    
    # Convert expiration to ISO 8601 string
    expiration_str = expiration.isoformat()
    
    # Prepare item for DynamoDB
    item = {
        'token_hash': {'S': token_hash},
        'email': {'S': email},
        'expiration': {'S': expiration_str},
        'created_at': {'S': created_at}
        # Note: used_at is not included initially (NULL in DynamoDB)
    }
    
    try:
        # Put item in DynamoDB (will overwrite if token_hash already exists)
        dynamodb.put_item(
            TableName=table_name,
            Item=item
        )
        
        logger.info(f"Stored reset token for email: {email}")
        return True
        
    except ClientError as e:
        # Handle DynamoDB client errors
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to store reset token: {error_message}")
        raise DatabaseError(f"Failed to store reset token: {error_message}") from e
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error storing reset token: {str(e)}")
        raise DatabaseError(f"Unexpected error storing reset token: {str(e)}") from e


def get_reset_token(token_hash: str) -> Optional[Dict[str, str]]:
    """
    Retrieves reset token data by hash.
    
    Returns dict with:
    - email
    - expiration
    - used_at
    - created_at
    
    Returns None if token doesn't exist.
    
    Args:
        token_hash: SHA-256 hash of the reset token
        
    Returns:
        Dictionary containing token data, or None if token doesn't exist:
        {
            "email": "user@example.com",
            "expiration": "2024-01-15T11:30:00+00:00",
            "used_at": "2024-01-15T10:45:00+00:00" or None,
            "created_at": "2024-01-15T10:30:00+00:00"
        }
        
    Raises:
        DatabaseError: If the database operation fails
        
    Examples:
        >>> token = get_reset_token("abc123hash")
        >>> token["email"]
        'user@example.com'
    """
    # Get table name from environment variable
    table_name = os.environ.get('RESET_TOKENS_TABLE_NAME')
    if not table_name:
        raise DatabaseError("RESET_TOKENS_TABLE_NAME environment variable not set")
    
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
        # Get item from DynamoDB using token_hash as partition key
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                'token_hash': {'S': token_hash}
            }
        )
        
        # Check if item exists
        if 'Item' not in response:
            logger.info(f"Reset token not found: {token_hash[:8]}...")
            return None
        
        # Extract item data
        item = response['Item']
        
        # Return token data
        result = {
            'email': item['email']['S'],
            'expiration': item['expiration']['S'],
            'created_at': item['created_at']['S'],
            'used_at': item.get('used_at', {}).get('S')  # May be None
        }
        
        logger.info(f"Retrieved reset token for email: {result['email']}")
        return result
        
    except ClientError as e:
        # Handle DynamoDB client errors
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to retrieve reset token: {error_message}")
        raise DatabaseError(f"Failed to retrieve reset token: {error_message}") from e
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error retrieving reset token: {str(e)}")
        raise DatabaseError(f"Unexpected error retrieving reset token: {str(e)}") from e


def mark_token_used(token_hash: str) -> bool:
    """
    Atomically marks a token as used.
    
    Sets used_at to current timestamp.
    Uses conditional update to ensure token hasn't been used already.
    Returns False if token was already used (race condition).
    
    Args:
        token_hash: SHA-256 hash of the reset token
        
    Returns:
        True if token was successfully marked as used
        False if token was already used (race condition)
        
    Raises:
        DatabaseError: If the database operation fails for reasons other than
                      the token already being used
        
    Examples:
        >>> mark_token_used("abc123hash")
        True
        >>> mark_token_used("abc123hash")  # Second call
        False
    """
    # Get table name from environment variable
    table_name = os.environ.get('RESET_TOKENS_TABLE_NAME')
    if not table_name:
        raise DatabaseError("RESET_TOKENS_TABLE_NAME environment variable not set")
    
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
    
    # Generate ISO 8601 timestamp for used_at
    used_at = datetime.now(timezone.utc).isoformat()
    
    try:
        # Update item with conditional check that used_at doesn't exist
        # This ensures atomic operation and prevents race conditions
        dynamodb.update_item(
            TableName=table_name,
            Key={
                'token_hash': {'S': token_hash}
            },
            UpdateExpression='SET used_at = :used_at',
            ExpressionAttributeValues={
                ':used_at': {'S': used_at}
            },
            ConditionExpression='attribute_not_exists(used_at)'
        )
        
        logger.info(f"Marked reset token as used: {token_hash[:8]}...")
        return True
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        
        # Handle conditional check failure (token already used)
        if error_code == 'ConditionalCheckFailedException':
            logger.warning(f"Token already used: {token_hash[:8]}...")
            return False
        
        # Handle other DynamoDB errors
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to mark token as used: {error_message}")
        raise DatabaseError(f"Failed to mark token as used: {error_message}") from e
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error marking token as used: {str(e)}")
        raise DatabaseError(f"Unexpected error marking token as used: {str(e)}") from e


def increment_session_version(email: str) -> int:
    """
    Atomically increments the session version for a user.
    
    Returns the new session version number.
    Used to invalidate all existing JWTs.
    
    Args:
        email: User's email address
        
    Returns:
        The new session version number after incrementing
        
    Raises:
        DatabaseError: If the database operation fails
        
    Examples:
        >>> increment_session_version("user@example.com")
        1
        >>> increment_session_version("user@example.com")
        2
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
        # Atomically increment session_version using ADD operation
        # ADD will initialize to 0 and then add 1 if attribute doesn't exist
        response = dynamodb.update_item(
            TableName=table_name,
            Key={
                'email': {'S': email}
            },
            UpdateExpression='ADD session_version :inc',
            ExpressionAttributeValues={
                ':inc': {'N': '1'}
            },
            ReturnValues='UPDATED_NEW'
        )
        
        # Extract the new session version from the response
        new_version = int(response['Attributes']['session_version']['N'])
        
        logger.info(f"Incremented session version for {email} to {new_version}")
        return new_version
        
    except ClientError as e:
        # Handle DynamoDB client errors
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to increment session version: {error_message}")
        raise DatabaseError(f"Failed to increment session version: {error_message}") from e
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error incrementing session version: {str(e)}")
        raise DatabaseError(f"Unexpected error incrementing session version: {str(e)}") from e


def get_session_version(email: str) -> int:
    """
    Retrieves the current session version for a user.
    
    Returns 0 if no version exists (backward compatibility).
    
    Args:
        email: User's email address
        
    Returns:
        The current session version number (0 if not set)
        
    Raises:
        DatabaseError: If the database operation fails
        
    Examples:
        >>> get_session_version("user@example.com")
        0
        >>> increment_session_version("user@example.com")
        1
        >>> get_session_version("user@example.com")
        1
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
            logger.warning(f"User with email {email} not found, returning version 0")
            return 0
        
        # Extract session_version, default to 0 if not present (backward compatibility)
        item = response['Item']
        session_version = int(item.get('session_version', {}).get('N', '0'))
        
        logger.info(f"Retrieved session version for {email}: {session_version}")
        return session_version
        
    except ClientError as e:
        # Handle DynamoDB client errors
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to retrieve session version: {error_message}")
        raise DatabaseError(f"Failed to retrieve session version: {error_message}") from e
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error retrieving session version: {str(e)}")
        raise DatabaseError(f"Unexpected error retrieving session version: {str(e)}") from e


def user_exists(email: str) -> bool:
    """
    Checks if a user with the given email exists.
    
    Args:
        email: User's email address
        
    Returns:
        True if user exists, False otherwise
        
    Raises:
        DatabaseError: If the database operation fails
        
    Examples:
        >>> user_exists("user@example.com")
        True
        >>> user_exists("nonexistent@example.com")
        False
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
    logger.debug(f"DynamoDB Config - Region: {region}, Endpoint: {endpoint_url}, Table: {table_name}")
    
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
        exists = 'Item' in response
        logger.debug(f"User existence check for {email}: {exists}")
        return exists
        
    except ClientError as e:
        # Handle DynamoDB client errors
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to check user existence: {error_message}")
        raise DatabaseError(f"Failed to check user existence: {error_message}") from e
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error checking user existence: {str(e)}")
        raise DatabaseError(f"Unexpected error checking user existence: {str(e)}") from e


def update_password(email: str, hashed_password: str) -> bool:
    """
    Updates a user's password.
    
    Args:
        email: User's email address
        hashed_password: Bcrypt hash of the new password
        
    Returns:
        True if password was updated successfully
        
    Raises:
        DatabaseError: If the database operation fails
        
    Examples:
        >>> update_password("user@example.com", "$2b$12$...")
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
        # Update the user's password
        dynamodb.update_item(
            TableName=table_name,
            Key={
                'email': {'S': email}
            },
            UpdateExpression='SET password_hash = :password',
            ExpressionAttributeValues={
                ':password': {'S': hashed_password}
            }
        )
        
        logger.info(f"Updated password for user: {email}")
        return True
        
    except ClientError as e:
        # Handle DynamoDB client errors
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to update password: {error_message}")
        raise DatabaseError(f"Failed to update password: {error_message}") from e
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error updating password: {str(e)}")
        raise DatabaseError(f"Unexpected error updating password: {str(e)}") from e
