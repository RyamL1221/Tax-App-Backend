"""
Custom exceptions for the tax document generation feature.

This module defines exception classes used throughout the tax document generation
system to handle various error conditions including authentication failures,
validation errors, template retrieval issues, document generation failures,
and S3 operation errors.
"""


class AuthenticationError(Exception):
    """
    Raised when JWT validation fails.
    
    This exception is raised when:
    - JWT token is invalid or malformed
    - JWT token has expired
    - JWT token signature verification fails
    - Authorization header is missing or malformed
    
    Requirements: 1.4, 8.1, 8.3
    """
    pass


class ValidationError(Exception):
    """
    Raised when form data validation fails.
    
    This exception is raised when:
    - Required form fields are missing
    - Field values have invalid data types
    - Field values have invalid formats (e.g., SSN format)
    - Field values are out of acceptable ranges
    - Document type is invalid or unsupported
    
    Requirements: 1.4, 2.1, 2.2, 2.3
    """
    pass


class TemplateNotFoundError(Exception):
    """
    Raised when IRS template is not found in S3.
    
    This exception is raised when:
    - The requested document type template does not exist in the Template_Store
    - The S3 key for the template cannot be found
    
    Requirements: 3.3, 9.3
    """
    pass


class GenerationError(Exception):
    """
    Raised when document generation fails.
    
    This exception is raised when:
    - PDF generation process fails
    - Template file is corrupted or invalid
    - Form field mapping fails
    - PDF flattening operation fails
    - Any other error occurs during document generation
    
    Requirements: 1.4, 9.3
    """
    pass


class S3Error(Exception):
    """
    Raised when S3 operations fail.
    
    This exception is raised when:
    - S3 GetObject operation fails (other than NoSuchKey)
    - S3 PutObject operation fails
    - S3 connection or network errors occur
    - S3 permission errors occur
    - Any other S3-related error occurs
    
    Requirements: 9.3
    """
    pass
