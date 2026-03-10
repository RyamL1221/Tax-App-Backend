"""
Unit tests for InputValidator class.

Tests input validation logic for forgot-password and reset-password endpoints.
"""

import os
import pytest
import sys

# Import the class to test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from password_recovery.input_validator import InputValidator


class TestValidateForgotPasswordInput:
    """Tests for validate_forgot_password_input method."""
    
    def test_returns_tuple_with_three_elements(self):
        """Test that validate_forgot_password_input returns a tuple with 3 elements."""
        validator = InputValidator()
        result = validator.validate_forgot_password_input({"email": "user@example.com"})
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        
        is_valid, email, error = result
        assert isinstance(is_valid, bool)
        assert email is None or isinstance(email, str)
        assert error is None or isinstance(error, str)
    
    def test_valid_email_returns_true(self):
        """Test that a valid email returns True with normalized email."""
        validator = InputValidator()
        
        is_valid, email, error = validator.validate_forgot_password_input({
            "email": "user@example.com"
        })
        
        assert is_valid is True
        assert email == "user@example.com"
        assert error is None
    
    def test_email_is_normalized_lowercase(self):
        """Test that email is converted to lowercase."""
        validator = InputValidator()
        
        is_valid, email, error = validator.validate_forgot_password_input({
            "email": "User@Example.COM"
        })
        
        assert is_valid is True
        assert email == "user@example.com"
        assert error is None
    
    def test_email_is_trimmed(self):
        """Test that email whitespace is trimmed."""
        validator = InputValidator()
        
        is_valid, email, error = validator.validate_forgot_password_input({
            "email": "  user@example.com  "
        })
        
        assert is_valid is True
        assert email == "user@example.com"
        assert error is None
    
    def test_missing_email_field_returns_false(self):
        """Test that missing email field returns False."""
        validator = InputValidator()
        
        is_valid, email, error = validator.validate_forgot_password_input({})
        
        assert is_valid is False
        assert email is None
        assert error is not None
        assert "required" in error.lower()
    
    def test_empty_email_returns_false(self):
        """Test that empty email returns False."""
        validator = InputValidator()
        
        is_valid, email, error = validator.validate_forgot_password_input({
            "email": ""
        })
        
        assert is_valid is False
        assert email is None
        assert error is not None
        assert "required" in error.lower()
    
    def test_whitespace_only_email_returns_false(self):
        """Test that whitespace-only email returns False."""
        validator = InputValidator()
        
        is_valid, email, error = validator.validate_forgot_password_input({
            "email": "   "
        })
        
        assert is_valid is False
        assert email is None
        assert error is not None
        assert "required" in error.lower()
    
    def test_invalid_email_format_returns_false(self):
        """Test that invalid email format returns False."""
        validator = InputValidator()
        
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user@domain",
            "user @example.com",
            "user@exam ple.com",
            "user@@example.com",
        ]
        
        for invalid_email in invalid_emails:
            is_valid, email, error = validator.validate_forgot_password_input({
                "email": invalid_email
            })
            
            assert is_valid is False, f"Email '{invalid_email}' should be invalid"
            assert email is None
            assert error is not None
            assert "valid email" in error.lower()
    
    def test_valid_email_formats(self):
        """Test various valid email formats."""
        validator = InputValidator()
        
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user_name@example.com",
            "user123@example.com",
            "user@subdomain.example.com",
            "user@example.co.uk",
        ]
        
        for valid_email in valid_emails:
            is_valid, email, error = validator.validate_forgot_password_input({
                "email": valid_email
            })
            
            assert is_valid is True, f"Email '{valid_email}' should be valid"
            assert email == valid_email.lower()
            assert error is None
    
    def test_non_dict_body_returns_false(self):
        """Test that non-dictionary body returns False."""
        validator = InputValidator()
        
        is_valid, email, error = validator.validate_forgot_password_input("not a dict")
        
        assert is_valid is False
        assert email is None
        assert error is not None
    
    def test_non_string_email_returns_false(self):
        """Test that non-string email returns False."""
        validator = InputValidator()
        
        is_valid, email, error = validator.validate_forgot_password_input({
            "email": 123
        })
        
        assert is_valid is False
        assert email is None
        assert error is not None


