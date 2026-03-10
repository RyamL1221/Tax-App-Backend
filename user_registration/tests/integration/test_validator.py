"""
Unit tests for the validator module.

Tests specific examples and edge cases for email, password, and name validation.
"""

import pytest
from user_registration.validator import (
    ValidationError,
    validate_email,
    validate_password_strength,
    validate_name,
    validate_registration_data
)


class TestValidateEmail:
    """Tests for email validation."""
    
    def test_valid_email(self):
        """Test that valid email formats are accepted."""
        assert validate_email("user@example.com") is True
        assert validate_email("test.user@example.co.uk") is True
        assert validate_email("user+tag@example.com") is True
    
    def test_invalid_email_no_at_symbol(self):
        """Test that email without @ symbol is rejected."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("userexample.com")
    
    def test_invalid_email_no_domain(self):
        """Test that email without domain is rejected."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@")
    
    def test_invalid_email_no_local_part(self):
        """Test that email without local part is rejected."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("@example.com")
    
    def test_empty_email(self):
        """Test that empty email is rejected."""
        with pytest.raises(ValidationError, match="Email must be a non-empty string"):
            validate_email("")
    
    def test_none_email(self):
        """Test that None email is rejected."""
        with pytest.raises(ValidationError, match="Email must be a non-empty string"):
            validate_email(None)
    
    # Additional edge case tests for task 2.5
    def test_invalid_email_multiple_at_symbols(self):
        """Test that email with multiple @ symbols is rejected."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@@example.com")
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@domain@example.com")
    
    def test_invalid_email_no_domain_extension(self):
        """Test that email without domain extension is rejected."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@domain")
    
    def test_invalid_email_special_characters_in_domain(self):
        """Test that email with invalid special characters in domain is rejected."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@domain!.com")
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@domain#test.com")
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@domain$.com")
    
    def test_invalid_email_spaces(self):
        """Test that email with spaces is rejected."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user name@example.com")
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@example .com")
    
    def test_invalid_email_starts_with_dot(self):
        """Test that email starting with dot is rejected."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email(".user@example.com")
    
    def test_invalid_email_ends_with_dot(self):
        """Test that email ending with dot before @ is rejected."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user.@example.com")
    
    def test_invalid_email_consecutive_dots(self):
        """Test that email with consecutive dots is rejected."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user..name@example.com")


class TestValidatePasswordStrength:
    """Tests for password strength validation."""
    
    def test_valid_password(self):
        """Test that password meeting all requirements is accepted."""
        assert validate_password_strength("SecurePass123!") is True
        assert validate_password_strength("Abcd1234!@#$") is True
    
    def test_password_too_short(self):
        """Test that password with less than 8 characters is rejected."""
        with pytest.raises(ValidationError, match="at least 8 characters"):
            validate_password_strength("Abc123!")
    
    def test_password_missing_uppercase(self):
        """Test that password without uppercase letter is rejected."""
        with pytest.raises(ValidationError, match="at least one uppercase letter"):
            validate_password_strength("password123!")
    
    def test_password_missing_lowercase(self):
        """Test that password without lowercase letter is rejected."""
        with pytest.raises(ValidationError, match="at least one lowercase letter"):
            validate_password_strength("PASSWORD123!")
    
    def test_password_missing_digit(self):
        """Test that password without digit is rejected."""
        with pytest.raises(ValidationError, match="at least one digit"):
            validate_password_strength("PasswordABC!")
    
    def test_password_missing_special_character(self):
        """Test that password without special character is rejected."""
        with pytest.raises(ValidationError, match="at least one special character"):
            validate_password_strength("Password123")
    
    def test_empty_password(self):
        """Test that empty password is rejected."""
        with pytest.raises(ValidationError, match="Password must be a non-empty string"):
            validate_password_strength("")
    
    def test_none_password(self):
        """Test that None password is rejected."""
        with pytest.raises(ValidationError, match="Password must be a non-empty string"):
            validate_password_strength(None)
    
    # Additional edge case tests for task 2.5
    def test_password_exactly_8_chars_valid(self):
        """Test that password with exactly 8 characters meeting all requirements is accepted."""
        assert validate_password_strength("Abcd123!") is True
    
    def test_password_exactly_8_chars_missing_uppercase(self):
        """Test that 8-character password missing uppercase is rejected."""
        with pytest.raises(ValidationError, match="at least one uppercase letter"):
            validate_password_strength("abcd123!")
    
    def test_password_exactly_8_chars_missing_lowercase(self):
        """Test that 8-character password missing lowercase is rejected."""
        with pytest.raises(ValidationError, match="at least one lowercase letter"):
            validate_password_strength("ABCD123!")
    
    def test_password_exactly_8_chars_missing_digit(self):
        """Test that 8-character password missing digit is rejected."""
        with pytest.raises(ValidationError, match="at least one digit"):
            validate_password_strength("Abcdefg!")
    
    def test_password_exactly_8_chars_missing_special(self):
        """Test that 8-character password missing special character is rejected."""
        with pytest.raises(ValidationError, match="at least one special character"):
            validate_password_strength("Abcd1234")
    
    def test_password_only_uppercase_letters(self):
        """Test that password with only uppercase letters is rejected."""
        with pytest.raises(ValidationError, match="at least one lowercase letter"):
            validate_password_strength("ABCDEFGHIJ")
    
    def test_password_only_lowercase_letters(self):
        """Test that password with only lowercase letters is rejected."""
        with pytest.raises(ValidationError, match="at least one uppercase letter"):
            validate_password_strength("abcdefghij")
    
    def test_password_only_digits(self):
        """Test that password with only digits is rejected."""
        with pytest.raises(ValidationError, match="at least one uppercase letter"):
            validate_password_strength("1234567890")
    
    def test_password_only_special_characters(self):
        """Test that password with only special characters is rejected."""
        with pytest.raises(ValidationError, match="at least one uppercase letter"):
            validate_password_strength("!@#$%^&*()")
    
    def test_password_uppercase_lowercase_only(self):
        """Test that password with only uppercase and lowercase is rejected."""
        with pytest.raises(ValidationError, match="at least one digit"):
            validate_password_strength("AbCdEfGhIj")
    
    def test_password_uppercase_digit_only(self):
        """Test that password with only uppercase and digits is rejected."""
        with pytest.raises(ValidationError, match="at least one lowercase letter"):
            validate_password_strength("ABCD1234")
    
    def test_password_lowercase_digit_only(self):
        """Test that password with only lowercase and digits is rejected."""
        with pytest.raises(ValidationError, match="at least one uppercase letter"):
            validate_password_strength("abcd1234")
    
    def test_password_uppercase_special_only(self):
        """Test that password with only uppercase and special characters is rejected."""
        with pytest.raises(ValidationError, match="at least one lowercase letter"):
            validate_password_strength("ABCD!@#$")
    
    def test_password_lowercase_special_only(self):
        """Test that password with only lowercase and special characters is rejected."""
        with pytest.raises(ValidationError, match="at least one uppercase letter"):
            validate_password_strength("abcd!@#$")
    
    def test_password_digit_special_only(self):
        """Test that password with only digits and special characters is rejected."""
        with pytest.raises(ValidationError, match="at least one uppercase letter"):
            validate_password_strength("1234!@#$")
    
    def test_password_various_special_characters(self):
        """Test that password with various special characters is accepted."""
        assert validate_password_strength("Pass123!@#") is True
        assert validate_password_strength("Pass123$%^") is True
        assert validate_password_strength("Pass123&*()") is True
        assert validate_password_strength("Pass123-_=+") is True
        assert validate_password_strength("Pass123[]{}") is True
        assert validate_password_strength("Pass123|\\;:") is True
        assert validate_password_strength("Pass123'\",.<>") is True
        assert validate_password_strength("Pass123?/~`") is True


