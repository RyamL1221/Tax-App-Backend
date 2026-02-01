"""
Property-based tests for missing required fields in the login endpoint.

These tests verify universal properties across randomized inputs using hypothesis.
Each property test runs with a minimum of 100 iterations.
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails


# Import will be available once lambda handler is implemented (task 8.1)
try:
    from user_login.app import lambda_handler
    LAMBDA_HANDLER_AVAILABLE = True
except ImportError:
    LAMBDA_HANDLER_AVAILABLE = False


class TestMissingRequiredFieldsProperty:
    """Property-based tests for missing required fields validation."""
    
    @pytest.mark.skipif(not LAMBDA_HANDLER_AVAILABLE, reason="Lambda handler not yet implemented (task 8.1)")
    @settings(max_examples=100)
    @given(
        email=st.one_of(emails(), st.none()),
        password=st.one_of(st.text(min_size=1, max_size=100), st.none())
    )
    def test_missing_required_fields_return_400(self, email, password):
        """
        **Validates: Requirements 1.3**
        Feature: user-login-endpoint, Property 1: Missing required fields return 400
        
        For any login request missing one or more required fields (email or password), 
        the endpoint should return a 400 status code with an error message indicating 
        which fields are missing.
        """
        # Skip if both fields are present (not testing missing fields case)
        if email is not None and password is not None:
            return
        
        # Build request body with potentially missing fields
        body_data = {}
        if email is not None:
            body_data['email'] = email
        if password is not None:
            body_data['password'] = password
        
        # Create API Gateway event
        event = {
            'body': json.dumps(body_data)
        }
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Verify 400 status code is returned
        assert response['statusCode'] == 400, \
            f"Expected 400 status code for missing fields, got {response['statusCode']}"
        
        # Verify response body is valid JSON
        assert 'body' in response
        body = json.loads(response['body'])
        
        # Verify error message is present
        assert 'error' in body, "Response should contain 'error' field"
        error_message = body['error']
        
        # Verify error message indicates missing fields
        assert 'Missing required fields' in error_message or 'missing' in error_message.lower(), \
            f"Error message should indicate missing fields, got: {error_message}"
        
        # Verify specific missing field is mentioned in error message
        if email is None:
            assert 'email' in error_message.lower(), \
                f"Error message should mention missing 'email' field, got: {error_message}"
        
        if password is None:
            assert 'password' in error_message.lower(), \
                f"Error message should mention missing 'password' field, got: {error_message}"
    
    @pytest.mark.skipif(not LAMBDA_HANDLER_AVAILABLE, reason="Lambda handler not yet implemented (task 8.1)")
    @settings(max_examples=100)
    @given(
        email=emails(),
        password=st.text(min_size=1, max_size=100)
    )
    def test_all_required_fields_present_does_not_return_400_for_missing_fields(self, email, password):
        """
        **Validates: Requirements 1.3, 1.4**
        Feature: user-login-endpoint, Property 1: Missing required fields return 400
        
        For any login request with all required fields present, the endpoint should 
        NOT return a 400 status code due to missing fields (it may return 400 for 
        other validation reasons, or other status codes for authentication failures).
        
        This test verifies the inverse property: when all fields are present, we 
        don't get a "missing fields" error.
        """
        # Build request body with all required fields
        body_data = {
            'email': email,
            'password': password
        }
        
        # Create API Gateway event
        event = {
            'body': json.dumps(body_data)
        }
        
        # Call lambda handler
        response = lambda_handler(event, None)
        
        # Verify response body is valid JSON
        assert 'body' in response
        body = json.loads(response['body'])
        
        # If status is 400, verify it's NOT due to missing fields
        if response['statusCode'] == 400:
            error_message = body.get('error', '')
            assert 'Missing required fields' not in error_message, \
                f"Should not get 'Missing required fields' error when all fields present, got: {error_message}"
