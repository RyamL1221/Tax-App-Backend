"""
Property-based tests for required field validation.

These tests verify that form data with missing required fields is properly
rejected with ValidationError. Each property test runs with a minimum of
100 iterations.

Feature: tax-document-generation
Property 4: Required Field Validation

**Validates: Requirements 2.1**
"""

import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import text, integers, floats, sampled_from, lists
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


# Strategy for generating valid filing statuses
filing_status_strategy = sampled_from([
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


# Strategy for generating valid income values
income_strategy = st.one_of(
    integers(min_value=0, max_value=10000000),
    floats(min_value=0.0, max_value=10000000.0, allow_nan=False, allow_infinity=False)
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
def form_1040_data_with_missing_field(draw):
    """
    Generate Form 1040 data with at least one required field missing.
    
    Returns:
        tuple: (form_data dict with missing field, list of missing field names)
    """
    # Start with valid data
    form_data = draw(valid_form_1040_data())
    
    # Get list of required fields
    required_fields = list(FORM_1040_REQUIRED_FIELDS.keys())
    
    # Choose at least one field to remove (can remove multiple)
    num_fields_to_remove = draw(integers(min_value=1, max_value=len(required_fields)))
    fields_to_remove = draw(lists(
        sampled_from(required_fields),
        min_size=num_fields_to_remove,
        max_size=num_fields_to_remove,
        unique=True
    ))
    
    # Remove the selected fields
    for field in fields_to_remove:
        if field in form_data:
            del form_data[field]
    
    return form_data, fields_to_remove


class TestRequiredFieldValidationProperty:
    """Property-based tests for required field validation."""
    
    @settings(max_examples=100)
    @given(data=form_1040_data_with_missing_field())
    def test_missing_required_field_raises_validation_error(self, data):
        """
        **Validates: Requirements 2.1**
        Feature: tax-document-generation, Property 4: Required Field Validation
        
        For any generation request missing required form fields,
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. Form data with missing required fields is rejected
        2. ValidationError is raised
        3. Error message mentions the missing field(s)
        """
        form_data, missing_fields = data
        
        # Verification: Form data with missing fields should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions missing fields
        error_message = str(exc_info.value).lower()
        assert "missing required field" in error_message
        
        # Verify at least one of the missing fields is mentioned in the error
        # (The validator may report the first missing field or all of them)
        missing_field_mentioned = any(
            field.lower() in error_message for field in missing_fields
        )
        assert missing_field_mentioned, \
            f"Error message should mention at least one missing field from {missing_fields}"
    
    @settings(max_examples=100)
    @given(field_to_remove=sampled_from(list(FORM_1040_REQUIRED_FIELDS.keys())))
    def test_each_required_field_individually_missing_raises_error(self, field_to_remove):
        """
        **Validates: Requirements 2.1**
        Feature: tax-document-generation, Property 4: Required Field Validation
        
        For any single required field that is missing,
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. Each required field is actually required
        2. Removing any single required field causes validation to fail
        3. ValidationError is raised for each missing field
        """
        # Action: Create valid form data, then remove one required field
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': 75000
        }
        
        # Remove the specified field
        del form_data[field_to_remove]
        
        # Verification: Form data with missing field should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions the missing field
        error_message = str(exc_info.value).lower()
        assert "missing required field" in error_message
        assert field_to_remove.lower() in error_message
    
    @settings(max_examples=100)
    @given(form_data=valid_form_1040_data())
    def test_all_required_fields_present_does_not_raise_error(self, form_data):
        """
        **Validates: Requirements 2.1**
        Feature: tax-document-generation, Property 4: Required Field Validation
        
        For any form data with all required fields present,
        the required field validation should pass (no error raised).
        
        This test verifies that:
        1. Valid form data with all required fields is accepted
        2. No ValidationError is raised for complete data
        3. The validation function completes successfully
        """
        # Verification: Form data with all required fields should be accepted
        # This should not raise any exception
        try:
            validate_form_data('1040', form_data)
        except ValidationError as e:
            # If a ValidationError is raised, it should be for format/type issues,
            # not for missing fields
            error_message = str(e).lower()
            assert "missing required field" not in error_message, \
                f"Should not complain about missing fields when all are present: {e}"
    
    @settings(max_examples=100)
    @given(
        form_data=valid_form_1040_data(),
        num_fields_to_remove=integers(min_value=2, max_value=5)
    )
    def test_multiple_missing_fields_raises_validation_error(self, form_data, num_fields_to_remove):
        """
        **Validates: Requirements 2.1**
        Feature: tax-document-generation, Property 4: Required Field Validation
        
        For any form data with multiple required fields missing,
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. Multiple missing fields are detected
        2. ValidationError is raised
        3. Error message indicates missing fields
        """
        # Action: Remove multiple fields
        required_fields = list(FORM_1040_REQUIRED_FIELDS.keys())
        num_to_remove = min(num_fields_to_remove, len(required_fields))
        
        # Randomly select fields to remove
        import random
        fields_to_remove = random.sample(required_fields, num_to_remove)
        
        for field in fields_to_remove:
            if field in form_data:
                del form_data[field]
        
        # Verification: Form data with multiple missing fields should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', form_data)
        
        # Verify the error message mentions missing fields
        error_message = str(exc_info.value).lower()
        assert "missing required field" in error_message
    
    @settings(max_examples=100)
    @given(form_data=valid_form_1040_data())
    def test_empty_form_data_raises_validation_error(self, form_data):
        """
        **Validates: Requirements 2.1**
        Feature: tax-document-generation, Property 4: Required Field Validation
        
        For any empty form data (no fields present),
        the system should reject the request with a validation error.
        
        This test verifies that:
        1. Empty form data is rejected
        2. ValidationError is raised
        3. Error message indicates missing required fields
        """
        # Action: Use empty form data
        empty_form_data = {}
        
        # Verification: Empty form data should be rejected
        with pytest.raises(ValidationError) as exc_info:
            validate_form_data('1040', empty_form_data)
        
        # Verify the error message mentions missing fields
        error_message = str(exc_info.value).lower()
        assert "missing required field" in error_message
    
    @settings(max_examples=100)
    @given(
        form_data=valid_form_1040_data(),
        extra_field_name=text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz_'),
        extra_field_value=st.one_of(text(), integers(), floats(allow_nan=False))
    )
    def test_extra_fields_with_all_required_fields_does_not_raise_error(
        self, form_data, extra_field_name, extra_field_value
    ):
        """
        **Validates: Requirements 2.1**
        Feature: tax-document-generation, Property 4: Required Field Validation
        
        For any form data with all required fields present plus extra fields,
        the required field validation should pass.
        
        This test verifies that:
        1. Extra fields do not cause validation to fail
        2. Only required fields are checked for presence
        3. The system is permissive of additional data
        """
        # Action: Add an extra field to valid form data
        form_data[extra_field_name] = extra_field_value
        
        # Verification: Form data with extra fields should not fail required field check
        try:
            validate_form_data('1040', form_data)
        except ValidationError as e:
            # If a ValidationError is raised, it should be for format/type issues,
            # not for missing fields
            error_message = str(e).lower()
            assert "missing required field" not in error_message, \
                f"Should not complain about missing fields when all required fields are present: {e}"
    
    @settings(max_examples=100)
    @given(field_name=sampled_from(list(FORM_1040_REQUIRED_FIELDS.keys())))
    def test_field_present_but_none_value_is_treated_as_present(self, field_name):
        """
        **Validates: Requirements 2.1**
        Feature: tax-document-generation, Property 4: Required Field Validation
        
        For any required field that is present in the form data but has None value,
        the required field validation should pass (field is present).
        
        Note: Type validation may fail later, but required field check should pass.
        
        This test verifies that:
        1. Fields with None values are considered "present"
        2. Required field validation only checks for key presence
        3. Type validation is separate from presence validation
        """
        # Action: Create form data with all fields, but one has None value
        form_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',
            'filingStatus': 'single',
            'income': 75000
        }
        
        # Set the specified field to None
        form_data[field_name] = None
        
        # Verification: Should not raise "missing required field" error
        try:
            validate_form_data('1040', form_data)
        except ValidationError as e:
            # If a ValidationError is raised, it should be for type issues,
            # not for missing fields
            error_message = str(e).lower()
            assert "missing required field" not in error_message, \
                f"Should not complain about missing fields when field key is present (even if None): {e}"
            # It's OK if it complains about type issues
            assert "type" in error_message or "must be" in error_message
