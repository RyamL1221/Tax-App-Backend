"""
Unit tests for new field type validation (Task 6.1).

This module tests the validation of new field types added in the
comprehensive schema update:
- State code validation (2-letter codes)
- ZIP code format validation (XXXXX or XXXXX-XXXX)
- Telephone number format validation (flexible formats)

Requirements: 5.1-5.5
"""

import pytest
from exceptions import ValidationError
from input_validator import (
    validate_form_data,
    _validate_state_code,
    _validate_zip_code,
    _validate_phone_number
)


class TestStateCodeValidation:
    """Test state code validation for new fields."""
    
    def test_valid_state_codes(self):
        """Test that valid 2-letter state codes are accepted."""
        valid_codes = ['NY', 'CA', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
        
        for code in valid_codes:
            # Should not raise exception
            _validate_state_code(code)
    
    def test_lowercase_state_codes_rejected(self):
        """Test that lowercase state codes are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            _validate_state_code('ny')
        
        assert 'uppercase' in str(exc_info.value).lower()
    
    def test_invalid_state_codes_rejected(self):
        """Test that invalid state codes are rejected."""
        invalid_codes = ['XX', 'ZZ', 'AB', '12', 'N', 'NYC']
        
        for code in invalid_codes:
            with pytest.raises(ValidationError) as exc_info:
                _validate_state_code(code)
            
            # Error message will vary based on format vs validity
            assert 'state' in str(exc_info.value).lower()
    
    def test_territories_accepted(self):
        """Test that US territories are accepted."""
        territories = ['DC', 'PR', 'VI', 'GU', 'AS', 'MP']
        
        for territory in territories:
            # Should not raise exception
            _validate_state_code(territory)
    
    def test_payer_state_validation_in_form_data(self):
        """Test that payerState field is validated."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00,
            'payerState': 'XX'  # Invalid state code
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        assert 'valid US state/territory code' in str(exc_info.value)
    
    def test_recipient_state_validation_in_form_data(self):
        """Test that recipientState field is validated."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00,
            'recipientState': 'ZZ'  # Invalid state code
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        assert 'valid US state/territory code' in str(exc_info.value)
    
    def test_state2_validation_in_form_data(self):
        """Test that state2 field is validated."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00,
            'state': 'NY',
            'state2': 'invalid'  # Invalid state code
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        assert 'state' in str(exc_info.value).lower()


class TestZipCodeValidation:
    """Test ZIP code validation for new fields."""
    
    def test_valid_5_digit_zip(self):
        """Test that 5-digit ZIP codes are accepted."""
        valid_zips = ['10001', '90210', '60601', '33101', '02101']
        
        for zip_code in valid_zips:
            # Should not raise exception
            _validate_zip_code(zip_code)
    
    def test_valid_9_digit_zip(self):
        """Test that ZIP+4 codes are accepted."""
        valid_zips = ['10001-1234', '90210-5678', '60601-9999']
        
        for zip_code in valid_zips:
            # Should not raise exception
            _validate_zip_code(zip_code)
    
    def test_invalid_zip_formats_rejected(self):
        """Test that invalid ZIP formats are rejected."""
        invalid_zips = [
            '1234',      # Too short
            '123456',    # Too long (no hyphen)
            '10001-',    # Missing +4
            '10001-12',  # +4 too short
            'ABCDE',     # Letters
            '10001 1234' # Space instead of hyphen
        ]
        
        for zip_code in invalid_zips:
            with pytest.raises(ValidationError) as exc_info:
                _validate_zip_code(zip_code)
            
            assert 'ZIP code must be in format' in str(exc_info.value)
    
    def test_payer_zip_validation_in_form_data(self):
        """Test that payerZip field is validated."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00,
            'payerZip': 'ABCDE'  # Invalid ZIP
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        assert 'ZIP code must be in format' in str(exc_info.value)
    
    def test_recipient_zip_validation_in_form_data(self):
        """Test that recipientZip field is validated."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00,
            'recipientZip': '123'  # Invalid ZIP
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        assert 'ZIP code must be in format' in str(exc_info.value)


class TestPhoneNumberValidation:
    """Test telephone number validation for new fields."""
    
    def test_valid_phone_formats(self):
        """Test that various valid phone formats are accepted."""
        valid_phones = [
            '(555) 123-4567',
            '555-123-4567',
            '+1 (555) 123-4567',
            '+1-555-123-4567',
            '+44 20 1234 5678',
            '1234567890',
            '+1 123 456 7890'
        ]
        
        for phone in valid_phones:
            # Should not raise exception
            _validate_phone_number(phone)
    
    def test_phone_with_too_few_digits_rejected(self):
        """Test that phone numbers with fewer than 10 digits are rejected."""
        invalid_phones = [
            '123-4567',      # Only 7 digits
            '(555) 1234',    # Only 7 digits
            '+1 123 4567'    # Only 7 digits
        ]
        
        for phone in invalid_phones:
            with pytest.raises(ValidationError) as exc_info:
                _validate_phone_number(phone)
            
            assert 'at least 10 digits' in str(exc_info.value)
    
    def test_phone_with_invalid_characters_rejected(self):
        """Test that phone numbers with invalid characters are rejected."""
        invalid_phones = [
            '555-123-ABCD',
            '(555) 123-4567 ext 123',
            '555.123.4567',
            '555/123/4567'
        ]
        
        for phone in invalid_phones:
            with pytest.raises(ValidationError) as exc_info:
                _validate_phone_number(phone)
            
            assert 'digits, spaces, hyphens, parentheses' in str(exc_info.value)
    
    def test_payer_telephone_number_validation_in_form_data(self):
        """Test that payerTelephoneNumber field is validated."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00,
            'payerTelephoneNumber': 'invalid'  # Invalid phone
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        assert 'Phone number' in str(exc_info.value)
    
    def test_legacy_payer_phone_field_validation(self):
        """Test that legacy payerPhone field is still validated."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00,
            'payerPhone': '123'  # Invalid phone
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        assert 'Phone number' in str(exc_info.value)


class TestIntegrationWithMultipleNewFields:
    """Test validation with multiple new fields together."""
    
    def test_valid_form_with_all_new_fields(self):
        """Test that a form with all new fields validates successfully."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'payerStreetAddress': '123 Main St',
            'payerCity': 'New York',
            'payerState': 'NY',
            'payerZip': '10001',
            'payerTelephoneNumber': '(555) 123-4567',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'recipientStreetAddress': '456 Oak Ave',
            'recipientCity': 'Los Angeles',
            'recipientState': 'CA',
            'recipientZip': '90001',
            'totalOrdinaryDividends': 1000.00,
            'state': 'NY',
            'state2': 'CA'
        }
        
        # Should not raise exception
        validate_form_data('1099-DIV', form_data)
    
    def test_form_with_zip_plus_4(self):
        """Test that ZIP+4 codes work in complete forms."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'payerZip': '10001-1234',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'recipientZip': '90001-5678',
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise exception
        validate_form_data('1099-DIV', form_data)
    
    def test_form_with_international_phone(self):
        """Test that international phone numbers work."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'payerTelephoneNumber': '+44 20 1234 5678',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise exception
        validate_form_data('1099-DIV', form_data)
    
    def test_form_with_territories(self):
        """Test that US territories work as state codes."""
        form_data = {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'payerState': 'PR',  # Puerto Rico
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'recipientState': 'VI',  # Virgin Islands
            'totalOrdinaryDividends': 1000.00,
            'state': 'GU',  # Guam
            'state2': 'DC'  # District of Columbia
        }
        
        # Should not raise exception
        validate_form_data('1099-DIV', form_data)
