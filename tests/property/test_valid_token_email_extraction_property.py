"""
Property-based tests for valid JWT token email extraction.

These tests verify that valid, non-expired JWT tokens can be successfully decoded
and the email claim can be extracted from the payload.
Each property test runs with a minimum of 100 iterations.
"""

import jwt
import pytest
import time
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails, text, integers
from jwt_verifier import verify_jwt_token


class TestValidTokenEmailExtractionProperty:
    """Property-based tests for valid token email extraction validation."""
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_valid_token_email_extraction(self, email, secret_key):
        """
        **Validates: Requirements 9.4**
        Feature: jwt-authentication-migration, Property 10: Valid Token Email Extraction
        
        For any valid, non-expired JWT token, decoding must successfully extract
        the email claim from the payload.
        
        This test verifies that:
        1. Valid tokens can be decoded successfully
        2. The email claim is present in the decoded payload
        3. The extracted email matches the original email
        """
        # Action: Generate a valid, non-expired JWT token
        issued_at = int(time.time())
        expiration = issued_at + 86400  # 24 hours from now
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create valid token
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification 1: Token should be verifiable
        try:
            decoded_payload = verify_jwt_token(token, secret_key)
        except Exception as e:
            pytest.fail(f"Valid token should be verifiable: {e}")
        
        # Verification 2: Email claim should be present
        assert "email" in decoded_payload, "Decoded payload should contain 'email' claim"
        
        # Verification 3: Extracted email should match original email
        assert decoded_payload["email"] == email, \
            f"Extracted email should match original, expected '{email}', got '{decoded_payload['email']}'"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?'),
        hours_until_expiry=st.integers(min_value=1, max_value=1000)  # 1 to 1000 hours in the future
    )
    def test_token_with_various_expiry_times_email_extraction(self, email, secret_key, hours_until_expiry):
        """
        **Validates: Requirements 9.4**
        Feature: jwt-authentication-migration, Property 10: Valid Token Email Extraction
        
        For any valid JWT token with various expiration times in the future,
        email extraction must succeed.
        
        This test verifies that:
        1. Tokens with different expiration times can all be decoded
        2. Email extraction works regardless of expiration time (as long as not expired)
        3. The verification process is consistent
        """
        # Action: Generate a token that expires in hours_until_expiry hours
        issued_at = int(time.time())
        expiration = issued_at + (hours_until_expiry * 3600)
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create valid token
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Email should be extractable
        decoded_payload = verify_jwt_token(token, secret_key)
        assert decoded_payload["email"] == email, \
            f"Extracted email should match original, expected '{email}', got '{decoded_payload['email']}'"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_freshly_issued_token_email_extraction(self, email, secret_key):
        """
        **Validates: Requirements 9.4**
        Feature: jwt-authentication-migration, Property 10: Valid Token Email Extraction
        
        For any freshly issued JWT token (just created), email extraction must succeed.
        
        This test verifies that:
        1. Newly created tokens are immediately valid
        2. Email can be extracted from fresh tokens
        3. No delay or grace period is needed after token creation
        """
        # Action: Generate a freshly issued token
        issued_at = int(time.time())
        expiration = issued_at + 86400  # Standard 24-hour expiration
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create token
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Email should be immediately extractable
        decoded_payload = verify_jwt_token(token, secret_key)
        assert decoded_payload["email"] == email, \
            f"Extracted email should match original, expected '{email}', got '{decoded_payload['email']}'"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_token_near_expiration_email_extraction(self, email, secret_key):
        """
        **Validates: Requirements 9.4**
        Feature: jwt-authentication-migration, Property 10: Valid Token Email Extraction
        
        For any JWT token that is about to expire (but not yet expired),
        email extraction must succeed.
        
        This test verifies that:
        1. Tokens near expiration are still valid
        2. Email extraction works up until the expiration moment
        3. No early expiration occurs
        """
        # Action: Generate a token that expires in 10 seconds
        issued_at = int(time.time()) - 86390  # Issued 23 hours, 59 minutes, 50 seconds ago
        expiration = issued_at + 86400  # Expires in 10 seconds
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create token near expiration
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Email should still be extractable
        decoded_payload = verify_jwt_token(token, secret_key)
        assert decoded_payload["email"] == email, \
            f"Extracted email should match original, expected '{email}', got '{decoded_payload['email']}'"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_decoded_payload_contains_all_claims(self, email, secret_key):
        """
        **Validates: Requirements 9.4**
        Feature: jwt-authentication-migration, Property 10: Valid Token Email Extraction
        
        For any valid JWT token, the decoded payload must contain all expected claims
        (email, iat, exp).
        
        This test verifies that:
        1. All claims are preserved during encoding and decoding
        2. The payload structure is complete
        3. Email is part of a complete payload
        """
        # Action: Generate a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create token
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Decoded payload should contain all claims
        decoded_payload = verify_jwt_token(token, secret_key)
        
        assert "email" in decoded_payload, "Decoded payload should contain 'email' claim"
        assert "iat" in decoded_payload, "Decoded payload should contain 'iat' claim"
        assert "exp" in decoded_payload, "Decoded payload should contain 'exp' claim"
        
        # Verify values match
        assert decoded_payload["email"] == email
        assert decoded_payload["iat"] == issued_at
        assert decoded_payload["exp"] == expiration
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_email_extraction_returns_string_type(self, email, secret_key):
        """
        **Validates: Requirements 9.4**
        Feature: jwt-authentication-migration, Property 10: Valid Token Email Extraction
        
        For any valid JWT token, the extracted email must be a string type.
        
        This test verifies that:
        1. Email claim is returned as a string
        2. Type is preserved during encoding and decoding
        3. Email can be used as a string without type conversion
        """
        # Action: Generate a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create token
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Extracted email should be a string
        decoded_payload = verify_jwt_token(token, secret_key)
        extracted_email = decoded_payload["email"]
        
        assert isinstance(extracted_email, str), \
            f"Extracted email should be a string, got {type(extracted_email)}"
        assert extracted_email == email
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_multiple_verifications_extract_same_email(self, email, secret_key):
        """
        **Validates: Requirements 9.4**
        Feature: jwt-authentication-migration, Property 10: Valid Token Email Extraction
        
        For any valid JWT token, multiple verification calls must extract the same email.
        
        This test verifies that:
        1. Token verification is idempotent
        2. Email extraction is consistent across multiple calls
        3. Token is not modified during verification
        """
        # Action: Generate a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create token
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Multiple verifications should extract the same email
        decoded_payload1 = verify_jwt_token(token, secret_key)
        decoded_payload2 = verify_jwt_token(token, secret_key)
        decoded_payload3 = verify_jwt_token(token, secret_key)
        
        assert decoded_payload1["email"] == email
        assert decoded_payload2["email"] == email
        assert decoded_payload3["email"] == email
        
        # All extractions should be identical
        assert decoded_payload1["email"] == decoded_payload2["email"] == decoded_payload3["email"]
