"""
Bug condition exploration test for update_password().

This test encodes the EXPECTED behavior: after calling update_password(email, new_hash),
the DynamoDB item's `password_hash` attribute should equal new_hash, and no extraneous
`hashed_password` attribute should exist.

On UNFIXED code, this test is EXPECTED TO FAIL because update_password() currently writes
to `hashed_password` instead of `password_hash`.

**Validates: Requirements 1.1, 2.1, 2.3**
"""

import os

import boto3
import pytest
from hypothesis import given, settings, strategies as st
from moto import mock_aws

from password_recovery.user_repository import update_password


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    """Set up environment and mocked AWS for all tests."""
    monkeypatch.setenv("USER_TABLE_NAME", "Users")
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)


@mock_aws
@given(
    email=st.emails(),
    new_hash=st.text(min_size=10, max_size=60),
)
@settings(max_examples=20, deadline=5000)
def test_update_password_writes_to_password_hash_attribute(email, new_hash):
    """
    Property: For any valid email and new_hash, calling update_password(email, new_hash)
    SHALL update the `password_hash` DynamoDB attribute to new_hash and SHALL NOT create
    a `hashed_password` attribute.

    **Validates: Requirements 1.1, 2.1, 2.3**
    """
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")

    # Ensure table exists (ignore if already created by a previous example)
    try:
        dynamodb.create_table(
            TableName="Users",
            KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    except dynamodb.exceptions.ResourceInUseException:
        pass

    # Insert a user record with an original password_hash
    original_hash = "original_hash_value_1234567890"
    dynamodb.put_item(
        TableName="Users",
        Item={
            "email": {"S": email},
            "name": {"S": "Test User"},
            "password_hash": {"S": original_hash},
            "session_version": {"N": "0"},
        },
    )

    # Call update_password on the unfixed code
    result = update_password(email, new_hash)
    assert result is True

    # Retrieve the item and inspect attributes
    response = dynamodb.get_item(
        TableName="Users",
        Key={"email": {"S": email}},
    )
    item = response["Item"]

    # Expected behavior: password_hash attribute equals new_hash
    assert item["password_hash"]["S"] == new_hash, (
        f"password_hash should be '{new_hash}' but is '{item['password_hash']['S']}'"
    )

    # Expected behavior: no extraneous hashed_password attribute
    assert "hashed_password" not in item, (
        f"Item should NOT contain 'hashed_password' attribute, but it does: "
        f"{item.get('hashed_password')}"
    )

    # Clean up the item for the next example
    dynamodb.delete_item(
        TableName="Users",
        Key={"email": {"S": email}},
    )
