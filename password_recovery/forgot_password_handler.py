"""
AWS Lambda handler for forgot password endpoint.

This module provides the main entry point for the forgot password Lambda function,
orchestrating validation, token generation, email delivery, and response formatting.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

from input_validator import InputValidator
from rate_limiter import RateLimiter
from token_generator import TokenGenerator
from user_repository import store_reset_token, DatabaseError, user_exists
from email_service import EmailService
from response_formatter import (
    forgot_password_success_response,
    validation_error_response,
    rate_limit_error_response,
    internal_error_response
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handles POST /forgot-password requests.
    
    This function orchestrates the password reset initiation process:
    1. Parse and validate request data
    2. Check rate limits
    3. Look up user by email (if exists)
    4. Generate reset token
    5. Store token hash in database
    6. Send reset email
    7. Return generic success response (non-enumeration)
    
    Args:
        event: API Gateway proxy event containing request data
        context: Lambda context object
        
    Returns:
        API Gateway proxy response with status code and body
        
    Security Notes:
        - Returns generic success message regardless of whether email exists
        - Rate limits requests to prevent abuse
        - Never logs sensitive data (tokens, passwords)
        - Email delivery failures don't expose account existence
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
    logger.info("Forgot password request initiated")
    
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
        is_valid, email, error_message = validator.validate_forgot_password_input(body)
        
        if not is_valid:
            logger.warning(f"Validation failed: {error_message}")
            return validation_error_response(error_message)
        
        # Extract client IP for rate limiting
        # API Gateway provides this in requestContext.identity.sourceIp
        client_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        logger.info(f"Request from IP: {client_ip}")
        
        # Check rate limit
        rate_limiter = RateLimiter()
        allowed, retry_after = rate_limiter.check_rate_limit(client_ip)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            # Record the blocked request for monitoring
            return rate_limit_error_response(retry_after)
        
        # Record this request for rate limiting
        rate_limiter.record_request(client_ip)
        
        # Look up user by email
        # We need to check if the user exists, but we'll return the same response either way
        user_found = False
        try:
            user_found = user_exists(email)
            if user_found:
                logger.info(f"User found for email: {email}")
            else:
                logger.info(f"User not found for email: {email} (non-enumeration response)")
        except DatabaseError as e:
            # Database error - log and return 500
            logger.error(f"Database error looking up user: {str(e)}")
            return internal_error_response()
        
        # If user exists, generate token and send email
        if user_found:
            try:
                # Generate reset token
                token_generator = TokenGenerator()
                plaintext_token, token_hash, expiration = token_generator.generate_reset_token(email)
                logger.info(f"Generated reset token for email: {email}")
                
                # DEV ONLY: Log plaintext token for local testing (LocalStack doesn't send real emails)
                aws_endpoint = os.environ.get('AWS_ENDPOINT_URL', '')
                if aws_endpoint and ('localstack' in aws_endpoint.lower() or 
                                     'localhost' in aws_endpoint.lower() or 
                                     '172.18.0.1' in aws_endpoint or
                                     '127.0.0.1' in aws_endpoint):
                    logger.info(f"[DEV ONLY] Reset token for {email}: {plaintext_token}")
                    logger.info(f"[DEV ONLY] Reset link: {os.environ.get('BASE_URL', 'http://localhost:3000')}/reset-password?token={plaintext_token}")
                
                # Store token hash in database
                store_reset_token(email, token_hash, expiration)
                logger.info(f"Stored reset token hash for email: {email}")
                
                # Send reset email
                email_service = EmailService()
                email_sent = email_service.send_reset_email(email, plaintext_token, expiration)
                
                if email_sent:
                    logger.info(f"Reset email sent successfully to: {email}")
                else:
                    # Email delivery failed - log but don't expose to client
                    logger.error(f"Failed to send reset email to: {email}")
                    # Still return success for non-enumeration
                
            except DatabaseError as e:
                # Database error storing token - log and return 500
                logger.error(f"Database error storing reset token: {str(e)}")
                return internal_error_response()
            except Exception as e:
                # Unexpected error - log and return 500
                logger.error(f"Unexpected error processing reset request: {type(e).__name__}: {str(e)}", exc_info=True)
                return internal_error_response()
        
        # Always return generic success response (non-enumeration)
        logger.info("Forgot password request completed successfully")
        return forgot_password_success_response()
        
    except Exception as e:
        # Catch unexpected exceptions at the top level
        logger.error(f"Unexpected error in forgot password handler: {type(e).__name__}: {str(e)}", exc_info=True)
        return internal_error_response()


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Alias for lambda_handler to support different invocation patterns.
    """
    return lambda_handler(event, context)
