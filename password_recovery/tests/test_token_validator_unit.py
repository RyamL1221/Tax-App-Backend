"""
Unit tests for TokenValidator class.

Tests token validation logic including expiration, usage, and database lookups.
"""

import base64
import hashlib
import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Import the class to test
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from password_recovery.token_validator import TokenValidator
from password_recovery.user_repository import DatabaseError


class TestTokenValidator:
    """Tests for TokenValidator class."""
    
    def test_validate_token_returns_tuple(self):
        """Test that validate_token returns a tuple with 3 elements."""
        validator = TokenValidator()
        
        # Create a mock token
        token_bytes = b'a' * 32
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        
        # Mock the database call
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = None
            
            result = validator.validate_token(plaintext_token)
            
            assert isinstance(result, tuple)
            assert len(result) == 3
            
            is_valid, email, error = result
            assert isinstance(is_valid, bool)
            assert email is None or isinstance(email, str)
            assert error is None or isinstance(error, str)
    
    def test_valid_token_returns_true(self):
        """Test that a valid token returns True with user email."""
        validator = TokenValidator()
        
        # Create a valid token
        token_bytes = b'a' * 32
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        token_hash = hashlib.sha256(token_bytes).hexdigest()
        
        # Mock database response with valid token
        future_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        mock_token_data = {
            'email': 'user@example.com',
            'expiration': future_time.isoformat(),
            'used_at': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = mock_token_data
            
            is_valid, email, error = validator.validate_token(plaintext_token)
            
            assert is_valid is True
            assert email == 'user@example.com'
            assert error is None
            
            # Verify the correct hash was used for lookup
            mock_get.assert_called_once_with(token_hash)
    
    def test_nonexistent_token_returns_false(self):
        """Test that a non-existent token returns False."""
        validator = TokenValidator()
        
        token_bytes = b'a' * 32
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        
        # Mock database response with None (token not found)
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = None
            
            is_valid, email, error = validator.validate_token(plaintext_token)
            
            assert is_valid is False
            assert email is None
            assert error is not None
            assert 'Invalid or expired' in error
    
    def test_expired_token_returns_false(self):
        """Test that an expired token returns False."""
        validator = TokenValidator()
        
        token_bytes = b'a' * 32
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        
        # Mock database response with expired token
        past_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        mock_token_data = {
            'email': 'user@example.com',
            'expiration': past_time.isoformat(),
            'used_at': None,
            'created_at': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        }
        
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = mock_token_data
            
            is_valid, email, error = validator.validate_token(plaintext_token)
            
            assert is_valid is False
            assert email is None
            assert error is not None
            assert 'expired' in error.lower()
    
    def test_used_token_returns_false(self):
        """Test that a used token returns False."""
        validator = TokenValidator()
        
        token_bytes = b'a' * 32
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        
        # Mock database response with used token
        future_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        used_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        mock_token_data = {
            'email': 'user@example.com',
            'expiration': future_time.isoformat(),
            'used_at': used_time.isoformat(),
            'created_at': (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        }
        
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = mock_token_data
            
            is_valid, email, error = validator.validate_token(plaintext_token)
            
            assert is_valid is False
            assert email is None
            assert error is not None
            assert 'already been used' in error
    
    def test_invalid_base64_token_returns_false(self):
        """Test that an invalid base64 token returns False."""
        validator = TokenValidator()
        
        # Invalid base64 string (not properly padded)
        invalid_token = "not-valid-base64!!!"
        
        # Mock the database to avoid environment variable issues
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = None
            
            is_valid, email, error = validator.validate_token(invalid_token)
            
            assert is_valid is False
            assert email is None
            assert error is not None
    
    def test_database_error_returns_false(self):
        """Test that a database error returns False with generic error."""
        validator = TokenValidator()
        
        token_bytes = b'a' * 32
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        
        # Mock database error
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.side_effect = DatabaseError("Database connection failed")
            
            is_valid, email, error = validator.validate_token(plaintext_token)
            
            assert is_valid is False
            assert email is None
            assert error is not None
            assert 'error occurred' in error.lower()
            # Should not expose database details
            assert 'Database connection failed' not in error
    
    def test_token_hash_computation_matches_generator(self):
        """Test that token hash is computed the same way as TokenGenerator."""
        validator = TokenValidator()
        
        # Create a token the same way TokenGenerator does
        import secrets
        token_bytes = secrets.token_bytes(32)
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        expected_hash = hashlib.sha256(token_bytes).hexdigest()
        
        # Mock database to capture the hash used for lookup
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = None
            
            validator.validate_token(plaintext_token)
            
            # Verify the hash matches what we expect
            mock_get.assert_called_once_with(expected_hash)
    
    def test_expiration_without_timezone_is_handled(self):
        """Test that expiration timestamps without timezone info are handled."""
        validator = TokenValidator()
        
        token_bytes = b'a' * 32
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        
        # Mock database response with timezone-naive expiration
        future_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        # Remove timezone info
        naive_time = future_time.replace(tzinfo=None)
        mock_token_data = {
            'email': 'user@example.com',
            'expiration': naive_time.isoformat(),
            'used_at': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = mock_token_data
            
            is_valid, email, error = validator.validate_token(plaintext_token)
            
            # Should still work (assumes UTC)
            assert is_valid is True
            assert email == 'user@example.com'
    
    def test_validation_checks_all_three_conditions(self):
        """Test that validation checks existence, expiration, and usage."""
        validator = TokenValidator()
        
        token_bytes = b'a' * 32
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        
        # Test 1: Non-existent token (fails check 1)
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = None
            is_valid, _, _ = validator.validate_token(plaintext_token)
            assert is_valid is False
        
        # Test 2: Expired token (fails check 2)
        past_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = {
                'email': 'user@example.com',
                'expiration': past_time.isoformat(),
                'used_at': None,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            is_valid, _, _ = validator.validate_token(plaintext_token)
            assert is_valid is False
        
        # Test 3: Used token (fails check 3)
        future_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = {
                'email': 'user@example.com',
                'expiration': future_time.isoformat(),
                'used_at': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            is_valid, _, _ = validator.validate_token(plaintext_token)
            assert is_valid is False
        
        # Test 4: Valid token (passes all checks)
        with patch('password_recovery.token_validator.get_reset_token') as mock_get:
            mock_get.return_value = {
                'email': 'user@example.com',
                'expiration': future_time.isoformat(),
                'used_at': None,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            is_valid, _, _ = validator.validate_token(plaintext_token)
            assert is_valid is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
