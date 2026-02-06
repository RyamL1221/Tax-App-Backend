"""
Unit tests for 1099-DIV required field validation.

These tests verify that the required fields for Form 1099-DIV are properly
validated and that error messages are clear and helpful.

Feature: update-1099-div-comprehensive-schema
Task 6.3: Update required field validation

**Validates: Requirements 1.9, 2.9, 2.10, 5.3**
"""

import pytest
from tax_document_generation.input_validator import (
    validate_form_data,
    FORM_1099_DIV_REQUIRED_FIELDS
)
from tax_document_generation.exceptions import ValidationError


class Test1099DivRequiredFieldValidation:
    """Unit tests for 1099-DIV required field validation."""
    
    def test_required_fields_are_correctly_defined(self):
        """
        Verify that the required fields for 1099-DIV are correctly defined.
        
        **Validates: Requirements 1.9, 2.9, 2.10**
        
        According to the spec, the following fields must be required:
        - payerTIN
        - recipientTIN
        - recipientName
        - payerName (also required)
        - totalOrdinaryDividends (also required)
        """
        required_fields = set(FORM_1099_DIV_REQUIRED_FIELDS.keys())
        
        # Verify the critical required fields are present
        assert 'payerTIN' in required_fields, "payerTIN must be required"
        assert 'recipientTIN' in required_fields, "recipientTIN must be required"
        assert 'recipientName' in required_fields, "recipientName must be required"
        
        # Also verify other required fields
        assert 'payerName' in required_fields, "payerName must be required"
        assert 'totalOrdinaryDividends' in required_fields, "totalOrdinaryDividends must be required"
    
    def test_missing_payer_tin_raises_clear_error(self):
        """
        Verify that missing payerTIN raises a clear validation error.
        
        **Validates: Requirements 1.9, 5.3**
        """
        form_data = {
            'payerName': 'Example Corporation',
            # 'payerTIN': '12-3456789',  # Missing
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        error_message = str(exc_info.value)
        
        # Verify error message is clear
        assert 'Missing required field' in error_message or 'missing required field' in error_message.lower()
        assert 'payerTIN' in error_message, "Error message should mention the missing field name"
    
    def test_missing_recipient_tin_raises_clear_error(self):
        """
        Verify that missing recipientTIN raises a clear validation error.
        
        **Validates: Requirements 2.9, 5.3**
        """
        form_data = {
            'payerName': 'Example Corporation',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            # 'recipientTIN': '123-45-6789',  # Missing
            'totalOrdinaryDividends': 1000.00
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        error_message = str(exc_info.value)
        
        # Verify error message is clear
        assert 'Missing required field' in error_message or 'missing required field' in error_message.lower()
        assert 'recipientTIN' in error_message, "Error message should mention the missing field name"
    
    def test_missing_recipient_name_raises_clear_error(self):
        """
        Verify that missing recipientName raises a clear validation error.
        
        **Validates: Requirements 2.10, 5.3**
        """
        form_data = {
            'payerName': 'Example Corporation',
            'payerTIN': '12-3456789',
            # 'recipientName': 'John Doe',  # Missing
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        error_message = str(exc_info.value)
        
        # Verify error message is clear
        assert 'Missing required field' in error_message or 'missing required field' in error_message.lower()
        assert 'recipientName' in error_message, "Error message should mention the missing field name"
    
    def test_missing_payer_name_raises_clear_error(self):
        """
        Verify that missing payerName raises a clear validation error.
        
        **Validates: Requirements 1.9, 5.3**
        """
        form_data = {
            # 'payerName': 'Example Corporation',  # Missing
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        error_message = str(exc_info.value)
        
        # Verify error message is clear
        assert 'Missing required field' in error_message or 'missing required field' in error_message.lower()
        assert 'payerName' in error_message, "Error message should mention the missing field name"
    
    def test_missing_total_ordinary_dividends_raises_clear_error(self):
        """
        Verify that missing totalOrdinaryDividends raises a clear validation error.
        
        **Validates: Requirements 5.3**
        """
        form_data = {
            'payerName': 'Example Corporation',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            # 'totalOrdinaryDividends': 1000.00  # Missing
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        error_message = str(exc_info.value)
        
        # Verify error message is clear
        assert 'Missing required field' in error_message or 'missing required field' in error_message.lower()
        assert 'totalOrdinaryDividends' in error_message, "Error message should mention the missing field name"
    
    def test_all_required_fields_present_passes_validation(self):
        """
        Verify that form data with all required fields passes validation.
        
        **Validates: Requirements 1.9, 2.9, 2.10, 5.3**
        """
        form_data = {
            'payerName': 'Example Corporation',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
    
    def test_multiple_missing_fields_raises_clear_error(self):
        """
        Verify that multiple missing required fields raise a clear error.
        
        **Validates: Requirements 5.3**
        """
        form_data = {
            'payerName': 'Example Corporation',
            # Missing: payerTIN, recipientName, recipientTIN, totalOrdinaryDividends
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)
        
        error_message = str(exc_info.value)
        
        # Verify error message is clear
        assert 'Missing required field' in error_message or 'missing required field' in error_message.lower()
        
        # The error should mention at least one of the missing fields
        # (implementation may report first missing field or all of them)
        missing_fields = ['payerTIN', 'recipientTIN', 'recipientName', 'totalOrdinaryDividends']
        assert any(field in error_message for field in missing_fields), \
            "Error message should mention at least one missing field"
    
    def test_optional_fields_can_be_omitted(self):
        """
        Verify that optional fields can be omitted without causing validation errors.
        
        **Validates: Requirements 5.3**
        """
        form_data = {
            'payerName': 'Example Corporation',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '123-45-6789',
            'totalOrdinaryDividends': 1000.00
            # Optional fields like payerStreetAddress, qualifiedDividends, etc. are omitted
        }
        
        # Should not raise any exception
        validate_form_data('1099-DIV', form_data)
    
    def test_error_message_format_is_consistent(self):
        """
        Verify that error messages follow a consistent format.
        
        **Validates: Requirements 5.3**
        """
        # Test with different missing fields to verify consistent format
        test_cases = [
            {'field_to_omit': 'payerTIN', 'other_fields': {
                'payerName': 'Example Corporation',
                'recipientName': 'John Doe',
                'recipientTIN': '123-45-6789',
                'totalOrdinaryDividends': 1000.00
            }},
            {'field_to_omit': 'recipientName', 'other_fields': {
                'payerName': 'Example Corporation',
                'payerTIN': '12-3456789',
                'recipientTIN': '123-45-6789',
                'totalOrdinaryDividends': 1000.00
            }}
        ]
        
        error_messages = []
        for test_case in test_cases:
            with pytest.raises(ValidationError) as exc_info:
                validate_form_data('1099-DIV', test_case['other_fields'])
            error_messages.append(str(exc_info.value))
        
        # All error messages should start with similar text
        for msg in error_messages:
            assert 'Missing required field' in msg or 'missing required field' in msg.lower(), \
                f"Error message format should be consistent: {msg}"
