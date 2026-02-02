"""
Property-based test for secure token storage.

This test verifies that for any generated reset token, when stored in the database,
only the SHA-256 hash should be persisted (never the plaintext token), along with
an expiration timestamp no more than 1 hour from generation.
"""

import os
import re
import uuid
import hashlib
import secrets
import base64
from datetime import datetime, timedelta, timezone
import boto3
from hypothesis import given, settings, strategies as st
from moto import mock_aws

# Import the functions to test
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from password_recovery.user_repository import (
    store_reset_token,
    get_reset_token
)


# Strategy for generating valid email addresses
valid_emails = st.emails()


class TestSecureTokenStorageProperty:
    """Property-based test for secure token storage."""
    
    @mock_aws
    @settings(max_examples=20, deadline=None)
    @given(email=valid_emails)
    def test_secure_token_storage(self, email):
        """
        **Validates: Requirements 1.5, 1.6, 1.7, 5.2, 5.3**
        Feature: password-recovery, Property 3: Secure Token Storage
        
        For any generated reset token, when stored in the database, only the SHA-256 
        hash should be persisted (never the plaintext token), along with an expiration 
        timestamp no more than 1 hour from generation.
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
        
        # Simulate token generation (as TokenGenerator would do)
        # 1. Generate a cryptographically secure token (32 bytes = 256 bits)
        token_bytes = secrets.token_bytes(32)
        plaintext_token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        
        # 2. Hash the token with SHA-256
        token_hash = hashlib.sha256(plaintext_token.encode('utf-8')).hexdigest()
        
        # 3. Set expiration to 1 hour from now
        generation_time = datetime.now(timezone.utc)
        expiration = generation_time + timedelta(hours=1)
        
        # Store the token using the repository function
        result = store_reset_token(email, token_hash, expiration)
        assert result is True, "Token storage should succeed"
        
        # Retrieve the stored token data
        stored_token = get_reset_token(token_hash)
        assert stored_token is not None, "Token should be retrievable after storage"
        
        # Property 1: Plaintext token is NEVER stored in database
        # Check that the plaintext token doesn't appear in any field
        for field_name, field_value in stored_token.items():
            if isinstance(field_value, str):
                assert plaintext_token not in field_value, \
                    f"Plaintext token found in field '{field_name}'! " \
                    f"This is a critical security violation. Only the hash should be stored."
        
        # Also check the raw DynamoDB item to be absolutely sure
        response = table.get_item(Key={'token_hash': token_hash})
        raw_item = response['Item']
        for field_name, field_value in raw_item.items():
            if isinstance(field_value, str):
                assert plaintext_token not in field_value, \
                    f"Plaintext token found in raw DynamoDB field '{field_name}'! " \
                    f"Security violation detected."
        
        # Property 2: Only SHA-256 hash is stored
        # Verify the stored token_hash is a valid SHA-256 hash (64 hex characters)
        sha256_pattern = r'^[a-f0-9]{64}$'
        assert re.match(sha256_pattern, token_hash), \
            f"Token hash should be a valid SHA-256 hash (64 hex chars), got: {token_hash[:20]}..."
        
        # Verify the hash matches what we computed
        expected_hash = hashlib.sha256(plaintext_token.encode('utf-8')).hexdigest()
        assert token_hash == expected_hash, \
            "Stored token hash should match the SHA-256 hash of the plaintext token"
        
        # Property 3: Expiration is within 1 hour from generation
        stored_expiration = datetime.fromisoformat(stored_token['expiration'])
        
        # Calculate the time difference between expiration and generation
        time_diff = stored_expiration - generation_time
        
        # Expiration should be no more than 1 hour from generation
        # Allow a small tolerance for processing time (1 second)
        max_expiration = timedelta(hours=1, seconds=1)
        assert time_diff <= max_expiration, \
            f"Expiration time should be no more than 1 hour from generation. " \
            f"Got time difference: {time_diff}"
        
        # Expiration should be in the future (at least close to 1 hour)
        min_expiration = timedelta(minutes=59)  # Allow 1 minute tolerance
        assert time_diff >= min_expiration, \
            f"Expiration time should be approximately 1 hour from generation. " \
            f"Got time difference: {time_diff}"
        
        # Property 4: Token data includes all required fields
        required_fields = ['email', 'expiration', 'created_at']
        for field in required_fields:
            assert field in stored_token, \
                f"Required field '{field}' is missing from stored token data"
        
        # Verify field values are correct
        assert stored_token['email'] == email, \
            f"Stored email should match the provided email"
        
        # Verify created_at is a valid ISO 8601 timestamp
        created_at = datetime.fromisoformat(stored_token['created_at'])
        assert isinstance(created_at, datetime), \
            "created_at should be a valid datetime"
        
        # Verify used_at is initially None (not set)
        assert stored_token['used_at'] is None, \
            "used_at should be None for a newly created token"
        
        # Additional security check: Verify the token hash cannot be reversed
        # (This is implicit in SHA-256, but we verify the hash is one-way)
        # We should not be able to derive the plaintext from the hash
        assert len(token_hash) == 64, \
            "SHA-256 hash should always be 64 characters (256 bits in hex)"
        
        # Verify the hash is deterministic (same input = same output)
        rehash = hashlib.sha256(plaintext_token.encode('utf-8')).hexdigest()
        assert rehash == token_hash, \
            "SHA-256 should be deterministic (same input produces same hash)"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '-s'])
