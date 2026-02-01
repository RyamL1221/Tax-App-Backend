"""
Property-based tests for password presence validation in the login endpoint.

These tests verify universal properties across randomized inputs using hypothesis.
Each property test runs with a minimum of 100 iterations.
"""

import pytest
from hypothesis import given, settings, strategies as st
from user_login.validator import ValidationError, validate_password_present


class TestPasswordPresenceProperty:
    """Property-based tests for password presence validation."""
    
    @settings(max_examples=100)
    @given(password=st.text(min_size=1))
    def test_non_empty_passwords_are_accepted(self, password):
        """
        **Validates: Requirements 2.3, 2.4**
        Feature: user-login-endpoint, Property 3: Password presence validation
        
        For any non-empty string password, the validator should accept it.
        """
        # Non-empty passwords should be accepted
        assert validate_password_present(password) is True
    
    @settings(max_examples=100)
    @given(
        invalid_password=st.one_of(
            # Empty string
            st.just(""),
            # None value
            st.none(),
            # Non-string types: integers
            st.integers(),
            # Non-string types: floats
            st.floats(allow_nan=False, allow_infinity=False),
            # Non-string types: booleans
            st.booleans(),
            # Non-string types: lists
            st.lists(st.text(), max_size=5),
            # Non-string types: dictionaries
            st.dictionaries(st.text(max_size=5), st.text(max_size=5), max_size=3),
        )
    )
    def test_invalid_passwords_are_rejected(self, invalid_password):
        """
        **Validates: Requirements 2.3, 2.4**
        Feature: user-login-endpoint, Property 3: Password presence validation
        
        For any empty string or non-string password value, the validator should 
        reject it with a ValidationError and descriptive error message.
        """
        # Invalid passwords (empty strings or non-strings) should raise ValidationError
        with pytest.raises(ValidationError):
            validate_password_present(invalid_password)
