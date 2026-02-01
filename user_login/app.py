"""
AWS Lambda handler for user login endpoint.

This module provides the main entry point for the login Lambda function,
orchestrating validation, authentication, token generation, and response
formatting.
"""

import json
import logging
import os
from typing import Any, Dict

from validator import validate_login_data, ValidationError
from user_repository import get_user_by_email, UserNotFoundError, DatabaseError
from password_verifier import verify_password, InvalidCredentialsError
from token_generator import generate_jwt_token
from response_formatter import (
    success_response,
    validation_error_response,
    authentication_error_response,
    internal_error_response
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handles user login requests.
    
    This function orchestrates the login process:
    1. Parse and validate request data
    2. Retrieve user from database
    3. Verify password
    4. Generate authentication token
    5. Return appropriate response
    
    Args:
        event: API Gateway proxy event containing request data
        context: Lambda context object
        
    Returns:
        API Gateway proxy response with status code and body
        
    Security Notes:
        - Uses generic error messages for authentication failures to prevent
          user enumeration attacks
        - Logs authentication attempts but never logs passwords or hashes
        - Uses constant-time password comparison to prevent timing attacks
    """
    # Log request initiation (without sensitive data)
    logger.info("Login request initiated")
    
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in request body")
                return validation_error_response("Invalid JSON format")
        
        # Extract email and password
        email = body.get('email', '')
        password = body.get('password', '')
        
        # Check for missing fields
        if not email and not password:
            logger.warning("Login attempt with missing email and password")
            return validation_error_response("Missing required fields: email, password")
        elif not email:
            logger.warning("Login attempt with missing email")
            return validation_error_response("Missing required field: email")
        elif not password:
            logger.warning(f"Login attempt with missing password for email: {email}")
            return validation_error_response("Missing required field: password")
        
        # Validate input data
        try:
            validate_login_data(email, password)
        except ValidationError as e:
            logger.warning(f"Validation failed for email {email}: {str(e)}")
            return validation_error_response(str(e))
        
        # Retrieve user from database
        try:
            user = get_user_by_email(email)
        except UserNotFoundError:
            # Log failed attempt for security monitoring
            logger.warning(f"Failed login attempt: user not found for email {email}")
            # Return generic error to prevent user enumeration
            return authentication_error_response()
        except DatabaseError as e:
            # Log database error with context
            logger.error(f"Database error during login for email {email}: {str(e)}")
            return internal_error_response()
        
        # Verify password
        try:
            verify_password(password, user['password_hash'])
        except InvalidCredentialsError:
            # Log failed attempt for security monitoring
            logger.warning(f"Failed login attempt: incorrect password for email {email}")
            # Return generic error to prevent revealing password was wrong
            return authentication_error_response()
        
        # Get JWT secret key from environment
        jwt_secret_key = os.environ.get('JWT_SECRET_KEY')
        if not jwt_secret_key:
            logger.error("JWT_SECRET_KEY environment variable not set")
            return internal_error_response()
        
        # Generate JWT authentication token
        try:
            token = generate_jwt_token(email, jwt_secret_key)
        except ValueError as e:
            logger.error(f"JWT token generation failed: {str(e)}")
            return internal_error_response()
        
        # Log successful login (without sensitive data)
        logger.info(f"Login successful for email: {email}")
        
        # Return success response
        return success_response(email, token)
        
    except Exception as e:
        # Log unexpected error with context
        logger.error(f"Unexpected error during login: {type(e).__name__}: {str(e)}", exc_info=True)
        return internal_error_response()
