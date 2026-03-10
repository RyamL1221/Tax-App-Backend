"""
AWS Lambda handler for reset password endpoint.

This module provides the main entry point for the reset password Lambda function,
orchestrating token validation, password hashing, database updates, and session invalidation.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

from input_validator import InputValidator
from token_validator import TokenValidator
from password_hasher import PasswordHasher
from session_manager import SessionManager
from user_repository import DatabaseError, mark_token_used, update_password
from response_formatter import (
    reset_password_success_response,
    validation_error_response,
    invalid_token_error_response,
    internal_error_response
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handles POST /reset-password requests.
    
    This function orchestrates the password reset process:
    1. Parse and validate request data
    2. Validate reset token
    3. Hash new password
    4. Update password in database
    5. Mark token as used atomically
    6. Invalidate all existing sessions
    7. Return success response
    
    Args:
        event: API Gateway proxy event containing request data
        context: Lambda context object
        
    Returns:
        API Gateway proxy response with status code and body
        
    Security Notes:
        - Validates token hasn't expired or been used
        - Hashes password with bcrypt (work factor 12)
        - Atomically marks token as used to prevent reuse
        - Invalidates all existing JWTs via session version increment
        - Never logs sensitive data (tokens, passwords)
    """
    # Handle OPTIONS requests for CORS preflight
    http_method = event.get('httpMethod', '')
    if http_method == 'OPTIONS':
        logger.info("OPTIONS request received for CORS preflight")
        cors_origin = os.environ.get('CORS_ALLOWED_ORIGIN', '*')
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': cors_origin,
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': ''
        }
    
    # Log request initiation (without sensitive data)
    logger.info("Reset password request initiated")
    
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in request body")
                return validation_error_response("Invalid JSON format")
        
        # Validate input
        validator = InputValidator()
        is_valid, token, new_password, error_message = validator.validate_reset_password_input(body)
        
        if not is_valid:
            logger.warning(f"Validation failed: {error_message}")
            return validation_error_response(error_message)
        
        # Validate reset token
        token_validator = TokenValidator()
        is_token_valid, email, token_error = token_validator.validate_token(token)
        
        if not is_token_valid:
            logger.warning(f"Token validation failed: {token_error}")
            return invalid_token_error_response()
        
        logger.info(f"Token validated successfully for email: {email}")
        
        try:
            # Hash the new password using bcrypt
            password_hasher = PasswordHasher()
            hashed_password = password_hasher.hash_password(new_password)
            logger.info(f"New password hashed for email: {email}")
            
            # Update password in database
            update_password(email, hashed_password)
            logger.info(f"Password updated in database for email: {email}")
            
            # Mark token as used atomically
            # We need to compute the token hash again
            try:
                token_hash = token_validator._get_token_hash(token)
            except ValueError:
                # This shouldn't happen since we already validated the token
                logger.error("Failed to compute token hash after validation")
                return internal_error_response()
            
            token_marked = mark_token_used(token_hash)
            if not token_marked:
                # Token was already used (race condition)
                logger.warning(f"Token already used (race condition) for email: {email}")
                return invalid_token_error_response()
            
            logger.info(f"Token marked as used for email: {email}")
            
            # Invalidate all existing sessions
            session_manager = SessionManager()
            session_manager.invalidate_all_sessions(email)
            logger.info(f"All sessions invalidated for email: {email}")
            
            # Log successful password reset for audit
            logger.info(f"Password reset completed successfully for email: {email}")
            
        except DatabaseError as e:
            # Database error - log and return 500
            logger.error(f"Database error during password reset: {str(e)}")
            return internal_error_response()
        except Exception as e:
            # Unexpected error - log and return 500
            logger.error(f"Unexpected error during password reset: {type(e).__name__}: {str(e)}", exc_info=True)
            return internal_error_response()
        
        # Return success response
        return reset_password_success_response()
        
    except Exception as e:
        # Catch unexpected exceptions at the top level
        logger.error(f"Unexpected error in reset password handler: {type(e).__name__}: {str(e)}", exc_info=True)
        return internal_error_response()


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Alias for lambda_handler to support different invocation patterns.
    """
    return lambda_handler(event, context)
