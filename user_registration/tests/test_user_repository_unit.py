"""
Unit tests for user repository with mocked DynamoDB.

These tests verify the core functionality of the user repository using moto
to mock DynamoDB operations.
"""

import os
import re
import uuid
from datetime import datetime
import boto3
import pytest
from moto import mock_aws
from user_registration.user_repository import (
    create_user,
    DuplicateUserError,
    DatabaseError
)


class TestUserRepositoryUnit:
    """Unit tests for user repository with mocked DynamoDB."""
    
    @mock_aws
    def test_successful_user_creation(self):
        """
        Test successful user creation with mocked DynamoDB.
        
        Verifies that create_user successfully stores a user in DynamoDB
        and returns the expected user data.
        
        Requirements: 4.1, 4.2, 4.3, 4.4
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
        
        # Test data
        email = 'test@example.com'
        name = 'Test User'
        password_hash = '$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJK'
        
        # Action: Create user
        result = create_user(email, name, password_hash)
        
        # Verification: Check returned data
        assert result is not None, "create_user should return user data"
        assert result['email'] == email, "Returned email should match input"
        assert result['name'] == name, "Returned name should match input"
        assert 'created_at' in result, "Result should contain created_at timestamp"
        assert 'password_hash' not in result, \
            "Password hash should not be in returned data"
        
        # Verification: Check data stored in DynamoDB
        response = table.get_item(Key={'email': email})
        assert 'Item' in response, "User should be stored in DynamoDB"
        
        stored_user = response['Item']
        assert stored_user['email'] == email, "Stored email should match input"
        assert stored_user['name'] == name, "Stored name should match input"
        assert stored_user['password_hash'] == password_hash, \
            "Stored password hash should match input"
        assert 'created_at' in stored_user, \
            "Stored user should have created_at timestamp"
    
    @mock_aws
    def test_duplicate_email_raises_error(self):
        """
        Test that duplicate email raises DuplicateUserError.
        
        Verifies that attempting to create a user with an email that already
        exists in the database raises a DuplicateUserError.
        
        Requirements: 4.4
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
        
        # Test data
        email = 'duplicate@example.com'
        name1 = 'First User'
        name2 = 'Second User'
        password_hash1 = '$2b$12$hash1hash1hash1hash1hash1hash1hash1hash1hash1hash1'
        password_hash2 = '$2b$12$hash2hash2hash2hash2hash2hash2hash2hash2hash2hash2'
        
        # Action 1: Create first user - should succeed
        result1 = create_user(email, name1, password_hash1)
        assert result1 is not None, "First user creation should succeed"
        assert result1['email'] == email, "First user should have correct email"
        
        # Action 2: Attempt to create second user with same email - should fail
        with pytest.raises(DuplicateUserError) as exc_info:
            create_user(email, name2, password_hash2)
        
        # Verification: Check error message
        error_message = str(exc_info.value)
        assert email in error_message, \
            f"Error message should mention the duplicate email. Got: {error_message}"
        
        # Verification: Original user data should remain unchanged
        response = table.get_item(Key={'email': email})
        assert 'Item' in response, "Original user should still exist"
        
        stored_user = response['Item']
        assert stored_user['name'] == name1, \
            "Original user name should be preserved"
        assert stored_user['password_hash'] == password_hash1, \
            "Original password hash should be preserved"
    
    @mock_aws
    def test_email_used_as_partition_key(self):
        """
        Test that email is used as the partition key.
        
        Verifies that the email field is used as the partition key in DynamoDB,
        allowing users to be retrieved by their email address.
        
        Requirements: 4.2
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
        
        # Test data
        email = 'partitionkey@example.com'
        name = 'Partition Key Test'
        password_hash = '$2b$12$partitionkeyhashpartitionkeyhashpartitionkeyhash'
        
        # Action: Create user
        result = create_user(email, name, password_hash)
        assert result is not None, "User creation should succeed"
        
        # Verification: Retrieve user using email as partition key
        response = table.get_item(Key={'email': email})
        assert 'Item' in response, \
            "User should be retrievable using email as partition key"
        
        stored_user = response['Item']
        assert stored_user['email'] == email, \
            "Retrieved user should have the correct email"
        assert stored_user['name'] == name, \
            "Retrieved user should have the correct name"
        
        # Verification: Verify that email is indeed the partition key
        # by checking the table's key schema
        table_description = dynamodb.meta.client.describe_table(
            TableName=table_name
        )
        key_schema = table_description['Table']['KeySchema']
        
        partition_key = next(
            (key for key in key_schema if key['KeyType'] == 'HASH'),
            None
        )
        assert partition_key is not None, "Table should have a partition key"
        assert partition_key['AttributeName'] == 'email', \
            "Partition key should be 'email'"
    
    @mock_aws
    def test_created_at_timestamp_present(self):
        """
        Test that created_at timestamp is present.
        
        Verifies that the created_at field is present in the stored user data
        and is a valid ISO 8601 timestamp.
        
        Requirements: 4.3
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
        
        # Test data
        email = 'timestamp@example.com'
        name = 'Timestamp Test'
        password_hash = '$2b$12$timestamphashstamphashstamphashstamphashstamphash'
        
        # Record time before creation
        time_before = datetime.now()
        
        # Action: Create user
        result = create_user(email, name, password_hash)
        
        # Record time after creation
        time_after = datetime.now()
        
        # Verification: Check created_at in returned data
        assert 'created_at' in result, \
            "Returned data should contain created_at timestamp"
        
        created_at_str = result['created_at']
        assert isinstance(created_at_str, str), \
            "created_at should be a string"
        
        # Verification: Check created_at is valid ISO 8601 format
        iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$'
        assert re.match(iso8601_pattern, created_at_str), \
            f"created_at should be valid ISO 8601 format. Got: {created_at_str}"
        
        # Verification: Parse and validate timestamp
        try:
            created_at = datetime.fromisoformat(
                created_at_str.replace('Z', '+00:00')
            )
            assert created_at is not None, \
                "created_at should be parseable as datetime"
        except ValueError as e:
            pytest.fail(f"created_at should be valid ISO 8601 timestamp: {e}")
        
        # Verification: Check created_at is stored in DynamoDB
        response = table.get_item(Key={'email': email})
        assert 'Item' in response, "User should be stored in DynamoDB"
        
        stored_user = response['Item']
        assert 'created_at' in stored_user, \
            "Stored user should have created_at timestamp"
        assert stored_user['created_at'] == created_at_str, \
            "Stored created_at should match returned created_at"
    
    @mock_aws
    def test_missing_table_name_raises_error(self):
        """
        Test that missing USER_TABLE_NAME environment variable raises DatabaseError.
        
        Verifies that the repository properly handles the case where the
        USER_TABLE_NAME environment variable is not set.
        """
        # Setup: Remove USER_TABLE_NAME environment variable
        if 'USER_TABLE_NAME' in os.environ:
            del os.environ['USER_TABLE_NAME']
        
        # Test data
        email = 'test@example.com'
        name = 'Test User'
        password_hash = '$2b$12$testhash'
        
        # Action & Verification: Should raise DatabaseError
        with pytest.raises(DatabaseError) as exc_info:
            create_user(email, name, password_hash)
        
        error_message = str(exc_info.value)
        assert 'USER_TABLE_NAME' in error_message, \
            f"Error message should mention USER_TABLE_NAME. Got: {error_message}"
    
    @mock_aws
    def test_multiple_users_can_be_created(self):
        """
        Test that multiple users with different emails can be created.
        
        Verifies that the repository can handle creating multiple users
        with different email addresses.
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
        
        # Test data: Multiple users
        users = [
            ('user1@example.com', 'User One', '$2b$12$hash1'),
            ('user2@example.com', 'User Two', '$2b$12$hash2'),
            ('user3@example.com', 'User Three', '$2b$12$hash3'),
        ]
        
        # Action: Create multiple users
        results = []
        for email, name, password_hash in users:
            result = create_user(email, name, password_hash)
            results.append(result)
        
        # Verification: All users should be created successfully
        assert len(results) == len(users), \
            "All users should be created successfully"
        
        for i, (email, name, password_hash) in enumerate(users):
            # Check returned data
            assert results[i]['email'] == email, \
                f"User {i+1} should have correct email"
            assert results[i]['name'] == name, \
                f"User {i+1} should have correct name"
            
            # Check stored data
            response = table.get_item(Key={'email': email})
            assert 'Item' in response, \
                f"User {i+1} should be stored in DynamoDB"
            
            stored_user = response['Item']
            assert stored_user['email'] == email, \
                f"Stored user {i+1} should have correct email"
            assert stored_user['name'] == name, \
                f"Stored user {i+1} should have correct name"
            assert stored_user['password_hash'] == password_hash, \
                f"Stored user {i+1} should have correct password hash"
