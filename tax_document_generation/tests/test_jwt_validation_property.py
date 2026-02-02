"""
Property-based tests for JWT token validation.

These tests verify that JWT tokens are properly validated, including
rejection of invalid and expired tokens. Each property test runs with
a minimum of 100 iterations.

Feature: tax-document-generation
Property 17: JWT Token Validation

**Validates: Requirements 8.1, 8.3**
"""

import jwt
import pytest
import time
from datetime import datetime, timedelta
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import text, integers
from tax_document_generation.jwt_validator import validate_jwt
from tax_document_generation.exceptions import AuthenticationError


# Strategy for generating valid secret keys (at least 32 characters)
secret_keys = text(
    min_size=32,
    max_size=128,
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?'
)

# Strategy for generating user IDs
user_ids = text(min_size=1, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')


class TestJWTValidationProperty:
    """Property-based tests for JWT token validation."""
    
    @settings(max_examples=100)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_expired_token_raises_authentication_error(self, user_id, secret_key):
        """
        **Validates: Requirements 8.1, 8.3**
        Feature: tax-document-generation, Property 17: JWT Token Validation
        
        For any JWT token with an expiration timestamp (exp claim) in the past,
        validation must fail and raise AuthenticationError.
        
        This test verifies that:
        1. Tokens with exp claim in the past are rejected
        2. AuthenticationError is raised for expired tokens
        3. Token expiration is properly enforced
        """
        # Action: Generate an expired JWT token
        # Set issued_at to 48 hours ago and expiration to 24 hours ago
        issued_at = datetime.utcnow() - timedelta(hours=48)
        expiration = datetime.utcnow() - timedelta(hours=24)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create expired token
        expired_token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Expired token should be rejected with AuthenticationError
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(expired_token, secret_key)
        
        # Verify the error message mentions expiration
        assert "expired" in str(exc_info.value).lower()
    
    @settings(max_examples=100)
    @given(
        user_id=user_ids,
        secret_key=secret_keys,
        hours_ago=integers(min_value=25, max_value=1000)
    )
    def test_token_expired_by_various_durations_raises_authentication_error(self, user_id, secret_key, hours_ago):
        """
        **Validates: Requirements 8.1, 8.3**
        Feature: tax-document-generation, Property 17: JWT Token Validation
        
        For any JWT token that expired hours ago, validation must fail.
        
        This test verifies that:
        1. Tokens expired by various durations are all rejected
        2. The expiration check works regardless of how long ago the token expired
        3. AuthenticationError is consistently raised
        """
        # Action: Generate a token that expired hours_ago hours ago
        issued_at = datetime.utcnow() - timedelta(hours=hours_ago + 24)
        expiration = datetime.utcnow() - timedelta(hours=hours_ago)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create expired token
        expired_token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Expired token should be rejected
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(expired_token, secret_key)
        
        assert "expired" in str(exc_info.value).lower()
    
    @settings(max_examples=100)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_invalid_signature_raises_authentication_error(self, user_id, secret_key):
        """
        **Validates: Requirements 8.1, 8.3**
        Feature: tax-document-generation, Property 17: JWT Token Validation
        
        For any JWT token signed with a different secret key,
        validation must fail and raise AuthenticationError.
        
        This test verifies that:
        1. Tokens with invalid signatures are rejected
        2. AuthenticationError is raised for signature mismatches
        3. Signature verification is properly enforced
        """
        # Action: Generate a token with one secret, try to validate with another
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create token with original secret
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Try to validate with a different secret
        wrong_secret = secret_key + "wrong"
        
        # Verification: Token with invalid signature should be rejected
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, wrong_secret)
        
        # Verify the error message mentions signature
        assert "signature" in str(exc_info.value).lower()
    
    @settings(max_examples=100)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_malformed_token_raises_authentication_error(self, user_id, secret_key):
        """
        **Validates: Requirements 8.1, 8.3**
        Feature: tax-document-generation, Property 17: JWT Token Validation
        
        For any malformed JWT token (invalid format),
        validation must fail and raise AuthenticationError.
        
        This test verifies that:
        1. Malformed tokens are rejected
        2. AuthenticationError is raised for format errors
        3. Token format validation is properly enforced
        """
        # Action: Create various malformed tokens
        malformed_tokens = [
            "not.a.valid.jwt",
            "invalid",
            "a.b",  # Too few parts
            "a.b.c.d.e",  # Too many parts
            "",  # Empty string
            "...",  # Empty parts
        ]
        
        # Verification: All malformed tokens should be rejected
        for malformed_token in malformed_tokens:
            with pytest.raises(AuthenticationError):
                validate_jwt(malformed_token, secret_key)
    
    @settings(max_examples=100)
    @given(
        user_id=user_ids,
        secret_key=secret_keys,
        seconds_in_past=integers(min_value=1, max_value=3600)
    )
    def test_token_expired_by_seconds_raises_authentication_error(self, user_id, secret_key, seconds_in_past):
        """
        **Validates: Requirements 8.1, 8.3**
        Feature: tax-document-generation, Property 17: JWT Token Validation
        
        For any JWT token that expired seconds ago, validation must fail.
        
        This test verifies that:
        1. Even recently expired tokens (seconds ago) are rejected
        2. Expiration is enforced immediately after the exp timestamp
        3. No grace period exists for expired tokens
        """
        # Action: Generate a token that expired seconds_in_past seconds ago
        issued_at = datetime.utcnow() - timedelta(hours=24)
        expiration = datetime.utcnow() - timedelta(seconds=seconds_in_past)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create expired token
        expired_token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Expired token should be rejected
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(expired_token, secret_key)
        
        assert "expired" in str(exc_info.value).lower()
    
    @settings(max_examples=100)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_expired_token_with_valid_signature_is_still_rejected(self, user_id, secret_key):
        """
        **Validates: Requirements 8.1, 8.3**
        Feature: tax-document-generation, Property 17: JWT Token Validation
        
        For any JWT token with a valid signature but expired timestamp,
        validation must fail due to expiration (not signature).
        
        This test verifies that:
        1. Valid signature does not override expiration check
        2. Both signature and expiration are validated
        3. Expiration takes precedence in error reporting
        """
        # Action: Generate an expired token with valid signature
        issued_at = datetime.utcnow() - timedelta(hours=48)
        expiration = datetime.utcnow() - timedelta(hours=24)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create expired token with valid signature
        expired_token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verify the token has a valid signature by checking it can be decoded without verification
        unverified_payload = jwt.decode(
            expired_token,
            options={"verify_signature": False, "verify_exp": False}
        )
        assert unverified_payload["userId"] == user_id, "Token should have valid structure"
        
        # Verification: Despite valid signature, expired token should be rejected
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(expired_token, secret_key)
        
        assert "expired" in str(exc_info.value).lower()
    
    @settings(max_examples=100)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_token_without_userid_raises_authentication_error(self, user_id, secret_key):
        """
        **Validates: Requirements 8.1, 8.3**
        Feature: tax-document-generation, Property 17: JWT Token Validation
        
        For any JWT token without a userId claim,
        validation must fail and raise AuthenticationError.
        
        This test verifies that:
        1. Tokens without userId claim are rejected
        2. AuthenticationError is raised for missing userId
        3. Required claims are properly enforced
        """
        # Action: Generate a token without userId claim
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "email": "test@example.com",  # Missing userId
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create token without userId
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Token without userId should be rejected
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, secret_key)
        
        # Verify the error message mentions userId
        error_message = str(exc_info.value).lower()
        assert "userid" in error_message
    
    @settings(max_examples=100)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_valid_token_does_not_raise_error(self, user_id, secret_key):
        """
        **Validates: Requirements 8.1, 8.3**
        Feature: tax-document-generation, Property 17: JWT Token Validation
        
        For any valid JWT token with proper signature and not expired,
        validation must succeed and return the payload.
        
        This test verifies that:
        1. Valid tokens are accepted
        2. No AuthenticationError is raised for valid tokens
        3. The returned payload contains the userId
        """
        # Action: Generate a valid token
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create valid token
        valid_token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Valid token should be accepted
        result = validate_jwt(valid_token, secret_key)
        
        # Verify the payload is returned correctly
        assert result["userId"] == user_id
    
    @settings(max_examples=100)
    @given(
        secret_key=secret_keys
    )
    def test_token_with_wrong_algorithm_raises_authentication_error(self, secret_key):
        """
        **Validates: Requirements 8.1, 8.3**
        Feature: tax-document-generation, Property 17: JWT Token Validation
        
        For any JWT token signed with an algorithm other than HS256,
        validation must fail and raise AuthenticationError.
        
        This test verifies that:
        1. Tokens signed with wrong algorithm are rejected
        2. AuthenticationError is raised for algorithm mismatches
        3. Algorithm validation is properly enforced
        """
        # Action: Generate a token with HS512 instead of HS256
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "userId": "test-user",
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create token with HS512 algorithm
        token = jwt.encode(payload, secret_key, algorithm="HS512")
        
        # Verification: Token with wrong algorithm should be rejected
        with pytest.raises(AuthenticationError):
            validate_jwt(token, secret_key)
