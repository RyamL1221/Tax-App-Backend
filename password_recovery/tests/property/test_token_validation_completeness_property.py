"""
Property-based test for token validation completeness.

This test verifies that for any submitted reset token, the validation process
should verify that: (1) the token hash exists in the database, (2) the token
has not expired, and (3) the token has not been previously used. All three
conditions must pass for the token to be considered valid.
"""

import os
import uuid
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
import boto3
from hypothesis import given, settings, strategies as st
from moto import mock_aws

# Import the classes to test
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from password_recovery.token_validator import TokenValidator
from password_recovery.user_repository import (
    store_reset_token,
    mark_token_used
)


# Strategy for generating valid email addresses
valid_emails = st.emails()

# Strategy for generating token states
# We'll test all combinations of: exists/not-exists, expired/not-expired, used/not-used
token_exists = st.booleans()
token_expired = st.booleans()
token_used = st.booleans()


class TestTokenValidationCompletenessProperty:
    """Property-based test for token validation completeness."""
    
    @mock_aws
    @settings(max_examples=20, deadline=None)
    @given(
        email=valid_emails,
        exists=token_exists,
        is_expired=token_expired,
        is_used=token_used
    )
    def test_token_validation_completeness(self, email, exists, is_expired, is_used):
        """
        **Validates: Requirements 3.3, 3.4, 3.5**
        Feature: password-recovery, Property 7: Token Validation Completeness
        
        For any submitted reset token, the validation process should verify that:
        (1) the token hash exists in the database,
        (2) the token has not expired, and
        (3) the token has not been previously used.
        All three conditions must pass for the token to be considered valid.
        """
        # Setup: Create a mock DynamoDB table with unique name per test
        table_name = f'test-reset-tokens-{uuid.uuid4().hex[:8]}'
        os.environ['RESET_TOKENS_TABLE_NAME'] = table_name
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'token_hash', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'token_hash', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Generate a token (as TokenGenerator would do)
        token_bytes = secrets.token_bytes(32)
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        token_hash = hashlib.sha256(token_bytes).hexdigest()
        
        # Setup token state based on test parameters
        if exists:
            # Determine expiration time based on is_expired parameter
            if is_expired:
                # Token expired 30 minutes ago
                expiration = datetime.now(timezone.utc) - timedelta(minutes=30)
            else:
                # Token expires 30 minutes from now
                expiration = datetime.now(timezone.utc) + timedelta(minutes=30)
            
            # Store the token in the database
            store_result = store_reset_token(email, token_hash, expiration)
            assert store_result is True, "Token storage should succeed"
            
            # Mark token as used if is_used is True
            if is_used:
                mark_result = mark_token_used(token_hash)
                assert mark_result is True, "Token should be marked as used successfully"
        
        # Create validator and validate the token
        validator = TokenValidator()
        is_valid, returned_email, error_message = validator.validate_token(plaintext_token)
        
        # Property: Token should ONLY be valid if ALL three conditions are met:
        # 1. Token exists in database (exists == True)
        # 2. Token has not expired (is_expired == False)
        # 3. Token has not been used (is_used == False)
        expected_valid = exists and not is_expired and not is_used
        
        # Assert the validation result matches expected outcome
        assert is_valid == expected_valid, \
            f"Token validation result mismatch. " \
            f"Expected valid={expected_valid}, got valid={is_valid}. " \
            f"Token state: exists={exists}, expired={is_expired}, used={is_used}. " \
            f"Error: {error_message}"
        
        # Additional assertions based on validation result
        if expected_valid:
            # If token is valid, email should be returned and no error
            assert returned_email == email, \
                f"Valid token should return the correct email. " \
                f"Expected {email}, got {returned_email}"
            assert error_message is None, \
                f"Valid token should not have an error message. Got: {error_message}"
        else:
            # If token is invalid, email should be None and error should be present
            assert returned_email is None, \
                f"Invalid token should not return an email. Got: {returned_email}"
            assert error_message is not None, \
                f"Invalid token should have an error message. " \
                f"Token state: exists={exists}, expired={is_expired}, used={is_used}"
            
            # Verify the error message is appropriate for the failure reason
            if not exists:
                # Check 1 failed: Token doesn't exist
                assert 'Invalid' in error_message or 'expired' in error_message, \
                    f"Non-existent token should have appropriate error. Got: {error_message}"
            elif is_used:
                # Check 3 failed: Token was already used
                assert 'used' in error_message.lower(), \
                    f"Used token should mention 'used' in error. Got: {error_message}"
            elif is_expired:
                # Check 2 failed: Token has expired
                assert 'expired' in error_message.lower(), \
                    f"Expired token should mention 'expired' in error. Got: {error_message}"
        
        # Property: Validation must check ALL three conditions
        # We verify this by testing each failure mode independently
        
        # Test that validation fails when token doesn't exist (Check 1)
        if not exists:
            assert is_valid is False, \
                "Validation should fail when token doesn't exist in database (Check 1)"
        
        # Test that validation fails when token is expired (Check 2)
        if exists and is_expired:
            assert is_valid is False, \
                "Validation should fail when token has expired (Check 2)"
        
        # Test that validation fails when token is used (Check 3)
        if exists and is_used:
            assert is_valid is False, \
                "Validation should fail when token has been used (Check 3)"
        
        # Property: All three checks must pass for token to be valid
        if is_valid:
            # If validation passed, all three conditions must be true
            assert exists is True, \
                "Valid token must exist in database"
            assert is_expired is False, \
                "Valid token must not be expired"
            assert is_used is False, \
                "Valid token must not be used"
        
        # Property: Validation is deterministic
        # Running validation again should give the same result
        is_valid2, returned_email2, error_message2 = validator.validate_token(plaintext_token)
        assert is_valid2 == is_valid, \
            "Token validation should be deterministic (same result on repeated calls)"
        assert returned_email2 == returned_email, \
            "Token validation should return same email on repeated calls"
        
        # Property: Return value structure is always consistent
        assert isinstance(is_valid, bool), \
            "First return value should always be a boolean"
        assert returned_email is None or isinstance(returned_email, str), \
            "Second return value should be None or a string"
        assert error_message is None or isinstance(error_message, str), \
            "Third return value should be None or a string"
        
        # Property: Exactly one of (email, error_message) should be set
        if is_valid:
            assert returned_email is not None, \
                "Valid token should return an email"
            assert error_message is None, \
                "Valid token should not return an error message"
        else:
            assert returned_email is None, \
                "Invalid token should not return an email"
            assert error_message is not None, \
                "Invalid token should return an error message"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '-s'])
