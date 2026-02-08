"""
Custom Exceptions for Document Download Lambda

This module defines custom exceptions for different error scenarios
in the document download workflow.
"""


class AuthenticationError(Exception):
    """Raised when JWT validation fails."""
    pass


class AuthorizationError(Exception):
    """Raised when user doesn't have permission to access a document."""
    pass


class JobNotFoundError(Exception):
    """Raised when job record doesn't exist in DynamoDB."""
    pass


class DocumentNotFoundError(Exception):
    """Raised when S3 document doesn't exist."""
    pass


class DocumentGenerationFailedError(Exception):
    """Raised when job status is FAILED."""
    pass


class DatabaseError(Exception):
    """Raised when DynamoDB operation fails."""
    pass


class S3Error(Exception):
    """Raised when S3 operation fails."""
    pass
