"""
Property-based tests for JWT session version validation.

Feature: password-recovery
Property 11: JWT Session Version Validation

**Validates: Requirements 4.2, 4.3**

For any JWT presented for authentication, if the session_version claim in the JWT 
is less than the current session_version stored for that user, the JWT should be 
rejected with a 401 status code.

Note: This test validates the SessionManager component's validation logic.
The actual HTTP status code (401) will be set by the authentication middleware.
"""

import pytest
from unittest.mock import Mock, MagicMock
from hypothesis import given, strategies as st, settings
from password_recovery.session_manager import SessionManager


class TestJWTSessionVersionValidationProperty:
    """Property-based tests for JWT session version validation."""
    
    def _create_mock_repository_module(self, current_version=0):
        """Helper to create a mock user repository module."""
        mock_module = Mock()
        mock_module.get_session_version = Mock(return_value=current_version)
        mock_module.increment_session_version = Mock(return_value=current_version + 1)
        return mock_module
    
    @given(st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_matching_version_accepted(self, version):
        """
        Property: JWTs with matching session version should be accepted.
        
        For any JWT where the session_version claim matches the current
        session_version in the database, the JWT should be accepted.
        """
        mock_repo = self._create_mock_repository_module(current_version=version)
        manager = SessionManager(user_repo_module=mock_repo)
        
        is_valid = manager.validate_session_version('user@example.com', version)
        
        assert is_valid is True
    
    @given(st.integers(min_value=0, max_value=100), st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_older_version_rejected(self, current_version, version_diff):
        """
        Property: JWTs with older session version should be rejected.
        
        For any JWT where the session_version claim is less than the current
        session_version, the JWT should be rejected.
        """
        token_version = max(0, current_version - version_diff)
        
        # Ensure token version is actually older
        if token_version >= current_version:
            return
        
        mock_repo = self._create_mock_repository_module(current_version=current_version)
        manager = SessionManager(user_repo_module=mock_repo)
        
        is_valid = manager.validate_session_version('user@example.com', token_version)
        
        assert is_valid is False
    
    @given(st.integers(min_value=0, max_value=100), st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_newer_version_rejected(self, current_version, version_diff):
        """
        Property: JWTs with newer session version should be rejected.
        
        For any JWT where the session_version claim is greater than the current
        session_version (shouldn't happen in practice), the JWT should be rejected.
        """
        token_version = current_version + version_diff
        
        mock_repo = self._create_mock_repository_module(current_version=current_version)
        manager = SessionManager(user_repo_module=mock_repo)
        
        is_valid = manager.validate_session_version('user@example.com', token_version)
        
        assert is_valid is False
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_invalidate_all_sessions_increments_version(self, email):
        """
        Property: Invalidating sessions should increment the version.
        
        For any user, calling invalidate_all_sessions should increment
        the session_version by exactly 1.
        """
        current_version = 5
        mock_repo = self._create_mock_repository_module(current_version=current_version)
        manager = SessionManager(user_repo_module=mock_repo)
        
        manager.invalidate_all_sessions(email)
        
        # Verify increment_session_version was called
        mock_repo.increment_session_version.assert_called_once_with(email)
    
    @given(st.text(min_size=1, max_size=100), st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_get_current_session_version(self, email, version):
        """
        Property: Getting current version should return the stored version.
        
        For any user, get_current_session_version should return the current
        session_version from the database.
        """
        mock_repo = self._create_mock_repository_module(current_version=version)
        manager = SessionManager(user_repo_module=mock_repo)
        
        result = manager.get_current_session_version(email)
        
        assert result == version
        mock_repo.get_session_version.assert_called_once_with(email)
    
    @given(st.text(min_size=1, max_size=100), st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_validation_queries_current_version(self, email, token_version):
        """
        Property: Validation should query the current version from database.
        
        For any validation request, the session manager should query the
        current session_version from the user repository.
        """
        mock_repo = self._create_mock_repository_module(current_version=token_version)
        manager = SessionManager(user_repo_module=mock_repo)
        
        manager.validate_session_version(email, token_version)
        
        # Verify get_session_version was called
        mock_repo.get_session_version.assert_called_once_with(email)
    
    @given(st.text(min_size=1, max_size=100), st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_repository_error_rejects_token(self, email, token_version):
        """
        Property: Repository errors should reject the token for security.
        
        For any error during version validation, the session manager should
        reject the token (fail closed) for security.
        """
        mock_repo = Mock()
        mock_repo.get_session_version = Mock(side_effect=Exception("Database error"))
        manager = SessionManager(user_repo_module=mock_repo)
        
        is_valid = manager.validate_session_version(email, token_version)
        
        # Should reject on error
        assert is_valid is False
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_invalidation_error_raises_exception(self, email):
        """
        Property: Errors during invalidation should raise exceptions.
        
        For any error during session invalidation, the session manager should
        raise an exception because invalidation is critical for security.
        """
        mock_repo = Mock()
        mock_repo.increment_session_version = Mock(side_effect=Exception("Database error"))
        manager = SessionManager(user_repo_module=mock_repo)
        
        with pytest.raises(Exception):
            manager.invalidate_all_sessions(email)
    
    @given(st.integers(min_value=0, max_value=10))
    @settings(max_examples=100)
    def test_version_zero_is_valid_default(self, token_version):
        """
        Property: Version 0 should be valid for backward compatibility.
        
        For any user without a session_version set (defaults to 0), tokens
        with version 0 should be accepted.
        """
        mock_repo = self._create_mock_repository_module(current_version=0)
        manager = SessionManager(user_repo_module=mock_repo)
        
        is_valid = manager.validate_session_version('user@example.com', token_version)
        
        # Should be valid only if token version is also 0
        if token_version == 0:
            assert is_valid is True
        else:
            assert is_valid is False
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_get_version_error_returns_zero(self, email):
        """
        Property: Errors getting version should return 0 for backward compatibility.
        
        For any error when getting the current session version, the session
        manager should return 0 as a safe default.
        """
        mock_repo = Mock()
        mock_repo.get_session_version = Mock(side_effect=Exception("Database error"))
        manager = SessionManager(user_repo_module=mock_repo)
        
        version = manager.get_current_session_version(email)
        
        # Should return 0 on error
        assert version == 0
