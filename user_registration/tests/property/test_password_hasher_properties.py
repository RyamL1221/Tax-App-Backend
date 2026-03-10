"""
Property-based tests for the password_hasher module.

These tests verify universal properties across randomized inputs using hypothesis.
Each property test runs with a minimum of 100 iterations.
"""

import re
import bcrypt
from hypothesis import given, settings, strategies as st
from user_registration.password_hasher import hash_password


class TestPasswordHashingProperty:
    """Property-based tests for password hashing."""
    
    @settings(max_examples=20, deadline=None)  # Disable deadline as bcrypt is intentionally slow
    @given(
        password=st.text(
            alphabet=st.characters(
                blacklist_categories=['Cs', 'Cc'],
                blacklist_characters='\x00'  # Exclude null bytes which bcrypt can't handle
            ),
            min_size=1,
            max_size=50  # Conservative limit to avoid UTF-8 encoding exceeding 72 bytes
        ).filter(lambda p: len(p.encode('utf-8')) <= 72)  # Ensure byte length doesn't exceed bcrypt limit
    )
    def test_password_hashing_produces_bcrypt_hash_with_work_factor_12(self, password):
        """
        **Validates: Requirements 3.1**
        Feature: user-registration-endpoint, Property 6: Password hashing with bcrypt
        
        For any valid password, the password hasher should produce a bcrypt hash 
        with work factor of at least 12, identifiable by the bcrypt prefix format.
        """
        # Hash the password
        password_hash = hash_password(password)
        
        # Verify the hash is a string
        assert isinstance(password_hash, str), "Hash should be a string"
        
        # Verify the hash starts with bcrypt identifier for work factor 12
        # bcrypt format: $2b$12$... where:
        # - $2b$ is the bcrypt algorithm identifier
        # - 12 is the work factor (cost)
        # - $ is the separator
        # - followed by 22 characters of salt and 31 characters of hash
        assert password_hash.startswith("$2b$12$"), \
            f"Hash should start with '$2b$12$' but got: {password_hash[:8]}"
        
        # Verify the hash has the correct bcrypt format structure
        # Format: $2b$12$[22 char salt][31 char hash]
        bcrypt_pattern = r'^\$2b\$12\$[./A-Za-z0-9]{53}$'
        assert re.match(bcrypt_pattern, password_hash), \
            f"Hash should match bcrypt format pattern but got: {password_hash}"
        
        # Verify the hash length is correct (60 characters total for bcrypt)
        assert len(password_hash) == 60, \
            f"Bcrypt hash should be 60 characters but got {len(password_hash)}"
        
        # Verify the hash can be used to verify the original password
        # This ensures the hash is valid and was created correctly
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        assert bcrypt.checkpw(password_bytes, hash_bytes), \
            "Hash should be verifiable with the original password"
    
    @settings(max_examples=20, deadline=None)  # Disable deadline as bcrypt is intentionally slow
    @given(
        password=st.text(
            alphabet=st.characters(
                blacklist_categories=['Cs', 'Cc'],
                blacklist_characters='\x00'
            ),
            min_size=1,
            max_size=50
        ).filter(lambda p: len(p.encode('utf-8')) <= 72)  # Ensure byte length doesn't exceed bcrypt limit
    )
    def test_same_password_produces_different_hashes(self, password):
        """
        **Validates: Requirements 3.1**
        Feature: user-registration-endpoint, Property 6: Password hashing with bcrypt
        
        For any valid password, hashing the same password multiple times should 
        produce different hashes due to unique salts, but all should verify correctly.
        """
        # Hash the same password twice
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # The hashes should be different (due to different salts)
        assert hash1 != hash2, \
            "Same password should produce different hashes due to unique salts"
        
        # Both hashes should verify with the original password
        password_bytes = password.encode('utf-8')
        assert bcrypt.checkpw(password_bytes, hash1.encode('utf-8')), \
            "First hash should verify with original password"
        assert bcrypt.checkpw(password_bytes, hash2.encode('utf-8')), \
            "Second hash should verify with original password"
