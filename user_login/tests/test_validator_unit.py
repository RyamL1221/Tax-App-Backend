"""
Unit tests for user login validator.

Tests specific examples and edge cases for email and password validation.
"""

import pytest
from user_login.validator import (
    ValidationError,
    validate_email,
    validate_password_present,
    validate_login_data
)


class TestValidateEmail:
    """Tests for email validation."""
    
    def test_valid_email(self):
        """Test that valid email passes validation."""
        assert validate_email("user@example.com") is True
    
    def test_valid_email_with_subdomain(self):
        """Test that email with subdomain passes validation."""
        assert validate_email("user@mail.example.com") is True
    
    def test_invalid_email_missing_at(self):
        """Test that email without @ symbol fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("userexample.com")
    
    def test_invalid_email_missing_domain(self):
        """Test that email without domain fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@")
    
    def test_empty_email(self):
        """Test that empty email fails validation."""
        with pytest.raises(ValidationError, match="Email must be a non-empty string"):
            validate_email("")
    
    def test_none_email(self):
        """Test that None email fails validation."""
        with pytest.raises(ValidationError, match="Email must be a non-empty string"):
            validate_email(None)
    
    def test_non_string_email(self):
        """Test that non-string email fails validation."""
        with pytest.raises(ValidationError, match="Email must be a non-empty string"):
            validate_email(123)
    
    # Edge case tests for specific invalid email formats
    def test_invalid_email_multiple_at_symbols(self):
        """Test that email with multiple @ symbols fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@@example.com")
    
    def test_invalid_email_at_symbol_only(self):
        """Test that @ symbol alone fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("@")
    
    def test_invalid_email_starts_with_at(self):
        """Test that email starting with @ fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("@example.com")
    
    def test_invalid_email_missing_local_part(self):
        """Test that email without local part fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("@example.com")
    
    def test_invalid_email_spaces_in_address(self):
        """Test that email with spaces fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user name@example.com")
    
    def test_invalid_email_special_chars_in_domain(self):
        """Test that email with invalid special characters in domain fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@exam ple.com")
    
    def test_invalid_email_missing_tld(self):
        """Test that email without top-level domain fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@example")
    
    def test_invalid_email_double_dots(self):
        """Test that email with consecutive dots fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user..name@example.com")
    
    def test_invalid_email_starts_with_dot(self):
        """Test that email starting with dot fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email(".user@example.com")
    
    def test_invalid_email_ends_with_dot(self):
        """Test that email ending with dot before @ fails validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user.@example.com")


class TestValidatePasswordPresent:
    """Tests for password presence validation."""
    
    def test_valid_password(self):
        """Test that non-empty password passes validation."""
        assert validate_password_present("password123") is True
    
    def test_valid_password_single_char(self):
        """Test that single character password passes validation."""
        assert validate_password_present("a") is True
    
    def test_empty_password(self):
        """Test that empty password fails validation."""
        with pytest.raises(ValidationError, match="Password must be a non-empty string"):
            validate_password_present("")
    
    def test_none_password(self):
        """Test that None password fails validation."""
        with pytest.raises(ValidationError, match="Password must be a string"):
            validate_password_present(None)
    
    def test_non_string_password(self):
        """Test that non-string password fails validation."""
        with pytest.raises(ValidationError, match="Password must be a string"):
            validate_password_present(123)
    
    # Edge case tests for whitespace-only passwords
    def test_whitespace_only_password_single_space(self):
        """Test that password with single space passes validation (whitespace is valid)."""
        # Note: For login, we only check presence, not content
        # Whitespace-only passwords are technically non-empty strings
        assert validate_password_present(" ") is True
    
    def test_whitespace_only_password_multiple_spaces(self):
        """Test that password with multiple spaces passes validation."""
        assert validate_password_present("   ") is True
    
    def test_whitespace_only_password_tabs(self):
        """Test that password with tabs passes validation."""
        assert validate_password_present("\t\t") is True
    
    def test_whitespace_only_password_newlines(self):
        """Test that password with newlines passes validation."""
        assert validate_password_present("\n\n") is True
    
    def test_whitespace_only_password_mixed(self):
        """Test that password with mixed whitespace passes validation."""
        assert validate_password_present(" \t\n ") is True
    
    def test_password_with_leading_whitespace(self):
        """Test that password with leading whitespace passes validation."""
        assert validate_password_present("  password") is True
    
    def test_password_with_trailing_whitespace(self):
        """Test that password with trailing whitespace passes validation."""
        assert validate_password_present("password  ") is True


class TestValidateLoginData:
    """Tests for complete login data validation."""
    
    def test_valid_login_data(self):
        """Test that valid email and password pass validation."""
        # Should not raise any exception
        validate_login_data("user@example.com", "password123")
    
    def test_invalid_email_fails_first(self):
        """Test that invalid email is caught before password validation."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_login_data("invalid-email", "password123")
    
    def test_empty_password_after_valid_email(self):
        """Test that empty password is caught after email validation."""
        with pytest.raises(ValidationError, match="Password must be a non-empty string"):
            validate_login_data("user@example.com", "")
    
    def test_both_invalid(self):
        """Test that email validation fails first when both are invalid."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_login_data("invalid-email", "")
