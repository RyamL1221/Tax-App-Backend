"""
Integration test for session invalidation after password reset.

This test verifies the complete flow:
1. User logs in and receives a JWT
2. User resets their password
3. Old JWT is rejected due to session version mismatch
4. User can log in again with new password and receive new JWT

Validates: Requirements 4.1, 4.2, 4.3
"""

import os
import sys
import json
import time
import bcrypt
import jwt
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'user_login'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from user_login.token_generator import generate_jwt_token
from jwt_verifier import verify_jwt_token, SessionVersionMismatchError
from password_recovery import user_repository


class TestSessionInvalidationIntegration:
    """Integration tests for session invalidation after password reset."""
    
    @pytest.fixture
    def mock_dynamodb(self):
        """Mock DynamoDB client for testing."""
        with patch('boto3.client') as mock_client:
            mock_db = MagicMock()
            mock_client.return_value = mock_db
            yield mock_db
    
    @pytest.fixture
    def jwt_secret(self):
        """JWT secret key for testing."""
        return "test-secret-key-at-least-32-characters-long"
    
    def test_session_invalidation_after_password_reset(
        self, 
        mock_dynamodb,
        jwt_secret
    ):
        """
        Test complete session invalidation flow.
        
        Flow:
        1. User logs in (session_version = 0)
        2. JWT is generated with session_version = 0
        3. User resets password (session_version incremented to 1)
        4. Old JWT with session_version = 0 is rejected
        5. User logs in again (session_version = 1)
        6. New JWT with session_version = 1 is accepted
        
        Validates: Requirements 4.1, 4.2, 4.3
        """
        email = "user@example.com"
        old_password = "OldPassword123!"
        new_password = "NewPassword456!"
        
        # Step 1: Initial login - user has session_version = 0
        initial_session_version = 0
        
        # Generate initial JWT token
        old_jwt = generate_jwt_token(email, jwt_secret, initial_session_version)
        
        # Verify old JWT can be decoded
        old_payload = jwt.decode(old_jwt, jwt_secret, algorithms=["HS256"])
        assert old_payload['email'] == email
        assert old_payload['session_version'] == 0
        
        # Mock get_session_version to return initial version
        def get_initial_session_version(user_email: str) -> int:
            assert user_email == email
            return initial_session_version
        
        # Verify old JWT is valid with session version check
        verified_payload = verify_jwt_token(
            old_jwt, 
            jwt_secret, 
            get_initial_session_version
        )
        assert verified_payload['email'] == email
        
        # Step 2: User resets password - session_version incremented to 1
        # Mock the increment_session_version call
        new_session_version = 1
        
        with patch.dict(os.environ, {
            'USER_TABLE_NAME': 'test-users-table',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            mock_dynamodb.update_item.return_value = {
                'Attributes': {
                    'session_version': {'N': str(new_session_version)}
                }
            }
            
            # Simulate password reset incrementing session version
            result_version = user_repository.increment_session_version(email)
            assert result_version == new_session_version
        
        # Step 3: Old JWT should now be rejected
        def get_new_session_version(user_email: str) -> int:
            assert user_email == email
            return new_session_version
        
        # Verify old JWT is rejected due to session version mismatch
        with pytest.raises(SessionVersionMismatchError) as exc_info:
            verify_jwt_token(old_jwt, jwt_secret, get_new_session_version)
        
        assert "session version" in str(exc_info.value).lower()
        assert str(initial_session_version) in str(exc_info.value)
        assert str(new_session_version) in str(exc_info.value)
        
        # Step 4: User logs in again with new password
        new_jwt = generate_jwt_token(email, jwt_secret, new_session_version)
        
        # Verify new JWT can be decoded
        new_payload = jwt.decode(new_jwt, jwt_secret, algorithms=["HS256"])
        assert new_payload['email'] == email
        assert new_payload['session_version'] == 1
        
        # Step 5: New JWT should be accepted
        verified_new_payload = verify_jwt_token(
            new_jwt,
            jwt_secret,
            get_new_session_version
        )
        assert verified_new_payload['email'] == email
        assert verified_new_payload['session_version'] == new_session_version
    
    def test_multiple_password_resets_invalidate_all_previous_tokens(
        self,
        mock_dynamodb,
        jwt_secret
    ):
        """
        Test that multiple password resets invalidate all previous tokens.
        
        Validates: Requirements 4.1, 4.2, 4.3
        """
        email = "user@example.com"
        
        # Generate tokens at different session versions
        jwt_v0 = generate_jwt_token(email, jwt_secret, 0)
        jwt_v1 = generate_jwt_token(email, jwt_secret, 1)
        jwt_v2 = generate_jwt_token(email, jwt_secret, 2)
        
        # After 3 password resets, session_version = 3
        current_session_version = 3
        
        def get_current_session_version(user_email: str) -> int:
            return current_session_version
        
        # All old tokens should be rejected
        with pytest.raises(SessionVersionMismatchError):
            verify_jwt_token(jwt_v0, jwt_secret, get_current_session_version)
        
        with pytest.raises(SessionVersionMismatchError):
            verify_jwt_token(jwt_v1, jwt_secret, get_current_session_version)
        
        with pytest.raises(SessionVersionMismatchError):
            verify_jwt_token(jwt_v2, jwt_secret, get_current_session_version)
        
        # Only current version token should be accepted
        jwt_v3 = generate_jwt_token(email, jwt_secret, 3)
        verified_payload = verify_jwt_token(
            jwt_v3,
            jwt_secret,
            get_current_session_version
        )
        assert verified_payload['session_version'] == 3
    
    def test_session_version_zero_for_new_users(
        self,
        jwt_secret
    ):
        """
        Test that new users start with session_version = 0.
        
        Validates: Requirements 4.1
        """
        email = "newuser@example.com"
        
        # New user has session_version = 0
        jwt_token = generate_jwt_token(email, jwt_secret, 0)
        
        payload = jwt.decode(jwt_token, jwt_secret, algorithms=["HS256"])
        assert payload['session_version'] == 0
        
        # Token should be valid with session version check
        def get_session_version(user_email: str) -> int:
            return 0
        
        verified_payload = verify_jwt_token(
            jwt_token,
            jwt_secret,
            get_session_version
        )
        assert verified_payload['session_version'] == 0
    
    def test_expired_token_rejected_before_session_version_check(
        self,
        jwt_secret
    ):
        """
        Test that expired tokens are rejected even if session version matches.
        
        Validates: Token expiration takes precedence over session version.
        """
        email = "user@example.com"
        session_version = 1
        
        # Create expired token
        issued_at = int(time.time()) - 7200  # 2 hours ago
        expiration = issued_at + 3600  # Expired 1 hour ago
        
        payload = {
            "email": email,
            "session_version": session_version,
            "iat": issued_at,
            "exp": expiration
        }
        
        expired_token = jwt.encode(payload, jwt_secret, algorithm="HS256")
        
        def get_session_version(user_email: str) -> int:
            return session_version
        
        # Should raise ExpiredSignatureError, not SessionVersionMismatchError
        with pytest.raises(jwt.ExpiredSignatureError):
            verify_jwt_token(expired_token, jwt_secret, get_session_version)
    
    def test_invalid_signature_rejected_before_session_version_check(
        self,
        jwt_secret
    ):
        """
        Test that tokens with invalid signatures are rejected before session version check.
        
        Validates: Signature verification takes precedence over session version.
        """
        email = "user@example.com"
        session_version = 1
        wrong_secret = "wrong-secret-key-at-least-32-characters-long"
        
        # Create token with wrong secret
        token = generate_jwt_token(email, wrong_secret, session_version)
        
        def get_session_version(user_email: str) -> int:
            return session_version
        
        # Should raise InvalidSignatureError, not SessionVersionMismatchError
        with pytest.raises(jwt.InvalidSignatureError):
            verify_jwt_token(token, jwt_secret, get_session_version)
    
    def test_session_version_validation_only_when_callback_provided(
        self,
        jwt_secret
    ):
        """
        Test that session version validation only occurs when callback is provided.
        
        Validates: Backward compatibility - tokens work without session version check.
        """
        email = "user@example.com"
        old_session_version = 0
        
        # Create token with old session version
        token = generate_jwt_token(email, jwt_secret, old_session_version)
        
        # Without callback, token should be accepted regardless of session version
        verified_payload = verify_jwt_token(token, jwt_secret)
        assert verified_payload['email'] == email
        assert verified_payload['session_version'] == old_session_version
        
        # This allows backward compatibility for endpoints that don't check session version
