"""
Property-based test for user data persistence in DynamoDB.

This test verifies that for any valid registration data (email, name, password),
when all validation passes, the endpoint stores a record in DynamoDB containing
email (as partition key), name, hashed password, and a created_at timestamp.
"""

import os
import re
import uuid
from datetime import datetime
import boto3
from hypothesis import given, settings, strategies as st
from moto import mock_aws
from user_registration.user_repository import create_user
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


class TestUserDataPersistenceProperty:
    """Property-based test for user data persistence in DynamoDB."""
    
    @mock_aws
    @settings(max_examples=20, deadline=None)
    @given(
        email=valid_emails,
        name=valid_names,
        password=valid_passwords
    )
    def test_user_data_persistence(self, email, name, password):
        """
        **Validates: Requirements 4.1, 4.2, 4.3**
        Feature: user-registration-endpoint, Property 8: User data persistence
        
        For any valid registration data (email, name, password), when all validation
        passes, the endpoint should store a record in DynamoDB containing email
        (as partition key), name, hashed password, and a created_at timestamp.
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
        
        # Action: Hash the password and create the user
        password_hash = hash_password(password)
        result = create_user(email, name, password_hash)
        
        # Verification 1: The create_user function should return user data
        assert result is not None, "create_user should return user data"
        assert 'email' in result, "Result should contain email"
        assert 'name' in result, "Result should contain name"
        assert 'created_at' in result, "Result should contain created_at timestamp"
        
        # Verification 2: The returned data should match the input
        assert result['email'] == email, f"Returned email should match input: {email}"
        assert result['name'] == name, f"Returned name should match input: {name}"
        
        # Verification 3: The password hash should NOT be in the returned data
        assert 'password_hash' not in result, \
            "Password hash should not be returned to prevent accidental exposure"
        
        # Verification 4: Retrieve the stored user data from DynamoDB
        response = table.get_item(Key={'email': email})
        assert 'Item' in response, f"User with email {email} should be stored in DynamoDB"
        
        stored_user = response['Item']
        
        # Verification 5: Email is used as partition key and stored correctly
        assert stored_user['email'] == email, \
            f"Stored email should match input. Expected: {email}, Got: {stored_user.get('email')}"
        
        # Verification 6: Name is stored correctly
        assert stored_user['name'] == name, \
            f"Stored name should match input. Expected: {name}, Got: {stored_user.get('name')}"
        
        # Verification 7: Password hash is stored (not plaintext)
        assert 'password_hash' in stored_user, \
            "password_hash field should be present in stored data"
        assert stored_user['password_hash'] == password_hash, \
            "Stored password hash should match the hashed password"
        assert stored_user['password_hash'] != password, \
            "Stored password should be hashed, not plaintext"
        
        # Verification 8: Password hash is a valid bcrypt hash
        bcrypt_pattern = r'^\$2b\$12\$[./A-Za-z0-9]{53}$'
        assert re.match(bcrypt_pattern, stored_user['password_hash']), \
            f"Stored password should be a valid bcrypt hash with work factor 12. " \
            f"Got: {stored_user['password_hash'][:20]}..."
        
        # Verification 9: created_at timestamp is present and valid
        assert 'created_at' in stored_user, \
            "created_at field should be present in stored data"
        
        created_at = stored_user['created_at']
        assert isinstance(created_at, str), \
            f"created_at should be a string. Got type: {type(created_at)}"
        
        # Verification 10: created_at is a valid ISO 8601 timestamp
        iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$'
        assert re.match(iso8601_pattern, created_at), \
            f"created_at should be a valid ISO 8601 timestamp. Got: {created_at}"
        
        # Verification 11: created_at can be parsed as a datetime
        try:
            parsed_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            assert parsed_time is not None, "created_at should be parseable as datetime"
        except ValueError as e:
            raise AssertionError(f"created_at should be a valid ISO 8601 timestamp: {e}")
        
        # Verification 12: All required fields are present
        required_fields = {'email', 'name', 'password_hash', 'created_at'}
        stored_fields = set(stored_user.keys())
        assert required_fields.issubset(stored_fields), \
            f"Stored user should contain all required fields. " \
            f"Missing: {required_fields - stored_fields}"
        
        # Verification 13: Email can be used to retrieve the user (verifying partition key)
        # Try retrieving again to ensure the partition key works correctly
        second_retrieval = table.get_item(Key={'email': email})
        assert 'Item' in second_retrieval, \
            "User should be retrievable by email (partition key)"
        assert second_retrieval['Item']['email'] == email, \
            "Retrieved user should have the correct email"
