"""
Unit tests for token generation functionality.

These tests verify specific examples and edge cases for JWT token generation.
"""

import jwt
import time
import pytest
from user_login.token_generator import generate_jwt_token


class TestTokenGenerator:
    """Unit tests for JWT token generator."""
    
    def test_token_has_jwt_format(self):
        """
        Test that generated token has JWT format (three segments separated by periods).
        
        Validates: Requirements 1.1
        """
        email = "test@example.com"
        secret_key = "a" * 32  # Minimum 32 characters
        
        token = generate_jwt_token(email, secret_key)
        
        # JWT format: header.payload.signature
        segments = token.split('.')
        assert len(segments) == 3, \
            f"JWT token should have 3 segments, got {len(segments)}"
    
    def test_token_is_string_type(self):
        """
        Test that generated token is a string.
        
        Validates: Requirements 1.1
        """
        email = "test@example.com"
        secret_key = "a" * 32
        
        token = generate_jwt_token(email, secret_key)
        
        assert isinstance(token, str), \
            f"Token should be a string, got {type(token)}"
    
    def test_token_contains_email_in_payload(self):
        """
        Test that token payload contains the user's email address.
        
        Validates: Requirements 1.2, 11.1
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        token = generate_jwt_token(email, secret_key)
        
        # Decode token to verify payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        assert payload["email"] == email, \
            f"Token payload should contain email '{email}', got '{payload['email']}'"
    
    def test_token_contains_iat_claim(self):
        """
        Test that token payload contains issued at (iat) timestamp.
        
        Validates: Requirements 1.3, 11.2
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        time_before = int(time.time())
        token = generate_jwt_token(email, secret_key)
        time_after = int(time.time())
        
        # Decode token to verify payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        assert "iat" in payload, \
            "Token payload should contain 'iat' claim"
        assert isinstance(payload["iat"], int), \
            f"iat claim should be an integer, got {type(payload['iat'])}"
        assert time_before <= payload["iat"] <= time_after, \
            f"iat claim should be current timestamp, got {payload['iat']}"
    
    def test_token_contains_exp_claim(self):
        """
        Test that token payload contains expiration (exp) timestamp.
        
        Validates: Requirements 1.4, 11.3
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        token = generate_jwt_token(email, secret_key)
        
        # Decode token to verify payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        assert "exp" in payload, \
            "Token payload should contain 'exp' claim"
        assert isinstance(payload["exp"], int), \
            f"exp claim should be an integer, got {type(payload['exp'])}"
    
    def test_token_expires_in_24_hours(self):
        """
        Test that token expiration is set to 24 hours (86400 seconds) from issuance.
        
        Validates: Requirements 1.4, 11.4
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        token = generate_jwt_token(email, secret_key)
        
        # Decode token to verify payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Calculate token lifetime
        token_lifetime = payload["exp"] - payload["iat"]
        
        assert token_lifetime == 86400, \
            f"Token should expire in 86400 seconds (24 hours), got {token_lifetime}"
    
    def test_token_uses_hs256_algorithm(self):
        """
        Test that token is signed using HS256 algorithm.
        
        Validates: Requirements 1.5
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        token = generate_jwt_token(email, secret_key)
        
        # Decode token header to verify algorithm
        header = jwt.get_unverified_header(token)
        
        assert header["alg"] == "HS256", \
            f"Token should use HS256 algorithm, got {header['alg']}"
    
    def test_token_is_verifiable_with_correct_secret(self):
        """
        Test that token can be verified using the correct secret key.
        
        Validates: Requirements 1.5, 9.1
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        token = generate_jwt_token(email, secret_key)
        
        # Verification should succeed
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            assert payload["email"] == email
        except jwt.InvalidTokenError as e:
            pytest.fail(f"Token should be verifiable with correct secret: {e}")
    
    def test_token_fails_verification_with_wrong_secret(self):
        """
        Test that token verification fails with wrong secret key.
        
        Validates: Requirements 1.5, 9.2
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        wrong_secret = "different-secret-key-with-32-chars-min"
        
        token = generate_jwt_token(email, secret_key)
        
        # Verification should fail with wrong secret
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, wrong_secret, algorithms=["HS256"])
    
    def test_multiple_tokens_are_unique(self):
        """
        Test that multiple token generations produce unique tokens.
        
        Due to different iat timestamps, tokens should be unique even with
        the same email and secret key. However, if generated within the same
        second, they may be identical since iat is in seconds.
        
        Validates: Requirements 1.1, 1.3
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Generate multiple tokens with small delays to ensure different timestamps
        tokens = []
        for _ in range(3):
            tokens.append(generate_jwt_token(email, secret_key))
            time.sleep(0.1)  # Small delay to potentially get different timestamps
        
        # Decode tokens to check timestamps
        payloads = [jwt.decode(token, secret_key, algorithms=["HS256"]) for token in tokens]
        
        # At least verify that tokens can be generated multiple times
        assert len(tokens) == 3, \
            f"Should generate 3 tokens, got {len(tokens)}"
        
        # If timestamps differ, tokens should be unique
        timestamps = [p["iat"] for p in payloads]
        if len(set(timestamps)) > 1:
            # Different timestamps should produce different tokens
            assert len(set(tokens)) > 1, \
                "Tokens with different timestamps should be unique"
    
    def test_empty_email_raises_value_error(self):
        """
        Test that empty email raises ValueError.
        
        Validates: Requirements 1.2, 2.3
        """
        email = ""
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        with pytest.raises(ValueError) as exc_info:
            generate_jwt_token(email, secret_key)
        
        assert "email" in str(exc_info.value).lower()
    
    def test_empty_secret_key_raises_value_error(self):
        """
        Test that empty secret key raises ValueError.
        
        Validates: Requirements 2.3, 2.4
        """
        email = "user@example.com"
        secret_key = ""
        
        with pytest.raises(ValueError) as exc_info:
            generate_jwt_token(email, secret_key)
        
        assert "secret" in str(exc_info.value).lower()
    
    def test_short_secret_key_raises_value_error(self):
        """
        Test that secret key shorter than 32 characters raises ValueError.
        
        Validates: Requirements 2.4
        """
        email = "user@example.com"
        secret_key = "short"  # Less than 32 characters
        
        with pytest.raises(ValueError) as exc_info:
            generate_jwt_token(email, secret_key)
        
        error_message = str(exc_info.value).lower()
        assert "32" in error_message or "characters" in error_message
    
    def test_secret_key_exactly_32_characters_succeeds(self):
        """
        Test that secret key with exactly 32 characters succeeds.
        
        Validates: Requirements 2.4
        """
        email = "user@example.com"
        secret_key = "a" * 32  # Exactly 32 characters
        
        # Should not raise an error
        token = generate_jwt_token(email, secret_key)
        
        assert isinstance(token, str)
        assert len(token.split('.')) == 3
    
    def test_secret_key_longer_than_32_characters_succeeds(self):
        """
        Test that secret key longer than 32 characters succeeds.
        
        Validates: Requirements 2.4
        """
        email = "user@example.com"
        secret_key = "a" * 64  # 64 characters
        
        # Should not raise an error
        token = generate_jwt_token(email, secret_key)
        
        assert isinstance(token, str)
        assert len(token.split('.')) == 3
    
    def test_none_email_raises_value_error(self):
        """
        Test that None email raises ValueError.
        
        Validates: Requirements 1.2
        """
        email = None
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            generate_jwt_token(email, secret_key)
    
    def test_none_secret_key_raises_value_error(self):
        """
        Test that None secret key raises ValueError.
        
        Validates: Requirements 2.3, 2.4
        """
        email = "user@example.com"
        secret_key = None
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            generate_jwt_token(email, secret_key)
    
    def test_token_payload_has_only_required_claims(self):
        """
        Test that token payload contains only required claims (email, iat, exp).
        
        Validates: Requirements 1.2, 1.3, 1.4, 11.5
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        token = generate_jwt_token(email, secret_key)
        
        # Decode token to verify payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Should have exactly 4 claims (email, session_version, iat, exp)
        assert len(payload) == 4, \
            f"Token payload should have exactly 4 claims, got {len(payload)}"
        
        # Should have specific claims
        assert set(payload.keys()) == {"email", "session_version", "iat", "exp"}, \
            f"Token payload should have email, session_version, iat, exp claims, got {set(payload.keys())}"
    
    def test_token_does_not_contain_password_field(self):
        """
        Test that token payload does not contain password or password_hash fields.
        
        Validates: Requirements 11.5
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        token = generate_jwt_token(email, secret_key)
        
        # Decode token to verify payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Should not contain password-related fields
        assert "password" not in payload, \
            "Token payload should not contain 'password' field"
        assert "password_hash" not in payload, \
            "Token payload should not contain 'password_hash' field"
    
    def test_different_emails_produce_different_tokens(self):
        """
        Test that different emails produce different tokens.
        
        Validates: Requirements 1.2
        """
        email1 = "user1@example.com"
        email2 = "user2@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        token1 = generate_jwt_token(email1, secret_key)
        token2 = generate_jwt_token(email2, secret_key)
        
        # Tokens should be different
        assert token1 != token2, \
            "Tokens with different emails should be different"
        
        # Verify emails in payloads
        payload1 = jwt.decode(token1, secret_key, algorithms=["HS256"])
        payload2 = jwt.decode(token2, secret_key, algorithms=["HS256"])
        
        assert payload1["email"] == email1
        assert payload2["email"] == email2
    
    def test_token_with_special_characters_in_email(self):
        """
        Test that token generation works with special characters in email.
        
        Validates: Requirements 1.2
        """
        email = "user+test@example.co.uk"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        token = generate_jwt_token(email, secret_key)
        
        # Decode token to verify email
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        assert payload["email"] == email, \
            f"Token should preserve special characters in email, expected '{email}', got '{payload['email']}'"

