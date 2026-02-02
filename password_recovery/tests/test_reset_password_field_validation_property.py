"""
Property-based tests for reset password field validation.

Feature: password-recovery
Property 14: Reset Password Field Validation

**Validates: Requirements 7.3**

For any /reset-password request, if the token or new_password fields are missing, 
the system should reject the request with a 400 status code and descriptive error message.
"""

import pytest
from hypothesis import given, strategies as st, settings
from password_recovery.input_validator import InputValidator


class TestResetPasswordFieldValidationProperty:
    """Property-based tests for reset password field validation."""
    
    @given(st.text(min_size=1, max_size=100), st.text(min_size=8, max_size=100))
    @settings(max_examples=100)
    def test_valid_fields_present_accepted(self, token, password):
        """
        Property: Requests with both token and new_password fields should pass field validation.
        
        For any request with both required fields present (as strings), the validator
        should not reject based on missing fields (though password strength may still fail).
        """
        validator = InputValidator()
        is_valid, returned_token, returned_password, error = validator.validate_reset_password_input({
            "token": token,
            "new_password": password
        })
        
        # Should not fail due to missing fields
        # (may fail due to password strength, but that's a different property)
        if not is_valid:
            # Error should not be about missing fields
            assert "required" not in error.lower() or "missing" not in error.lower()
        else:
            # If valid, should return the token (trimmed)
            assert returned_token == token.strip()
            assert returned_password == password
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_missing_token_field_rejected(self, password):
        """
        Property: Requests missing the token field should be rejected.
        
        For any request body without a token field, the validator should
        reject it with an error message indicating the token is required.
        """
        validator = InputValidator()
        is_valid, token, returned_password, error = validator.validate_reset_password_input({
            "new_password": password
        })
        
        assert is_valid is False
        assert token is None
        assert returned_password is None
        assert error is not None
        assert "token" in error.lower() and "required" in error.lower()
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_missing_password_field_rejected(self, token):
        """
        Property: Requests missing the new_password field should be rejected.
        
        For any request body without a new_password field, the validator should
        reject it with an error message indicating the password is required.
        """
        validator = InputValidator()
        is_valid, returned_token, password, error = validator.validate_reset_password_input({
            "token": token
        })
        
        assert is_valid is False
        assert returned_token is None
        assert password is None
        assert error is not None
        assert "password" in error.lower() and "required" in error.lower()
    
    @settings(max_examples=100)
    @given(st.just(None))
    def test_missing_both_fields_rejected(self, _):
        """
        Property: Requests missing both fields should be rejected.
        
        For any request body without token or new_password fields, the validator
        should reject it with an appropriate error message.
        """
        validator = InputValidator()
        is_valid, token, password, error = validator.validate_reset_password_input({})
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "required" in error.lower()
    
    @given(st.one_of(
        st.none(),
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    ))
    @settings(max_examples=100)
    def test_non_string_token_rejected(self, non_string_value):
        """
        Property: Requests with non-string token field should be rejected.
        
        For any token value that is not a string, the validator should
        reject it with an appropriate error message.
        """
        validator = InputValidator()
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": non_string_value,
            "new_password": "ValidPass123!"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
    
    @given(st.one_of(
        st.none(),
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    ))
    @settings(max_examples=100)
    def test_non_string_password_rejected(self, non_string_value):
        """
        Property: Requests with non-string new_password field should be rejected.
        
        For any password value that is not a string, the validator should
        reject it with an appropriate error message.
        """
        validator = InputValidator()
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "valid-token-123",
            "new_password": non_string_value
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
    
    @given(st.text(alphabet=' \t\n', max_size=10))
    @settings(max_examples=100)
    def test_empty_token_after_trim_rejected(self, whitespace_token):
        """
        Property: Requests with empty token (after trimming) should be rejected.
        
        For any token that is empty or only whitespace, the validator should
        reject it with an error message indicating the token is required.
        """
        validator = InputValidator()
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": whitespace_token,
            "new_password": "ValidPass123!"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "token" in error.lower() and "required" in error.lower()
    
    @given(st.one_of(
        st.none(),
        st.integers(),
        st.floats(),
        st.lists(st.text()),
        st.text()
    ))
    @settings(max_examples=100)
    def test_non_dict_body_rejected(self, non_dict_body):
        """
        Property: Non-dictionary request bodies should be rejected.
        
        For any request body that is not a dictionary, the validator should
        reject it with an appropriate error message.
        """
        validator = InputValidator()
        is_valid, token, password, error = validator.validate_reset_password_input(non_dict_body)
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "format" in error.lower() or "invalid" in error.lower()
