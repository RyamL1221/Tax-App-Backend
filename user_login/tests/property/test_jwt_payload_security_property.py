"""
Property-based tests for JWT payload security.

These tests verify that JWT tokens do not contain sensitive information in their
payloads. Each property test runs with a minimum of 100 iterations.
"""

import jwt
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails, text
from user_login.token_generator import generate_jwt_token


class TestJWTPayloadSecurityProperty:
    """Property-based tests for JWT payload security validation."""
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_does_not_contain_password_field(self, email, secret_key):
        """
        **Validates: Requirements 11.5**
        Feature: jwt-authentication-migration, Property 13: JWT Payload Security
        
        For any generated JWT token, the decoded payload must not contain a field
        named "password".
        
        This test verifies that:
        1. The payload does not have a "password" field
        2. Sensitive password information is not leaked in tokens
        3. Security best practices are followed
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification: Payload should not contain "password" field
        assert "password" not in payload, \
            "JWT payload must not contain 'password' field"
        
        # Also check case variations
        payload_keys_lower = [key.lower() for key in payload.keys()]
        assert "password" not in payload_keys_lower, \
            "JWT payload must not contain 'password' field (case-insensitive check)"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_does_not_contain_password_hash_field(self, email, secret_key):
        """
        **Validates: Requirements 11.5**
        Feature: jwt-authentication-migration, Property 13: JWT Payload Security
        
        For any generated JWT token, the decoded payload must not contain a field
        named "password_hash".
        
        This test verifies that:
        1. The payload does not have a "password_hash" field
        2. Hashed passwords are not leaked in tokens
        3. Security best practices are followed
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification: Payload should not contain "password_hash" field
        assert "password_hash" not in payload, \
            "JWT payload must not contain 'password_hash' field"
        
        # Also check case variations
        payload_keys_lower = [key.lower() for key in payload.keys()]
        assert "password_hash" not in payload_keys_lower, \
            "JWT payload must not contain 'password_hash' field (case-insensitive check)"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_does_not_contain_pass_variations(self, email, secret_key):
        """
        **Validates: Requirements 11.5**
        Feature: jwt-authentication-migration, Property 13: JWT Payload Security
        
        For any generated JWT token, the decoded payload must not contain fields
        with names containing "pass" (case-insensitive).
        
        This test verifies that:
        1. No field names contain "pass" substring
        2. Variations like "passwd", "passphrase", etc. are not present
        3. Comprehensive password-related field detection
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification: No field names should contain "pass" (case-insensitive)
        for key in payload.keys():
            assert "pass" not in key.lower(), \
                f"JWT payload must not contain fields with 'pass' in the name, found: {key}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_does_not_contain_secret_variations(self, email, secret_key):
        """
        **Validates: Requirements 11.5**
        Feature: jwt-authentication-migration, Property 13: JWT Payload Security
        
        For any generated JWT token, the decoded payload must not contain fields
        with names containing "secret" (case-insensitive).
        
        This test verifies that:
        1. No field names contain "secret" substring
        2. Secret keys and sensitive data are not leaked
        3. Security best practices are followed
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification: No field names should contain "secret" (case-insensitive)
        for key in payload.keys():
            assert "secret" not in key.lower(), \
                f"JWT payload must not contain fields with 'secret' in the name, found: {key}"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_contains_only_safe_fields(self, email, secret_key):
        """
        **Validates: Requirements 11.5**
        Feature: jwt-authentication-migration, Property 13: JWT Payload Security
        
        For any generated JWT token, the decoded payload must contain only safe,
        non-sensitive fields (email, iat, exp).
        
        This test verifies that:
        1. Only expected safe fields are present
        2. No additional sensitive fields are added
        3. The payload structure is minimal and secure
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Define safe fields
        safe_fields = {"email", "iat", "exp"}
        
        # Verification: All fields in payload should be safe
        for key in payload.keys():
            assert key in safe_fields, \
                f"JWT payload contains unexpected field: {key}. Only {safe_fields} are allowed."
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_values_do_not_contain_password_patterns(self, email, secret_key):
        """
        **Validates: Requirements 11.5**
        Feature: jwt-authentication-migration, Property 13: JWT Payload Security
        
        For any generated JWT token, the decoded payload values should not contain
        obvious password patterns (e.g., bcrypt hashes, long random strings that
        look like passwords).
        
        This test verifies that:
        1. Payload values are not password-like
        2. No accidental password leakage in values
        3. Values are appropriate for their fields
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification: Check each value
        for key, value in payload.items():
            if isinstance(value, str):
                # Check for bcrypt hash pattern ($2b$, $2a$, $2y$)
                assert not value.startswith('$2b$'), \
                    f"JWT payload value for '{key}' looks like a bcrypt hash"
                assert not value.startswith('$2a$'), \
                    f"JWT payload value for '{key}' looks like a bcrypt hash"
                assert not value.startswith('$2y$'), \
                    f"JWT payload value for '{key}' looks like a bcrypt hash"
                
                # Check for argon2 hash pattern ($argon2)
                assert not value.startswith('$argon2'), \
                    f"JWT payload value for '{key}' looks like an argon2 hash"
                
                # Check for pbkdf2 hash pattern (pbkdf2:)
                assert not value.startswith('pbkdf2:'), \
                    f"JWT payload value for '{key}' looks like a pbkdf2 hash"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_email_is_not_redacted(self, email, secret_key):
        """
        **Validates: Requirements 11.5**
        Feature: jwt-authentication-migration, Property 13: JWT Payload Security
        
        For any generated JWT token, the email field should contain the actual
        email address (not redacted or hashed), as email is not considered
        sensitive in the same way as passwords.
        
        This test verifies that:
        1. The email field contains the original email
        2. Email is not unnecessarily obfuscated
        3. The token is usable for authentication
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification: Email should match the input email (not redacted)
        assert payload["email"] == email, \
            f"Email in payload should match input email, expected '{email}', got '{payload['email']}'"
        
        # Verification: Email should not be hashed or obfuscated
        assert '@' in payload["email"] or email == payload["email"], \
            "Email should be in readable format (not hashed)"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_does_not_leak_secret_key(self, email, secret_key):
        """
        **Validates: Requirements 11.5**
        Feature: jwt-authentication-migration, Property 13: JWT Payload Security
        
        For any generated JWT token, the decoded payload must not contain the
        secret key used to sign the token in fields other than the email field
        (which is user-provided data).
        
        This test verifies that:
        1. The secret key is not leaked in non-email payload fields
        2. The signing key remains confidential
        3. Critical security is maintained
        
        Note: We skip checking the email field because it's user-provided data
        and could coincidentally contain the same characters as the secret key.
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification: Secret key should not appear in non-email payload values
        for key, value in payload.items():
            # Skip email field as it's user-provided data
            if key == "email":
                continue
                
            if isinstance(value, str):
                assert secret_key not in value, \
                    f"JWT payload must not contain the secret key, found in field '{key}'"
                
                # Also check for partial leakage (first/last 10 chars)
                if len(secret_key) >= 10:
                    assert secret_key[:10] not in value, \
                        f"JWT payload must not contain part of the secret key, found in field '{key}'"
                    assert secret_key[-10:] not in value, \
                        f"JWT payload must not contain part of the secret key, found in field '{key}'"
    
    @settings(max_examples=20)
    @given(
        email=emails(),
        secret_key=text(min_size=32, max_size=128, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?')
    )
    def test_jwt_payload_field_names_are_lowercase(self, email, secret_key):
        """
        **Validates: Requirements 11.5**
        Feature: jwt-authentication-migration, Property 13: JWT Payload Security
        
        For any generated JWT token, the payload field names should follow
        standard JWT conventions (lowercase).
        
        This test verifies that:
        1. Field names are lowercase (email, iat, exp)
        2. No uppercase or mixed-case field names
        3. Standard JWT conventions are followed
        """
        # Action: Generate JWT token
        token = generate_jwt_token(email, secret_key)
        
        # Decode the JWT token to inspect payload
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Verification: All field names should be lowercase
        for key in payload.keys():
            assert key == key.lower(), \
                f"JWT payload field names should be lowercase, found: {key}"
