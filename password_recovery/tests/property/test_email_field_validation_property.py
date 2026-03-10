"""
Property-based tests for email field validation.

Feature: password-recovery
Property 13: Email Field Validation

**Validates: Requirements 7.1, 7.2**

For any /forgot-password request, if the email field is missing or not in a valid 
email format, the system should reject the request with a 400 status code and 
descriptive error message.
"""

import pytest
from hypothesis import given, strategies as st, settings
from password_recovery.input_validator import InputValidator


# Strategy for generating valid emails matching our simplified regex
# Pattern: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
@st.composite
def valid_simple_emails(draw):
    """Generate email addresses that match our simplified email regex."""
    # Local part: [a-zA-Z0-9._%+-]+
    local_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+-'
    local_part = draw(st.text(alphabet=local_chars, min_size=1, max_size=30))
    
    # Domain part: [a-zA-Z0-9.-]+
    domain_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-'
    domain_part = draw(st.text(alphabet=domain_chars, min_size=1, max_size=30))
    
    # TLD: [a-zA-Z]{2,}
    tld_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    tld = draw(st.text(alphabet=tld_chars, min_size=2, max_size=10))
    
    return f"{local_part}@{domain_part}.{tld}"


# Strategy for generating invalid email formats
@st.composite
def invalid_emails(draw):
    """Generate strings that are not valid email addresses."""
    choice = draw(st.integers(min_value=0, max_value=5))
    
    if choice == 0:
        # Missing @ symbol
        return draw(st.text(alphabet=st.characters(blacklist_characters='@'), min_size=1, max_size=50))
    elif choice == 1:
        # Multiple @ symbols
        local = draw(st.text(min_size=1, max_size=20))
        domain = draw(st.text(min_size=1, max_size=20))
        return f"{local}@@{domain}"
    elif choice == 2:
        # Missing domain
        local = draw(st.text(min_size=1, max_size=20))
        return f"{local}@"
    elif choice == 3:
        # Missing local part
        domain = draw(st.text(min_size=1, max_size=20))
        return f"@{domain}"
    elif choice == 4:
        # Missing TLD
        local = draw(st.text(min_size=1, max_size=20))
        domain = draw(st.text(alphabet=st.characters(blacklist_characters='.'), min_size=1, max_size=20))
        return f"{local}@{domain}"
    else:
        # Empty string or whitespace only
        return draw(st.text(alphabet=' \t\n', max_size=10))


class TestEmailFieldValidationProperty:
    """Property-based tests for email field validation."""
    
    @given(valid_simple_emails())
    @settings(max_examples=100)
    def test_valid_email_format_accepted(self, email):
        """
        Property: Valid email formats should be accepted.
        
        For any valid email address (matching our simplified regex), the validator 
        should accept it and return the normalized (lowercase, trimmed) version.
        """
        validator = InputValidator()
        is_valid, normalized_email, error = validator.validate_forgot_password_input({"email": email})
        
        assert is_valid is True, f"Valid email {email} was rejected: {error}"
        assert normalized_email is not None
        assert error is None
        # Email should be normalized to lowercase
        assert normalized_email == email.strip().lower()
    
    @given(invalid_emails())
    @settings(max_examples=100)
    def test_invalid_email_format_rejected(self, invalid_email):
        """
        Property: Invalid email formats should be rejected with descriptive error.
        
        For any string that is not a valid email format, the validator should
        reject it with an appropriate error message.
        """
        validator = InputValidator()
        is_valid, normalized_email, error = validator.validate_forgot_password_input({"email": invalid_email})
        
        # Should be rejected
        assert is_valid is False, f"Invalid email {invalid_email} was accepted"
        assert normalized_email is None
        assert error is not None
        # Error message should be descriptive
        assert len(error) > 0
        assert isinstance(error, str)
    
    @given(st.one_of(
        st.none(),
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    ))
    @settings(max_examples=100)
    def test_missing_email_field_rejected(self, non_email_value):
        """
        Property: Requests with missing or non-string email field should be rejected.
        
        For any request body that doesn't contain a valid email string field,
        the validator should reject it with an appropriate error message.
        """
        validator = InputValidator()
        
        # Test with missing email field
        is_valid, normalized_email, error = validator.validate_forgot_password_input({})
        assert is_valid is False
        assert normalized_email is None
        assert error is not None
        assert "required" in error.lower() or "missing" in error.lower()
        
        # Test with non-string email value (if not None, as None would be missing)
        if non_email_value is not None:
            is_valid, normalized_email, error = validator.validate_forgot_password_input({"email": non_email_value})
            assert is_valid is False
            assert normalized_email is None
            assert error is not None
    
    @given(valid_simple_emails(), st.text(alphabet=' \t', min_size=0, max_size=10), st.text(alphabet=' \t', min_size=0, max_size=10))
    @settings(max_examples=100)
    def test_email_normalization_with_whitespace(self, email, prefix_whitespace, suffix_whitespace):
        """
        Property: Emails with surrounding whitespace should be normalized.
        
        For any valid email with surrounding whitespace, the validator should
        accept it and return the trimmed, lowercase version.
        """
        validator = InputValidator()
        email_with_whitespace = f"{prefix_whitespace}{email}{suffix_whitespace}"
        
        is_valid, normalized_email, error = validator.validate_forgot_password_input({"email": email_with_whitespace})
        
        assert is_valid is True, f"Email with whitespace was rejected: {error}"
        assert normalized_email == email.strip().lower()
        assert error is None
    
    @given(st.one_of(
        st.none(),
        st.integers(),
        st.floats(),
        st.lists(st.text()),
        st.text()
    ))
    @settings(max_examples=100)
    def test_non_dict_body_rejected(self, non_dict_body):
        """
        Property: Non-dictionary request bodies should be rejected.
        
        For any request body that is not a dictionary, the validator should
        reject it with an appropriate error message.
        """
        validator = InputValidator()
        is_valid, normalized_email, error = validator.validate_forgot_password_input(non_dict_body)
        
        assert is_valid is False
        assert normalized_email is None
        assert error is not None
        assert "format" in error.lower() or "invalid" in error.lower()
