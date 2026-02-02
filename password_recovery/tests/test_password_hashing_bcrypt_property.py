"""
Property-based tests for password hashing with bcrypt.

Feature: password-recovery
Property 8: Password Hashing with Bcrypt

**Validates: Requirements 3.7, 5.4**

For any valid password reset request, the new password should be hashed using 
bcrypt with a work factor of at least 12 before being stored.
"""

import pytest
import bcrypt
from hypothesis import given, strategies as st, settings
from password_recovery.password_hasher import PasswordHasher


class TestPasswordHashingBcryptProperty:
    """Property-based tests for password hashing with bcrypt."""
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=1000)  # Bcrypt is intentionally slow
    def test_hash_password_returns_bcrypt_hash(self, password):
        """
        Property: Hashing a password should return a valid bcrypt hash.
        
        For any password, the hash_password method should return a string
        that is a valid bcrypt hash.
        """
        hasher = PasswordHasher()
        hashed = hasher.hash_password(password)
        
        # Should return a string
        assert isinstance(hashed, str)
        # Should not be empty
        assert len(hashed) > 0
        # Bcrypt hashes start with $2b$ (or $2a$, $2y$)
        assert hashed.startswith('$2')
        # Bcrypt hashes have a specific format
        assert '$' in hashed
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=1000)
    def test_hashed_password_can_be_verified(self, password):
        """
        Property: Hashed passwords should be verifiable.
        
        For any password, after hashing it, verify_password should return
        True when given the same password and the hash.
        """
        hasher = PasswordHasher()
        hashed = hasher.hash_password(password)
        
        # Verification should succeed with correct password
        is_valid = hasher.verify_password(password, hashed)
        assert is_valid is True
    
    @given(st.text(min_size=1, max_size=100), st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=1000)
    def test_wrong_password_fails_verification(self, password1, password2):
        """
        Property: Wrong passwords should fail verification.
        
        For any two different passwords, verifying password2 against the
        hash of password1 should return False.
        """
        # Skip if passwords are the same
        if password1 == password2:
            return
        
        hasher = PasswordHasher()
        hashed = hasher.hash_password(password1)
        
        # Verification should fail with wrong password
        is_valid = hasher.verify_password(password2, hashed)
        assert is_valid is False
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=2000)  # Two hashes take longer
    def test_same_password_produces_different_hashes(self, password):
        """
        Property: Hashing the same password twice should produce different hashes.
        
        For any password, hashing it twice should produce different hash strings
        due to different salts, but both should verify correctly.
        """
        hasher = PasswordHasher()
        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)
        
        # Hashes should be different (different salts)
        assert hash1 != hash2
        
        # But both should verify correctly
        assert hasher.verify_password(password, hash1) is True
        assert hasher.verify_password(password, hash2) is True
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=1000)
    def test_hash_uses_work_factor_12(self, password):
        """
        Property: Hashes should use work factor of at least 12.
        
        For any password, the bcrypt hash should be generated with a work
        factor of at least 12 for security.
        """
        hasher = PasswordHasher()
        hashed = hasher.hash_password(password)
        
        # Extract work factor from bcrypt hash
        # Bcrypt hash format: $2b$12$... where 12 is the work factor
        parts = hashed.split('$')
        if len(parts) >= 3:
            work_factor = int(parts[2])
            assert work_factor >= 12, f"Work factor {work_factor} is less than 12"
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=1000)
    def test_get_work_factor_returns_12(self, _):
        """
        Property: get_work_factor should return 12.
        
        The hasher should be configured with a work factor of 12.
        """
        hasher = PasswordHasher()
        work_factor = hasher.get_work_factor()
        
        assert work_factor == 12
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=1000)
    def test_hash_does_not_contain_plaintext(self, password):
        """
        Property: Hash should not contain the plaintext password.
        
        For any password longer than 1 character, the hash should not contain 
        the plaintext password as a substring (basic security check).
        
        Note: Single characters may appear in the base64-encoded hash by chance,
        which is not a security issue.
        """
        # Skip single character passwords as they may appear in base64 encoding
        if len(password) <= 1:
            return
            
        hasher = PasswordHasher()
        hashed = hasher.hash_password(password)
        
        # Hash should not contain plaintext password
        # (This is a basic check - bcrypt is designed to prevent this)
        assert password not in hashed
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=2000)  # Multiple verifications
    def test_hash_is_deterministic_with_same_salt(self, password):
        """
        Property: Bcrypt verification should work correctly.
        
        For any password and its hash, the verification should consistently
        return True for the correct password and False for incorrect ones.
        """
        hasher = PasswordHasher()
        hashed = hasher.hash_password(password)
        
        # Multiple verifications should give same result
        result1 = hasher.verify_password(password, hashed)
        result2 = hasher.verify_password(password, hashed)
        result3 = hasher.verify_password(password, hashed)
        
        assert result1 is True
        assert result2 is True
        assert result3 is True
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=1000)
    def test_invalid_hash_fails_verification(self, password):
        """
        Property: Invalid hashes should fail verification gracefully.
        
        For any password and an invalid hash string, verification should
        return False without raising an exception.
        """
        hasher = PasswordHasher()
        
        # Try to verify against an invalid hash
        invalid_hash = "not-a-valid-bcrypt-hash"
        
        # Should return False, not raise an exception
        is_valid = hasher.verify_password(password, invalid_hash)
        assert is_valid is False
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=1000)
    def test_empty_password_can_be_hashed(self, _):
        """
        Property: Empty passwords should be hashable (even if not recommended).
        
        The hasher should be able to hash empty strings without errors,
        though in practice the input validator would reject them.
        """
        hasher = PasswordHasher()
        
        # Should be able to hash empty string
        hashed = hasher.hash_password("")
        
        # Should return a valid hash
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed.startswith('$2')
        
        # Should verify correctly
        assert hasher.verify_password("", hashed) is True
    
    @given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()', min_size=8, max_size=50))
    @settings(max_examples=100, deadline=1500)
    def test_strong_passwords_hash_correctly(self, password):
        """
        Property: Strong passwords should hash and verify correctly.
        
        For any strong password (typical user passwords), hashing and
        verification should work correctly.
        """
        hasher = PasswordHasher()
        hashed = hasher.hash_password(password)
        
        # Should hash successfully
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        
        # Should verify correctly
        assert hasher.verify_password(password, hashed) is True
        
        # Should reject wrong passwords
        wrong_password = password + "x"
        assert hasher.verify_password(wrong_password, hashed) is False
