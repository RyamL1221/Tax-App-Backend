"""
Unit tests for the password_hasher module.

These tests verify specific examples and edge cases for password hashing functionality.
"""

import bcrypt
import pytest
from user_registration.password_hasher import hash_password


class TestPasswordHasher:
    """Unit tests for password hashing functionality."""
    
    def test_hash_starts_with_bcrypt_identifier(self):
        """
        Test that hash starts with bcrypt identifier $2b$12$
        
        Validates: Requirements 3.1
        """
        password = "SecurePass123!"
        password_hash = hash_password(password)
        
        # Verify the hash starts with the correct bcrypt identifier
        assert password_hash.startswith("$2b$12$"), \
            f"Hash should start with '$2b$12$' but got: {password_hash[:8]}"
    
    def test_same_password_produces_different_hashes(self):
        """
        Test that same password produces different hashes due to unique salts
        
        Validates: Requirements 3.1
        """
        password = "TestPassword456!"
        
        # Hash the same password multiple times
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        hash3 = hash_password(password)
        
        # All hashes should be different due to unique salts
        assert hash1 != hash2, "First and second hash should be different"
        assert hash1 != hash3, "First and third hash should be different"
        assert hash2 != hash3, "Second and third hash should be different"
    
    def test_hash_can_be_verified_with_bcrypt_checkpw(self):
        """
        Test that hash can be verified with bcrypt.checkpw()
        
        Validates: Requirements 3.1
        """
        password = "VerifyMe789!"
        password_hash = hash_password(password)
        
        # Convert strings to bytes for bcrypt verification
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        
        # Verify the hash with the original password
        assert bcrypt.checkpw(password_bytes, hash_bytes), \
            "Hash should be verifiable with the original password"
        
        # Verify that a different password does not match
        wrong_password = "WrongPassword123!"
        wrong_password_bytes = wrong_password.encode('utf-8')
        assert not bcrypt.checkpw(wrong_password_bytes, hash_bytes), \
            "Hash should not verify with a different password"
    
    def test_hash_format_and_length(self):
        """
        Test that hash has correct bcrypt format and length
        
        Validates: Requirements 3.1
        """
        password = "FormatTest123!"
        password_hash = hash_password(password)
        
        # Bcrypt hashes are always 60 characters long
        assert len(password_hash) == 60, \
            f"Bcrypt hash should be 60 characters but got {len(password_hash)}"
        
        # Verify it's a valid string (not bytes)
        assert isinstance(password_hash, str), \
            "Hash should be returned as a string, not bytes"
    
    def test_hash_with_special_characters(self):
        """
        Test hashing passwords with various special characters
        
        Validates: Requirements 3.1
        """
        passwords = [
            "P@ssw0rd!",
            "Test#123$",
            "Complex&Pass*456",
            "Symbols%^&*()_+-=",
        ]
        
        for password in passwords:
            password_hash = hash_password(password)
            
            # Verify hash starts with correct identifier
            assert password_hash.startswith("$2b$12$")
            
            # Verify hash can be verified
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            assert bcrypt.checkpw(password_bytes, hash_bytes)
    
    def test_hash_with_unicode_characters(self):
        """
        Test hashing passwords with unicode characters
        
        Validates: Requirements 3.1
        """
        passwords = [
            "Pässwörd123!",
            "Test密码123!",
            "Contraseña456!",
        ]
        
        for password in passwords:
            password_hash = hash_password(password)
            
            # Verify hash starts with correct identifier
            assert password_hash.startswith("$2b$12$")
            
            # Verify hash can be verified
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            assert bcrypt.checkpw(password_bytes, hash_bytes)
    
    def test_hash_minimum_length_password(self):
        """
        Test hashing a very short password (edge case)
        
        Validates: Requirements 3.1
        """
        password = "A1!"  # Very short but valid for bcrypt
        password_hash = hash_password(password)
        
        # Verify hash starts with correct identifier
        assert password_hash.startswith("$2b$12$")
        
        # Verify hash can be verified
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        assert bcrypt.checkpw(password_bytes, hash_bytes)
    
    def test_hash_long_password(self):
        """
        Test hashing a long password (edge case)
        
        Validates: Requirements 3.1
        """
        # Create a long password (bcrypt has a 72 byte limit)
        password = "A1!" + "x" * 60  # 63 characters, well within bcrypt's limit
        password_hash = hash_password(password)
        
        # Verify hash starts with correct identifier
        assert password_hash.startswith("$2b$12$")
        
        # Verify hash can be verified
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        assert bcrypt.checkpw(password_bytes, hash_bytes)
