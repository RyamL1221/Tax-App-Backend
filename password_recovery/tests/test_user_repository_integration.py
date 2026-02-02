"""
Integration tests for password recovery user repository methods.

Tests the reset token storage, retrieval, and atomic invalidation methods
with a real DynamoDB instance (LocalStack).
"""

import os
import pytest
from datetime import datetime, timedelta, timezone
import hashlib

# Import the functions to test
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from password_recovery.user_repository import (
    store_reset_token,
    get_reset_token,
    mark_token_used,
    DatabaseError
)


@pytest.fixture(scope="module")
def setup_environment():
    """Set up environment variables for LocalStack."""
    os.environ['RESET_TOKENS_TABLE_NAME'] = 'ResetTokens'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    yield
    # Cleanup is handled by LocalStack restart


class TestResetTokenIntegration:
    """Integration tests for reset token operations."""
    
    def test_store_and_retrieve_token(self, setup_environment):
        """Test storing and retrieving a reset token."""
        # Setup
        email = "integration-test@example.com"
        token = "integration-test-token-" + str(datetime.now().timestamp())
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Store token
        result = store_reset_token(email, token_hash, expiration)
        assert result is True
        
        # Retrieve token
        retrieved = get_reset_token(token_hash)
        assert retrieved is not None
        assert retrieved['email'] == email
        assert retrieved['expiration'] == expiration.isoformat()
        assert retrieved['used_at'] is None
        assert 'created_at' in retrieved
    
    def test_retrieve_nonexistent_token(self, setup_environment):
        """Test retrieving a token that doesn't exist."""
        token_hash = "nonexistent-token-hash"
        
        result = get_reset_token(token_hash)
        assert result is None
    
    def test_mark_token_used_success(self, setup_environment):
        """Test marking a token as used."""
        # Setup - create a token first
        email = "mark-used-test@example.com"
        token = "mark-used-token-" + str(datetime.now().timestamp())
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        store_reset_token(email, token_hash, expiration)
        
        # Mark as used
        result = mark_token_used(token_hash)
        assert result is True
        
        # Verify it's marked as used
        retrieved = get_reset_token(token_hash)
        assert retrieved is not None
        assert retrieved['used_at'] is not None
    
    def test_mark_token_used_twice(self, setup_environment):
        """Test marking a token as used twice (race condition)."""
        # Setup - create a token first
        email = "mark-twice-test@example.com"
        token = "mark-twice-token-" + str(datetime.now().timestamp())
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        store_reset_token(email, token_hash, expiration)
        
        # Mark as used first time
        result1 = mark_token_used(token_hash)
        assert result1 is True
        
        # Mark as used second time (should fail)
        result2 = mark_token_used(token_hash)
        assert result2 is False
    
    def test_store_token_overwrites_existing(self, setup_environment):
        """Test that storing a token with the same hash overwrites the existing one."""
        # Setup
        email1 = "overwrite-test1@example.com"
        email2 = "overwrite-test2@example.com"
        token = "overwrite-token-" + str(datetime.now().timestamp())
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expiration1 = datetime.now(timezone.utc) + timedelta(hours=1)
        expiration2 = datetime.now(timezone.utc) + timedelta(hours=2)
        
        # Store first token
        store_reset_token(email1, token_hash, expiration1)
        
        # Store second token with same hash
        store_reset_token(email2, token_hash, expiration2)
        
        # Retrieve and verify it's the second one
        retrieved = get_reset_token(token_hash)
        assert retrieved is not None
        assert retrieved['email'] == email2
        assert retrieved['expiration'] == expiration2.isoformat()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



class TestSessionVersionIntegration:
    """Integration tests for session version operations."""
    
    def test_increment_and_get_session_version(self, setup_environment):
        """Test incrementing and retrieving session version."""
        # Import the functions
        from password_recovery.user_repository import (
            increment_session_version,
            get_session_version
        )
        
        # Setup - we need a user in the Users table
        # For this test, we'll use the user_registration module to create a user
        import boto3
        
        email = f"session-test-{datetime.now().timestamp()}@example.com"
        
        # Create a test user in the Users table
        dynamodb = boto3.client(
            'dynamodb',
            region_name='us-east-1',
            endpoint_url='http://localhost:4566'
        )
        
        # Set USER_TABLE_NAME environment variable
        os.environ['USER_TABLE_NAME'] = 'Users'
        
        # Create user
        dynamodb.put_item(
            TableName='Users',
            Item={
                'email': {'S': email},
                'name': {'S': 'Test User'},
                'password_hash': {'S': 'dummy_hash'},
                'created_at': {'S': datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Test initial session version (should be 0)
        initial_version = get_session_version(email)
        assert initial_version == 0
        
        # Increment session version
        new_version = increment_session_version(email)
        assert new_version == 1
        
        # Get session version again
        current_version = get_session_version(email)
        assert current_version == 1
        
        # Increment again
        new_version = increment_session_version(email)
        assert new_version == 2
        
        # Get session version again
        current_version = get_session_version(email)
        assert current_version == 2
    
    def test_get_session_version_nonexistent_user(self, setup_environment):
        """Test getting session version for a user that doesn't exist."""
        from password_recovery.user_repository import get_session_version
        
        os.environ['USER_TABLE_NAME'] = 'Users'
        
        email = "nonexistent-user@example.com"
        
        # Should return 0 for non-existent user
        version = get_session_version(email)
        assert version == 0
    
    def test_increment_session_version_atomic(self, setup_environment):
        """Test that session version increment is atomic."""
        from password_recovery.user_repository import (
            increment_session_version,
            get_session_version
        )
        
        import boto3
        
        email = f"atomic-test-{datetime.now().timestamp()}@example.com"
        
        # Create a test user
        dynamodb = boto3.client(
            'dynamodb',
            region_name='us-east-1',
            endpoint_url='http://localhost:4566'
        )
        
        os.environ['USER_TABLE_NAME'] = 'Users'
        
        dynamodb.put_item(
            TableName='Users',
            Item={
                'email': {'S': email},
                'name': {'S': 'Test User'},
                'password_hash': {'S': 'dummy_hash'},
                'created_at': {'S': datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Increment multiple times rapidly
        versions = []
        for _ in range(5):
            version = increment_session_version(email)
            versions.append(version)
        
        # Verify versions are sequential
        assert versions == [1, 2, 3, 4, 5]
        
        # Verify final version
        final_version = get_session_version(email)
        assert final_version == 5
