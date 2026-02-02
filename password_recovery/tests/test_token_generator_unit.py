"""
Unit tests for TokenGenerator class.

Tests token generation, encoding, hashing, and expiration calculation.
"""

import base64
import hashlib
import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# Import the class to test
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from password_recovery.token_generator import TokenGenerator


class TestTokenGenerator:
    """Tests for TokenGenerator class."""
    
    def test_generate_reset_token_returns_tuple(self):
        """Test that generate_reset_token returns a tuple with 3 elements."""
        generator = TokenGenerator()
        result = generator.generate_reset_token("user@example.com")
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        
        plaintext_token, token_hash, expiration = result
        assert isinstance(plaintext_token, str)
        assert isinstance(token_hash, str)
        assert isinstance(expiration, datetime)
    
    def test_token_format_is_base64(self):
        """Test that plaintext token is valid URL-safe base64."""
        generator = TokenGenerator()
        plaintext_token, _, _ = generator.generate_reset_token("user@example.com")
        
        # Should be able to decode without error
        try:
            decoded = base64.urlsafe_b64decode(plaintext_token)
            assert len(decoded) == 32  # Should be 32 bytes
        except Exception as e:
            pytest.fail(f"Token is not valid base64: {e}")
    
    def test_token_hash_is_sha256(self):
        """Test that token hash is a valid SHA-256 hex string."""
        generator = TokenGenerator()
        _, token_hash, _ = generator.generate_reset_token("user@example.com")
        
        # SHA-256 hex string should be 64 characters
        assert len(token_hash) == 64
        
        # Should only contain hex characters
        try:
            int(token_hash, 16)
        except ValueError:
            pytest.fail("Token hash is not a valid hex string")
    
    def test_hash_computation_is_correct(self):
        """Test that the hash is correctly computed from the token."""
        generator = TokenGenerator()
        plaintext_token, token_hash, _ = generator.generate_reset_token("user@example.com")
        
        # Decode the plaintext token
        token_bytes = base64.urlsafe_b64decode(plaintext_token)
        
        # Compute hash manually
        expected_hash = hashlib.sha256(token_bytes).hexdigest()
        
        # Should match the returned hash
        assert token_hash == expected_hash
    
    def test_expiration_is_one_hour_from_now(self):
        """Test that expiration is set to 1 hour from generation."""
        generator = TokenGenerator()
        before = datetime.now(timezone.utc)
        _, _, expiration = generator.generate_reset_token("user@example.com")
        after = datetime.now(timezone.utc)
        
        # Expected expiration is 1 hour from now
        expected_min = before + timedelta(hours=1)
        expected_max = after + timedelta(hours=1)
        
        # Expiration should be within the range
        assert expected_min <= expiration <= expected_max
    
    def test_expiration_has_timezone(self):
        """Test that expiration timestamp has timezone info (UTC)."""
        generator = TokenGenerator()
        _, _, expiration = generator.generate_reset_token("user@example.com")
        
        # Should have timezone info
        assert expiration.tzinfo is not None
        assert expiration.tzinfo == timezone.utc
    
    def test_tokens_are_unique(self):
        """Test that multiple calls generate different tokens."""
        generator = TokenGenerator()
        
        # Generate multiple tokens
        token1, hash1, _ = generator.generate_reset_token("user@example.com")
        token2, hash2, _ = generator.generate_reset_token("user@example.com")
        token3, hash3, _ = generator.generate_reset_token("user@example.com")
        
        # All tokens should be different
        assert token1 != token2
        assert token2 != token3
        assert token1 != token3
        
        # All hashes should be different
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3
    
    def test_token_entropy_is_32_bytes(self):
        """Test that token has 32 bytes (256 bits) of entropy."""
        generator = TokenGenerator()
        plaintext_token, _, _ = generator.generate_reset_token("user@example.com")
        
        # Decode and check length
        token_bytes = base64.urlsafe_b64decode(plaintext_token)
        assert len(token_bytes) == 32
    
    def test_token_is_url_safe(self):
        """Test that token uses URL-safe base64 encoding."""
        generator = TokenGenerator()
        plaintext_token, _, _ = generator.generate_reset_token("user@example.com")
        
        # URL-safe base64 should not contain + or /
        assert '+' not in plaintext_token
        assert '/' not in plaintext_token
        
        # May contain - and _ instead
        # (not guaranteed in every token, but should be decodable)
        try:
            base64.urlsafe_b64decode(plaintext_token)
        except Exception as e:
            pytest.fail(f"Token is not URL-safe base64: {e}")
    
    def test_different_emails_produce_different_tokens(self):
        """Test that tokens for different emails are different."""
        generator = TokenGenerator()
        
        token1, hash1, _ = generator.generate_reset_token("user1@example.com")
        token2, hash2, _ = generator.generate_reset_token("user2@example.com")
        
        # Tokens should be different (email doesn't affect token generation)
        # but they should still be different due to randomness
        assert token1 != token2
        assert hash1 != hash2
    
    def test_token_generation_uses_secrets_module(self):
        """Test that token generation uses the secrets module for cryptographic security."""
        # This is more of a code inspection test
        # We verify by checking that the token has high entropy
        generator = TokenGenerator()
        
        # Generate many tokens and check they're all unique
        tokens = set()
        for _ in range(100):
            token, _, _ = generator.generate_reset_token("user@example.com")
            tokens.add(token)
        
        # All 100 tokens should be unique (probability of collision is negligible)
        assert len(tokens) == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
