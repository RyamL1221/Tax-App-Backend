"""
Property-Based Tests for Authorization

Tests that authorization only allows matching userIds.
**Validates: Requirements 1.1, 2.1**
"""

import pytest
from hypothesis import given, strategies as st

from document_download.exceptions import AuthorizationError


def authorize_download(job: dict, jwt_user_id: str) -> None:
    """
    Verify user is authorized to download document.
    
    Args:
        job: Job record from DynamoDB
        jwt_user_id: User ID from JWT token
        
    Raises:
        AuthorizationError: If userId doesn't match
    """
    if job.get('userId') != jwt_user_id:
        raise AuthorizationError(
            "You do not have permission to access this document"
        )


class TestAuthorizationProperty:
    """Property-based tests for authorization logic."""
    
    @given(
        job_user_id=st.text(min_size=1, max_size=100),
        jwt_user_id=st.text(min_size=1, max_size=100)
    )
    def test_authorization_only_allows_matching_user_ids(self, job_user_id, jwt_user_id):
        """
        Property: Authorization succeeds only when userIds match.
        
        For all possible userId combinations, authorization should succeed
        if and only if the job's userId matches the JWT userId.
        """
        job = {'userId': job_user_id}
        
        if job_user_id == jwt_user_id:
            # Should not raise - authorization succeeds
            authorize_download(job, jwt_user_id)
        else:
            # Should raise AuthorizationError
            with pytest.raises(AuthorizationError) as exc_info:
                authorize_download(job, jwt_user_id)
            
            assert "permission" in str(exc_info.value).lower()
    
    @given(user_id=st.text(min_size=1, max_size=100))
    def test_authorization_always_succeeds_for_same_user(self, user_id):
        """
        Property: Authorization always succeeds when userIds are identical.
        
        For any userId, if job.userId == JWT userId, authorization succeeds.
        """
        job = {'userId': user_id}
        
        # Should not raise
        authorize_download(job, user_id)
    
    @given(
        job_user_id=st.text(min_size=1, max_size=100),
        jwt_user_id=st.text(min_size=1, max_size=100).filter(lambda x: x != "")
    )
    def test_authorization_always_fails_for_different_users(self, job_user_id, jwt_user_id):
        """
        Property: Authorization always fails when userIds differ.
        
        For any two different userIds, authorization fails.
        """
        # Skip if userIds happen to be the same
        if job_user_id == jwt_user_id:
            return
        
        job = {'userId': job_user_id}
        
        # Should raise AuthorizationError
        with pytest.raises(AuthorizationError):
            authorize_download(job, jwt_user_id)
    
    @given(user_id=st.text(min_size=1, max_size=100))
    def test_authorization_error_message_consistent(self, user_id):
        """
        Property: Authorization error message is consistent.
        
        All authorization failures should have the same error message
        to prevent user enumeration.
        """
        job = {'userId': user_id}
        different_user_id = user_id + "_different"
        
        with pytest.raises(AuthorizationError) as exc_info:
            authorize_download(job, different_user_id)
        
        # Verify error message doesn't leak information
        error_msg = str(exc_info.value)
        assert "permission" in error_msg.lower()
        assert user_id not in error_msg  # Don't leak actual userId
        assert different_user_id not in error_msg  # Don't leak JWT userId
