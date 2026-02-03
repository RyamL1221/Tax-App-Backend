"""
Property and Example Tests: Logging

Feature: tax-document-generation
Property 19: Sensitive Data Exclusion from Logs
Property 20: Error Message Sanitization
Example 2: Error Logging with Context
Example 3: Success Logging

Tests logging behavior for security and completeness.
**Validates: Requirements 9.1, 9.2, 9.3, 9.4**
"""

import json
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock
from tax_document_generation.logger import (
    log_error,
    log_success,
    sanitize_data,
    sanitize_error_message
)


@st.composite
def form_data_with_sensitive_fields(draw):
    """Generate form data with sensitive fields."""
    return {
        "firstName": draw(st.text(min_size=1, max_size=50)),
        "lastName": draw(st.text(min_size=1, max_size=50)),
        "ssn": draw(st.from_regex(r'\d{3}-\d{2}-\d{4}', fullmatch=True)),
        "income": draw(st.integers(min_value=0, max_value=10000000)),
        "bankAccount": draw(st.from_regex(r'\d{10,12}', fullmatch=True))
    }


@settings(max_examples=20)
@given(form_data=form_data_with_sensitive_fields())
def test_sensitive_data_exclusion_from_logs(form_data):
    """
    Property 19: For any error or success log entry, the log should not
    contain sensitive user data such as SSN, income values, or other PII
    from form fields.
    
    This ensures user privacy and security compliance.
    """
    # Sanitize the data
    sanitized = sanitize_data(form_data)
    
    # Verify sensitive fields are redacted
    assert sanitized['ssn'] == '[REDACTED]'
    assert sanitized['income'] == '[REDACTED]'
    assert sanitized['bankAccount'] == '[REDACTED]'
    
    # Verify non-sensitive fields are preserved
    assert sanitized['firstName'] == form_data['firstName']
    assert sanitized['lastName'] == form_data['lastName']
    
    # Verify the original data is not modified
    assert form_data['ssn'] != '[REDACTED]'


@st.composite
def error_messages_with_internal_details(draw):
    """Generate error messages with internal system details."""
    error_types = [
        "Traceback (most recent call last):\n  File \"/app/handler.py\", line 42, in lambda_handler\n    raise Exception('Database connection failed')\nException: Database connection failed",
        "Failed to connect to arn:aws:dynamodb:us-east-1:123456789012:table/JobsTable",
        "Error in /var/task/tax_document_generation/app.py at line 123",
        "Connection refused at 192.168.1.100:5432"
    ]
    return draw(st.sampled_from(error_types))


@settings(max_examples=20)
@given(error_message=error_messages_with_internal_details())
def test_error_message_sanitization(error_message):
    """
    Property 20: For any error response, the error message should not
    expose internal system details such as stack traces, AWS resource names,
    or internal error codes.
    
    This prevents information leakage to potential attackers.
    """
    sanitized = sanitize_error_message(error_message)
    
    # Verify stack traces are removed
    assert 'Traceback' not in sanitized
    assert 'File "' not in sanitized
    
    # Verify AWS ARNs are redacted
    assert 'arn:aws:' not in sanitized
    if 'arn:aws:' in error_message:
        assert '[AWS_RESOURCE]' in sanitized
    
    # Verify file paths are redacted
    assert '/var/task/' not in sanitized
    assert '/app/' not in sanitized
    
    # Verify IP addresses are redacted
    assert not any(char.isdigit() and '.' in sanitized for char in sanitized.split())


def test_error_logging_with_context():
    """
    Example 2: Error Logging with Context
    
    When an error occurs during generation, the system should log an error
    entry containing at minimum: timestamp, error type, jobId, and error message.
    
    **Validates: Requirements 9.1**
    """
    with patch('tax_document_generation.logger.logger') as mock_logger:
        job_id = "job-123"
        error = Exception("Template not found")
        context = {"documentType": "1040", "userId": "user-456"}
        
        log_error(job_id, error, context)
        
        # Verify logger was called
        mock_logger.error.assert_called_once()
        
        # Parse the log entry
        log_call = mock_logger.error.call_args[0][0]
        log_entry = json.loads(log_call)
        
        # Verify required fields are present
        assert 'level' in log_entry
        assert log_entry['level'] == 'ERROR'
        assert 'jobId' in log_entry
        assert log_entry['jobId'] == job_id
        assert 'errorType' in log_entry
        assert log_entry['errorType'] == 'Exception'
        assert 'errorMessage' in log_entry
        assert 'Template not found' in log_entry['errorMessage']
        assert 'context' in log_entry


