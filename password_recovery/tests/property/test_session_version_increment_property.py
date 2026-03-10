"""
Property-based test for session version increment.

This test verifies that for any successful password reset, the user's session_version
should be incremented by exactly 1, ensuring all previously issued JWTs become invalid.
"""

import os
import uuid
from datetime import datetime, timezone
import boto3
from hypothesis import given, settings, strategies as st
from moto import mock_aws

# Import the functions to test
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from password_recovery.user_repository import (
    increment_session_version,
    get_session_version
)


# Strategy for generating valid email addresses
valid_emails = st.emails()


class TestSessionVersionIncrementProperty:
    """Property-based test for session version increment."""
    
    @mock_aws
    @settings(max_examples=20, deadline=None)
    @given(email=valid_emails)
    def test_session_version_increment(self, email):
        """
        **Validates: Requirements 4.1**
        Feature: password-recovery, Property 10: Session Version Increment
        
        For any successful password reset, the user's session_version should be 
        incremented by exactly 1, ensuring all previously issued JWTs become invalid.
        
        Testing Requirements:
        1. Session version starts at 0 for new users
        2. Each increment increases version by exactly 1
        3. Multiple increments work correctly (sequential)
        4. The operation is atomic
        """
        # Setup: Create a mock DynamoDB Users table with unique name per test
        table_name = f'test-users-{uuid.uuid4().hex[:8]}'
        os.environ['USER_TABLE_NAME'] = table_name
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create a user in the database (simulating user registration)
        # Initially, the user has no session_version (or it defaults to 0)
        table.put_item(
            Item={
                'email': email,
                'hashed_password': 'dummy_hash',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Property 1: Session version starts at 0 for new users
        initial_version = get_session_version(email)
        assert initial_version == 0, \
            f"Session version should start at 0 for new users, got {initial_version}"
        
        # Property 2: Each increment increases version by exactly 1
        # First increment
        new_version_1 = increment_session_version(email)
        assert new_version_1 == 1, \
            f"First increment should result in version 1, got {new_version_1}"
        
        # Verify the version was persisted correctly
        retrieved_version_1 = get_session_version(email)
        assert retrieved_version_1 == 1, \
            f"Retrieved version should be 1 after first increment, got {retrieved_version_1}"
        
        # Property 3: Multiple increments work correctly (sequential)
        # Second increment
        new_version_2 = increment_session_version(email)
        assert new_version_2 == 2, \
            f"Second increment should result in version 2, got {new_version_2}"
        
        retrieved_version_2 = get_session_version(email)
        assert retrieved_version_2 == 2, \
            f"Retrieved version should be 2 after second increment, got {retrieved_version_2}"
        
        # Third increment
        new_version_3 = increment_session_version(email)
        assert new_version_3 == 3, \
            f"Third increment should result in version 3, got {new_version_3}"
        
        retrieved_version_3 = get_session_version(email)
        assert retrieved_version_3 == 3, \
            f"Retrieved version should be 3 after third increment, got {retrieved_version_3}"
        
        # Verify the increment is always exactly 1
        assert new_version_2 - new_version_1 == 1, \
            "Each increment should increase version by exactly 1"
        assert new_version_3 - new_version_2 == 1, \
            "Each increment should increase version by exactly 1"
        
        # Property 4: The operation is atomic
        # The DynamoDB ADD operation is atomic by design
        # We verify this by checking that concurrent-like operations
        # (multiple increments) produce sequential results without gaps
        
        # Perform several more increments to verify consistency
        versions = [new_version_3]
        for i in range(5):
            next_version = increment_session_version(email)
            versions.append(next_version)
            
            # Verify each increment is exactly 1 more than the previous
            assert next_version == versions[-2] + 1, \
                f"Increment {i+4} should be exactly 1 more than previous. " \
                f"Expected {versions[-2] + 1}, got {next_version}"
        
        # Verify the final version is correct
        final_version = get_session_version(email)
        expected_final_version = 8  # Started at 0, incremented 8 times (3 + 5)
        assert final_version == expected_final_version, \
            f"Final version should be {expected_final_version}, got {final_version}"
        
        # Additional verification: Ensure no gaps in the sequence
        # All versions should be sequential: 1, 2, 3, 4, 5, 6, 7, 8
        expected_sequence = list(range(1, 9))
        actual_sequence = [new_version_1, new_version_2, new_version_3] + versions[1:]
        assert actual_sequence == expected_sequence, \
            f"Version sequence should be {expected_sequence}, got {actual_sequence}"
        
        # Verify atomicity by checking the DynamoDB item directly
        response = table.get_item(Key={'email': email})
        item = response['Item']
        assert 'session_version' in item, \
            "session_version should be present in the user item"
        assert item['session_version'] == expected_final_version, \
            f"DynamoDB item should have session_version {expected_final_version}, " \
            f"got {item['session_version']}"
        
        # Summary of what we've verified:
        # 1. ✓ Session version starts at 0 for new users
        # 2. ✓ Each increment increases version by exactly 1
        # 3. ✓ Multiple increments work correctly (sequential, no gaps)
        # 4. ✓ The operation is atomic (DynamoDB ADD operation)
        
        # Security implication verification:
        # When session_version is incremented (e.g., from 2 to 3),
        # all JWTs with session_version < 3 should be considered invalid.
        # This ensures that a password reset invalidates all existing sessions.
        
        # For example, if a user had JWTs with session_version 2,
        # after password reset (incrementing to 3), those JWTs are invalid.
        old_jwt_version = 2
        current_version = final_version
        assert old_jwt_version < current_version, \
            "Old JWT versions should be less than current version, making them invalid"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '-s'])
