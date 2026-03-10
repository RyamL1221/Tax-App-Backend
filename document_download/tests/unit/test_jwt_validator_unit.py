"""
Unit Tests for JWT Validator

Tests JWT token validation functionality.
"""

import pytest
import jwt
from datetime import datetime, timedelta

from document_download.jwt_validator import validate_jwt
from document_download.exceptions import AuthenticationError


class TestJWTValidator:
    """Test suite for JWT validator."""
    
    def test_valid_token_returns_payload(self):
        """Test that valid token returns payload."""
        secret = "test-secret-key-at-least-32-characters-long"
        payload = {
            "userId": "user123",
            "email": "test@example.com",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        result = validate_jwt(token, secret)
        
        assert result["userId"] == "user123"
        assert result["email"] == "test@example.com"
    
    def test_expired_token_raises_authentication_error(self):
        """Test that expired token raises AuthenticationError."""
        secret = "test-secret-key-at-least-32-characters-long"
        payload = {
            "userId": "user123",
            "email": "test@example.com",
            "iat": datetime.utcnow() - timedelta(hours=2),
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, secret)
        
        assert "expired" in str(exc_info.value).lower()
    
    def test_invalid_signature_raises_authentication_error(self):
        """Test that invalid signature raises AuthenticationError."""
        secret = "test-secret-key-at-least-32-characters-long"
        wrong_secret = "wrong-secret-key-at-least-32-characters-long"
        payload = {
            "userId": "user123",
            "email": "test@example.com",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, wrong_secret)
        
        assert "signature" in str(exc_info.value).lower()
    
    def test_missing_user_id_claim_raises_authentication_error(self):
        """Test that missing userId claim raises AuthenticationError."""
        secret = "test-secret-key-at-least-32-characters-long"
        payload = {
            "email": "test@example.com",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, secret)
        
        assert "userId" in str(exc_info.value)
    
    def test_missing_email_claim_raises_authentication_error(self):
        """Test that missing email claim raises AuthenticationError."""
        secret = "test-secret-key-at-least-32-characters-long"
        payload = {
            "userId": "user123",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, secret)
        
        assert "email" in str(exc_info.value)
    
    def test_invalid_token_format_raises_authentication_error(self):
        """Test that invalid token format raises AuthenticationError."""
        secret = "test-secret-key-at-least-32-characters-long"
        invalid_token = "not.a.valid.jwt.token"
        
        with pytest.raises(AuthenticationError):
            validate_jwt(invalid_token, secret)
