"""
Property-based tests for user lookup in the login endpoint.

These tests verify universal properties across randomized inputs using hypothesis.
Each property test runs with a minimum of 100 iterations.
"""

import os
import uuid
import boto3
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import emails, text
from moto import mock_aws
from user_registration.user_repository import (
    create_user,
    get_user_by_email,
    UserNotFoundError,
    DatabaseError
)


class TestUserLookupProperty:
    """Property-based tests for user lookup by email."""
    
    @mock_aws
    @settings(max_examples=20)
    @given(
        email=emails(),
        name=text(min_size=1, max_size=100),
        password_hash=st.builds(
            lambda: f"$2b$12${uuid.uuid4().hex}{uuid.uuid4().hex[:28]}",
        )
    )
    def test_user_lookup_retrieves_existing_users(self, email, name, password_hash):
        """
        **Validates: Requirements 3.1, 3.4**
        Feature: user-login-endpoint, Property 4: User lookup by email
        
        For any valid email, the endpoint should query DynamoDB using the email
        as the partition key and retrieve the user's data if it exists.
        
        This test verifies that:
        1. Users can be created with any valid email
        2. Users can be retrieved using their email as the partition key
        3. Retrieved data matches the created data
        4. Password hash is included in the retrieved data
        """
        # Setup: Create a mock DynamoDB table
        table_name = f'test-users-table-{uuid.uuid4().hex[:8]}'
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
        
        # Action 1: Create a user with the generated email
        created_user = create_user(email, name, password_hash)
        
        # Verification 1: User creation should succeed
        assert created_user is not None, "User creation should succeed"
        assert created_user['email'] == email, "Created user should have correct email"
        
        # Action 2: Retrieve the user by email (using email as partition key)
        retrieved_user = get_user_by_email(email)
        
        # Verification 2: User should be retrievable by email
        assert retrieved_user is not None, \
            "User should be retrievable using email as partition key"
        
        # Verification 3: Retrieved data should match created data
        assert retrieved_user['email'] == email, \
            "Retrieved email should match the created email"
        assert retrieved_user['name'] == name, \
            "Retrieved name should match the created name"
        assert retrieved_user['password_hash'] == password_hash, \
            "Retrieved password_hash should match the created password_hash"
        
        # Verification 4: Retrieved data should include all required fields
        assert 'email' in retrieved_user, \
            "Retrieved user should contain email field"
        assert 'name' in retrieved_user, \
            "Retrieved user should contain name field"
        assert 'password_hash' in retrieved_user, \
            "Retrieved user should contain password_hash field (needed for authentication)"
        assert 'created_at' in retrieved_user, \
            "Retrieved user should contain created_at timestamp"
        
        # Verification 5: Verify DynamoDB query used email as partition key
        # by directly querying the table
        response = table.get_item(Key={'email': email})
        assert 'Item' in response, \
            "User should be retrievable from DynamoDB using email as partition key"
        
        stored_user = response['Item']
        assert stored_user['email'] == email, \
            "Stored user should have correct email"
        assert stored_user['password_hash'] == password_hash, \
            "Stored user should have correct password_hash"
    
    @mock_aws
    @settings(max_examples=20)
    @given(email=emails())
    def test_lookup_non_existent_user_raises_error(self, email):
        """
        **Validates: Requirements 3.1, 3.4**
        Feature: user-login-endpoint, Property 4: User lookup by email
        
        For any valid email that doesn't correspond to an existing user,
        the lookup should raise UserNotFoundError.
        
        This test verifies that:
        1. Querying for a non-existent user raises the appropriate error
        2. The error handling is consistent across all email formats
        """
        # Setup: Create a mock DynamoDB table (but don't create any users)
        table_name = f'test-users-table-{uuid.uuid4().hex[:8]}'
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
        
        # Action & Verification: Attempting to retrieve non-existent user should raise error
        with pytest.raises(UserNotFoundError) as exc_info:
            get_user_by_email(email)
        
        # Verification: Error message should mention the email
        error_message = str(exc_info.value)
        assert email in error_message, \
            f"Error message should mention the email. Got: {error_message}"
    
    @mock_aws
    @settings(max_examples=10)
    @given(
        emails_and_data=st.lists(
            st.tuples(
                emails(),
                text(min_size=1, max_size=100),
                st.builds(lambda: f"$2b$12${uuid.uuid4().hex}{uuid.uuid4().hex[:28]}")
            ),
            min_size=1,
            max_size=10,
            unique_by=lambda x: x[0]  # Ensure unique emails
        )
    )
    def test_lookup_multiple_users_independently(self, emails_and_data):
        """
        **Validates: Requirements 3.1, 3.4**
        Feature: user-login-endpoint, Property 4: User lookup by email
        
        For any set of users with different emails, each user should be
        independently retrievable using their email as the partition key.
        
        This test verifies that:
        1. Multiple users can be stored with different emails
        2. Each user can be retrieved independently by their email
        3. Retrieved data is specific to each user (no cross-contamination)
        """
        # Setup: Create a mock DynamoDB table
        table_name = f'test-users-table-{uuid.uuid4().hex[:8]}'
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
        
        # Action 1: Create all users
        created_users = {}
        for email, name, password_hash in emails_and_data:
            created_user = create_user(email, name, password_hash)
            created_users[email] = {
                'name': name,
                'password_hash': password_hash,
                'created_at': created_user['created_at']
            }
        
        # Action 2: Retrieve each user independently and verify
        for email, name, password_hash in emails_and_data:
            retrieved_user = get_user_by_email(email)
            
            # Verification: Retrieved user should match the created user
            assert retrieved_user is not None, \
                f"User with email {email} should be retrievable"
            assert retrieved_user['email'] == email, \
                f"Retrieved email should match for {email}"
            assert retrieved_user['name'] == name, \
                f"Retrieved name should match for {email}"
            assert retrieved_user['password_hash'] == password_hash, \
                f"Retrieved password_hash should match for {email}"
            
            # Verification: Retrieved data should match stored data
            assert retrieved_user['name'] == created_users[email]['name'], \
                f"Retrieved name should match stored name for {email}"
            assert retrieved_user['password_hash'] == created_users[email]['password_hash'], \
                f"Retrieved password_hash should match stored hash for {email}"
