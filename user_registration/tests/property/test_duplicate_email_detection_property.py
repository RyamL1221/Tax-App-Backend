"""
Property-based test for duplicate email detection.

This test verifies that for any email address, attempting to register a user
with that email twice should succeed on the first attempt and fail on the
second attempt with a DuplicateUserError.
"""

import os
import uuid
import boto3
from hypothesis import given, settings, strategies as st
from moto import mock_aws
import pytest
from user_registration.user_repository import create_user, DuplicateUserError
from user_registration.password_hasher import hash_password


# Strategy for generating valid passwords (meeting strength requirements)
valid_passwords = st.text(
    alphabet=st.characters(
        blacklist_categories=['Cs', 'Cc'],
        blacklist_characters='\x00'
    ),
    min_size=8,
    max_size=50
).filter(
    lambda p: (
        len(p.encode('utf-8')) <= 72 and  # bcrypt limit
        any(c.isupper() for c in p) and  # at least one uppercase
        any(c.islower() for c in p) and  # at least one lowercase
        any(c.isdigit() for c in p) and  # at least one digit
        any(not c.isalnum() for c in p)  # at least one special character
    )
)

# Strategy for generating valid email addresses
valid_emails = st.emails()

# Strategy for generating valid names
valid_names = st.text(
    alphabet=st.characters(
        whitelist_categories=['L', 'N'],  # Letters and numbers
        whitelist_characters=' -\''  # Common name characters
    ),
    min_size=1,
    max_size=100
).filter(lambda n: n.strip() != '')  # Non-empty after trimming


class TestDuplicateEmailDetectionProperty:
    """Property-based test for duplicate email detection."""
    
    @mock_aws
    @settings(max_examples=20, deadline=None)
    @given(
        email=valid_emails,
        name1=valid_names,
        name2=valid_names,
        password1=valid_passwords,
        password2=valid_passwords
    )
    def test_duplicate_email_detection(self, email, name1, name2, password1, password2):
        """
        **Validates: Requirements 4.4**
        Feature: user-registration-endpoint, Property 9: Duplicate email detection
        
        For any email address, attempting to register a user with that email twice
        should succeed on the first attempt and fail on the second attempt with a
        DuplicateUserError.
        """
        # Setup: Create a mock DynamoDB table with unique name per test
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
        
        # Action 1: First registration attempt - should succeed
        password_hash1 = hash_password(password1)
        result1 = create_user(email, name1, password_hash1)
        
        # Verification 1: First registration should succeed
        assert result1 is not None, "First registration should succeed"
        assert result1['email'] == email, \
            f"First registration should return the correct email: {email}"
        assert result1['name'] == name1, \
            f"First registration should return the correct name: {name1}"
        
        # Verification 2: User should be stored in DynamoDB
        response = table.get_item(Key={'email': email})
        assert 'Item' in response, \
            f"User with email {email} should be stored in DynamoDB after first registration"
        
        stored_user = response['Item']
        assert stored_user['email'] == email, \
            "Stored email should match the registered email"
        assert stored_user['name'] == name1, \
            "Stored name should match the first registration"
        
        # Action 2: Second registration attempt with same email - should fail
        password_hash2 = hash_password(password2)
        
        # Verification 3: Second registration should raise DuplicateUserError
        with pytest.raises(DuplicateUserError) as exc_info:
            create_user(email, name2, password_hash2)
        
        # Verification 4: Error message should mention the duplicate email
        error_message = str(exc_info.value)
        assert email in error_message, \
            f"Error message should mention the duplicate email. Got: {error_message}"
        
        # Verification 5: Original user data should remain unchanged
        response_after = table.get_item(Key={'email': email})
        assert 'Item' in response_after, \
            "Original user should still exist in DynamoDB after duplicate attempt"
        
        stored_user_after = response_after['Item']
        assert stored_user_after['email'] == email, \
            "Email should remain unchanged"
        assert stored_user_after['name'] == name1, \
            "Name should remain unchanged (first registration data preserved)"
        assert stored_user_after['password_hash'] == password_hash1, \
            "Password hash should remain unchanged (first registration data preserved)"
        
        # Verification 6: Only one user with this email should exist
        # Scan the table to ensure no duplicate entries
        scan_response = table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        assert scan_response['Count'] == 1, \
            f"Only one user with email {email} should exist in the database. " \
            f"Found: {scan_response['Count']}"
