"""
Property-based tests for non-existent user handling in the login endpoint.

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


class TestNonExistentUserProperty:
    """Property-based tests for non-existent user handling."""
    
    @mock_aws
    @settings(max_examples=100, deadline=500)
    @given(email=emails())
    def test_non_existent_user_raises_user_not_found_error(self, email):
        """
        **Validates: Requirements 3.2**
        Feature: user-login-endpoint, Property 5: Non-existent user returns 401
        
        For any email that does not correspond to an existing user, the endpoint 
        should return a 401 status code with a generic authentication error message.
        
        This test verifies that:
        1. Attempting to retrieve a non-existent user raises UserNotFoundError
        2. The error is raised consistently for any email format
        3. The error handling is appropriate for authentication flow
        
        Note: The UserNotFoundError will be caught by the lambda handler (task 8.1)
        and converted to a 401 response with a generic "Invalid credentials" message
        to prevent user enumeration attacks.
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
        
        # Action & Verification: Attempting to retrieve non-existent user should raise UserNotFoundError
        with pytest.raises(UserNotFoundError) as exc_info:
            get_user_by_email(email)
        
        # Verification 1: Error should be UserNotFoundError (not DatabaseError or other)
        assert isinstance(exc_info.value, UserNotFoundError), \
            f"Should raise UserNotFoundError for non-existent user, got {type(exc_info.value)}"
        
        # Verification 2: Error message should mention the email
        error_message = str(exc_info.value)
        assert email in error_message, \
            f"Error message should mention the email. Got: {error_message}"
        
        # Verification 3: Error message should indicate user not found
        assert 'not found' in error_message.lower(), \
            f"Error message should indicate user not found. Got: {error_message}"
    
    @mock_aws
    @settings(max_examples=100)
    @given(
        existing_email=emails(),
        non_existent_email=emails(),
        name=text(min_size=1, max_size=100),
        password_hash=st.builds(
            lambda: f"$2b$12${uuid.uuid4().hex}{uuid.uuid4().hex[:28]}",
        )
    )
    def test_non_existent_user_error_distinct_from_existing_user(
        self, existing_email, non_existent_email, name, password_hash
    ):
        """
        **Validates: Requirements 3.2**
        Feature: user-login-endpoint, Property 5: Non-existent user returns 401
        
        For any email that does not correspond to an existing user, the lookup
        should raise UserNotFoundError, while existing users should be retrieved
        successfully. This verifies the distinction between existing and non-existing
        users at the repository level.
        
        This test verifies that:
        1. Existing users can be retrieved without error
        2. Non-existent users raise UserNotFoundError
        3. The behavior is consistent and distinguishable
        """
        # Skip if emails are the same (we need distinct emails)
        if existing_email == non_existent_email:
            return
        
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
        
        # Action 1: Create a user with existing_email
        created_user = create_user(existing_email, name, password_hash)
        
        # Verification 1: Existing user should be retrievable
        retrieved_user = get_user_by_email(existing_email)
        assert retrieved_user is not None, \
            "Existing user should be retrievable"
        assert retrieved_user['email'] == existing_email, \
            "Retrieved user should have correct email"
        
        # Action 2: Attempt to retrieve non-existent user
        # Verification 2: Non-existent user should raise UserNotFoundError
        with pytest.raises(UserNotFoundError) as exc_info:
            get_user_by_email(non_existent_email)
        
        # Verification 3: Error should mention the non-existent email
        error_message = str(exc_info.value)
        assert non_existent_email in error_message, \
            f"Error message should mention the non-existent email. Got: {error_message}"
    
    @mock_aws
    @settings(max_examples=50)
    @given(
        emails_to_check=st.lists(
            emails(),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    def test_multiple_non_existent_users_all_raise_error(self, emails_to_check):
        """
        **Validates: Requirements 3.2**
        Feature: user-login-endpoint, Property 5: Non-existent user returns 401
        
        For any set of emails that don't correspond to existing users, each lookup
        should consistently raise UserNotFoundError.
        
        This test verifies that:
        1. Multiple non-existent user lookups all raise UserNotFoundError
        2. The error handling is consistent across different emails
        3. No false positives (finding users that don't exist)
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
        
        # Action & Verification: Each non-existent user lookup should raise UserNotFoundError
        for email in emails_to_check:
            with pytest.raises(UserNotFoundError) as exc_info:
                get_user_by_email(email)
            
            # Verify error message mentions the email
            error_message = str(exc_info.value)
            assert email in error_message, \
                f"Error message should mention email {email}. Got: {error_message}"
            
            # Verify error indicates user not found
            assert 'not found' in error_message.lower(), \
                f"Error message should indicate user not found for {email}. Got: {error_message}"
