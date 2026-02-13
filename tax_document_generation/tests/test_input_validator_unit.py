"""
Unit tests for input validator module.

Tests specific examples and edge cases for form data validation including
required field checking, data type validation, and format validation.
"""

import pytest
from tax_document_generation.input_validator import validate_form_data
from tax_document_generation.exceptions import ValidationError


class TestValidateFormData:
    """Unit tests for validate_form_data function."""
    
    def test_valid_form_1040_data(self):
        """Test that valid Form 1040 data passes validation."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': 75000
        }
        
        # Should not raise any exception
        validate_form_data('1040', form_data)
    
    def test_valid_form_1040_with_float_income(self):
        """Test that Form 1040 with float income passes validation."""
        form_data = {
            'firstName': 'Jane',
            'lastName': 'Smith',
            'ssn': '987-65-4321',
            'filingStatus': 'married_filing_jointly',
            'income': 125000.50
        }
        
        # Should not raise any exception
        validate_form_data('1040', form_data)
    
    def test_missing_required_field_single(self):
        """Test that missing a single required field raises ValidationError."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single'
            # Missing 'income'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        assert 'Missing required field: income' in str(exc_info.value)
    
    def test_missing_multiple_required_fields(self):
        """Test that missing multiple required fields raises ValidationError."""
        form_data = {
            'firstName': 'John'
            # Missing lastName, ssn, filingStatus, income
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        error_msg = str(exc_info.value)
        assert 'Missing required fields:' in error_msg
        assert 'lastName' in error_msg
        assert 'ssn' in error_msg
        assert 'filingStatus' in error_msg
        assert 'income' in error_msg
    
    def test_ssn_without_dashes_accepted(self):
        """Test that SSN without dashes is now accepted (flexible input)."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123456789',  # No dashes - should be accepted
            'filingStatus': 'single',
            'income': 75000
        }
        
        # Should not raise - flexible input formatting accepts both formats
        validate_form_data('1040', form_data)
    
    def test_invalid_ssn_format_wrong_pattern(self):
        """Test that SSN with wrong pattern raises ValidationError."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '12-345-6789',  # Wrong pattern
            'filingStatus': 'single',
            'income': 75000
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        assert 'SSN must be in format XXX-XX-XXXX' in str(exc_info.value)
    
    def test_invalid_ssn_with_letters(self):
        """Test that SSN with letters raises ValidationError."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': 'ABC-DE-FGHI',
            'filingStatus': 'single',
            'income': 75000
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        assert 'SSN must be in format XXX-XX-XXXX' in str(exc_info.value)
    
    def test_invalid_filing_status(self):
        """Test that invalid filing status raises ValidationError."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'invalid_status',
            'income': 75000
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        error_msg = str(exc_info.value)
        assert 'Filing status must be one of:' in error_msg
    
    def test_all_valid_filing_statuses(self):
        """Test that all valid filing statuses pass validation."""
        valid_statuses = [
            'single',
            'married_filing_jointly',
            'married_filing_separately',
            'head_of_household',
            'qualifying_widow'
        ]
        
        for status in valid_statuses:
            form_data = {
                'firstName': 'John',
                'lastName': 'Doe',
                'ssn': '123-45-6789',
                'filingStatus': status,
                'income': 75000
            }
            
            # Should not raise any exception
            validate_form_data('1040', form_data)
    
    def test_negative_income(self):
        """Test that negative income raises ValidationError."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': -5000
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        assert 'non-negative number' in str(exc_info.value)
    
    def test_zero_income(self):
        """Test that zero income is valid."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': 0
        }
        
        # Should not raise any exception
        validate_form_data('1040', form_data)
    
    def test_invalid_income_type_string(self):
        """Test that string income raises ValidationError."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': '75000'  # String instead of number
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        assert "Field 'income' must be of type int or float" in str(exc_info.value)
    
    def test_invalid_ssn_type_number(self):
        """Test that numeric SSN raises ValidationError."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': 123456789,  # Number instead of string
            'filingStatus': 'single',
            'income': 75000
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        assert "Field 'ssn' must be of type str" in str(exc_info.value)
    
    def test_empty_first_name(self):
        """Test that empty firstName raises ValidationError."""
        form_data = {
            'firstName': '',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': 75000
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        assert "Field 'firstName' must be a non-empty string" in str(exc_info.value)
    
    def test_whitespace_only_last_name(self):
        """Test that whitespace-only lastName raises ValidationError."""
        form_data = {
            'firstName': 'John',
            'lastName': '   ',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': 75000
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        assert "Field 'lastName' must be a non-empty string" in str(exc_info.value)
    
    def test_unsupported_document_type(self):
        """Test that unsupported document type raises ValidationError."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': 75000
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('9999', form_data)
        
        assert 'Unsupported document type: 9999' in str(exc_info.value)
    
    def test_form_data_not_dict(self):
        """Test that non-dict form_data raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', 'not a dict')
        
        assert 'Form data must be a dictionary' in str(exc_info.value)
    
    def test_form_data_none(self):
        """Test that None form_data raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', None)
        
        assert 'Form data must be a dictionary' in str(exc_info.value)
    
    def test_extra_fields_allowed(self):
        """Test that extra fields beyond required ones are allowed."""
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': 75000,
            'extraField1': 'value1',
            'extraField2': 123
        }
        
        # Should not raise any exception - extra fields are allowed
        validate_form_data('1040', form_data)
