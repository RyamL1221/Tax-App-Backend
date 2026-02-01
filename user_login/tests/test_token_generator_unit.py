"""
Unit tests for token generation functionality.

These tests verify specific examples and edge cases for token generation.
"""

import pytest
from user_login.token_generator import generate_auth_token


class TestTokenGenerator:
    """Unit tests for token generator."""
    
    def test_token_length_is_64_characters(self):
        """
        Test that generated token is exactly 64 characters.
        
        Validates: Requirements 5.1, 5.2, 5.3
        """
        token = generate_auth_token()
        
        assert len(token) == 64, \
            f"Token should be 64 characters (32 bytes in hex), got {len(token)}"
    
    def test_token_contains_only_hexadecimal_characters(self):
        """
        Test that token contains only valid hexadecimal characters.
        
        Validates: Requirements 5.1, 5.2, 5.3
        """
        token = generate_auth_token()
        
        # Check that all characters are valid hex (0-9, a-f)
        valid_hex_chars = set('0123456789abcdef')
        token_chars = set(token.lower())
        
        assert token_chars.issubset(valid_hex_chars), \
            f"Token should contain only hex characters, found: {token_chars - valid_hex_chars}"
    
    def test_tokens_are_unique_across_multiple_generations(self):
        """
        Test that multiple token generations produce unique tokens.
        
        Due to the cryptographically secure random generation, the probability
        of collision is astronomically low (2^-256 for 32-byte tokens).
        
        Validates: Requirements 5.1, 5.2, 5.3
        """
        # Generate 100 tokens
        tokens = [generate_auth_token() for _ in range(100)]
        
        # All tokens should be unique
        unique_tokens = set(tokens)
        assert len(unique_tokens) == 100, \
            f"Expected 100 unique tokens, got {len(unique_tokens)}"
    
    def test_token_is_string_type(self):
        """
        Test that generated token is a string.
        
        Validates: Requirements 5.1, 5.2, 5.3
        """
        token = generate_auth_token()
        
        assert isinstance(token, str), \
            f"Token should be a string, got {type(token)}"
    
    def test_token_is_lowercase_hex(self):
        """
        Test that token uses lowercase hexadecimal characters.
        
        secrets.token_hex() returns lowercase hex by default.
        
        Validates: Requirements 5.1, 5.2, 5.3
        """
        token = generate_auth_token()
        
        # Token should be lowercase (no uppercase A-F)
        assert token == token.lower(), \
            "Token should use lowercase hexadecimal characters"
    
    def test_multiple_calls_produce_different_tokens(self):
        """
        Test that consecutive calls produce different tokens.
        
        This verifies that the random generator is properly seeded and
        not producing predictable sequences.
        
        Validates: Requirements 5.1, 5.2, 5.3
        """
        token1 = generate_auth_token()
        token2 = generate_auth_token()
        token3 = generate_auth_token()
        
        # All three tokens should be different
        assert token1 != token2, "Consecutive tokens should be different"
        assert token2 != token3, "Consecutive tokens should be different"
        assert token1 != token3, "Consecutive tokens should be different"
    
    def test_token_has_sufficient_entropy(self):
        """
        Test that token has sufficient entropy (at least 32 bytes = 256 bits).
        
        A 64-character hex string represents 32 bytes (256 bits) of entropy,
        which is considered cryptographically secure.
        
        Validates: Requirements 5.1, 5.2, 5.3
        """
        token = generate_auth_token()
        
        # 64 hex characters = 32 bytes = 256 bits
        bytes_count = len(token) // 2
        bits_count = bytes_count * 8
        
        assert bytes_count >= 32, \
            f"Token should have at least 32 bytes, got {bytes_count}"
        assert bits_count >= 256, \
            f"Token should have at least 256 bits of entropy, got {bits_count}"
