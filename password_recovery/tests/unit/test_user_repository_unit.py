"""
Unit tests for password recovery user repository methods.

Tests the reset token storage, retrieval, and atomic invalidation methods.
"""

import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Import the functions to test
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from password_recovery.user_repository import (
    store_reset_token,
    get_reset_token,
    mark_token_used,
    DatabaseError,
    TokenAlreadyUsedError
)


class TestStoreResetToken:
    """Tests for store_reset_token function."""
    
    def test_store_reset_token_success(self):
        """Test successful token storage."""
        # Setup
        email = "user@example.com"
        token_hash = "abc123hash"
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Mock DynamoDB client
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.return_value = {}
        
        with patch.dict(os.environ, {
            'RESET_TOKENS_TABLE_NAME': 'ResetTokens',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                # Execute
                result = store_reset_token(email, token_hash, expiration)
                
                # Verify
                assert result is True
                mock_dynamodb.put_item.assert_called_once()
                
                # Check the item structure
                call_args = mock_dynamodb.put_item.call_args
                item = call_args[1]['Item']
                
                assert item['token_hash']['S'] == token_hash
                assert item['email']['S'] == email
                assert item['expiration']['S'] == expiration.isoformat()
                assert 'created_at' in item
                assert 'used_at' not in item  # Should not be set initially
    
    def test_store_reset_token_missing_table_name(self):
        """Test error when RESET_TOKENS_TABLE_NAME is not set."""
        email = "user@example.com"
        token_hash = "abc123hash"
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(DatabaseError, match="RESET_TOKENS_TABLE_NAME"):
                store_reset_token(email, token_hash, expiration)
    
    def test_store_reset_token_dynamodb_error(self):
        """Test handling of DynamoDB errors."""
        email = "user@example.com"
        token_hash = "abc123hash"
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Mock DynamoDB client to raise error
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.side_effect = Exception("DynamoDB error")
        
        with patch.dict(os.environ, {
            'RESET_TOKENS_TABLE_NAME': 'ResetTokens',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                with pytest.raises(DatabaseError, match="Unexpected error"):
                    store_reset_token(email, token_hash, expiration)


class TestGetResetToken:
    """Tests for get_reset_token function."""
    
    def test_get_reset_token_success(self):
        """Test successful token retrieval."""
        token_hash = "abc123hash"
        
        # Mock DynamoDB response
        mock_response = {
            'Item': {
                'token_hash': {'S': token_hash},
                'email': {'S': 'user@example.com'},
                'expiration': {'S': '2024-01-15T11:30:00+00:00'},
                'created_at': {'S': '2024-01-15T10:30:00+00:00'}
            }
        }
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.get_item.return_value = mock_response
        
        with patch.dict(os.environ, {
            'RESET_TOKENS_TABLE_NAME': 'ResetTokens',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                # Execute
                result = get_reset_token(token_hash)
                
                # Verify
                assert result is not None
                assert result['email'] == 'user@example.com'
                assert result['expiration'] == '2024-01-15T11:30:00+00:00'
                assert result['created_at'] == '2024-01-15T10:30:00+00:00'
                assert result['used_at'] is None
    
    def test_get_reset_token_with_used_at(self):
        """Test retrieval of a used token."""
        token_hash = "abc123hash"
        
        # Mock DynamoDB response with used_at
        mock_response = {
            'Item': {
                'token_hash': {'S': token_hash},
                'email': {'S': 'user@example.com'},
                'expiration': {'S': '2024-01-15T11:30:00+00:00'},
                'created_at': {'S': '2024-01-15T10:30:00+00:00'},
                'used_at': {'S': '2024-01-15T10:45:00+00:00'}
            }
        }
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.get_item.return_value = mock_response
        
        with patch.dict(os.environ, {
            'RESET_TOKENS_TABLE_NAME': 'ResetTokens',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                # Execute
                result = get_reset_token(token_hash)
                
                # Verify
                assert result is not None
                assert result['used_at'] == '2024-01-15T10:45:00+00:00'
    
    def test_get_reset_token_not_found(self):
        """Test retrieval when token doesn't exist."""
        token_hash = "nonexistent"
        
        # Mock DynamoDB response with no item
        mock_response = {}
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.get_item.return_value = mock_response
        
        with patch.dict(os.environ, {
            'RESET_TOKENS_TABLE_NAME': 'ResetTokens',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                # Execute
                result = get_reset_token(token_hash)
                
                # Verify
                assert result is None
    
    def test_get_reset_token_missing_table_name(self):
        """Test error when RESET_TOKENS_TABLE_NAME is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(DatabaseError, match="RESET_TOKENS_TABLE_NAME"):
                get_reset_token("abc123hash")


class TestMarkTokenUsed:
    """Tests for mark_token_used function."""
    
    def test_mark_token_used_success(self):
        """Test successfully marking a token as used."""
        token_hash = "abc123hash"
        
        # Mock DynamoDB client
        mock_dynamodb = MagicMock()
        mock_dynamodb.update_item.return_value = {}
        
        with patch.dict(os.environ, {
            'RESET_TOKENS_TABLE_NAME': 'ResetTokens',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                # Execute
                result = mark_token_used(token_hash)
                
                # Verify
                assert result is True
                mock_dynamodb.update_item.assert_called_once()
                
                # Check the update expression
                call_args = mock_dynamodb.update_item.call_args
                assert call_args[1]['UpdateExpression'] == 'SET used_at = :used_at'
                assert call_args[1]['ConditionExpression'] == 'attribute_not_exists(used_at)'
    
    def test_mark_token_used_already_used(self):
        """Test marking a token that's already been used (race condition)."""
        token_hash = "abc123hash"
        
        # Mock DynamoDB client to raise ConditionalCheckFailedException
        from botocore.exceptions import ClientError
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.update_item.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'ConditionalCheckFailedException',
                    'Message': 'The conditional request failed'
                }
            },
            'UpdateItem'
        )
        
        with patch.dict(os.environ, {
            'RESET_TOKENS_TABLE_NAME': 'ResetTokens',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                # Execute
                result = mark_token_used(token_hash)
                
                # Verify - should return False, not raise exception
                assert result is False
    
    def test_mark_token_used_missing_table_name(self):
        """Test error when RESET_TOKENS_TABLE_NAME is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(DatabaseError, match="RESET_TOKENS_TABLE_NAME"):
                mark_token_used("abc123hash")
    
    def test_mark_token_used_dynamodb_error(self):
        """Test handling of other DynamoDB errors."""
        token_hash = "abc123hash"
        
        # Mock DynamoDB client to raise a different error
        from botocore.exceptions import ClientError
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.update_item.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'InternalServerError',
                    'Message': 'Internal error'
                }
            },
            'UpdateItem'
        )
        
        with patch.dict(os.environ, {
            'RESET_TOKENS_TABLE_NAME': 'ResetTokens',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                with pytest.raises(DatabaseError, match="Failed to mark token as used"):
                    mark_token_used(token_hash)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



class TestIncrementSessionVersion:
    """Tests for increment_session_version function."""
    
    def test_increment_session_version_success(self):
        """Test successfully incrementing session version."""
        email = "user@example.com"
        
        # Mock DynamoDB response
        mock_response = {
            'Attributes': {
                'session_version': {'N': '1'}
            }
        }
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.update_item.return_value = mock_response
        
        with patch.dict(os.environ, {
            'USER_TABLE_NAME': 'Users',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                # Import here to avoid issues with patching
                from password_recovery.user_repository import increment_session_version
                
                # Execute
                result = increment_session_version(email)
                
                # Verify
                assert result == 1
                mock_dynamodb.update_item.assert_called_once()
                
                # Check the update expression
                call_args = mock_dynamodb.update_item.call_args
                assert call_args[1]['UpdateExpression'] == 'ADD session_version :inc'
                assert call_args[1]['ExpressionAttributeValues'][':inc']['N'] == '1'
                assert call_args[1]['ReturnValues'] == 'UPDATED_NEW'
    
    def test_increment_session_version_multiple_times(self):
        """Test incrementing session version multiple times."""
        email = "user@example.com"
        
        # Mock DynamoDB to return incrementing values
        mock_dynamodb = MagicMock()
        mock_dynamodb.update_item.side_effect = [
            {'Attributes': {'session_version': {'N': '1'}}},
            {'Attributes': {'session_version': {'N': '2'}}},
            {'Attributes': {'session_version': {'N': '3'}}}
        ]
        
        with patch.dict(os.environ, {
            'USER_TABLE_NAME': 'Users',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                from password_recovery.user_repository import increment_session_version
                
                # Execute multiple times
                result1 = increment_session_version(email)
                result2 = increment_session_version(email)
                result3 = increment_session_version(email)
                
                # Verify
                assert result1 == 1
                assert result2 == 2
                assert result3 == 3
    
    def test_increment_session_version_missing_table_name(self):
        """Test error when USER_TABLE_NAME is not set."""
        with patch.dict(os.environ, {}, clear=True):
            from password_recovery.user_repository import increment_session_version
            
            with pytest.raises(DatabaseError, match="USER_TABLE_NAME"):
                increment_session_version("user@example.com")
    
    def test_increment_session_version_dynamodb_error(self):
        """Test handling of DynamoDB errors."""
        email = "user@example.com"
        
        # Mock DynamoDB client to raise error
        from botocore.exceptions import ClientError
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.update_item.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'InternalServerError',
                    'Message': 'Internal error'
                }
            },
            'UpdateItem'
        )
        
        with patch.dict(os.environ, {
            'USER_TABLE_NAME': 'Users',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                from password_recovery.user_repository import increment_session_version
                
                with pytest.raises(DatabaseError, match="Failed to increment session version"):
                    increment_session_version(email)


class TestGetSessionVersion:
    """Tests for get_session_version function."""
    
    def test_get_session_version_success(self):
        """Test successfully retrieving session version."""
        email = "user@example.com"
        
        # Mock DynamoDB response
        mock_response = {
            'Item': {
                'email': {'S': email},
                'session_version': {'N': '5'}
            }
        }
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.get_item.return_value = mock_response
        
        with patch.dict(os.environ, {
            'USER_TABLE_NAME': 'Users',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                from password_recovery.user_repository import get_session_version
                
                # Execute
                result = get_session_version(email)
                
                # Verify
                assert result == 5
                mock_dynamodb.get_item.assert_called_once()
    
    def test_get_session_version_default_zero(self):
        """Test retrieving session version when not set (backward compatibility)."""
        email = "user@example.com"
        
        # Mock DynamoDB response without session_version
        mock_response = {
            'Item': {
                'email': {'S': email}
            }
        }
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.get_item.return_value = mock_response
        
        with patch.dict(os.environ, {
            'USER_TABLE_NAME': 'Users',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                from password_recovery.user_repository import get_session_version
                
                # Execute
                result = get_session_version(email)
                
                # Verify - should return 0 for backward compatibility
                assert result == 0
    
    def test_get_session_version_user_not_found(self):
        """Test retrieving session version when user doesn't exist."""
        email = "nonexistent@example.com"
        
        # Mock DynamoDB response with no item
        mock_response = {}
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.get_item.return_value = mock_response
        
        with patch.dict(os.environ, {
            'USER_TABLE_NAME': 'Users',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                from password_recovery.user_repository import get_session_version
                
                # Execute
                result = get_session_version(email)
                
                # Verify - should return 0 for non-existent user
                assert result == 0
    
    def test_get_session_version_missing_table_name(self):
        """Test error when USER_TABLE_NAME is not set."""
        with patch.dict(os.environ, {}, clear=True):
            from password_recovery.user_repository import get_session_version
            
            with pytest.raises(DatabaseError, match="USER_TABLE_NAME"):
                get_session_version("user@example.com")
    
    def test_get_session_version_dynamodb_error(self):
        """Test handling of DynamoDB errors."""
        email = "user@example.com"
        
        # Mock DynamoDB client to raise error
        from botocore.exceptions import ClientError
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.get_item.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'InternalServerError',
                    'Message': 'Internal error'
                }
            },
            'GetItem'
        )
        
        with patch.dict(os.environ, {
            'USER_TABLE_NAME': 'Users',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            with patch('boto3.client', return_value=mock_dynamodb):
                from password_recovery.user_repository import get_session_version
                
                with pytest.raises(DatabaseError, match="Failed to retrieve session version"):
                    get_session_version(email)
