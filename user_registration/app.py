"""
Lambda handler for user registration endpoint.

This module provides the main entry point for the user registration Lambda function.
It orchestrates validation, password hashing, and user storage in DynamoDB.
"""

import json
import logging
import sys
import os
from typing import Any, Dict

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

from validator import ValidationError, validate_registration_data
from password_hasher import hash_password
from user_repository import create_user, DuplicateUserError, DatabaseError
from response_formatter import (
    success_response,
    validation_error_response,
    duplicate_user_response,
    internal_error_response
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handles user registration requests.
    
    Args:
        event: API Gateway proxy event containing request data
        context: Lambda context object
        
    Returns:
        API Gateway proxy response with status code and body
    """
    # Handle OPTIONS requests for CORS preflight
    http_method = event.get('httpMethod', '')
    if http_method == 'OPTIONS':
        logger.info("OPTIONS request received for CORS preflight")
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': ''
        }
    
    logger.info("User registration request received")
    
    try:
        # Parse API Gateway event and extract request body
        body = event.get('body')
        
        # Handle missing body
        if body is None:
            logger.warning("Request missing body")
            return validation_error_response("Request body is required")
        
        # Handle invalid JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in request body: {str(e)}")
            return validation_error_response("Invalid JSON format")
        
        # Extract email, name, password from body
        email = data.get('email')
        name = data.get('name')
        password = data.get('password')
        
        # Check for missing required fields
        missing_fields = []
        if email is None:
            missing_fields.append('email')
        if name is None:
            missing_fields.append('name')
        if password is None:
            missing_fields.append('password')
        
        if missing_fields:
            missing_fields_str = ', '.join(missing_fields)
            logger.warning(f"Missing required fields: {missing_fields_str}")
            return validation_error_response(f"Missing required fields: {missing_fields_str}")
        
        # Call validator, catch ValidationError and return 400
        try:
            validate_registration_data(email, name, password)
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return validation_error_response(str(e))
        
        # Call password hasher, catch exceptions and return 500
        try:
            password_hash = hash_password(password)
        except Exception as e:
            logger.error(f"Password hashing failed: {str(e)}")
            return internal_error_response()
        
        # Call repository create_user, catch DuplicateUserError and return 409
        try:
            user_data = create_user(email, name, password_hash)
            logger.info(f"User registered successfully: {email}")
            return success_response(email)
        except DuplicateUserError as e:
            logger.warning(f"Duplicate user registration attempt: {email}")
            return duplicate_user_response()
        except DatabaseError as e:
            logger.error(f"Database error: {str(e)}")
            return internal_error_response()
        
    except Exception as e:
        # Catch unexpected exceptions, log, and return 500
        logger.error(f"Unexpected error during user registration: {str(e)}", exc_info=True)
        return internal_error_response()
