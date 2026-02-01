"""
Unit tests for JWT verification functionality.

These tests verify specific examples and edge cases for JWT token verification,
including signature verification, expiration handling, email extraction, and error cases.
"""

import jwt
import time
import pytest
from jwt_verifier import verify_jwt_token


class TestJWTVerifier:
    """Unit tests for JWT verifier."""
    
    def test_verify_valid_token_succeeds(self):
        """
        Test that verification succeeds for a valid, non-expired token.
        
        Validates: Requirements 9.1, 9.4
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400  # 24 hours from now
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification should succeed
        decoded_payload = verify_jwt_token(token, secret_key)
        
        assert decoded_payload["email"] == email
        assert decoded_payload["iat"] == issued_at
        assert decoded_payload["exp"] == expiration
    
    def test_verify_token_extracts_email(self):
        """
        Test that verification extracts the email claim from valid token.
        
        Validates: Requirements 9.4
        """
        email = "user@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Extract email
        decoded_payload = verify_jwt_token(token, secret_key)
        extracted_email = decoded_payload["email"]
        
        assert extracted_email == email
        assert isinstance(extracted_email, str)
    
    def test_verify_token_with_invalid_signature_raises_error(self):
        """
        Test that verification fails for token with invalid signature.
        
        Validates: Requirements 9.2
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        wrong_secret = "different-secret-key-with-32-chars-min"
        
        # Create token with one secret
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verify with different secret should fail
        with pytest.raises(jwt.InvalidSignatureError):
            verify_jwt_token(token, wrong_secret)
    
    def test_verify_expired_token_raises_error(self):
        """
        Test that verification fails for expired token.
        
        Validates: Requirements 9.3
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create an expired token
        issued_at = int(time.time()) - 172800  # 48 hours ago
        expiration = issued_at + 86400  # 24 hours ago
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification should fail
        with pytest.raises(jwt.ExpiredSignatureError):
            verify_jwt_token(token, secret_key)
    
    def test_verify_token_with_tampered_payload_raises_error(self):
        """
        Test that verification fails for token with tampered payload.
        
        Validates: Requirements 9.2
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Tamper with the payload
        parts = token.split('.')
        header = parts[0]
        payload_part = parts[1]
        signature = parts[2]
        
        # Modify the payload
        if payload_part[-1] == 'a':
            tampered_payload = payload_part[:-1] + 'b'
        else:
            tampered_payload = payload_part[:-1] + 'a'
        
        tampered_token = f"{header}.{tampered_payload}.{signature}"
        
        # Verification should fail
        with pytest.raises(jwt.InvalidSignatureError):
            verify_jwt_token(tampered_token, secret_key)
    
    def test_verify_token_with_invalid_format_raises_error(self):
        """
        Test that verification fails for token with invalid format.
        
        Validates: Requirements 9.1
        """
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Invalid token formats
        invalid_tokens = [
            "not.a.valid.jwt.token",  # Too many segments
            "only.two",  # Too few segments
            "nosegments",  # No segments
            "",  # Empty string
            "a.b.c.d.e",  # Too many segments
        ]
        
        for invalid_token in invalid_tokens:
            with pytest.raises((jwt.DecodeError, ValueError)):
                verify_jwt_token(invalid_token, secret_key)
    
    def test_verify_empty_token_raises_error(self):
        """
        Test that verification fails for empty token.
        
        Validates: Requirements 9.1
        """
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        with pytest.raises(ValueError) as exc_info:
            verify_jwt_token("", secret_key)
        
        assert "token" in str(exc_info.value).lower()
    
    def test_verify_none_token_raises_error(self):
        """
        Test that verification fails for None token.
        
        Validates: Requirements 9.1
        """
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            verify_jwt_token(None, secret_key)
    
    def test_verify_empty_secret_key_raises_error(self):
        """
        Test that verification fails for empty secret key.
        
        Validates: Requirements 9.1
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verify with empty secret should fail
        with pytest.raises(ValueError) as exc_info:
            verify_jwt_token(token, "")
        
        assert "secret" in str(exc_info.value).lower()
    
    def test_verify_none_secret_key_raises_error(self):
        """
        Test that verification fails for None secret key.
        
        Validates: Requirements 9.1
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verify with None secret should fail
        with pytest.raises((ValueError, TypeError, AttributeError)):
            verify_jwt_token(token, None)
    
    def test_verify_token_returns_dict(self):
        """
        Test that verification returns a dictionary payload.
        
        Validates: Requirements 9.4
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verify and check return type
        decoded_payload = verify_jwt_token(token, secret_key)
        
        assert isinstance(decoded_payload, dict)
        assert "email" in decoded_payload
        assert "iat" in decoded_payload
        assert "exp" in decoded_payload
    
    def test_verify_token_with_special_characters_in_email(self):
        """
        Test that verification works with special characters in email.
        
        Validates: Requirements 9.4
        """
        email = "user+test@example.co.uk"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verify and extract email
        decoded_payload = verify_jwt_token(token, secret_key)
        
        assert decoded_payload["email"] == email
    
    def test_verify_token_near_expiration(self):
        """
        Test that verification succeeds for token near expiration but not expired.
        
        Validates: Requirements 9.3, 9.4
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a token that expires in 10 seconds
        issued_at = int(time.time()) - 86390  # Issued 23:59:50 ago
        expiration = issued_at + 86400  # Expires in 10 seconds
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification should succeed
        decoded_payload = verify_jwt_token(token, secret_key)
        
        assert decoded_payload["email"] == email
    
    def test_verify_freshly_issued_token(self):
        """
        Test that verification succeeds for freshly issued token.
        
        Validates: Requirements 9.1, 9.4
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a fresh token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification should succeed immediately
        decoded_payload = verify_jwt_token(token, secret_key)
        
        assert decoded_payload["email"] == email
    
    def test_verify_token_multiple_times_is_idempotent(self):
        """
        Test that verifying the same token multiple times produces same result.
        
        Validates: Requirements 9.1, 9.4
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a valid token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verify multiple times
        decoded1 = verify_jwt_token(token, secret_key)
        decoded2 = verify_jwt_token(token, secret_key)
        decoded3 = verify_jwt_token(token, secret_key)
        
        # All results should be identical
        assert decoded1 == decoded2 == decoded3
        assert decoded1["email"] == email
    
    def test_verify_token_with_long_expiration(self):
        """
        Test that verification succeeds for token with long expiration time.
        
        Validates: Requirements 9.1, 9.4
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a token that expires in 1 year
        issued_at = int(time.time())
        expiration = issued_at + (365 * 24 * 3600)  # 1 year
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification should succeed
        decoded_payload = verify_jwt_token(token, secret_key)
        
        assert decoded_payload["email"] == email
        assert decoded_payload["exp"] == expiration
    
    def test_verify_token_uses_hs256_algorithm(self):
        """
        Test that verification uses HS256 algorithm.
        
        Validates: Requirements 9.1
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a token with HS256
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification should succeed with HS256
        decoded_payload = verify_jwt_token(token, secret_key)
        
        assert decoded_payload["email"] == email
    
    def test_verify_token_with_different_algorithm_fails(self):
        """
        Test that verification fails for token signed with different algorithm.
        
        Validates: Requirements 9.1, 9.2
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a token with HS512 algorithm
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS512")
        
        # Verification should fail (verifier expects HS256)
        with pytest.raises(jwt.InvalidAlgorithmError):
            verify_jwt_token(token, secret_key)
    
    def test_verify_token_preserves_all_claims(self):
        """
        Test that verification preserves all claims in the payload.
        
        Validates: Requirements 9.4
        """
        email = "test@example.com"
        secret_key = "my-secret-key-with-at-least-32-characters"
        
        # Create a token
        issued_at = int(time.time())
        expiration = issued_at + 86400
        
        payload = {
            "email": email,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verify and check all claims are present
        decoded_payload = verify_jwt_token(token, secret_key)
        
        assert decoded_payload["email"] == email
        assert decoded_payload["iat"] == issued_at
        assert decoded_payload["exp"] == expiration
        assert len(decoded_payload) == 3  # Only these 3 claims