def test_success_logging():
    """
    Example 3: Success Logging
    
    When a document is successfully generated, the system should log a
    success entry containing jobId and processing duration in milliseconds.
    
    **Validates: Requirements 9.4**
    """
    with patch('tax_document_generation.logger.logger') as mock_logger:
        job_id = "job-789"
        duration_ms = 1234.56
        context = {"documentType": "1040"}
        
        log_success(job_id, duration_ms, context)
        
        # Verify logger was called
        mock_logger.info.assert_called_once()
        
        # Parse the log entry
        log_call = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call)
        
        # Verify required fields are present
        assert 'level' in log_entry
        assert log_entry['level'] == 'INFO'
        assert 'jobId' in log_entry
        assert log_entry['jobId'] == job_id
        assert 'duration_ms' in log_entry
        assert log_entry['duration_ms'] == duration_ms
        assert 'status' in log_entry
        assert log_entry['status'] == 'SUCCESS'


def test_sanitize_nested_sensitive_data():
    """
    Unit test: Verify nested sensitive data is sanitized.
    """
    data = {
        "user": {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "contact": {
                "email": "john@example.com",
                "income": 75000
            }
        }
    }
    
    sanitized = sanitize_data(data)
    
    assert sanitized['user']['name'] == "John Doe"
    assert sanitized['user']['ssn'] == '[REDACTED]'
    assert sanitized['user']['contact']['email'] == "john@example.com"
    assert sanitized['user']['contact']['income'] == '[REDACTED]'


def test_sanitize_list_with_sensitive_data():
    """
    Unit test: Verify lists containing sensitive data are sanitized.
    """
    data = [
        {"name": "Alice", "ssn": "111-11-1111"},
        {"name": "Bob", "income": 50000}
    ]
    
    sanitized = sanitize_data(data)
    
    assert sanitized[0]['name'] == "Alice"
    assert sanitized[0]['ssn'] == '[REDACTED]'
    assert sanitized[1]['name'] == "Bob"
    assert sanitized[1]['income'] == '[REDACTED]'


def test_sanitize_error_with_stack_trace():
    """
    Unit test: Verify stack traces are removed from error messages.
    """
    error_message = """Traceback (most recent call last):
  File "/app/handler.py", line 42, in lambda_handler
    raise ValueError('Invalid input')
ValueError: Invalid input"""
    
    sanitized = sanitize_error_message(error_message)
    
    assert 'Traceback' not in sanitized
    assert 'File' not in sanitized
    assert 'ValueError: Invalid input' in sanitized or 'Invalid input' in sanitized


def test_sanitize_error_with_aws_arn():
    """
    Unit test: Verify AWS ARNs are redacted from error messages.
    """
    error_message = "Failed to access arn:aws:s3:::my-bucket/templates/1040.pdf"
    
    sanitized = sanitize_error_message(error_message)
    
    assert 'arn:aws:' not in sanitized
    assert '[AWS_RESOURCE]' in sanitized


def test_log_error_without_context():
    """
    Unit test: Verify error logging works without context.
    """
    with patch('tax_document_generation.logger.logger') as mock_logger:
        job_id = "job-999"
        error = ValueError("Invalid document type")
        
        log_error(job_id, error)
        
        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args[0][0]
        log_entry = json.loads(log_call)
        
        assert log_entry['jobId'] == job_id
        assert log_entry['errorType'] == 'ValueError'


def test_log_success_without_context():
    """
    Unit test: Verify success logging works without context.
    """
    with patch('tax_document_generation.logger.logger') as mock_logger:
        job_id = "job-888"
        duration_ms = 500.0
        
        log_success(job_id, duration_ms)
        
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call)
        
        assert log_entry['jobId'] == job_id
        assert log_entry['duration_ms'] == duration_ms
