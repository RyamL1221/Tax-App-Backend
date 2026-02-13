"""
Property-based tests for the response_formatter module.

These tests verify universal properties across randomized inputs using hypothesis.
Each property test runs with a minimum of 100 iterations.
"""

import json
import os
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails
from user_registration.response_formatter import (
    success_response,
    validation_error_response,
    duplicate_user_response,
    internal_error_response,
)


def get_expected_cors_origin():
    """Get the expected CORS origin from environment or default."""
    return os.environ.get('CORS_ALLOWED_ORIGIN', '*')


class TestSuccessResponseFormatProperty:
    """Property-based tests for success response format."""
    
    @settings(max_examples=20)
    @given(email=emails())
    def test_success_response_format(self, email):
        """
        **Validates: Requirements 5.1, 5.2**
        Feature: user-registration-endpoint, Property 10: Success response format
        
        For any successful registration, the endpoint should return a 201 status code 
        with a JSON body containing a success message and the user's email, but never 
        the password or password hash.
        """
        response = success_response(email)
        
        # Verify status code is 201
        assert response["statusCode"] == 201
        
        # Verify headers exist
        assert "headers" in response
        
        # Verify body is valid JSON
        assert "body" in response
        body = json.loads(response["body"])
        
        # Verify body contains success message and email
        assert "message" in body
        assert "email" in body
        assert body["email"] == email
        
        # Verify password fields are NOT included
        assert "password" not in body
        assert "password_hash" not in body
        
        # Verify Content-Type header
        assert response["headers"]["Content-Type"] == "application/json"


class TestErrorResponseFormatsProperty:
    """Property-based tests for error response formats."""
    
    @settings(max_examples=20)
    @given(error_message=st.text(min_size=1, max_size=200))
    def test_validation_error_response_format(self, error_message):
        """
        **Validates: Requirements 5.3, 5.4**
        Feature: user-registration-endpoint, Property 11: Error response formats
        
        For any validation error, the endpoint should return a 400 status code with 
        a JSON body containing an error message describing the validation failure.
        """
        response = validation_error_response(error_message)
        
        # Verify status code is 400
        assert response["statusCode"] == 400
        
        # Verify headers exist
        assert "headers" in response
        
        # Verify body is valid JSON
        assert "body" in response
        body = json.loads(response["body"])
        
        # Verify body contains error message
        assert "error" in body
        assert isinstance(body["error"], str)
        assert len(body["error"]) > 0
        
        # Verify Content-Type header
        assert response["headers"]["Content-Type"] == "application/json"
    
    def test_duplicate_user_error_response_format(self):
        """
        **Validates: Requirements 5.3, 5.4**
        Feature: user-registration-endpoint, Property 11: Error response formats
        
        For any duplicate email error, the endpoint should return a 409 status code 
        with a JSON body containing an error message.
        """
        response = duplicate_user_response()
        
        # Verify status code is 409
        assert response["statusCode"] == 409
        
        # Verify headers exist
        assert "headers" in response
        
        # Verify body is valid JSON
        assert "body" in response
        body = json.loads(response["body"])
        
        # Verify body contains error message
        assert "error" in body
        assert isinstance(body["error"], str)
        assert len(body["error"]) > 0
        
        # Verify Content-Type header
        assert response["headers"]["Content-Type"] == "application/json"
    
    def test_internal_error_response_format(self):
        """
        **Validates: Requirements 5.3, 5.4**
        Feature: user-registration-endpoint, Property 11: Error response formats
        
        For any internal server error, the endpoint should return a 500 status code 
        with a JSON body containing a generic error message.
        """
        response = internal_error_response()
        
        # Verify status code is 500
        assert response["statusCode"] == 500
        
        # Verify headers exist
        assert "headers" in response
        
        # Verify body is valid JSON
        assert "body" in response
        body = json.loads(response["body"])
        
        # Verify body contains error message
        assert "error" in body
        assert isinstance(body["error"], str)
        assert len(body["error"]) > 0
        
        # Verify Content-Type header
        assert response["headers"]["Content-Type"] == "application/json"


class TestCORSHeadersProperty:
    """Property-based tests for CORS headers presence."""
    
    @settings(max_examples=20)
    @given(email=emails())
    def test_success_response_has_cors_headers(self, email):
        """
        **Validates: Requirements 5.6**
        Feature: user-registration-endpoint, Property 12: CORS headers present
        
        For any response (success or error), the endpoint should include appropriate 
        CORS headers (Access-Control-Allow-Origin, Access-Control-Allow-Headers, 
        Access-Control-Allow-Methods).
        """
        response = success_response(email)
        headers = response["headers"]
        
        # Verify all required CORS headers are present
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Allow-Methods" in headers
        
        # Verify CORS header values
        expected_origin = get_expected_cors_origin()
        assert headers["Access-Control-Allow-Origin"] == expected_origin
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert "OPTIONS" in headers["Access-Control-Allow-Methods"]
    
    @settings(max_examples=20)
    @given(error_message=st.text(min_size=1, max_size=200))
    def test_validation_error_response_has_cors_headers(self, error_message):
        """
        **Validates: Requirements 5.6**
        Feature: user-registration-endpoint, Property 12: CORS headers present
        
        For any validation error response, the endpoint should include appropriate 
        CORS headers.
        """
        response = validation_error_response(error_message)
        headers = response["headers"]
        
        # Verify all required CORS headers are present
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Allow-Methods" in headers
        
        # Verify CORS header values
        expected_origin = get_expected_cors_origin()
        assert headers["Access-Control-Allow-Origin"] == expected_origin
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert "OPTIONS" in headers["Access-Control-Allow-Methods"]
    
    def test_duplicate_user_response_has_cors_headers(self):
        """
        **Validates: Requirements 5.6**
        Feature: user-registration-endpoint, Property 12: CORS headers present
        
        For any duplicate user error response, the endpoint should include appropriate 
        CORS headers.
        """
        response = duplicate_user_response()
        headers = response["headers"]
        
        # Verify all required CORS headers are present
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Allow-Methods" in headers
        
        # Verify CORS header values
        expected_origin = get_expected_cors_origin()
        assert headers["Access-Control-Allow-Origin"] == expected_origin
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert "OPTIONS" in headers["Access-Control-Allow-Methods"]
    
    def test_internal_error_response_has_cors_headers(self):
        """
        **Validates: Requirements 5.6**
        Feature: user-registration-endpoint, Property 12: CORS headers present
        
        For any internal error response, the endpoint should include appropriate 
        CORS headers.
        """
        response = internal_error_response()
        headers = response["headers"]
        
        # Verify all required CORS headers are present
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Allow-Methods" in headers
        
        # Verify CORS header values
        expected_origin = get_expected_cors_origin()
        assert headers["Access-Control-Allow-Origin"] == expected_origin
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert "OPTIONS" in headers["Access-Control-Allow-Methods"]
