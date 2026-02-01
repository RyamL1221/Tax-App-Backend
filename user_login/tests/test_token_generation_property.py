"""
Property-based tests for token generation.

**Validates: Requirements 5.1, 5.2, 5.3**

Property 8: Token generation properties
For any successful authentication, the token generator should produce a
cryptographically secure token of at least 64 hexadecimal characters (32 bytes)
using a secure random generator.
"""

import pytest
from hypothesis import given, settings, strategies as st
from user_login.token_generator import generate_auth_token


@settings(max_examples=100)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_token_length_property(iteration):
    """
    Property 8: Token generation properties - Length
    
    For any invocation, the generated token should be exactly 64 characters long
    (representing 32 bytes).
    
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    token = generate_auth_token()
    
    # Token should be exactly 64 characters (32 bytes in hex)
    assert len(token) == 64, f"Token should be 64 characters, got {len(token)}"


@settings(max_examples=100)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_token_format_property(iteration):
    """
    Property 8: Token generation properties - Format
    
    For any invocation, the generated token should contain only valid
    hexadecimal characters (0-9, a-f).
    
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    token = generate_auth_token()
    
    # Token should contain only hexadecimal characters
    valid_hex_chars = set('0123456789abcdef')
    token_chars = set(token.lower())
    
    assert token_chars.issubset(valid_hex_chars), \
        f"Token should contain only hex characters, got: {token_chars - valid_hex_chars}"


@settings(max_examples=100)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_token_uniqueness_property(iteration):
    """
    Property 8: Token generation properties - Uniqueness
    
    For any invocation, the generated token should be unique (with extremely
    high probability) due to the use of cryptographically secure random generation.
    
    We test this by generating multiple tokens and ensuring they are all different.
    
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    # Generate 10 tokens
    tokens = [generate_auth_token() for _ in range(10)]
    
    # All tokens should be unique
    assert len(tokens) == len(set(tokens)), \
        "All generated tokens should be unique"


@settings(max_examples=100)
@given(iteration=st.integers(min_value=0, max_value=1000))
def test_token_is_string_property(iteration):
    """
    Property 8: Token generation properties - Type
    
    For any invocation, the generated token should be a string.
    
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    token = generate_auth_token()
    
    # Token should be a string
    assert isinstance(token, str), f"Token should be a string, got {type(token)}"
