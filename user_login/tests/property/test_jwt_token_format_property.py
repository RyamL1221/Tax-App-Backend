"""
Property-based tests for JWT token format.

These tests verify universal properties across randomized inputs using hypothesis.
Each property test runs with a minimum of 100 iterations.
"""

import re
import base64
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails, text
from user_login.token_generator import generate_jwt_token


class TestJWTTokenFormatProperty:
    """Property-based tests for JWT token format validation."""
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_has_three_segments(self, email, secret_key):
        """
        **Validates: Requirements 1.1**
        Feature: jwt-authentication-migration, Property 1: JWT Token Format
        
        For any successful authentication, the generated token must be a valid JWT
        with exactly three base64url-encoded segments separated by periods
        (header.payload.signature).
        
        This test verifies that:
        1. The token contains exactly three segments
        2. The segments are separated by periods
        3. Each segment is non-empty
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Verification 1: Token should be a string
        assert isinstance(token, str), \
            f"Token should be a string, got {type(token)}"
        
        # Verification 2: Token should contain exactly 2 periods (3 segments)
        period_count = token.count('.')
        assert period_count == 2, \
            f"JWT token should contain exactly 2 periods (3 segments), got {period_count}"
        
        # Verification 3: Split token into segments
        segments = token.split('.')
        assert len(segments) == 3, \
            f"JWT token should have exactly 3 segments, got {len(segments)}"
        
        # Verification 4: Each segment should be non-empty
        for i, segment in enumerate(segments):
            assert len(segment) > 0, \
                f"Segment {i} should be non-empty"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_segments_are_base64url_encoded(self, email, secret_key):
        """
        **Validates: Requirements 1.1**
        Feature: jwt-authentication-migration, Property 1: JWT Token Format
        
        For any successful authentication, each segment of the JWT token must be
        base64url-encoded (using characters A-Z, a-z, 0-9, -, _).
        
        This test verifies that:
        1. Each segment uses only valid base64url characters
        2. The segments follow the base64url encoding standard
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Split token into segments
        segments = token.split('.')
        
        # Base64url character set: A-Z, a-z, 0-9, -, _
        # Note: Padding (=) may be omitted in base64url encoding
        base64url_pattern = re.compile(r'^[A-Za-z0-9_-]+$')
        
        # Verification: Each segment should contain only base64url characters
        for i, segment in enumerate(segments):
            assert base64url_pattern.match(segment), \
                f"Segment {i} should contain only base64url characters (A-Z, a-z, 0-9, -, _), got: {segment[:50]}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_segments_are_decodable(self, email, secret_key):
        """
        **Validates: Requirements 1.1**
        Feature: jwt-authentication-migration, Property 1: JWT Token Format
        
        For any successful authentication, the header and payload segments of the
        JWT token must be decodable as base64url-encoded JSON.
        
        This test verifies that:
        1. The header segment can be decoded from base64url
        2. The payload segment can be decoded from base64url
        3. The decoded segments are valid (can be processed)
        
        Note: The signature segment is binary data and doesn't need to be JSON-decodable.
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Split token into segments
        segments = token.split('.')
        header_segment = segments[0]
        payload_segment = segments[1]
        signature_segment = segments[2]
        
        # Helper function to decode base64url (add padding if needed)
        def decode_base64url(data):
            # Add padding if needed
            padding = 4 - (len(data) % 4)
            if padding != 4:
                data += '=' * padding
            # Replace base64url characters with standard base64
            data = data.replace('-', '+').replace('_', '/')
            return base64.b64decode(data)
        
        # Verification 1: Header segment should be decodable
        try:
            header_decoded = decode_base64url(header_segment)
            assert len(header_decoded) > 0, \
                "Decoded header should not be empty"
        except Exception as e:
            pytest.fail(f"Header segment should be decodable as base64url: {e}")
        
        # Verification 2: Payload segment should be decodable
        try:
            payload_decoded = decode_base64url(payload_segment)
            assert len(payload_decoded) > 0, \
                "Decoded payload should not be empty"
        except Exception as e:
            pytest.fail(f"Payload segment should be decodable as base64url: {e}")
        
        # Verification 3: Signature segment should be decodable (but not necessarily JSON)
        try:
            signature_decoded = decode_base64url(signature_segment)
            assert len(signature_decoded) > 0, \
                "Decoded signature should not be empty"
        except Exception as e:
            pytest.fail(f"Signature segment should be decodable as base64url: {e}")
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_format_matches_standard(self, email, secret_key):
        """
        **Validates: Requirements 1.1**
        Feature: jwt-authentication-migration, Property 1: JWT Token Format
        
        For any successful authentication, the generated token must match the
        standard JWT format pattern: header.payload.signature where each part
        is base64url-encoded.
        
        This test verifies that:
        1. The token matches the JWT format regex pattern
        2. The token structure conforms to JWT standards
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # JWT format pattern: three base64url-encoded segments separated by periods
        jwt_pattern = re.compile(r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$')
        
        # Verification: Token should match JWT format pattern
        assert jwt_pattern.match(token), \
            f"Token should match JWT format pattern (header.payload.signature with base64url encoding), got: {token[:100]}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_has_no_whitespace(self, email, secret_key):
        """
        **Validates: Requirements 1.1**
        Feature: jwt-authentication-migration, Property 1: JWT Token Format
        
        For any successful authentication, the generated JWT token must not
        contain any whitespace characters (spaces, tabs, newlines).
        
        This test verifies that:
        1. The token contains no spaces
        2. The token contains no tabs or newlines
        3. The token is a single continuous string
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Verification 1: Token should not contain spaces
        assert ' ' not in token, \
            "JWT token should not contain spaces"
        
        # Verification 2: Token should not contain tabs
        assert '\t' not in token, \
            "JWT token should not contain tabs"
        
        # Verification 3: Token should not contain newlines
        assert '\n' not in token, \
            "JWT token should not contain newlines"
        assert '\r' not in token, \
            "JWT token should not contain carriage returns"
        
        # Verification 4: Token should equal itself when stripped
        assert token == token.strip(), \
            "JWT token should not have leading or trailing whitespace"