class TestValidateResetPasswordInput:
    """Tests for validate_reset_password_input method."""
    
    def test_returns_tuple_with_four_elements(self):
        """Test that validate_reset_password_input returns a tuple with 4 elements."""
        validator = InputValidator()
        result = validator.validate_reset_password_input({
            "token": "abc123",
            "new_password": "SecurePass123!"
        })
        
        assert isinstance(result, tuple)
        assert len(result) == 4
        
        is_valid, token, password, error = result
        assert isinstance(is_valid, bool)
        assert token is None or isinstance(token, str)
        assert password is None or isinstance(password, str)
        assert error is None or isinstance(error, str)
    
    def test_valid_input_returns_true(self):
        """Test that valid input returns True."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "abc123xyz",
            "new_password": "SecurePass123!"
        })
        
        assert is_valid is True
        assert token == "abc123xyz"
        assert password == "SecurePass123!"
        assert error is None
    
    def test_token_is_trimmed(self):
        """Test that token whitespace is trimmed."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "  abc123xyz  ",
            "new_password": "SecurePass123!"
        })
        
        assert is_valid is True
        assert token == "abc123xyz"
        assert error is None
    
    def test_missing_token_field_returns_false(self):
        """Test that missing token field returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "new_password": "SecurePass123!"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "token" in error.lower()
        assert "required" in error.lower()
    
    def test_empty_token_returns_false(self):
        """Test that empty token returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "",
            "new_password": "SecurePass123!"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "token" in error.lower()
        assert "required" in error.lower()
    
    def test_whitespace_only_token_returns_false(self):
        """Test that whitespace-only token returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "   ",
            "new_password": "SecurePass123!"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "token" in error.lower()
        assert "required" in error.lower()
    
    def test_missing_password_field_returns_false(self):
        """Test that missing new_password field returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "abc123xyz"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "password" in error.lower()
        assert "required" in error.lower()
    
    def test_password_too_short_returns_false(self):
        """Test that password shorter than 8 characters returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "abc123xyz",
            "new_password": "Short1!"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "8 characters" in error
    
    def test_password_without_uppercase_returns_false(self):
        """Test that password without uppercase returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "abc123xyz",
            "new_password": "lowercase123!"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "uppercase" in error.lower()
    
    def test_password_without_lowercase_returns_false(self):
        """Test that password without lowercase returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "abc123xyz",
            "new_password": "UPPERCASE123!"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "lowercase" in error.lower()
    
    def test_password_without_digit_returns_false(self):
        """Test that password without digit returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "abc123xyz",
            "new_password": "NoDigitsHere!"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "digit" in error.lower()
    
    def test_password_without_special_char_returns_false(self):
        """Test that password without special character returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "abc123xyz",
            "new_password": "NoSpecialChar123"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
        assert "special character" in error.lower()
    
    def test_valid_passwords_with_various_special_chars(self):
        """Test that passwords with various special characters are valid."""
        validator = InputValidator()
        
        valid_passwords = [
            "Password123!",
            "Password123@",
            "Password123#",
            "Password123$",
            "Password123%",
            "Password123^",
            "Password123&",
            "Password123*",
            "Password123(",
            "Password123)",
            "Password123-",
            "Password123_",
            "Password123=",
            "Password123+",
            "Password123[",
            "Password123]",
            "Password123{",
            "Password123}",
            "Password123|",
            "Password123\\",
            "Password123:",
            "Password123;",
            "Password123'",
            "Password123\"",
            "Password123<",
            "Password123>",
            "Password123,",
            "Password123.",
            "Password123?",
            "Password123/",
            "Password123~",
            "Password123`",
        ]
        
        for valid_password in valid_passwords:
            is_valid, token, password, error = validator.validate_reset_password_input({
                "token": "abc123xyz",
                "new_password": valid_password
            })
            
            assert is_valid is True, f"Password '{valid_password}' should be valid"
            assert token == "abc123xyz"
            assert password == valid_password
            assert error is None
    
    def test_non_dict_body_returns_false(self):
        """Test that non-dictionary body returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input("not a dict")
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
    
    def test_non_string_token_returns_false(self):
        """Test that non-string token returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": 123,
            "new_password": "SecurePass123!"
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
    
    def test_non_string_password_returns_false(self):
        """Test that non-string password returns False."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "abc123xyz",
            "new_password": 123
        })
        
        assert is_valid is False
        assert token is None
        assert password is None
        assert error is not None
    
    def test_password_exactly_8_chars_is_valid(self):
        """Test that password with exactly 8 characters is valid."""
        validator = InputValidator()
        
        is_valid, token, password, error = validator.validate_reset_password_input({
            "token": "abc123xyz",
            "new_password": "Pass123!"
        })
        
        assert is_valid is True
        assert token == "abc123xyz"
        assert password == "Pass123!"
        assert error is None
    
    def test_all_password_requirements_checked(self):
        """Test that all password requirements are checked."""
        validator = InputValidator()
        
        # Test each requirement individually
        test_cases = [
            ("Short1!", "8 characters"),  # Too short
            ("lowercase123!", "uppercase"),  # No uppercase
            ("UPPERCASE123!", "lowercase"),  # No lowercase
            ("NoDigitsHere!", "digit"),  # No digit
            ("NoSpecialChar123", "special character"),  # No special char
        ]
        
        for invalid_password, expected_error_keyword in test_cases:
            is_valid, token, password, error = validator.validate_reset_password_input({
                "token": "abc123xyz",
                "new_password": invalid_password
            })
            
            assert is_valid is False, f"Password '{invalid_password}' should be invalid"
            assert token is None
            assert password is None
            assert error is not None
            assert expected_error_keyword.lower() in error.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
