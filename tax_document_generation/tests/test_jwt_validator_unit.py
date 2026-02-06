"""
Unit tests for JWT validator module.

This module tests the validate_jwt function with various token scenarios
including valid tokens, expired tokens, invalid signatures, and malformed tokens.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from tax_document_generation.jwt_validator import validate_jwt
from tax_document_generation.exceptions import AuthenticationError


class TestValidateJWT:
    """Unit tests for validate_jwt function."""
    
    def test_valid_token_returns_payload(self):
        """Test that a valid JWT token returns the decoded payload."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        user_id = "user-123"
        payload = {
            "userId": user_id,
            "email": "test@example.com",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Act
        result = validate_jwt(token, secret)
        
        # Assert
        assert result["userId"] == user_id
        assert result["email"] == "test@example.com"
    
    def test_expired_token_raises_authentication_error(self):
        """Test that an expired JWT token raises AuthenticationError."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        payload = {
            "userId": "user-123",
            "iat": datetime.utcnow() - timedelta(hours=2),
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, secret)
        
        assert "expired" in str(exc_info.value).lower()
    
    def test_invalid_signature_raises_authentication_error(self):
        """Test that a token with invalid signature raises AuthenticationError."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        wrong_secret = "wrong-secret-key-at-least-32-characters-long"
        payload = {
            "userId": "user-123",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, wrong_secret)
        
        assert "signature" in str(exc_info.value).lower()
    
    def test_malformed_token_raises_authentication_error(self):
        """Test that a malformed JWT token raises AuthenticationError."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        malformed_token = "not.a.valid.jwt.token"
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(malformed_token, secret)
        
        assert "format" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
    
    def test_empty_token_raises_authentication_error(self):
        """Test that an empty token raises AuthenticationError."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt("", secret)
        
        assert "non-empty" in str(exc_info.value).lower()
    
    def test_empty_secret_raises_authentication_error(self):
        """Test that an empty secret raises AuthenticationError."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        payload = {
            "userId": "user-123",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, "")
        
        assert "non-empty" in str(exc_info.value).lower()
    
    def test_token_without_userid_raises_authentication_error(self):
        """Test that a token without userId claim raises AuthenticationError."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        payload = {
            "email": "test@example.com",  # Missing userId
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            validate_jwt(token, secret)
        
        assert "userId" in str(exc_info.value)
    
    def test_token_with_different_algorithm_raises_authentication_error(self):
        """Test that a token signed with a different algorithm raises AuthenticationError."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        payload = {
            "userId": "user-123",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        # Sign with HS512 instead of HS256
        token = jwt.encode(payload, secret, algorithm="HS512")
        
        # Act & Assert
        # This should fail because validate_jwt only accepts HS256
        with pytest.raises(AuthenticationError):
            validate_jwt(token, secret)
    
    def test_none_token_raises_authentication_error(self):
        """Test that None as token raises AuthenticationError."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        
        # Act & Assert
        with pytest.raises(AuthenticationError):
            validate_jwt(None, secret)
    
    def test_none_secret_raises_authentication_error(self):
        """Test that None as secret raises AuthenticationError."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        payload = {
            "userId": "user-123",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Act & Assert
        with pytest.raises(AuthenticationError):
            validate_jwt(token, None)
    
    def test_valid_token_with_additional_claims(self):
        """Test that a valid token with additional claims works correctly."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        user_id = "user-456"
        payload = {
            "userId": user_id,
            "email": "test@example.com",
            "role": "admin",
            "permissions": ["read", "write"],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Act
        result = validate_jwt(token, secret)
        
        # Assert
        assert result["userId"] == user_id
        assert result["email"] == "test@example.com"
        assert result["role"] == "admin"
        assert result["permissions"] == ["read", "write"]
    
    def test_token_about_to_expire_is_still_valid(self):
        """Test that a token about to expire (but not yet expired) is still valid."""
        # Arrange
        secret = "test-secret-key-at-least-32-characters-long"
        user_id = "user-789"
        payload = {
            "userId": user_id,
            "iat": datetime.utcnow() - timedelta(minutes=59),
            "exp": datetime.utcnow() + timedelta(seconds=5)  # Expires in 5 seconds
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Act
        result = validate_jwt(token, secret)
        
        # Assert
        assert result["userId"] == user_id
