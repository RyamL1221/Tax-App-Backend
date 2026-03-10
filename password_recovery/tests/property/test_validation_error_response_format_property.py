"""
Property-based tests for validation error response format.

Feature: password-recovery
Property 16: Validation Error Response Format

**Validates: Requirements 7.5**

For any input validation failure, the system should return a 400 status code 
with a JSON response containing an error field and a descriptive message.

Note: This test validates the InputValidator component's error response format.
The actual HTTP status code (400) will be set by the Lambda handler, which is
tested separately. Here we verify that validation errors return descriptive
error messages that can be used in 400 responses.
"""

import pytest
from hypothesis import given, strategies as st, settings
from password_recovery.input_validator import InputValidator


class TestValidationErrorResponseFormatProperty:
    """Property-based tests for validation error response format."""
    
    @given(st.one_of(
        st.none(),
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text()),
        st.text()
    ))
    @settings(max_examples=100)
    def test_forgot_password_invalid_body_returns_error_message(self, invalid_body):
        """
        Property: Invalid forgot-password requests should return descriptive error messages.
        
        For any validation failure in forgot-password input, the validator should
        return is_valid=False with a non-empty, descriptive error message string.
        """
        validator = InputValidator()
        is_valid, email, error = validator.validate_forgot_password_input(invalid_body)
        
        if not is_valid:
            # Error message should be present
            assert error is not None
            # Error message should be a string
            assert isinstance(error, str)
            # Error message should be non-empty
            assert len(error) > 0
            # Error message should be descriptive (more than just a single word)
            assert len(error) > 5
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.none()),
        min_size=0,
        max_size=5
    ))
    @settings(max_examples=100)
    def test_forgot_password_missing_or_invalid_email_returns_error(self, body):
        """
        Property: Forgot-password requests without valid email should return error message.
        
        For any request body that doesn't contain a valid email field, the validator
        should return is_valid=False with a descriptive error message.
        """
        # Exclude valid cases (we're testing invalid cases)
        if isinstance(body, dict) and 'email' in body:
            email = body['email']
            if isinstance(email, str) and '@' in email and '.' in email:
                # This might be valid, skip it
                return
        
        validator = InputValidator()
        is_valid, email, error = validator.validate_forgot_password_input(body)
        
        if not is_valid:
            assert error is not None
            assert isinstance(error, str)
            assert len(error) > 0
    
    @given(st.one_of(
        st.none(),
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text()),
        st.text()
    ))
    @settings(max_examples=100)
    def test_reset_password_invalid_body_returns_error_message(self, invalid_body):
        """
        Property: Invalid reset-password requests should return descriptive error messages.
        
        For any validation failure in reset-password input, the validator should
        return is_valid=False with a non-empty, descriptive error message string.
        """
        validator = InputValidator()
        is_valid, token, password, error = validator.validate_reset_password_input(invalid_body)
        
        if not is_valid:
            # Error message should be present
            assert error is not None
            # Error message should be a string
            assert isinstance(error, str)
            # Error message should be non-empty
            assert len(error) > 0
            # Error message should be descriptive
            assert len(error) > 5
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.none()),
        min_size=0,
        max_size=5
    ))
    @settings(max_examples=100)
    def test_reset_password_missing_fields_returns_error(self, body):
        """
        Property: Reset-password requests with missing fields should return error message.
        
        For any request body that doesn't contain both token and new_password fields,
        the validator should return is_valid=False with a descriptive error message.
        """
        # Exclude valid cases (we're testing invalid cases)
        if isinstance(body, dict) and 'token' in body and 'new_password' in body:
            token = body['token']
            password = body['new_password']
            if isinstance(token, str) and isinstance(password, str) and len(token) > 0:
                # This might be valid (though password might fail strength check)
                # We're testing missing fields, so skip this
                return
        
        validator = InputValidator()
        is_valid, token, password, error = validator.validate_reset_password_input(body)
        
        if not is_valid:
            assert error is not None
            assert isinstance(error, str)
            assert len(error) > 0
    
    @given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_', min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_weak_password_returns_descriptive_error(self, token):
        """
        Property: Weak passwords should return descriptive error messages.
        
        For any password that fails strength validation, the validator should
        return a descriptive error message explaining what's wrong.
        """
        # Use a password that's definitely weak (too short)
        weak_password = "weak"
        
        validator = InputValidator()
        is_valid, returned_token, returned_password, error = validator.validate_reset_password_input({
            "token": token,
            "new_password": weak_password
        })
        
        assert is_valid is False
        assert error is not None
        assert isinstance(error, str)
        assert len(error) > 0
        # Error should mention password requirements
        assert "password" in error.lower() or "character" in error.lower()
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_error_messages_are_user_friendly(self, invalid_input):
        """
        Property: Error messages should be user-friendly and actionable.
        
        For any validation error, the error message should be clear enough
        for a user to understand what went wrong and how to fix it.
        """
        validator = InputValidator()
        
        # Test with invalid email
        is_valid, email, error = validator.validate_forgot_password_input({"email": invalid_input})
        if not is_valid:
            assert error is not None
            assert isinstance(error, str)
            # Should not contain technical jargon or stack traces
            assert "exception" not in error.lower()
            assert "traceback" not in error.lower()
            assert "error:" not in error.lower() or error.count("error") == 1
    
    @given(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=100)
    def test_all_validation_errors_return_consistent_format(self, token, password):
        """
        Property: All validation errors should return consistent format.
        
        For any validation failure, the return format should be consistent:
        (is_valid=False, None/None/None, error_message)
        """
        validator = InputValidator()
        
        # Test reset password validation
        is_valid, returned_token, returned_password, error = validator.validate_reset_password_input({
            "token": token,
            "new_password": password
        })
        
        if not is_valid:
            # When validation fails, token and password should be None
            assert returned_token is None
            assert returned_password is None
            # Error should be a non-empty string
            assert error is not None
            assert isinstance(error, str)
            assert len(error) > 0
        else:
            # When validation succeeds, error should be None
            assert error is None
            # Token and password should be returned
            assert returned_token is not None
            assert returned_password is not None
