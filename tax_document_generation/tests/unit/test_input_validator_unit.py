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


class TestOptionalEmptyStringFields:
    """
    Regression tests for empty-string / whitespace-only OPTIONAL fields.

    Frontends commonly submit "" for optional inputs the user left blank
    (e.g. an unused second state). These must be treated as absent rather
    than run through format validation, which would otherwise reject "" for
    state codes, ZIPs, amounts, etc.

    Reported failure this guards against:
        POST /documents/generate with state2="" returned HTTP 400
        "State code must be exactly 2 uppercase letters (e.g., 'NY', 'CA')".

    The empty-string skip must apply to OPTIONAL fields only; required fields
    with empty values must still be rejected.
    """

    def _base_1099_div(self):
        """Minimal valid 1099-DIV payload; mutate one field per test."""
        return {
            'payerName': 'Example Corp',
            'payerTIN': '12-3456789',
            'recipientName': 'John Doe',
            'recipientTIN': '987-65-4321',
            'totalOrdinaryDividends': 1000.00,
        }

    # ------------------------------------------------------------------
    # Empty / whitespace-only optional fields -> treated as absent (accepted)
    # ------------------------------------------------------------------

    def test_optional_state2_empty_string_treated_as_absent(self):
        """state2='' (the exact reported frontend failure) is accepted."""
        form_data = self._base_1099_div()
        form_data['state2'] = ''

        # Should not raise - empty optional field is treated as absent
        validate_form_data('1099-DIV', form_data)

    def test_optional_field_whitespace_only_treated_as_absent(self):
        """state2='   ' (whitespace only) is accepted."""
        form_data = self._base_1099_div()
        form_data['state2'] = '   '

        validate_form_data('1099-DIV', form_data)

    def test_optional_first_state_empty_string_treated_as_absent(self):
        """state='' (first-state field) gets the same treatment as state2."""
        form_data = self._base_1099_div()
        form_data['state'] = ''

        validate_form_data('1099-DIV', form_data)

    def test_optional_payer_recipient_state_empty_string_treated_as_absent(self):
        """payerState='' and recipientState='' are accepted."""
        form_data = self._base_1099_div()
        form_data['payerState'] = ''
        form_data['recipientState'] = ''

        validate_form_data('1099-DIV', form_data)

    def test_optional_payer_zip_empty_string_treated_as_absent(self):
        """payerZip='' is accepted (blank optional ZIP)."""
        form_data = self._base_1099_div()
        form_data['payerZip'] = ''

        validate_form_data('1099-DIV', form_data)

    def test_optional_state_tax_withheld2_empty_string_treated_as_absent(self):
        """stateTaxWithheld2='' is accepted (blank optional amount)."""
        form_data = self._base_1099_div()
        form_data['stateTaxWithheld2'] = ''

        validate_form_data('1099-DIV', form_data)

    def test_complete_second_state_block_accepted(self):
        """A fully populated second-state block is accepted unchanged."""
        form_data = self._base_1099_div()
        form_data['state2'] = 'CA'
        form_data['stateIdentificationNumber2'] = 'CA-67890'
        form_data['stateTaxWithheld2'] = 25.00

        # Should not raise; validate_form_data does not mutate form_data,
        # so the caller's values pass through unchanged.
        validate_form_data('1099-DIV', form_data)
        assert form_data['state2'] == 'CA'
        assert form_data['stateIdentificationNumber2'] == 'CA-67890'
        assert form_data['stateTaxWithheld2'] == 25.00

    # ------------------------------------------------------------------
    # Malformed NON-empty optional values -> still rejected
    # ------------------------------------------------------------------

    def test_optional_state2_lowercase_still_rejected(self):
        """state2='ny' (lowercase, non-empty) is still rejected on format."""
        form_data = self._base_1099_div()
        form_data['state2'] = 'ny'

        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)

        assert 'State code must be exactly 2 uppercase letters' in str(exc_info.value)

    def test_optional_state2_single_char_still_rejected(self):
        """state2='N' (1 char, non-empty) is still rejected on format."""
        form_data = self._base_1099_div()
        form_data['state2'] = 'N'

        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)

        assert 'State code must be exactly 2 uppercase letters' in str(exc_info.value)

    def test_optional_state_tax_withheld2_non_numeric_still_rejected(self):
        """stateTaxWithheld2='abc' (non-numeric, non-empty) is still rejected."""
        form_data = self._base_1099_div()
        form_data['stateTaxWithheld2'] = 'abc'

        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)

        assert "Field 'stateTaxWithheld2' must be a valid number" in str(exc_info.value)

    # ------------------------------------------------------------------
    # Required-field integrity -> empty-string skip is optional-only
    # ------------------------------------------------------------------

    def test_required_field_missing_still_rejected(self):
        """Missing required payerName is still rejected."""
        form_data = self._base_1099_div()
        del form_data['payerName']

        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)

        assert 'Missing required field' in str(exc_info.value)
        assert 'payerName' in str(exc_info.value)

    def test_required_field_empty_string_still_rejected(self):
        """
        Required payerName='' is still rejected (confirms the empty-string
        skip applies to optional fields only, not universally).
        """
        form_data = self._base_1099_div()
        form_data['payerName'] = ''

        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1099-DIV', form_data)

        assert "Field 'payerName' must be a non-empty string" in str(exc_info.value)
