"""
Logger Module

This module provides structured logging utilities for the tax document generation feature.
Ensures sensitive data is never logged and error messages are sanitized.
"""

import logging
import json
import re
from typing import Dict, Any, Optional


# Configure structured logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Sensitive field patterns to exclude from logs
SENSITIVE_FIELDS = [
    'ssn', 'socialSecurityNumber', 'social_security_number',
    'income', 'wages', 'salary', 'earnings',
    'bankAccount', 'bank_account', 'accountNumber', 'account_number',
    'routingNumber', 'routing_number',
    'password', 'secret', 'token', 'apiKey', 'api_key'
]


def sanitize_data(data: Any) -> Any:
    """
    Sanitize data by removing sensitive information.
    
    Args:
        data: Data to sanitize (dict, list, or primitive)
        
    Returns:
        Sanitized data with sensitive fields redacted
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Check if key is sensitive
            if any(sensitive.lower() in key.lower() for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = sanitize_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    else:
        return data


def sanitize_error_message(error_message: str) -> str:
    """
    Sanitize error message by removing internal system details.
    
    Args:
        error_message: Raw error message
        
    Returns:
        Sanitized error message without stack traces or AWS resource names
    """
    # Remove stack traces
    if 'Traceback' in error_message or 'File "' in error_message:
        # Extract just the error type and message
        lines = error_message.split('\n')
        for line in reversed(lines):
            if line.strip() and not line.startswith(' '):
                error_message = line
                break
    
    # Remove AWS resource ARNs
    error_message = re.sub(r'arn:aws:[a-z0-9-]+:[a-z0-9-]*:(\d{12})?:[^\s]+', '[AWS_RESOURCE]', error_message)
    
    # Remove file paths
    error_message = re.sub(r'/[a-zA-Z0-9_/.-]+\.py', '[FILE]', error_message)
    
    # Remove IP addresses
    error_message = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_ADDRESS]', error_message)
    
    return error_message


def log_error(job_id: str, error: Exception, context: Optional[Dict] = None) -> None:
    """
    Log an error with context.
    
    Args:
        job_id: Job identifier
        error: Exception that occurred
        context: Additional context (will be sanitized)
    """
    sanitized_context = sanitize_data(context) if context else {}
    
    log_entry = {
        'level': 'ERROR',
        'jobId': job_id,
        'errorType': type(error).__name__,
        'errorMessage': sanitize_error_message(str(error)),
        'context': sanitized_context
    }
    
    logger.error(json.dumps(log_entry))


def log_success(job_id: str, duration_ms: float, context: Optional[Dict] = None) -> None:
    """
    Log a successful operation.
    
    Args:
        job_id: Job identifier
        duration_ms: Processing duration in milliseconds
        context: Additional context (will be sanitized)
    """
    sanitized_context = sanitize_data(context) if context else {}
    
    log_entry = {
        'level': 'INFO',
        'jobId': job_id,
        'duration_ms': duration_ms,
        'status': 'SUCCESS',
        'context': sanitized_context
    }
    
    logger.info(json.dumps(log_entry))


def log_info(message: str, context: Optional[Dict] = None) -> None:
    """
    Log an informational message.
    
    Args:
        message: Log message
        context: Additional context (will be sanitized)
    """
    sanitized_context = sanitize_data(context) if context else {}
    
    log_entry = {
        'level': 'INFO',
        'message': message,
        'context': sanitized_context
    }
    
    logger.info(json.dumps(log_entry))
