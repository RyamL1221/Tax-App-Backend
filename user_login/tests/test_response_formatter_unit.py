"""
Unit tests for response formatter functionality.

These tests verify specific examples and edge cases for response formatting.
"""

import json
import pytest
from user_login.response_formatter import (
    success_response,
    validation_error_response,
    authentication_error_response,
    internal_error_response,
    error_response
)


class TestSuccessResponse:
    """Unit tests for success response."""
    
    def test_success_response_structure(self):
        """
        Test that success response has correct structure.
        
        Validates: Requirements 6.1, 6.2, 5.4
        """
        email = "user@example.com"
        token = "a1b2c3d4e5f6" * 5 + "abcd"  # 64 chars
        
        response = success_response(email, token)
        
        assert response["statusCode"] == 200
        assert "headers" in response
        assert "body" in response
        
        body = json.loads(response["body"])
        assert body["message"] == "Login successful"
        assert body["email"] == email
        assert body["token"] == token
    
    def test_success_response_cors_headers(self):
        """
        Test that success response includes CORS headers.
        
        Validates: Requirements 6.7
        """
        response = success_response("user@example.com", "a" * 64)
        headers = response["headers"]
        
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert headers["Content-Type"] == "application/json"
    
    def test_success_response_password_not_in_response(self):
        """
        Test that password/hash not included in success response.
        
        Validates: Requirements 6.2
        """
        response = success_response("user@example.com", "a" * 64)
        body = json.loads(response["body"])
        
        assert "password" not in body
        assert "password_hash" not in body


class TestValidationErrorResponse:
    """Unit tests for validation error response."""
    
    def test_validation_error_response_structure(self):
        """
        Test that validation error response has correct structure.
        
        Validates: Requirements 6.3
        """
        message = "Invalid email format"
        response = validation_error_response(message)
        
        assert response["statusCode"] == 400
        assert "headers" in response
        assert "body" in response
        
        body = json.loads(response["body"])
        assert "error" in body
        assert message in body["error"]
        assert body["error"].startswith("Validation failed: ")
    
    def test_validation_error_response_cors_headers(self):
        """
        Test that validation error response includes CORS headers.
        
        Validates: Requirements 6.7
        """
        response = validation_error_response("Test error")
        headers = response["headers"]
        
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["Content-Type"] == "application/json"


class TestAuthenticationErrorResponse:
    """Unit tests for authentication error response."""
    
    def test_authentication_error_response_structure(self):
        """
        Test that authentication error response has correct structure.
        
        Validates: Requirements 6.4, 6.5, 7.1
        """
        response = authentication_error_response()
        
        assert response["statusCode"] == 401
        assert "headers" in response
        assert "body" in response
        
        body = json.loads(response["body"])
        assert body["error"] == "Invalid credentials"
    
    def test_authentication_error_response_is_generic(self):
        """
        Test that authentication error uses generic message.
        
        This prevents user enumeration attacks by not revealing whether
        the email exists or the password was incorrect.
        
        Validates: Requirements 6.4, 6.5, 7.1
        """
        response = authentication_error_response()
        body = json.loads(response["body"])
        
        # Should not contain revealing phrases
        error_message = body["error"].lower()
        assert "user not found" not in error_message
        assert "email not found" not in error_message
        assert "incorrect password" not in error_message
        assert "wrong password" not in error_message
    
    def test_authentication_error_response_cors_headers(self):
        """
        Test that authentication error response includes CORS headers.
        
        Validates: Requirements 6.7
        """
        response = authentication_error_response()
        headers = response["headers"]
        
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["Content-Type"] == "application/json"


class TestInternalErrorResponse:
    """Unit tests for internal error response."""
    
    def test_internal_error_response_structure(self):
        """
        Test that internal error response has correct structure.
        
        Validates: Requirements 6.6
        """
        response = internal_error_response()
        
        assert response["statusCode"] == 500
        assert "headers" in response
        assert "body" in response
        
        body = json.loads(response["body"])
        assert body["error"] == "Internal server error"
    
    def test_internal_error_response_cors_headers(self):
        """
        Test that internal error response includes CORS headers.
        
        Validates: Requirements 6.7
        """
        response = internal_error_response()
        headers = response["headers"]
        
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["Content-Type"] == "application/json"


class TestGenericErrorResponse:
    """Unit tests for generic error response."""
    
    def test_error_response_with_custom_status_code(self):
        """
        Test that error response accepts custom status code.
        
        Validates: Requirements 6.3, 6.4, 6.6
        """
        response = error_response(403, "Forbidden")
        
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"] == "Forbidden"
    
    def test_error_response_cors_headers(self):
        """
        Test that error response includes CORS headers.
        
        Validates: Requirements 6.7
        """
        response = error_response(404, "Not found")
        headers = response["headers"]
        
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["Content-Type"] == "application/json"


class TestCORSHeadersConsistency:
    """Unit tests for CORS headers consistency across all responses."""
    
    def test_all_responses_have_same_cors_headers(self):
        """
        Test that all response types have consistent CORS headers.
        
        Validates: Requirements 6.7
        """
        success_resp = success_response("user@example.com", "a" * 64)
        validation_resp = validation_error_response("Test")
        auth_resp = authentication_error_response()
        internal_resp = internal_error_response()
        generic_resp = error_response(404, "Not found")
        
        # All should have the same CORS headers
        cors_origin = success_resp["headers"]["Access-Control-Allow-Origin"]
        assert validation_resp["headers"]["Access-Control-Allow-Origin"] == cors_origin
        assert auth_resp["headers"]["Access-Control-Allow-Origin"] == cors_origin
        assert internal_resp["headers"]["Access-Control-Allow-Origin"] == cors_origin
        assert generic_resp["headers"]["Access-Control-Allow-Origin"] == cors_origin
        
        cors_methods = success_resp["headers"]["Access-Control-Allow-Methods"]
        assert validation_resp["headers"]["Access-Control-Allow-Methods"] == cors_methods
        assert auth_resp["headers"]["Access-Control-Allow-Methods"] == cors_methods
        assert internal_resp["headers"]["Access-Control-Allow-Methods"] == cors_methods
        assert generic_resp["headers"]["Access-Control-Allow-Methods"] == cors_methods
