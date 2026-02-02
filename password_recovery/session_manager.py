"""
Session manager for password recovery.

This module manages session invalidation through version tracking, ensuring
that all existing JWTs are invalidated when a user resets their password.
"""

import logging
import user_repository


logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages session invalidation through version tracking.
    
    When a user resets their password, all existing sessions (JWTs) are
    invalidated by incrementing the session version. JWTs with old versions
    will be rejected during authentication.
    """
    
    def __init__(self, user_repo_module=None):
        """
        Initialize the session manager.
        
        Args:
            user_repo_module: Optional user repository module (for testing)
        """
        self.user_repo = user_repo_module or user_repository
        logger.debug("SessionManager initialized")
    
    def invalidate_all_sessions(self, email: str) -> None:
        """
        Invalidates all existing sessions for a user.
        
        Increments the session_version in the user record.
        All JWTs issued before this increment will be rejected.
        
        Args:
            email: User's email address
            
        Examples:
            >>> manager = SessionManager()
            >>> manager.invalidate_all_sessions("user@example.com")
            >>> # All existing JWTs for this user are now invalid
        """
        try:
            new_version = self.user_repo.increment_session_version(email)
            logger.info(f"Invalidated all sessions for user. New version: {new_version}")
        except Exception as e:
            logger.error(f"Error invalidating sessions: {e}")
            # Re-raise because session invalidation is critical for security
            raise
    
    def validate_session_version(self, email: str, token_version: int) -> bool:
        """
        Validates that a JWT's session version is current.
        
        Args:
            email: User's email from JWT
            token_version: Session version from JWT claims
            
        Returns:
            True if token version matches current version
            
        Examples:
            >>> manager = SessionManager()
            >>> # Check if a JWT with version 1 is still valid
            >>> is_valid = manager.validate_session_version("user@example.com", 1)
            >>> if not is_valid:
            ...     print("Session has been invalidated")
        """
        try:
            current_version = self.user_repo.get_session_version(email)
            
            # Token is valid if its version matches the current version
            is_valid = token_version == current_version
            
            if not is_valid:
                logger.info(
                    f"Session version mismatch: token={token_version}, "
                    f"current={current_version}"
                )
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating session version: {e}")
            # On error, reject the token for security
            return False
    
    def get_current_session_version(self, email: str) -> int:
        """
        Gets the current session version for a user.
        
        Args:
            email: User's email address
            
        Returns:
            Current session version (0 if not set)
            
        Examples:
            >>> manager = SessionManager()
            >>> version = manager.get_current_session_version("user@example.com")
            >>> print(f"Current session version: {version}")
        """
        try:
            return self.user_repo.get_session_version(email)
        except Exception as e:
            logger.error(f"Error getting session version: {e}")
            # Return 0 as default for backward compatibility
            return 0
