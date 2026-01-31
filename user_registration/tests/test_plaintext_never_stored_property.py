"""
Property-based test for verifying plaintext passwords are never stored.

This test verifies that for any successful user registration, the stored password
field in DynamoDB is a bcrypt hash and never matches the original plaintext password.
"""

import os
import re
import uuid
import bcrypt
import boto3
from hypothesis import given, settings, strategies as st
from moto import mock_aws
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


class TestPlaintextNeverStoredProperty:
    """Property-based test for plaintext password storage prevention."""
    
    @mock_aws
    @settings(max_examples=20, deadline=None)
    @given(
        email=valid_emails,
        name=valid_names,
        password=valid_passwords
    )
    def test_plaintext_password_never_stored_in_dynamodb(self, email, name, password):
        """
        **Validates: Requirements 3.2**
        Feature: user-registration-endpoint, Property 7: Plaintext passwords never stored
        
        For any successful user registration, the stored password field in DynamoDB 
        should be a bcrypt hash and never match the original plaintext password.
        """
        # Setup: Create a mock DynamoDB table with unique name per test
        # Using a unique table name to avoid conflicts between test iterations
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
        
        # Simulate the registration process:
        # 1. Hash the password (this is what the registration endpoint should do)
        password_hash = hash_password(password)
        
        # 2. Store user data in DynamoDB (simulating what user_repository.create_user will do)
        table.put_item(
            Item={
                'email': email,
                'name': name,
                'password_hash': password_hash,
                'created_at': '2024-01-15T10:30:00Z'
            }
        )
        
        # 3. Retrieve the stored user data
        response = table.get_item(Key={'email': email})
        stored_user = response['Item']
        
        # Property verification: The stored password field should NEVER be the plaintext password
        stored_password_hash = stored_user['password_hash']
        
        # Assert 1: The stored password is NOT the plaintext password
        assert stored_password_hash != password, \
            f"Plaintext password was stored! This is a critical security violation. " \
            f"Expected a bcrypt hash but found the plaintext password."
        
        # Assert 2: The stored password is a valid bcrypt hash
        bcrypt_pattern = r'^\$2b\$12\$[./A-Za-z0-9]{53}$'
        assert re.match(bcrypt_pattern, stored_password_hash), \
            f"Stored password is not a valid bcrypt hash. Got: {stored_password_hash[:20]}..."
        
        # Assert 3: The stored hash starts with the bcrypt identifier
        assert stored_password_hash.startswith('$2b$12$'), \
            f"Stored password hash should start with '$2b$12$' but got: {stored_password_hash[:8]}"
        
        # Assert 4: The stored hash can verify the original password (proving it's a proper hash)
        password_bytes = password.encode('utf-8')
        hash_bytes = stored_password_hash.encode('utf-8')
        assert bcrypt.checkpw(password_bytes, hash_bytes), \
            "Stored hash should be verifiable with the original password"
        
        # Assert 5: The plaintext password should not appear anywhere in the stored data
        # Check all string fields in the stored user data
        for field_name, field_value in stored_user.items():
            if isinstance(field_value, str):
                assert password not in field_value, \
                    f"Plaintext password found in field '{field_name}'. " \
                    f"Passwords must never be stored in any field."
