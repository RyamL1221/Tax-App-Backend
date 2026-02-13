"""
Unit tests for the response_formatter module.

These tests verify specific examples and edge cases for response formatting functions.
"""

import json
import pytest
from user_registration.response_formatter import (
    success_response,
    validation_error_response,
    duplicate_user_response,
    internal_error_response,
)


class TestSuccessResponse:
    """Unit tests for success_response function."""
    
    def test_returns_201_status_code(self):
        """Test that success response returns 201 status code."""
        response = success_response("user@example.com")
        assert response["statusCode"] == 201
    
    def test_includes_cors_headers(self):
        """Test that success response includes CORS headers."""
        response = success_response("user@example.com")
        headers = response["headers"]
        
        assert "Access-Control-Allow-Origin" in headers
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "Access-Control-Allow-Headers" in headers
        assert headers["Access-Control-Allow-Headers"] == "Content-Type,Authorization"
        assert "Access-Control-Allow-Methods" in headers
        assert headers["Access-Control-Allow-Methods"] == "POST,OPTIONS"
    
    def test_includes_content_type_json(self):
        """Test that success response includes Content-Type: application/json."""
        response = success_response("user@example.com")
        assert response["headers"]["Content-Type"] == "application/json"
    
    def test_body_is_valid_json(self):
        """Test that success response body is valid JSON."""
        response = success_response("user@example.com")
        body = json.loads(response["body"])
        
        assert isinstance(body, dict)
        assert "message" in body
        assert "email" in body
    
    def test_includes_email_in_body(self):
        """Test that success response includes the user's email."""
        email = "test@example.com"
        response = success_response(email)
        body = json.loads(response["body"])
        
        assert body["email"] == email
    
    def test_includes_success_message(self):
        """Test that success response includes a success message."""
        response = success_response("user@example.com")
        body = json.loads(response["body"])
        
        assert body["message"] == "User registered successfully"
    
    def test_does_not_include_password_fields(self):
        """Test that success response does not include password or password_hash."""
        response = success_response("user@example.com")
        body = json.loads(response["body"])
        
        assert "password" not in body
        assert "password_hash" not in body


class TestValidationErrorResponse:
    """Unit tests for validation_error_response function."""
    
    def test_returns_400_status_code(self):
        """Test that validation error response returns 400 status code."""
        response = validation_error_response("Invalid email format")
        assert response["statusCode"] == 400
    
    def test_includes_cors_headers(self):
        """Test that validation error response includes CORS headers."""
        response = validation_error_response("Invalid email format")
        headers = response["headers"]
        
        assert "Access-Control-Allow-Origin" in headers
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Allow-Methods" in headers
    
    def test_includes_content_type_json(self):
        """Test that validation error response includes Content-Type: application/json."""
        response = validation_error_response("Invalid email format")
        assert response["headers"]["Content-Type"] == "application/json"
    
    def test_body_is_valid_json(self):
        """Test that validation error response body is valid JSON."""
        response = validation_error_response("Invalid email format")
        body = json.loads(response["body"])
        
        assert isinstance(body, dict)
        assert "error" in body
    
    def test_includes_error_message(self):
        """Test that validation error response includes the error message."""
        error_msg = "Invalid email format"
        response = validation_error_response(error_msg)
        body = json.loads(response["body"])
        
        assert "Validation failed:" in body["error"]
        assert error_msg in body["error"]
    
    def test_handles_different_error_messages(self):
        """Test that validation error response handles different error messages."""
        messages = [
            "Invalid email format",
            "Password too weak",
            "Name is required",
            "Missing required fields"
        ]
        
        for msg in messages:
            response = validation_error_response(msg)
            body = json.loads(response["body"])
            assert msg in body["error"]


class TestDuplicateUserResponse:
    """Unit tests for duplicate_user_response function."""
    
    def test_returns_409_status_code(self):
        """Test that duplicate user response returns 409 status code."""
        response = duplicate_user_response()
        assert response["statusCode"] == 409
    
    def test_includes_cors_headers(self):
        """Test that duplicate user response includes CORS headers."""
        response = duplicate_user_response()
        headers = response["headers"]
        
        assert "Access-Control-Allow-Origin" in headers
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Allow-Methods" in headers
    
    def test_includes_content_type_json(self):
        """Test that duplicate user response includes Content-Type: application/json."""
        response = duplicate_user_response()
        assert response["headers"]["Content-Type"] == "application/json"
    
    def test_body_is_valid_json(self):
        """Test that duplicate user response body is valid JSON."""
        response = duplicate_user_response()
        body = json.loads(response["body"])
        
        assert isinstance(body, dict)
        assert "error" in body
    
    def test_includes_duplicate_error_message(self):
        """Test that duplicate user response includes appropriate error message."""
        response = duplicate_user_response()
        body = json.loads(response["body"])
        
        assert body["error"] == "Email already registered"


class TestInternalErrorResponse:
    """Unit tests for internal_error_response function."""
    
    def test_returns_500_status_code(self):
        """Test that internal error response returns 500 status code."""
        response = internal_error_response()
        assert response["statusCode"] == 500
    
    def test_includes_cors_headers(self):
        """Test that internal error response includes CORS headers."""
        response = internal_error_response()
        headers = response["headers"]
        
        assert "Access-Control-Allow-Origin" in headers
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Allow-Methods" in headers
    
    def test_includes_content_type_json(self):
        """Test that internal error response includes Content-Type: application/json."""
        response = internal_error_response()
        assert response["headers"]["Content-Type"] == "application/json"
    
    def test_body_is_valid_json(self):
        """Test that internal error response body is valid JSON."""
        response = internal_error_response()
        body = json.loads(response["body"])
        
        assert isinstance(body, dict)
        assert "error" in body
    
    def test_includes_generic_error_message(self):
        """Test that internal error response includes generic error message."""
        response = internal_error_response()
        body = json.loads(response["body"])
        
        assert body["error"] == "Internal server error"
    
    def test_does_not_expose_internal_details(self):
        """Test that internal error response does not expose internal details."""
        response = internal_error_response()
        body = json.loads(response["body"])
        
        # Should only contain generic error message, no stack traces or details
        assert len(body) == 1
        assert "error" in body


class TestCORSHeadersConsistency:
    """Test that all response functions include consistent CORS headers."""
    
    def test_all_responses_have_same_cors_headers(self):
        """Test that all response types include the same CORS headers."""
        responses = [
            success_response("user@example.com"),
            validation_error_response("Test error"),
            duplicate_user_response(),
            internal_error_response()
        ]
        
        # Extract CORS headers from all responses
        cors_headers_list = []
        for response in responses:
            headers = response["headers"]
            cors_headers = {
                k: v for k, v in headers.items()
                if k.startswith("Access-Control-") or k == "Content-Type"
            }
            cors_headers_list.append(cors_headers)
        
        # All CORS headers should be identical
        first_cors_headers = cors_headers_list[0]
        for cors_headers in cors_headers_list[1:]:
            assert cors_headers == first_cors_headers
