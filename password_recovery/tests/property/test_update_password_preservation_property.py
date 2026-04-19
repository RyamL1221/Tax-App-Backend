"""
Preservation property tests for update_password() — run BEFORE implementing the fix.

These tests verify behavior that must be PRESERVED after the fix.
They should all PASS on the current unfixed code.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**
"""

import os

import boto3
import pytest
from hypothesis import given, settings, strategies as st
from moto import mock_aws

from password_recovery.user_repository import DatabaseError, update_password
from user_login.user_repository import get_user_by_email


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_users_table(dynamodb):
    """Create the Users DynamoDB table (idempotent)."""
    try:
        dynamodb.create_table(
            TableName="Users",
            KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    except dynamodb.exceptions.ResourceInUseException:
        pass


# ---------------------------------------------------------------------------
# 1. Registration read-back preservation
# ---------------------------------------------------------------------------

@mock_aws
@given(
    email=st.emails(),
    password_hash=st.text(min_size=10, max_size=60),
)
@settings(max_examples=20, deadline=5000)
def test_registration_read_back_preservation(email, password_hash):
    """
    Property: For all valid email/hash pairs, inserting a user record with
    `password_hash` and then calling get_user_by_email() returns the same
    `password_hash`. This verifies the registration + login read path is
    unaffected by the update_password bug.

    **Validates: Requirements 3.1, 3.2**
    """
    os.environ["USER_TABLE_NAME"] = "Users"
    os.environ.pop("AWS_ENDPOINT_URL", None)

    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    _create_users_table(dynamodb)

    # Insert a user record (simulating registration)
    dynamodb.put_item(
        TableName="Users",
        Item={
            "email": {"S": email},
            "name": {"S": "Test User"},
            "password_hash": {"S": password_hash},
            "session_version": {"N": "0"},
            "created_at": {"S": "2024-01-01T00:00:00+00:00"},
        },
    )

    # Read back via the login repository
    user = get_user_by_email(email)
    assert user["password_hash"] == password_hash, (
        f"Expected password_hash '{password_hash}' but got '{user['password_hash']}'"
    )

    # Clean up
    dynamodb.delete_item(TableName="Users", Key={"email": {"S": email}})


# ---------------------------------------------------------------------------
# 2. update_password return value preservation
# ---------------------------------------------------------------------------

@mock_aws
@given(
    email=st.emails(),
    password_hash=st.text(min_size=10, max_size=60),
)
@settings(max_examples=20, deadline=5000)
def test_update_password_returns_true_on_success(email, password_hash):
    """
    Property: For all valid email/hash pairs, update_password() returns True
    on success.

    **Validates: Requirements 3.4**
    """
    os.environ["USER_TABLE_NAME"] = "Users"
    os.environ.pop("AWS_ENDPOINT_URL", None)

    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    _create_users_table(dynamodb)

    # Seed a user record
    dynamodb.put_item(
        TableName="Users",
        Item={
            "email": {"S": email},
            "name": {"S": "Test User"},
            "password_hash": {"S": "original_hash_1234567890"},
            "session_version": {"N": "0"},
            "created_at": {"S": "2024-01-01T00:00:00+00:00"},
        },
    )

    result = update_password(email, password_hash)
    assert result is True, f"Expected True but got {result}"

    # Clean up
    dynamodb.delete_item(TableName="Users", Key={"email": {"S": email}})


# ---------------------------------------------------------------------------
# 3. update_password error handling preservation
# ---------------------------------------------------------------------------

@given(
    email=st.emails(),
    password_hash=st.text(min_size=10, max_size=60),
)
@settings(max_examples=20, deadline=5000)
def test_update_password_raises_database_error_when_table_not_set(email, password_hash):
    """
    Property: Calling update_password() when USER_TABLE_NAME env var is NOT
    set raises DatabaseError.

    **Validates: Requirements 3.3**
    """
    os.environ.pop("USER_TABLE_NAME", None)
    os.environ.pop("AWS_ENDPOINT_URL", None)

    with pytest.raises(DatabaseError):
        update_password(email, password_hash)
