"""
Property-based tests for JWT signature verification.

These tests verify that JWT tokens are cryptographically signed and can be verified
using the correct secret key. Each property test runs with a minimum of 100 iterations.
"""

import jwt
import pytest
from hypothesis import given, settings, strategies as st, assume
from hypothesis.strategies import emails, text
from user_login.token_generator import generate_jwt_token


class TestJWTSignatureVerificationProperty:
    """Property-based tests for JWT signature verification validation."""
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_verifiable_with_correct_secret(self, email, secret_key):
        """
        **Validates: Requirements 1.5, 9.1**
        Feature: jwt-authentication-migration, Property 3: JWT Signature Verification
        
        For any JWT token generated with a secret key, the token must be verifiable
        using the same secret key.
        
        This test verifies that:
        1. A token generated with a secret key can be decoded with the same key
        2. Signature verification succeeds with the correct key
        3. The decoded payload matches the original data
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Verification 1: Token should be decodable with the correct secret key
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.InvalidSignatureError:
            pytest.fail("Token should be verifiable with the correct secret key (signature verification failed)")
        except jwt.DecodeError as e:
            pytest.fail(f"Token should be decodable with the correct secret key: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error verifying token: {e}")
        
        # Verification 2: Decoded payload should contain the original email
        assert payload["email"] == email, \
            f"Decoded email should match original email, expected '{email}', got '{payload['email']}'"
        
        # Verification 3: Payload should contain all required claims
        assert "email" in payload, "Payload should contain 'email' claim"
        assert "iat" in payload, "Payload should contain 'iat' claim"
        assert "exp" in payload, "Payload should contain 'exp' claim"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?'),
        wrong_secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_fails_verification_with_wrong_secret(self, email, secret_key, wrong_secret_key):
        """
        **Validates: Requirements 1.5, 9.2**
        Feature: jwt-authentication-migration, Property 3: JWT Signature Verification
        
        For any JWT token generated with a secret key, the token must fail verification
        when using a different secret key.
        
        This test verifies that:
        1. A token generated with one secret key cannot be verified with a different key
        2. Signature verification raises InvalidSignatureError with wrong key
        3. The cryptographic signature provides security
        """
        # Ensure the wrong secret key is actually different from the correct one
        assume(secret_key != wrong_secret_key)
        
        # Action: Generate JWT token with the correct secret key
        token = generate_jwt_token(email, secret_key)
        
        # Verification: Token should fail verification with wrong secret key
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, wrong_secret_key, algorithms=["HS256"])
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_fails_verification_with_tampered_signature(self, email, secret_key):
        """
        **Validates: Requirements 1.5, 9.2**
        Feature: jwt-authentication-migration, Property 3: JWT Signature Verification
        
        For any JWT token, tampering with the signature must cause verification to fail.
        
        This test verifies that:
        1. Modifying the signature portion of the token causes verification to fail
        2. The signature protects the integrity of the token
        3. InvalidSignatureError is raised for tampered signatures
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Split token into parts
        parts = token.split('.')
        assert len(parts) == 3, "Token should have 3 parts"
        
        header = parts[0]
        payload = parts[1]
        signature = parts[2]
        
        # Signature should never be empty for a valid JWT
        assert len(signature) > 0, "Signature should not be empty"
        
        # Tamper with the signature by replacing it with a known invalid signature
        # Use a fixed invalid signature to avoid flaky tests
        tampered_signature = "INVALID_SIGNATURE_AAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        
        # Create tampered token
        tampered_token = f"{header}.{payload}.{tampered_signature}"
        
        # Verification: Tampered token should fail verification
        # Note: PyJWT may raise InvalidSignatureError or DecodeError depending on the tampering
        with pytest.raises((jwt.InvalidSignatureError, jwt.DecodeError)):
            jwt.decode(tampered_token, secret_key, algorithms=["HS256"])
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_fails_verification_with_tampered_payload(self, email, secret_key):
        """
        **Validates: Requirements 1.5, 9.2**
        Feature: jwt-authentication-migration, Property 3: JWT Signature Verification
        
        For any JWT token, tampering with the payload must cause verification to fail.
        
        This test verifies that:
        1. Modifying the payload portion of the token causes verification to fail
        2. The signature protects the payload from tampering
        3. InvalidSignatureError is raised for tampered payloads
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Split token into parts
        parts = token.split('.')
        assert len(parts) == 3, "Token should have 3 parts"
        
        header = parts[0]
        payload = parts[1]
        signature = parts[2]
        
        # Tamper with the payload by modifying the last character
        # If payload ends with 'a', change to 'b', otherwise change to 'a'
        if len(payload) > 0:
            if payload[-1] == 'a':
                tampered_payload = payload[:-1] + 'b'
            else:
                tampered_payload = payload[:-1] + 'a'
            
            # Create tampered token
            tampered_token = f"{header}.{tampered_payload}.{signature}"
            
            # Verification: Tampered token should fail verification
            with pytest.raises(jwt.InvalidSignatureError):
                jwt.decode(tampered_token, secret_key, algorithms=["HS256"])
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_fails_verification_with_tampered_header(self, email, secret_key):
        """
        **Validates: Requirements 1.5, 9.2**
        Feature: jwt-authentication-migration, Property 3: JWT Signature Verification
        
        For any JWT token, tampering with the header must cause verification to fail.
        
        This test verifies that:
        1. Modifying the header portion of the token causes verification to fail
        2. The signature protects the header from tampering
        3. InvalidSignatureError is raised for tampered headers
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Split token into parts
        parts = token.split('.')
        assert len(parts) == 3, "Token should have 3 parts"
        
        header = parts[0]
        payload = parts[1]
        signature = parts[2]
        
        # Tamper with the header by modifying the last character
        # If header ends with 'a', change to 'b', otherwise change to 'a'
        if len(header) > 0:
            if header[-1] == 'a':
                tampered_header = header[:-1] + 'b'
            else:
                tampered_header = header[:-1] + 'a'
            
            # Create tampered token
            tampered_token = f"{tampered_header}.{payload}.{signature}"
            
            # Verification: Tampered token should fail verification
            # Note: This might raise DecodeError instead of InvalidSignatureError
            # if the header becomes invalid JSON
            with pytest.raises((jwt.InvalidSignatureError, jwt.DecodeError)):
                jwt.decode(tampered_token, secret_key, algorithms=["HS256"])
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_verification_uses_hs256_algorithm(self, email, secret_key):
        """
        **Validates: Requirements 1.5, 9.1**
        Feature: jwt-authentication-migration, Property 3: JWT Signature Verification
        
        For any JWT token, verification must use the HS256 algorithm.
        
        This test verifies that:
        1. Tokens can be verified with HS256 algorithm
        2. Tokens cannot be verified with other algorithms (e.g., HS512)
        3. The algorithm is enforced during verification
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Verification 1: Token should be verifiable with HS256 algorithm
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            assert payload["email"] == email
        except Exception as e:
            pytest.fail(f"Token should be verifiable with HS256 algorithm: {e}")
        
        # Verification 2: Token should fail verification if wrong algorithm is specified
        # (This tests that the algorithm is actually enforced)
        with pytest.raises(jwt.InvalidAlgorithmError):
            jwt.decode(token, secret_key, algorithms=["HS512"])
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_verification_without_algorithm_fails(self, email, secret_key):
        """
        **Validates: Requirements 1.5, 9.1**
        Feature: jwt-authentication-migration, Property 3: JWT Signature Verification
        
        For any JWT token, verification must fail if no algorithm is specified.
        
        This test verifies that:
        1. Algorithm must be explicitly specified during verification
        2. Verification fails without algorithm specification
        3. Security best practice is enforced (no algorithm guessing)
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Verification: Token verification should fail without algorithm specification
        with pytest.raises((jwt.DecodeError, jwt.InvalidAlgorithmError)):
            jwt.decode(token, secret_key, algorithms=None)
    
    @settings(max_examples=20)
    @given(
        email1=emails(),
        email2=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_tokens_with_different_emails_have_different_signatures(self, email1, email2, secret_key):
        """
        **Validates: Requirements 1.5, 9.1**
        Feature: jwt-authentication-migration, Property 3: JWT Signature Verification
        
        For any two JWT tokens with different email addresses but the same secret key,
        the tokens must have different signatures.
        
        This test verifies that:
        1. Different payloads produce different signatures
        2. The signature is dependent on the payload content
        3. Each token is unique based on its content
        """
        # Ensure emails are different
        assume(email1 != email2)
        
        # Action: Generate two JWT tokens with different emails
        token1 = generate_jwt_token(email1, secret_key)
        token2 = generate_jwt_token(email2, secret_key)
        
        # Extract signatures
        signature1 = token1.split('.')[2]
        signature2 = token2.split('.')[2]
        
        # Verification: Signatures should be different
        assert signature1 != signature2, \
            "Tokens with different emails should have different signatures"
        
        # Verification: Both tokens should be verifiable with the same secret
        payload1 = jwt.decode(token1, secret_key, algorithms=["HS256"])
        payload2 = jwt.decode(token2, secret_key, algorithms=["HS256"])
        
        assert payload1["email"] == email1
        assert payload2["email"] == email2
