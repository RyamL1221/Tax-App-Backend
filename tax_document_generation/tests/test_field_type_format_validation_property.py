"""
Property-based tests for field type and format validation.

These tests verify that form data with invalid data types or formats is properly
rejected with ValidationError. Each property test runs with a minimum of
100 iterations.

Feature: tax-document-generation
Property 5: Field Type and Format Validation

**Validates: Requirements 2.2**
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from hypothesis.strategies import text, integers, floats, sampled_from, lists, one_of, none
from tax_document_generation.input_validator import validate_form_data, FORM_1040_REQUIRED_FIELDS
from tax_document_generation.exceptions import ValidationError


# Strategy for generating valid SSN format
def ssn_strategy():
    """Generate valid SSN in format XXX-XX-XXXX."""
    return st.builds(
        lambda a, b, c: f"{a:03d}-{b:02d}-{c:04d}",
        st.integers(min_value=0, max_value=999),
        st.integers(min_value=0, max_value=99),
        st.integers(min_value=0, max_value=9999)
    )


# Strategy for generating invalid SSN formats
def invalid_ssn_strategy():
    """Generate invalid SSN formats."""
    return one_of(
        # No dashes
        st.builds(
            lambda n: f"{n:09d}",
            st.integers(min_value=0, max_value=999999999)
        ),
        # Wrong pattern (XX-XXX-XXXX)
        st.builds(
            lambda a, b, c: f"{a:02d}-{b:03d}-{c:04d}",
            st.integers(min_value=0, max_value=99),
            st.integers(min_value=0, max_value=999),
            st.integers(min_value=0, max_value=9999)
        ),
        # Letters instead of numbers
        text(min_size=11, max_size=11, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ-'),
        # Too short
        text(min_size=1, max_size=10, alphabet='0123456789-'),
        # Too long
        text(min_size=12, max_size=20, alphabet='0123456789-'),
        # Empty string
        st.just(''),
        # Only dashes
        st.just('---'),
        # Partial format
        st.just('123-45'),
        st.just('123-45-'),
        st.just('-45-6789'),
    )


# Strategy for generating valid filing statuses
filing_status_strategy = sampled_from([
    'single',
    'married_filing_jointly',
    'married_filing_separately',
    'head_of_household',
    'qualifying_widow'
])


# Strategy for generating invalid filing statuses
invalid_filing_status_strategy = text(
    min_size=1,
    max_size=50
).filter(lambda s: s not in [
    'single',
    'married_filing_jointly',
    'married_filing_separately',
    'head_of_household',
    'qualifying_widow'
])


# Strategy for generating valid names (non-empty strings)
name_strategy = text(
    min_size=1,
    max_size=100,
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ -\''
).filter(lambda s: s.strip())  # Ensure not just whitespace


# Strategy for generating invalid names (empty or whitespace-only)
invalid_name_strategy = one_of(
    st.just(''),
    st.just(' '),
    st.just('   '),
    st.just('\t'),
    st.just('\n'),
)


# Strategy for generating valid income values
income_strategy = one_of(
    integers(min_value=0, max_value=10000000),
    floats(min_value=0.0, max_value=10000000.0, allow_nan=False, allow_infinity=False)
)


# Strategy for generating invalid income values (negative)
invalid_income_value_strategy = one_of(
    integers(max_value=-1),
    floats(max_value=-0.01, allow_nan=False, allow_infinity=False)
)


# Strategy for generating invalid income types (non-numeric)
invalid_income_type_strategy = one_of(
    text(min_size=1, max_size=20),  # String
    lists(integers()),  # List
    st.builds(dict),  # Dict
    none(),  # None
)


@st.composite
def valid_form_1040_data(draw):
    """
    Generate valid Form 1040 data with all required fields.
    
    Returns:
        dict: Valid form data with all required fields
    """
    return {
        'firstName': draw(name_strategy),
        'lastName': draw(name_strategy),
        'ssn': draw(ssn_strategy()),
        'filingStatus': draw(filing_status_strategy),
        'income': draw(income_strategy)
    }


@st.composite
def form_1040_data_with_invalid_ssn_format(draw):
    """
    Generate Form 1040 data with invalid SSN format.
    
    Returns:
        dict: Form data with invalid SSN format
    """
    form_data = draw(valid_form_1040_data())
    form_data['ssn'] = draw(invalid_ssn_strategy())
    return form_data


@st.composite
def form_1040_data_with_invalid_ssn_type(draw):
    """
    Generate Form 1040 data with invalid SSN type (non-string).
    
    Returns:
        dict: Form data with invalid SSN type
    """
    form_data = draw(valid_form_1040_data())
    # Use numeric or other non-string type
    form_data['ssn'] = draw(one_of(
        integers(),
        floats(allow_nan=False, allow_infinity=False),
        lists(text()),
        none()
    ))
    return form_data


@st.composite
def form_1040_data_with_invalid_filing_status(draw):
    """
    Generate Form 1040 data with invalid filing status.
    
    Returns:
        dict: Form data with invalid filing status
    """
    form_data = draw(valid_form_1040_data())
    form_data['filingStatus'] = draw(invalid_filing_status_strategy)
    return form_data


@st.composite
def form_1040_data_with_invalid_income_value(draw):
    """
    Generate Form 1040 data with invalid income value (negative).
    
    Returns:
        dict: Form data with negative income
    """
    form_data = draw(valid_form_1040_data())
    form_data['income'] = draw(invalid_income_value_strategy)
    return form_data


@st.composite
def form_1040_data_with_invalid_income_type(draw):
    """
    Generate Form 1040 data with invalid income type (non-numeric).
    
    Returns:
        dict: Form data with non-numeric income
    """
    form_data = draw(valid_form_1040_data())
    form_data['income'] = draw(invalid_income_type_strategy)
    return form_data


@st.composite
def form_1040_data_with_invalid_name(draw):
    """
    Generate Form 1040 data with invalid name (empty or whitespace).
    
    Returns:
        tuple: (form_data dict, field_name that is invalid)
    """
    form_data = draw(valid_form_1040_data())
    # Choose which name field to make invalid
    field_name = draw(sampled_from(['firstName', 'lastName']))
    form_data[field_name] = draw(invalid_name_strategy)
    return form_data, field_name


class TestFieldTypeFormatValidationProperty:
    """Property-based tests for field type and format validation."""
    
    @settings(max_examples=100)
    @given(form_data=form_1040_data_with_invalid_ssn_format())
    def test_invalid_ssn_format_raises_validation_error(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any generation request with SSN in invalid format,
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. SSN format validation is enforced
        2. Invalid SSN formats are rejected
        3. ValidationError is raised with appropriate message
        """
        # Verification: Form data with invalid SSN format should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions SSN format
        error_message = str(exc_info.value).lower()
        assert 'ssn' in error_message, \
            f"Error message should mention SSN: {exc_info.value}"
    
    @settings(max_examples=100)
    @given(form_data=form_1040_data_with_invalid_ssn_type())
    def test_invalid_ssn_type_raises_validation_error(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any generation request with SSN of wrong type (non-string),
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. SSN type validation is enforced
        2. Non-string SSN values are rejected
        3. ValidationError is raised with appropriate message
        """
        # Verification: Form data with invalid SSN type should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions SSN or type
        error_message = str(exc_info.value).lower()
        assert 'ssn' in error_message or 'type' in error_message, \
            f"Error message should mention SSN or type: {exc_info.value}"
    
    @settings(max_examples=100)
    @given(form_data=form_1040_data_with_invalid_filing_status())
    def test_invalid_filing_status_raises_validation_error(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any generation request with invalid filing status,
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. Filing status validation is enforced
        2. Invalid filing status values are rejected
        3. ValidationError is raised with appropriate message
        """
        # Verification: Form data with invalid filing status should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions filing status
        error_message = str(exc_info.value).lower()
        assert 'filing status' in error_message or 'filingstatus' in error_message, \
            f"Error message should mention filing status: {exc_info.value}"
    
    @settings(max_examples=100)
    @given(form_data=form_1040_data_with_invalid_income_value())
    def test_negative_income_raises_validation_error(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any generation request with negative income,
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. Income value validation is enforced
        2. Negative income values are rejected
        3. ValidationError is raised with appropriate message
        """
        # Verification: Form data with negative income should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions income
        error_message = str(exc_info.value).lower()
        assert 'income' in error_message, \
            f"Error message should mention income: {exc_info.value}"
    
    @settings(max_examples=100)
    @given(form_data=form_1040_data_with_invalid_income_type())
    def test_non_numeric_income_raises_validation_error(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any generation request with non-numeric income,
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. Income type validation is enforced
        2. Non-numeric income values are rejected
        3. ValidationError is raised with appropriate message
        """
        # Verification: Form data with non-numeric income should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions income or type
        error_message = str(exc_info.value).lower()
        assert 'income' in error_message or 'type' in error_message, \
            f"Error message should mention income or type: {exc_info.value}"
    
    @settings(max_examples=100)
    @given(data=form_1040_data_with_invalid_name())
    def test_empty_or_whitespace_name_raises_validation_error(self, data):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any generation request with empty or whitespace-only name fields,
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. Name field validation is enforced
        2. Empty or whitespace-only names are rejected
        3. ValidationError is raised with appropriate message
        """
        form_data, invalid_field = data
        
        # Verification: Form data with invalid name should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions the field name
        error_message = str(exc_info.value).lower()
        assert invalid_field.lower() in error_message or 'non-empty' in error_message, \
            f"Error message should mention {invalid_field} or non-empty: {exc_info.value}"
    
    @settings(max_examples=100)
    @given(
        valid_ssn=ssn_strategy(),
        invalid_type=one_of(text(min_size=1), lists(text()), st.builds(dict), none())
    )
    def test_field_type_mismatch_detected(self, valid_ssn, invalid_type):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any field with a type mismatch (expected type vs actual type),
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. Type validation is enforced for all fields
        2. Type mismatches are detected and rejected
        3. ValidationError is raised with appropriate message
        
        Note: This test uses non-numeric types for income field since income
        accepts both int and float.
        """
        # Create form data with a type mismatch
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': valid_ssn,
            'filingStatus': 'single',
            'income': invalid_type  # Wrong type for income (non-numeric)
        }
        
        # Verification: Form data with type mismatch should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions type or the field
        error_message = str(exc_info.value).lower()
        assert 'type' in error_message or 'income' in error_message, \
            f"Error message should mention type or income: {exc_info.value}"
    
    @settings(max_examples=100)
    @given(form_data=valid_form_1040_data())
    def test_valid_types_and_formats_do_not_raise_error(self, form_data):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any form data with valid types and formats,
        the type and format validation should pass (no error raised).
        
        This test verifies that:
        1. Valid data types are accepted
        2. Valid formats are accepted
        3. No ValidationError is raised for valid data
        """
        # Verification: Form data with valid types and formats should be accepted
        # This should not raise any exception
        validate_form_data('1040', form_data)
    
    @settings(max_examples=100)
    @given(
        first_name=name_strategy,
        last_name=name_strategy,
        ssn=ssn_strategy(),
        filing_status=filing_status_strategy,
        income=income_strategy
    )
    def test_all_valid_field_combinations_accepted(
        self, first_name, last_name, ssn, filing_status, income
    ):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any combination of valid field values,
        the validation should pass without errors.
        
        This test verifies that:
        1. All valid combinations of field values are accepted
        2. The validator correctly identifies valid data
        3. No false positives in validation
        """
        form_data = {
            'firstName': first_name,
            'lastName': last_name,
            'ssn': ssn,
            'filingStatus': filing_status,
            'income': income
        }
        
        # Verification: Valid form data should be accepted
        validate_form_data('1040', form_data)
    
    @settings(max_examples=100)
    @given(
        invalid_ssn=text(min_size=1, max_size=50).filter(
            lambda s: not (len(s) == 11 and s[3] == '-' and s[6] == '-' and 
                          s[:3].isdigit() and s[4:6].isdigit() and s[7:].isdigit())
        )
    )
    def test_any_non_conforming_ssn_rejected(self, invalid_ssn):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any SSN that doesn't conform to XXX-XX-XXXX format,
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. SSN format validation is strict
        2. Any deviation from the expected format is rejected
        3. ValidationError is raised for non-conforming SSNs
        """
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': invalid_ssn,
            'filingStatus': 'single',
            'income': 75000
        }
        
        # Verification: Form data with non-conforming SSN should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions SSN
        error_message = str(exc_info.value).lower()
        assert 'ssn' in error_message, \
            f"Error message should mention SSN: {exc_info.value}"
    
    @settings(max_examples=100)
    @given(
        income_str=text(min_size=1, max_size=20, alphabet='0123456789.')
    )
    def test_string_income_rejected_even_if_numeric_string(self, income_str):
        """
        **Validates: Requirements 2.2**
        Feature: tax-document-generation, Property 5: Field Type and Format Validation
        
        For any income value that is a string (even if it looks numeric),
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. Type validation is strict (doesn't accept string representations)
        2. String income values are rejected
        3. ValidationError is raised for string income
        """
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': income_str  # String instead of number
        }
        
        # Verification: Form data with string income should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions income or type
        error_message = str(exc_info.value).lower()
        assert 'income' in error_message or 'type' in error_message, \
            f"Error message should mention income or type: {exc_info.value}"
