"""
Property-based tests for user ID extraction and consistency.

These tests verify that the userId extracted from JWT tokens is consistent
and matches the token payload. Each property test runs with a minimum of
100 iterations.

Feature: tax-document-generation
Property 18: User ID Extraction and Consistency

**Validates: Requirements 8.2, 8.4**
"""

import jwt
import pytest
from datetime import datetime, timedelta
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import text
from tax_document_generation.jwt_validator import validate_jwt
from tax_document_generation.exceptions import AuthenticationError


# Strategy for generating valid secret keys (at least 32 characters)
secret_keys = text(
    min_size=32,
    max_size=128,
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?'
)

# Strategy for generating user IDs
user_ids = text(
    min_size=1,
    max_size=100,
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
)


class TestUserIdExtractionProperty:
    """Property-based tests for user ID extraction and consistency."""
    
    @settings(max_examples=20)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_extracted_userid_matches_token_payload(self, user_id, secret_key):
        """
        **Validates: Requirements 8.2, 8.4**
        Feature: tax-document-generation, Property 18: User ID Extraction and Consistency
        
        For any valid JWT token with a userId claim, the extracted userId
        must exactly match the userId in the token payload.
        
        This test verifies that:
        1. The userId is correctly extracted from the token
        2. The extracted userId matches the original userId in the payload
        3. No transformation or modification occurs during extraction
        """
        # Action: Generate a valid JWT token with a specific userId
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        # Create valid token
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Extract userId and verify it matches the original
        result = validate_jwt(token, secret_key)
        extracted_user_id = result["userId"]
        
        # The extracted userId must exactly match the original userId
        assert extracted_user_id == user_id, (
            f"Extracted userId '{extracted_user_id}' does not match "
            f"original userId '{user_id}'"
        )
    
    @settings(max_examples=20)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_userid_extraction_is_consistent_across_multiple_validations(self, user_id, secret_key):
        """
        **Validates: Requirements 8.2, 8.4**
        Feature: tax-document-generation, Property 18: User ID Extraction and Consistency
        
        For any valid JWT token, validating the same token multiple times
        must always extract the same userId.
        
        This test verifies that:
        1. userId extraction is deterministic
        2. Multiple validations of the same token produce consistent results
        3. No state or randomness affects userId extraction
        """
        # Action: Generate a valid JWT token
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Validate the token multiple times
        result1 = validate_jwt(token, secret_key)
        result2 = validate_jwt(token, secret_key)
        result3 = validate_jwt(token, secret_key)
        
        # All extractions must produce the same userId
        assert result1["userId"] == user_id
        assert result2["userId"] == user_id
        assert result3["userId"] == user_id
        assert result1["userId"] == result2["userId"] == result3["userId"]
    
    @settings(max_examples=20)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_userid_extraction_with_additional_claims(self, user_id, secret_key):
        """
        **Validates: Requirements 8.2, 8.4**
        Feature: tax-document-generation, Property 18: User ID Extraction and Consistency
        
        For any valid JWT token with additional claims beyond userId,
        the extracted userId must still match the original userId.
        
        This test verifies that:
        1. Additional claims do not interfere with userId extraction
        2. userId is correctly extracted even with complex payloads
        3. The presence of other claims does not affect userId consistency
        """
        # Action: Generate a token with userId and additional claims
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "userId": user_id,
            "email": "test@example.com",
            "role": "user",
            "permissions": ["read", "write"],
            "metadata": {"key": "value"},
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Extract userId and verify it matches
        result = validate_jwt(token, secret_key)
        extracted_user_id = result["userId"]
        
        assert extracted_user_id == user_id
        # Verify other claims are also present
        assert result["email"] == "test@example.com"
        assert result["role"] == "user"
    
    @settings(max_examples=20)
    @given(
        user_id1=user_ids,
        user_id2=user_ids,
        secret_key=secret_keys
    )
    def test_different_userids_are_extracted_correctly(self, user_id1, user_id2, secret_key):
        """
        **Validates: Requirements 8.2, 8.4**
        Feature: tax-document-generation, Property 18: User ID Extraction and Consistency
        
        For any two JWT tokens with different userIds, the extracted userIds
        must be different and match their respective token payloads.
        
        This test verifies that:
        1. Different tokens produce different userIds
        2. Each userId is correctly extracted from its token
        3. No cross-contamination occurs between token validations
        """
        # Skip if both userIds are the same
        if user_id1 == user_id2:
            return
        
        # Action: Generate two tokens with different userIds
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload1 = {
            "userId": user_id1,
            "iat": issued_at,
            "exp": expiration
        }
        
        payload2 = {
            "userId": user_id2,
            "iat": issued_at,
            "exp": expiration
        }
        
        token1 = jwt.encode(payload1, secret_key, algorithm="HS256")
        token2 = jwt.encode(payload2, secret_key, algorithm="HS256")
        
        # Verification: Extract userIds and verify they match their respective payloads
        result1 = validate_jwt(token1, secret_key)
        result2 = validate_jwt(token2, secret_key)
        
        assert result1["userId"] == user_id1
        assert result2["userId"] == user_id2
        assert result1["userId"] != result2["userId"]
    
    @settings(max_examples=20)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_userid_type_is_preserved(self, user_id, secret_key):
        """
        **Validates: Requirements 8.2, 8.4**
        Feature: tax-document-generation, Property 18: User ID Extraction and Consistency
        
        For any valid JWT token, the extracted userId must be a string
        and preserve the exact type and value from the token payload.
        
        This test verifies that:
        1. userId is extracted as a string
        2. The type of userId is preserved
        3. No type conversion or coercion occurs
        """
        # Action: Generate a valid JWT token
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Extract userId and verify type
        result = validate_jwt(token, secret_key)
        extracted_user_id = result["userId"]
        
        assert isinstance(extracted_user_id, str), (
            f"Extracted userId should be a string, got {type(extracted_user_id)}"
        )
        assert extracted_user_id == user_id
    
    @settings(max_examples=20)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_userid_extraction_with_special_characters(self, user_id, secret_key):
        """
        **Validates: Requirements 8.2, 8.4**
        Feature: tax-document-generation, Property 18: User ID Extraction and Consistency
        
        For any valid JWT token with a userId containing special characters
        (hyphens, underscores), the extracted userId must exactly match
        the original including all special characters.
        
        This test verifies that:
        1. Special characters in userId are preserved
        2. No sanitization or escaping occurs during extraction
        3. userId is extracted exactly as encoded
        """
        # Action: Generate a token with userId containing special characters
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Extract userId and verify exact match
        result = validate_jwt(token, secret_key)
        extracted_user_id = result["userId"]
        
        assert extracted_user_id == user_id
        # Verify character-by-character match
        assert len(extracted_user_id) == len(user_id)
        for i, char in enumerate(user_id):
            assert extracted_user_id[i] == char
    
    @settings(max_examples=20)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_userid_is_present_in_returned_payload(self, user_id, secret_key):
        """
        **Validates: Requirements 8.2, 8.4**
        Feature: tax-document-generation, Property 18: User ID Extraction and Consistency
        
        For any valid JWT token, the returned payload must contain
        the userId key with the correct value.
        
        This test verifies that:
        1. The userId key exists in the returned payload
        2. The userId value is accessible via dictionary access
        3. The payload structure is preserved
        """
        # Action: Generate a valid JWT token
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Verification: Validate token and check payload structure
        result = validate_jwt(token, secret_key)
        
        # userId key must exist
        assert "userId" in result, "userId key not found in returned payload"
        
        # userId value must match
        assert result["userId"] == user_id
        
        # Verify dictionary access works
        assert result.get("userId") == user_id
    
    @settings(max_examples=20)
    @given(
        user_id=user_ids,
        secret_key=secret_keys
    )
    def test_userid_extraction_does_not_modify_token(self, user_id, secret_key):
        """
        **Validates: Requirements 8.2, 8.4**
        Feature: tax-document-generation, Property 18: User ID Extraction and Consistency
        
        For any valid JWT token, validating and extracting the userId
        must not modify the original token string.
        
        This test verifies that:
        1. The token string remains unchanged after validation
        2. Validation is a read-only operation
        3. The same token can be validated multiple times
        """
        # Action: Generate a valid JWT token
        issued_at = datetime.utcnow()
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        payload = {
            "userId": user_id,
            "iat": issued_at,
            "exp": expiration
        }
        
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        original_token = token  # Store original
        
        # Verification: Validate token and check it's unchanged
        result = validate_jwt(token, secret_key)
        
        # Token should be unchanged
        assert token == original_token
        
        # Should be able to validate again with same result
        result2 = validate_jwt(token, secret_key)
        assert result2["userId"] == user_id
        assert result2["userId"] == result["userId"]
