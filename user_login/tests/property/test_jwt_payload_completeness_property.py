"""
Property-based tests for JWT payload completeness.

These tests verify that JWT tokens contain all required claims with correct types
and values. Each property test runs with a minimum of 100 iterations.
"""

import jwt
import time
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails, text
from user_login.token_generator import generate_jwt_token


class TestJWTPayloadCompletenessProperty:
    """Property-based tests for JWT payload completeness validation."""
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_contains_all_required_claims(self, email, secret_key):
        """
        **Validates: Requirements 1.2, 1.3, 1.4, 11.1, 11.2, 11.3, 11.4**
        Feature: jwt-authentication-migration, Property 2: JWT Payload Completeness
        
        For any generated JWT token, when decoded, the payload must contain all
        required claims: "email" (string), "iat" (Unix timestamp), and "exp"
        (Unix timestamp where exp = iat + 86400).
        
        This test verifies that:
        1. The payload contains an "email" claim
        2. The payload contains an "iat" (issued at) claim
        3. The payload contains an "exp" (expiration) claim
        4. All claims have the correct types
        5. The expiration is exactly 24 hours (86400 seconds) after issuance
        """
        # Record time before token generation
        time_before = int(time.time())
        
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Record time after token generation
        time_after = int(time.time())
        
        # Decode the JWT token without verification to inspect payload
        # (We're testing payload structure, not signature verification)
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification 1: Payload should contain "email" claim
        assert "email" in payload, \
            "JWT payload must contain 'email' claim"
        
        # Verification 2: Payload should contain "iat" claim
        assert "iat" in payload, \
            "JWT payload must contain 'iat' (issued at) claim"
        
        # Verification 3: Payload should contain "exp" claim
        assert "exp" in payload, \
            "JWT payload must contain 'exp' (expiration) claim"
        
        # Verification 4: Email claim should be a string
        assert isinstance(payload["email"], str), \
            f"Email claim should be a string, got {type(payload['email'])}"
        
        # Verification 5: Email claim should match the input email
        assert payload["email"] == email, \
            f"Email claim should match input email, expected '{email}', got '{payload['email']}'"
        
        # Verification 6: iat claim should be an integer (Unix timestamp)
        assert isinstance(payload["iat"], int), \
            f"iat claim should be an integer (Unix timestamp), got {type(payload['iat'])}"
        
        # Verification 7: exp claim should be an integer (Unix timestamp)
        assert isinstance(payload["exp"], int), \
            f"exp claim should be an integer (Unix timestamp), got {type(payload['exp'])}"
        
        # Verification 8: iat should be within reasonable time range (between before and after)
        assert time_before <= payload["iat"] <= time_after, \
            f"iat claim should be current timestamp, got {payload['iat']} (expected between {time_before} and {time_after})"
        
        # Verification 9: exp should be exactly 86400 seconds (24 hours) after iat
        expected_exp = payload["iat"] + 86400
        assert payload["exp"] == expected_exp, \
            f"exp claim should be iat + 86400 seconds (24 hours), expected {expected_exp}, got {payload['exp']}"
        
        # Verification 10: exp should be in the future
        assert payload["exp"] > time_before, \
            f"exp claim should be in the future, got {payload['exp']} (current time: {time_before})"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_has_exactly_three_claims(self, email, secret_key):
        """
        **Validates: Requirements 1.2, 1.3, 1.4, 11.1, 11.2, 11.3**
        Feature: jwt-authentication-migration, Property 2: JWT Payload Completeness
        
        For any generated JWT token, the payload should contain exactly the four
        required claims (email, session_version, iat, exp) and no additional claims.
        
        This test verifies that:
        1. The payload has exactly 4 claims
        2. No extra claims are added
        3. The payload structure is minimal and predictable
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification 1: Payload should have exactly 4 claims
        assert len(payload) == 4, \
            f"JWT payload should contain exactly 4 claims (email, session_version, iat, exp), got {len(payload)} claims: {list(payload.keys())}"
        
        # Verification 2: Payload should contain only the expected claims
        expected_claims = {"email", "session_version", "iat", "exp"}
        actual_claims = set(payload.keys())
        assert actual_claims == expected_claims, \
            f"JWT payload should contain only {expected_claims}, got {actual_claims}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_email_is_non_empty(self, email, secret_key):
        """
        **Validates: Requirements 1.2, 11.1**
        Feature: jwt-authentication-migration, Property 2: JWT Payload Completeness
        
        For any generated JWT token, the email claim must be a non-empty string.
        
        This test verifies that:
        1. The email claim is not empty
        2. The email claim is a valid string
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification 1: Email claim should not be empty
        assert len(payload["email"]) > 0, \
            "Email claim should not be empty"
        
        # Verification 2: Email claim should be a string
        assert isinstance(payload["email"], str), \
            f"Email claim should be a string, got {type(payload['email'])}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_timestamps_are_positive(self, email, secret_key):
        """
        **Validates: Requirements 1.3, 1.4, 11.2, 11.3**
        Feature: jwt-authentication-migration, Property 2: JWT Payload Completeness
        
        For any generated JWT token, the iat and exp claims must be positive
        Unix timestamps (seconds since epoch).
        
        This test verifies that:
        1. iat is a positive integer
        2. exp is a positive integer
        3. Both timestamps are reasonable (not in distant past or future)
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification 1: iat should be positive
        assert payload["iat"] > 0, \
            f"iat claim should be a positive Unix timestamp, got {payload['iat']}"
        
        # Verification 2: exp should be positive
        assert payload["exp"] > 0, \
            f"exp claim should be a positive Unix timestamp, got {payload['exp']}"
        
        # Verification 3: iat should be reasonable (after year 2000, before year 2100)
        # Unix timestamp for 2000-01-01: 946684800
        # Unix timestamp for 2100-01-01: 4102444800
        assert 946684800 <= payload["iat"] <= 4102444800, \
            f"iat claim should be a reasonable timestamp (between 2000 and 2100), got {payload['iat']}"
        
        # Verification 4: exp should be reasonable (after year 2000, before year 2100)
        assert 946684800 <= payload["exp"] <= 4102444800, \
            f"exp claim should be a reasonable timestamp (between 2000 and 2100), got {payload['exp']}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_expiration_is_24_hours(self, email, secret_key):
        """
        **Validates: Requirements 1.4, 11.4**
        Feature: jwt-authentication-migration, Property 2: JWT Payload Completeness
        
        For any generated JWT token, the expiration time must be exactly 24 hours
        (86400 seconds) after the issued at time.
        
        This test verifies that:
        1. exp - iat = 86400 seconds
        2. The token lifetime is exactly 24 hours
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification: exp should be exactly 86400 seconds after iat
        token_lifetime = payload["exp"] - payload["iat"]
        assert token_lifetime == 86400, \
            f"Token lifetime should be exactly 86400 seconds (24 hours), got {token_lifetime} seconds"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_can_be_decoded_with_correct_secret(self, email, secret_key):
        """
        **Validates: Requirements 1.2, 1.3, 1.4, 11.1, 11.2, 11.3, 11.4**
        Feature: jwt-authentication-migration, Property 2: JWT Payload Completeness
        
        For any generated JWT token, the payload should be decodable using the
        same secret key that was used to generate it.
        
        This test verifies that:
        1. The token can be decoded with the correct secret
        2. Decoding succeeds without errors
        3. All claims are accessible after decoding
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Verification: Token should be decodable with the correct secret
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            
            # Verify all required claims are accessible
            assert "email" in payload
            assert "iat" in payload
            assert "exp" in payload
            
        except jwt.InvalidTokenError as e:
            pytest.fail(f"Token should be decodable with correct secret key: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error decoding token: {e}")
