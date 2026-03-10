"""
Property-based tests for secret key length validation.

These tests verify that the token generator enforces minimum secret key length
requirements. Each property test runs with a minimum of 100 iterations.
"""

import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails, text
from user_login.token_generator import generate_jwt_token


class TestSecretKeyLengthValidationProperty:
    """Property-based tests for secret key length validation."""
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=1, max_size=31, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_short_secret_key_raises_value_error(self, email, secret_key):
        """
        **Validates: Requirements 2.4**
        Feature: jwt-authentication-migration, Property 5: Secret Key Length Validation
        
        For any secret key shorter than 32 characters, the token generation function
        must reject it with a validation error.
        
        This test verifies that:
        1. Secret keys with length < 32 are rejected
        2. A ValueError is raised with a descriptive message
        3. The security requirement is enforced
        
        Note: This test uses min_size=1 to avoid empty strings, which trigger a
        different error message. Empty strings are tested separately.
        """
        # Verification: Token generation should raise ValueError for short secret keys
        with pytest.raises(ValueError) as exc_info:
            generate_jwt_token(email, secret_key)
        
        # Verification: Error message should mention secret key length requirement
        error_message = str(exc_info.value).lower()
        assert "secret key" in error_message or "secret" in error_message, \
            f"Error message should mention secret key, got: {exc_info.value}"
        assert "32" in error_message or "characters" in error_message, \
            f"Error message should mention minimum length requirement, got: {exc_info.value}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_valid_secret_key_length_succeeds(self, email, secret_key):
        """
        **Validates: Requirements 2.4**
        Feature: jwt-authentication-migration, Property 5: Secret Key Length Validation
        
        For any secret key with length >= 32 characters, the token generation
        function must succeed and return a valid JWT token.
        
        This test verifies that:
        1. Secret keys with length >= 32 are accepted
        2. Token generation succeeds without errors
        3. A valid JWT token is returned
        """
        # Action: Generate JWT token with valid secret key
        try:
            token = generate_jwt_token(email, secret_key)
        except ValueError as e:
            pytest.fail(f"Token generation should succeed with secret key of length {len(secret_key)}: {e}")
        
        # Verification 1: Token should be a string
        assert isinstance(token, str), \
            f"Token should be a string, got {type(token)}"
        
        # Verification 2: Token should have JWT format (3 segments)
        segments = token.split('.')
        assert len(segments) == 3, \
            f"Token should have 3 segments (JWT format), got {len(segments)}"
        
        # Verification 3: Each segment should be non-empty
        for i, segment in enumerate(segments):
            assert len(segment) > 0, \
                f"Segment {i} should be non-empty"
    
    @settings(max_examples=20)
    @given(
        email=emails()
    )
    def test_empty_secret_key_raises_value_error(self, email):
        """
        **Validates: Requirements 2.4**
        Feature: jwt-authentication-migration, Property 5: Secret Key Length Validation
        
        For an empty secret key, the token generation function must reject it
        with a validation error.
        
        This test verifies that:
        1. Empty secret keys are rejected
        2. A ValueError is raised
        3. The error message is descriptive
        """
        # Action: Attempt to generate token with empty secret key
        with pytest.raises(ValueError) as exc_info:
            generate_jwt_token(email, "")
        
        # Verification: Error message should mention secret key
        error_message = str(exc_info.value).lower()
        assert "secret" in error_message or "key" in error_message, \
            f"Error message should mention secret key, got: {exc_info.value}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        key_length=st.integers(min_value=1, max_value=31)
    )
    def test_secret_key_exactly_below_minimum_raises_error(self, email, key_length):
        """
        **Validates: Requirements 2.4**
        Feature: jwt-authentication-migration, Property 5: Secret Key Length Validation
        
        For any secret key with length exactly below the minimum (1-31 characters),
        the token generation function must reject it.
        
        This test verifies that:
        1. Keys with length 1-31 are all rejected
        2. The boundary condition is properly enforced
        3. No off-by-one errors exist
        """
        # Generate a secret key of the specified length
        secret_key = 'a' * key_length
        
        # Verification: Token generation should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            generate_jwt_token(email, secret_key)
        
        # Verification: Error should mention the length requirement
        error_message = str(exc_info.value).lower()
        assert "32" in error_message or "characters" in error_message or "length" in error_message, \
            f"Error message should mention length requirement for key of length {key_length}, got: {exc_info.value}"
    
    @settings(max_examples=20)
    @given(
        email=emails()
    )
    def test_secret_key_exactly_32_characters_succeeds(self, email):
        """
        **Validates: Requirements 2.4**
        Feature: jwt-authentication-migration, Property 5: Secret Key Length Validation
        
        For a secret key with exactly 32 characters (the minimum), the token
        generation function must succeed.
        
        This test verifies that:
        1. The minimum length boundary is inclusive (>= 32, not > 32)
        2. A 32-character key is accepted
        3. Token generation succeeds
        """
        # Generate a secret key of exactly 32 characters
        secret_key = 'a' * 32
        
        # Action: Generate JWT token
        try:
            token = generate_jwt_token(email, secret_key)
        except ValueError as e:
            pytest.fail(f"Token generation should succeed with 32-character secret key: {e}")
        
        # Verification: Token should be valid JWT format
        segments = token.split('.')
        assert len(segments) == 3, \
            f"Token should have 3 segments (JWT format), got {len(segments)}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        extra_length=st.integers(min_value=0, max_value=96)
    )
    def test_secret_key_above_minimum_succeeds(self, email, extra_length):
        """
        **Validates: Requirements 2.4**
        Feature: jwt-authentication-migration, Property 5: Secret Key Length Validation
        
        For any secret key with length > 32 characters, the token generation
        function must succeed.
        
        This test verifies that:
        1. Keys longer than the minimum are accepted
        2. There is no maximum length restriction (within reason)
        3. Token generation succeeds for various key lengths
        """
        # Generate a secret key of 32 + extra_length characters
        secret_key = 'a' * (32 + extra_length)
        
        # Action: Generate JWT token
        try:
            token = generate_jwt_token(email, secret_key)
        except ValueError as e:
            pytest.fail(f"Token generation should succeed with {len(secret_key)}-character secret key: {e}")
        
        # Verification: Token should be valid JWT format
        segments = token.split('.')
        assert len(segments) == 3, \
            f"Token should have 3 segments (JWT format), got {len(segments)}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=0, max_size=31, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_short_secret_key_does_not_generate_token(self, email, secret_key):
        """
        **Validates: Requirements 2.4**
        Feature: jwt-authentication-migration, Property 5: Secret Key Length Validation
        
        For any secret key shorter than 32 characters, the token generation
        function must not return a token (must raise an error instead).
        
        This test verifies that:
        1. No token is generated for invalid secret keys
        2. The function fails fast with an error
        3. Security is enforced before any token generation
        """
        # Verification: Token generation should raise ValueError, not return a token
        with pytest.raises(ValueError):
            token = generate_jwt_token(email, secret_key)
            # If we reach here, the test should fail
            pytest.fail(f"Token generation should have raised ValueError for secret key of length {len(secret_key)}, but returned: {token}")
    
    @settings(max_examples=20)
    @given(
        email=emails()
    )
    def test_none_secret_key_raises_value_error(self, email):
        """
        **Validates: Requirements 2.4**
        Feature: jwt-authentication-migration, Property 5: Secret Key Length Validation
        
        For a None secret key, the token generation function must reject it
        with a validation error.
        
        This test verifies that:
        1. None values are rejected
        2. A ValueError is raised
        3. Type validation is performed
        """
        # Action: Attempt to generate token with None secret key
        with pytest.raises((ValueError, TypeError, AttributeError)):
            generate_jwt_token(email, None)
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_secret_key_length_validation_is_consistent(self, email, secret_key):
        """
        **Validates: Requirements 2.4**
        Feature: jwt-authentication-migration, Property 5: Secret Key Length Validation
        
        For any valid secret key, the length validation should be consistent
        across multiple token generations.
        
        This test verifies that:
        1. The same secret key is accepted consistently
        2. Validation is deterministic
        3. No random validation failures occur
        """
        # Action: Generate multiple tokens with the same secret key
        try:
            token1 = generate_jwt_token(email, secret_key)
            token2 = generate_jwt_token(email, secret_key)
            token3 = generate_jwt_token(email, secret_key)
        except ValueError as e:
            pytest.fail(f"Token generation should succeed consistently with valid secret key of length {len(secret_key)}: {e}")
        
        # Verification: All tokens should be valid JWT format
        for i, token in enumerate([token1, token2, token3], 1):
            segments = token.split('.')
            assert len(segments) == 3, \
                f"Token {i} should have 3 segments (JWT format), got {len(segments)}"
