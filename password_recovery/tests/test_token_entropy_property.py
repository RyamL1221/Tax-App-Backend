"""
Property-based test for token entropy requirement.

This test verifies that for any registered user requesting a password reset,
the generated reset token should have at least 32 bytes (256 bits) of entropy
from a cryptographically secure random source.
"""

import os
import base64
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from hypothesis import given, settings, strategies as st
from password_recovery.token_generator import TokenGenerator


# Strategy for generating valid email addresses
valid_emails = st.emails()


class TestTokenEntropyProperty:
    """Property-based test for token entropy requirement."""
    
    @settings(max_examples=20, deadline=None)
    @given(email=valid_emails)
    def test_token_entropy_requirement(self, email):
        """
        **Validates: Requirements 1.4, 5.1**
        Feature: password-recovery, Property 2: Token Entropy Requirement
        
        For any registered user requesting a password reset, the generated reset 
        token should have at least 32 bytes (256 bits) of entropy from a 
        cryptographically secure random source.
        """
        # Create token generator
        generator = TokenGenerator()
        
        # Generate a reset token for the user
        plaintext_token, token_hash, expiration = generator.generate_reset_token(email)
        
        # Property 1: Token should be a non-empty string
        assert isinstance(plaintext_token, str), \
            "Plaintext token should be a string"
        assert len(plaintext_token) > 0, \
            "Plaintext token should not be empty"
        
        # Property 2: Token should be valid base64-encoded
        try:
            token_bytes = base64.urlsafe_b64decode(plaintext_token)
        except Exception as e:
            raise AssertionError(f"Token should be valid URL-safe base64: {e}")
        
        # Property 3: Token should have exactly 32 bytes (256 bits) of entropy
        assert len(token_bytes) == 32, \
            f"Token should have exactly 32 bytes (256 bits) of entropy. " \
            f"Got {len(token_bytes)} bytes instead."
        
        # Property 4: Token bytes should appear random (basic entropy check)
        # Check that not all bytes are the same (would indicate poor randomness)
        unique_bytes = len(set(token_bytes))
        assert unique_bytes > 1, \
            "Token bytes should have variety (not all the same value). " \
            f"Only {unique_bytes} unique byte value(s) found."
        
        # Property 5: Multiple tokens should be unique (no collisions)
        # Generate a second token for the same email
        plaintext_token2, token_hash2, _ = generator.generate_reset_token(email)
        
        assert plaintext_token != plaintext_token2, \
            "Multiple tokens for the same user should be unique (different random values)"
        assert token_hash != token_hash2, \
            "Multiple token hashes for the same user should be unique"
        
        # Property 6: Token should use cryptographically secure randomness
        # We verify this indirectly by checking that tokens are highly unique
        # Generate multiple tokens and verify they're all different
        tokens = set()
        for _ in range(10):
            token, _, _ = generator.generate_reset_token(email)
            tokens.add(token)
        
        assert len(tokens) == 10, \
            "All generated tokens should be unique. " \
            f"Expected 10 unique tokens, got {len(tokens)}. " \
            "This suggests poor randomness or insufficient entropy."
        
        # Property 7: Token hash should be SHA-256 (64 hex characters)
        assert len(token_hash) == 64, \
            f"Token hash should be 64 characters (SHA-256 hex). Got {len(token_hash)}"
        
        # Verify hash contains only hex characters
        try:
            int(token_hash, 16)
        except ValueError:
            raise AssertionError("Token hash should be a valid hexadecimal string")
        
        # Property 8: Token should be URL-safe (no + or / characters)
        assert '+' not in plaintext_token, \
            "Token should use URL-safe base64 encoding (no + characters)"
        assert '/' not in plaintext_token, \
            "Token should use URL-safe base64 encoding (no / characters)"
        
        # Property 9: Expiration should be set (verified in other tests, but check it exists)
        assert expiration is not None, \
            "Expiration timestamp should be set"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '-s'])
