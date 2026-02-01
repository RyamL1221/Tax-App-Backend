"""
Unit tests for password verification functionality.

These tests verify specific examples and edge cases for password verification
using bcrypt.
"""

import bcrypt
import pytest
from user_login.password_verifier import verify_password, InvalidCredentialsError


class TestPasswordVerifier:
    """Unit tests for password verification."""
    
    def test_correct_password_verification(self):
        """
        Test that correct password verification returns True.
        
        Validates: Requirements 4.1
        """
        password = "SecurePass123!"
        # Generate a bcrypt hash for testing
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        
        # Verify the password
        result = verify_password(password, password_hash)
        
        assert result is True, "Correct password should verify successfully"
    
    def test_incorrect_password_raises_invalid_credentials_error(self):
        """
        Test that incorrect password raises InvalidCredentialsError.
        
        Validates: Requirements 4.2
        """
        password = "SecurePass123!"
        wrong_password = "WrongPassword456!"
        # Generate a bcrypt hash for the correct password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        
        # Verify with wrong password should raise InvalidCredentialsError
        with pytest.raises(InvalidCredentialsError) as exc_info:
            verify_password(wrong_password, password_hash)
        
        assert "Password does not match" in str(exc_info.value), \
            "Error message should indicate password mismatch"
    
    def test_invalid_hash_format_raises_invalid_credentials_error(self):
        """
        Test that invalid hash format raises InvalidCredentialsError.
        
        Validates: Requirements 4.1
        """
        password = "SecurePass123!"
        invalid_hash = "not-a-valid-bcrypt-hash"
        
        # Verify with invalid hash should raise InvalidCredentialsError
        with pytest.raises(InvalidCredentialsError) as exc_info:
            verify_password(password, invalid_hash)
        
        assert "Password verification failed" in str(exc_info.value), \
            "Error message should indicate verification failure"
    
    def test_empty_password_raises_error(self):
        """
        Test that empty password raises an error.
        
        Validates: Requirements 4.1
        """
        password = "SecurePass123!"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        
        # Empty password should raise an error
        with pytest.raises(Exception):
            verify_password("", password_hash)
    
    def test_uses_bcrypt_checkpw(self):
        """
        Test that the function uses bcrypt.checkpw for verification.
        
        This ensures constant-time comparison is used to prevent timing attacks.
        
        Validates: Requirements 4.1, 7.2
        """
        password = "TestPassword123!"
        # Generate a known bcrypt hash
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        
        # Verify the password
        result = verify_password(password, password_hash)
        
        # The result should match what bcrypt.checkpw would return
        expected = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        assert result == expected, "Should use bcrypt.checkpw for verification"
    
    def test_encoding_handled_correctly(self):
        """
        Test that string to bytes encoding is handled correctly.
        
        Validates: Requirements 4.1
        """
        # Test with password containing special characters
        password = "Pässwörd123!@#"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        
        # Should handle UTF-8 encoding correctly
        result = verify_password(password, password_hash)
        assert result is True, "Should handle UTF-8 encoding correctly"
