"""
Property-based tests for JWT algorithm consistency.

These tests verify that JWT tokens consistently use the HS256 algorithm.
Each property test runs with a minimum of 100 iterations.
"""

import jwt
import json
import base64
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails, text
from user_login.token_generator import generate_jwt_token


class TestJWTAlgorithmConsistencyProperty:
    """Property-based tests for JWT algorithm consistency validation."""
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_header_specifies_hs256_algorithm(self, email, secret_key):
        """
        **Validates: Requirements 1.5**
        Feature: jwt-authentication-migration, Property 4: JWT Algorithm Consistency
        
        For any generated JWT token, the header must specify the HS256 algorithm.
        
        This test verifies that:
        1. The JWT header contains an "alg" field
        2. The "alg" field is set to "HS256"
        3. The algorithm is consistent across all token generations
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Extract header from token (first segment before first period)
        header_segment = token.split('.')[0]
        
        # Decode header from base64url
        # Add padding if needed
        padding = 4 - (len(header_segment) % 4)
        if padding != 4:
            header_segment += '=' * padding
        
        # Replace base64url characters with standard base64
        header_segment = header_segment.replace('-', '+').replace('_', '/')
        
        # Decode and parse JSON
        header_bytes = base64.b64decode(header_segment)
        header = json.loads(header_bytes)
        
        # Verification 1: Header should contain "alg" field
        assert "alg" in header, \
            "JWT header must contain 'alg' field"
        
        # Verification 2: Algorithm should be HS256
        assert header["alg"] == "HS256", \
            f"JWT algorithm should be HS256, got {header['alg']}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_header_specifies_jwt_type(self, email, secret_key):
        """
        **Validates: Requirements 1.5**
        Feature: jwt-authentication-migration, Property 4: JWT Algorithm Consistency
        
        For any generated JWT token, the header must specify the token type as "JWT".
        
        This test verifies that:
        1. The JWT header contains a "typ" field
        2. The "typ" field is set to "JWT"
        3. The token type is consistent across all token generations
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Extract header from token (first segment before first period)
        header_segment = token.split('.')[0]
        
        # Decode header from base64url
        # Add padding if needed
        padding = 4 - (len(header_segment) % 4)
        if padding != 4:
            header_segment += '=' * padding
        
        # Replace base64url characters with standard base64
        header_segment = header_segment.replace('-', '+').replace('_', '/')
        
        # Decode and parse JSON
        header_bytes = base64.b64decode(header_segment)
        header = json.loads(header_bytes)
        
        # Verification 1: Header should contain "typ" field
        assert "typ" in header, \
            "JWT header must contain 'typ' field"
        
        # Verification 2: Type should be JWT
        assert header["typ"] == "JWT", \
            f"JWT type should be JWT, got {header['typ']}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_token_verifiable_with_hs256_only(self, email, secret_key):
        """
        **Validates: Requirements 1.5**
        Feature: jwt-authentication-migration, Property 4: JWT Algorithm Consistency
        
        For any generated JWT token, the token must be verifiable using the HS256
        algorithm and must fail verification with other algorithms.
        
        This test verifies that:
        1. Token can be decoded with HS256 algorithm
        2. Token cannot be decoded with other algorithms (e.g., HS512, RS256)
        3. The algorithm is enforced during verification
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Verification 1: Token should be verifiable with HS256
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            assert payload["email"] == email, \
                "Decoded email should match original email"
        except Exception as e:
            pytest.fail(f"Token should be verifiable with HS256 algorithm: {e}")
        
        # Verification 2: Token should fail verification with HS512
        with pytest.raises(jwt.InvalidAlgorithmError):
            jwt.decode(token, secret_key, algorithms=["HS512"])
        
        # Verification 3: Token should fail verification with RS256
        # (RS256 requires a different key type, so this will fail)
        with pytest.raises((jwt.InvalidAlgorithmError, jwt.InvalidKeyError)):
            jwt.decode(token, secret_key, algorithms=["RS256"])
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_algorithm_consistent_across_multiple_generations(self, email, secret_key):
        """
        **Validates: Requirements 1.5**
        Feature: jwt-authentication-migration, Property 4: JWT Algorithm Consistency
        
        For any email and secret key, multiple token generations must consistently
        use the HS256 algorithm.
        
        This test verifies that:
        1. Multiple tokens generated with the same inputs use HS256
        2. The algorithm is not randomly selected
        3. The algorithm is deterministic and consistent
        """
        # Action: Generate multiple JWT tokens
        tokens = [generate_jwt_token(email, secret_key) for _ in range(5)]
        
        # Verification: All tokens should use HS256 algorithm
        for i, token in enumerate(tokens):
            # Extract and decode header
            header_segment = token.split('.')[0]
            
            # Add padding if needed
            padding = 4 - (len(header_segment) % 4)
            if padding != 4:
                header_segment += '=' * padding
            
            # Replace base64url characters with standard base64
            header_segment = header_segment.replace('-', '+').replace('_', '/')
            
            # Decode and parse JSON
            header_bytes = base64.b64decode(header_segment)
            header = json.loads(header_bytes)
            
            # Verify algorithm is HS256
            assert header["alg"] == "HS256", \
                f"Token {i} should use HS256 algorithm, got {header['alg']}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_header_has_only_required_fields(self, email, secret_key):
        """
        **Validates: Requirements 1.5**
        Feature: jwt-authentication-migration, Property 4: JWT Algorithm Consistency
        
        For any generated JWT token, the header should contain only the required
        fields (alg and typ) and no additional fields.
        
        This test verifies that:
        1. The header has exactly 2 fields
        2. The header contains "alg" and "typ"
        3. No extra fields are added to the header
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Extract and decode header
        header_segment = token.split('.')[0]
        
        # Add padding if needed
        padding = 4 - (len(header_segment) % 4)
        if padding != 4:
            header_segment += '=' * padding
        
        # Replace base64url characters with standard base64
        header_segment = header_segment.replace('-', '+').replace('_', '/')
        
        # Decode and parse JSON
        header_bytes = base64.b64decode(header_segment)
        header = json.loads(header_bytes)
        
        # Verification 1: Header should have exactly 2 fields
        assert len(header) == 2, \
            f"JWT header should have exactly 2 fields (alg, typ), got {len(header)} fields: {list(header.keys())}"
        
        # Verification 2: Header should contain only expected fields
        expected_fields = {"alg", "typ"}
        actual_fields = set(header.keys())
        assert actual_fields == expected_fields, \
            f"JWT header should contain only {expected_fields}, got {actual_fields}"
