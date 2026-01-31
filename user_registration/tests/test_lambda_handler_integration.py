"""
Integration tests for the Lambda handler.

These tests verify the end-to-end behavior of the lambda_handler function
with various input scenarios and error conditions.
"""

import json
import os
import pytest
from moto import mock_aws
import boto3

# Import the lambda handler
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import lambda_handler


@pytest.fixture
def dynamodb_table():
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        # Set up environment
        os.environ['USER_TABLE_NAME'] = 'test-users-table'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        
        # Create DynamoDB table
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='test-users-table',
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield dynamodb
        
        # Cleanup
        if 'USER_TABLE_NAME' in os.environ:
            del os.environ['USER_TABLE_NAME']


def test_successful_registration(dynamodb_table):
    """Test successful user registration with valid data."""
    event = {
        'body': json.dumps({
            'email': 'test@example.com',
            'name': 'Test User',
            'password': 'SecurePass123!'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert body['message'] == 'User registered successfully'
    assert body['email'] == 'test@example.com'
    assert 'password' not in body
    assert 'password_hash' not in body
    
    # Verify CORS headers
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
    assert response['headers']['Content-Type'] == 'application/json'


def test_missing_request_body(dynamodb_table):
    """Test that missing request body returns 400."""
    event = {}
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Request body is required' in body['error']


def test_invalid_json(dynamodb_table):
    """Test that invalid JSON returns 400."""
    event = {
        'body': 'not valid json {'
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Invalid JSON format' in body['error']


def test_missing_email_field(dynamodb_table):
    """Test that missing email field returns 400 with field name."""
    event = {
        'body': json.dumps({
            'name': 'Test User',
            'password': 'SecurePass123!'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'email' in body['error']
    assert 'Missing required fields' in body['error']


def test_missing_name_field(dynamodb_table):
    """Test that missing name field returns 400 with field name."""
    event = {
        'body': json.dumps({
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'name' in body['error']
    assert 'Missing required fields' in body['error']


def test_missing_password_field(dynamodb_table):
    """Test that missing password field returns 400 with field name."""
    event = {
        'body': json.dumps({
            'email': 'test@example.com',
            'name': 'Test User'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'password' in body['error']
    assert 'Missing required fields' in body['error']


def test_missing_multiple_fields(dynamodb_table):
    """Test that missing multiple fields returns 400 with all field names."""
    event = {
        'body': json.dumps({
            'name': 'Test User'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'email' in body['error']
    assert 'password' in body['error']
    assert 'Missing required fields' in body['error']


def test_invalid_email_format(dynamodb_table):
    """Test that invalid email format returns 400."""
    event = {
        'body': json.dumps({
            'email': 'not-an-email',
            'name': 'Test User',
            'password': 'SecurePass123!'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Validation failed' in body['error']


def test_weak_password(dynamodb_table):
    """Test that weak password returns 400."""
    event = {
        'body': json.dumps({
            'email': 'test@example.com',
            'name': 'Test User',
            'password': 'weak'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Validation failed' in body['error']


def test_empty_name(dynamodb_table):
    """Test that empty name returns 400."""
    event = {
        'body': json.dumps({
            'email': 'test@example.com',
            'name': '   ',
            'password': 'SecurePass123!'
        })
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Validation failed' in body['error']


def test_duplicate_email(dynamodb_table):
    """Test that duplicate email returns 409."""
    event = {
        'body': json.dumps({
            'email': 'duplicate@example.com',
            'name': 'Test User',
            'password': 'SecurePass123!'
        })
    }
    
    # First registration should succeed
    response1 = lambda_handler(event, None)
    assert response1['statusCode'] == 201
    
    # Second registration with same email should fail
    response2 = lambda_handler(event, None)
    assert response2['statusCode'] == 409
    body = json.loads(response2['body'])
    assert 'Email already registered' in body['error']


def test_cors_headers_on_all_responses(dynamodb_table):
    """Test that all responses include CORS headers."""
    # Test success response
    event_success = {
        'body': json.dumps({
            'email': 'cors@example.com',
            'name': 'CORS Test',
            'password': 'SecurePass123!'
        })
    }
    response = lambda_handler(event_success, None)
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert 'Access-Control-Allow-Headers' in response['headers']
    assert 'Access-Control-Allow-Methods' in response['headers']
    
    # Test error response
    event_error = {
        'body': json.dumps({
            'email': 'invalid',
            'name': 'Test',
            'password': 'SecurePass123!'
        })
    }
    response = lambda_handler(event_error, None)
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert 'Access-Control-Allow-Headers' in response['headers']
    assert 'Access-Control-Allow-Methods' in response['headers']