class TestValidateName:
    """Tests for name validation."""
    
    def test_valid_name(self):
        """Test that valid names are accepted."""
        assert validate_name("John Doe") is True
        assert validate_name("Alice") is True
        assert validate_name("  Bob  ") is True  # Whitespace is trimmed
    
    def test_empty_name(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("")
    
    def test_whitespace_only_name(self):
        """Test that whitespace-only name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("   ")
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("\t\n")
    
    def test_none_name(self):
        """Test that None name is rejected."""
        with pytest.raises(ValidationError, match="Name must be a string"):
            validate_name(None)
    
    # Additional edge case tests for task 2.5
    def test_whitespace_only_single_space(self):
        """Test that single space name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name(" ")
    
    def test_whitespace_only_multiple_spaces(self):
        """Test that multiple spaces name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("     ")
    
    def test_whitespace_only_single_tab(self):
        """Test that single tab name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("\t")
    
    def test_whitespace_only_multiple_tabs(self):
        """Test that multiple tabs name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("\t\t\t")
    
    def test_whitespace_only_single_newline(self):
        """Test that single newline name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("\n")
    
    def test_whitespace_only_multiple_newlines(self):
        """Test that multiple newlines name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("\n\n\n")
    
    def test_whitespace_only_carriage_return(self):
        """Test that carriage return name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("\r")
    
    def test_whitespace_only_mixed_whitespace(self):
        """Test that mixed whitespace characters name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name(" \t \n \r ")
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("\t\n\r\t\n\r")
    
    def test_whitespace_only_form_feed(self):
        """Test that form feed name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("\f")
    
    def test_whitespace_only_vertical_tab(self):
        """Test that vertical tab name is rejected."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_name("\v")
    
    def test_name_with_leading_whitespace(self):
        """Test that name with leading whitespace is accepted (whitespace is trimmed)."""
        assert validate_name("   John") is True
        assert validate_name("\tJohn") is True
        assert validate_name("\nJohn") is True
    
    def test_name_with_trailing_whitespace(self):
        """Test that name with trailing whitespace is accepted (whitespace is trimmed)."""
        assert validate_name("John   ") is True
        assert validate_name("John\t") is True
        assert validate_name("John\n") is True
    
    def test_name_with_internal_whitespace(self):
        """Test that name with internal whitespace is accepted."""
        assert validate_name("John Doe") is True
        assert validate_name("Mary Jane Watson") is True
        assert validate_name("Jean-Luc Picard") is True


class TestValidateRegistrationData:
    """Tests for orchestrated validation of all registration data."""
    
    def test_valid_registration_data(self):
        """Test that valid registration data passes all validations."""
        # Should not raise any exception
        validate_registration_data(
            email="user@example.com",
            name="John Doe",
            password="SecurePass123!"
        )
    
    def test_invalid_email_fails_first(self):
        """Test that invalid email is caught first."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_registration_data(
                email="invalid-email",
                name="John Doe",
                password="SecurePass123!"
            )
    
    def test_invalid_name_fails_after_email(self):
        """Test that invalid name is caught after email validation."""
        with pytest.raises(ValidationError, match="non-empty string after trimming"):
            validate_registration_data(
                email="user@example.com",
                name="",
                password="SecurePass123!"
            )
    
    def test_invalid_password_fails_last(self):
        """Test that invalid password is caught after email and name validation."""
        with pytest.raises(ValidationError, match="at least 8 characters"):
            validate_registration_data(
                email="user@example.com",
                name="John Doe",
                password="weak"
            )
