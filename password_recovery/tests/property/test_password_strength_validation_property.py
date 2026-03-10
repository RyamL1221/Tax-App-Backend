"""
Property-based tests for password strength validation.

Feature: password-recovery
Property 15: Password Strength Validation

**Validates: Requirements 7.4**

For any /reset-password request, if the new password does not meet minimum security 
requirements (at least 8 characters, containing uppercase, lowercase, digit, and 
special character), the system should reject the request with a 400 status code.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from password_recovery.input_validator import InputValidator


# Strategy for generating valid strong passwords
@st.composite
def strong_passwords(draw):
    """Generate passwords that meet all strength requirements."""
    # Minimum 8 characters, with at least one of each required type
    length = draw(st.integers(min_value=8, max_value=50))
    
    # Ensure we have at least one of each required character type
    uppercase = draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=1))
    lowercase = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=1))
    digit = draw(st.text(alphabet='0123456789', min_size=1, max_size=1))
    special = draw(st.text(alphabet='!@#$%^&*()_+-=[]{}|;:,.<>?', min_size=1, max_size=1))
    
    # Fill the rest with any printable characters
    remaining_length = length - 4
    if remaining_length > 0:
        filler = draw(st.text(
            alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?',
            min_size=remaining_length,
            max_size=remaining_length
        ))
    else:
        filler = ''
    
    # Combine and shuffle
    chars = list(uppercase + lowercase + digit + special + filler)
    draw(st.randoms()).shuffle(chars)
    return ''.join(chars)


# Strategy for generating weak passwords (missing requirements)
@st.composite
def weak_passwords(draw):
    """Generate passwords that fail at least one strength requirement."""
    choice = draw(st.integers(min_value=0, max_value=4))
    
    if choice == 0:
        # Too short (less than 8 characters)
        return draw(st.text(min_size=0, max_size=7))
    elif choice == 1:
        # Missing uppercase
        length = draw(st.integers(min_value=8, max_value=50))
        lowercase = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=length-2))
        digit = draw(st.text(alphabet='0123456789', min_size=1, max_size=1))
        special = draw(st.text(alphabet='!@#$%^&*()_+-=[]{}|;:,.<>?', min_size=1, max_size=1))
        return lowercase + digit + special
    elif choice == 2:
        # Missing lowercase
        length = draw(st.integers(min_value=8, max_value=50))
        uppercase = draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=length-2))
        digit = draw(st.text(alphabet='0123456789', min_size=1, max_size=1))
        special = draw(st.text(alphabet='!@#$%^&*()_+-=[]{}|;:,.<>?', min_size=1, max_size=1))
        return uppercase + digit + special
    elif choice == 3:
        # Missing digit
        length = draw(st.integers(min_value=8, max_value=50))
        uppercase = draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=1))
        lowercase = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=length-2, max_size=length-2))
        special = draw(st.text(alphabet='!@#$%^&*()_+-=[]{}|;:,.<>?', min_size=1, max_size=1))
        return uppercase + lowercase + special
    else:
        # Missing special character
        length = draw(st.integers(min_value=8, max_value=50))
        uppercase = draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=1))
        lowercase = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=length-2, max_size=length-2))
        digit = draw(st.text(alphabet='0123456789', min_size=1, max_size=1))
        return uppercase + lowercase + digit


class TestPasswordStrengthValidationProperty:
    """Property-based tests for password strength validation."""
    
    @given(strong_passwords())
    @settings(max_examples=100)
    def test_strong_password_accepted(self, password):
        """
        Property: Passwords meeting all strength requirements should be accepted.
        
        For any password with at least 8 characters, containing uppercase, lowercase,
        digit, and special character, the validator should accept it.
        """
        validator = InputValidator()
        is_valid, token, returned_password, error = validator.validate_reset_password_input({
            "token": "valid-token-123",
            "new_password": password
        })
        
        assert is_valid is True, f"Strong password was rejected: {error}"
        assert token == "valid-token-123"
        assert returned_password == password
        assert error is None
    
    @given(weak_passwords())
    @settings(max_examples=100)
    def test_weak_password_rejected(self, password):
        """
        Property: Passwords failing strength requirements should be rejected.
        
        For any password that doesn't meet the minimum requirements, the validator
        should reject it with a descriptive error message.
        """
        validator = InputValidator()
        is_valid, token, returned_password, error = validator.validate_reset_password_input({
            "token": "valid-token-123",
            "new_password": password
        })
        
        assert is_valid is False, f"Weak password was accepted: {password}"
        assert token is None
        assert returned_password is None
        assert error is not None
        # Error should mention password requirements
        assert "password" in error.lower()
    
    @given(st.text(max_size=7))
    @settings(max_examples=100)
    def test_short_password_rejected(self, short_password):
        """
        Property: Passwords shorter than 8 characters should be rejected.
        
        For any password with fewer than 8 characters, the validator should
        reject it with an error mentioning the length requirement.
        """
        validator = InputValidator()
        is_valid, token, returned_password, error = validator.validate_reset_password_input({
            "token": "valid-token-123",
            "new_password": short_password
        })
        
        assert is_valid is False
        assert token is None
        assert returned_password is None
        assert error is not None
        assert "8" in error or "character" in error.lower()
    
    @given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*', min_size=8, max_size=50))
    @settings(max_examples=100)
    def test_password_without_uppercase_rejected(self, base_password):
        """
        Property: Passwords without uppercase letters should be rejected.
        
        For any password without an uppercase letter, the validator should
        reject it with an error mentioning the uppercase requirement.
        """
        # Ensure the password has lowercase, digit, and special char but no uppercase
        # Add these if missing to isolate the uppercase requirement
        password = base_password
        if not any(c.islower() for c in password):
            password += 'a'
        if not any(c.isdigit() for c in password):
            password += '1'
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            password += '!'
        
        # Ensure no uppercase
        assume(not any(c.isupper() for c in password))
        
        validator = InputValidator()
        is_valid, token, returned_password, error = validator.validate_reset_password_input({
            "token": "valid-token-123",
            "new_password": password
        })
        
        assert is_valid is False
        assert token is None
        assert returned_password is None
        assert error is not None
        assert "uppercase" in error.lower()
    
    @given(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*', min_size=8, max_size=50))
    @settings(max_examples=100)
    def test_password_without_lowercase_rejected(self, base_password):
        """
        Property: Passwords without lowercase letters should be rejected.
        
        For any password without a lowercase letter, the validator should
        reject it with an error mentioning the lowercase requirement.
        """
        # Ensure the password has uppercase, digit, and special char but no lowercase
        password = base_password
        if not any(c.isupper() for c in password):
            password += 'A'
        if not any(c.isdigit() for c in password):
            password += '1'
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            password += '!'
        
        # Ensure no lowercase
        assume(not any(c.islower() for c in password))
        
        validator = InputValidator()
        is_valid, token, returned_password, error = validator.validate_reset_password_input({
            "token": "valid-token-123",
            "new_password": password
        })
        
        assert is_valid is False
        assert token is None
        assert returned_password is None
        assert error is not None
        assert "lowercase" in error.lower()
    
    @given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*', min_size=8, max_size=50))
    @settings(max_examples=100)
    def test_password_without_digit_rejected(self, base_password):
        """
        Property: Passwords without digits should be rejected.
        
        For any password without a digit, the validator should
        reject it with an error mentioning the digit requirement.
        """
        # Ensure the password has uppercase, lowercase, and special char but no digit
        password = base_password
        if not any(c.isupper() for c in password):
            password += 'A'
        if not any(c.islower() for c in password):
            password += 'a'
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            password += '!'
        
        # Ensure no digit
        assume(not any(c.isdigit() for c in password))
        
        validator = InputValidator()
        is_valid, token, returned_password, error = validator.validate_reset_password_input({
            "token": "valid-token-123",
            "new_password": password
        })
        
        assert is_valid is False
        assert token is None
        assert returned_password is None
        assert error is not None
        assert "digit" in error.lower()
    
    @given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=8, max_size=50))
    @settings(max_examples=100)
    def test_password_without_special_char_rejected(self, base_password):
        """
        Property: Passwords without special characters should be rejected.
        
        For any password without a special character, the validator should
        reject it with an error mentioning the special character requirement.
        """
        # Ensure the password has uppercase, lowercase, and digit but no special char
        password = base_password
        if not any(c.isupper() for c in password):
            password += 'A'
        if not any(c.islower() for c in password):
            password += 'a'
        if not any(c.isdigit() for c in password):
            password += '1'
        
        validator = InputValidator()
        is_valid, token, returned_password, error = validator.validate_reset_password_input({
            "token": "valid-token-123",
            "new_password": password
        })
        
        assert is_valid is False
        assert token is None
        assert returned_password is None
        assert error is not None
        assert "special" in error.lower()
