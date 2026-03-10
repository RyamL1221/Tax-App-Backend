"""
Unit tests for input normalizer module.

Tests specific normalization examples and edge cases for decimal and TIN fields.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5
"""

import pytest
from tax_document_generation.input_normalizer import (
    normalize_decimal_field,
    normalize_tin_field,
    normalize_form_data,
    NormalizationResult
)


class TestNormalizeDecimalField:
    """Test decimal field normalization."""
    
    def test_integer_string_adds_decimal_places(self):
        """Test that integer strings get .00 added."""
        assert normalize_decimal_field("1000") == "1000.00"
        assert normalize_decimal_field("0") == "0.00"
        assert normalize_decimal_field("999999") == "999999.00"
    
    def test_integer_adds_decimal_places(self):
        """Test that integer values get .00 added."""
        assert normalize_decimal_field(1000) == "1000.00"
        assert normalize_decimal_field(0) == "0.00"
        assert normalize_decimal_field(999999) == "999999.00"
    
    def test_one_decimal_place_adds_trailing_zero(self):
        """Test that values with one decimal place get trailing zero."""
        assert normalize_decimal_field("1000.5") == "1000.50"
        assert normalize_decimal_field("0.1") == "0.10"
        assert normalize_decimal_field(1000.5) == "1000.50"
    
    def test_two_decimal_places_unchanged(self):
        """Test that values with two decimal places remain unchanged."""
        assert normalize_decimal_field("1000.00") == "1000.00"
        assert normalize_decimal_field("1000.50") == "1000.50"
        assert normalize_decimal_field("1000.99") == "1000.99"
        assert normalize_decimal_field(1000.00) == "1000.00"
    
    def test_excess_decimal_places_rounded(self):
        """Test that values with more than two decimal places are rounded."""
        assert normalize_decimal_field("1000.123") == "1000.12"
        assert normalize_decimal_field("1000.125") == "1000.12"  # Banker's rounding
        assert normalize_decimal_field("1000.126") == "1000.13"
        assert normalize_decimal_field("1000.999") == "1001.00"
    
    def test_float_values(self):
        """Test that float values are normalized correctly."""
        assert normalize_decimal_field(1000.0) == "1000.00"
        assert normalize_decimal_field(1000.5) == "1000.50"
        assert normalize_decimal_field(1000.123) == "1000.12"
    
    def test_whitespace_stripped(self):
        """Test that whitespace is stripped from string values."""
        assert normalize_decimal_field("  1000  ") == "1000.00"
        assert normalize_decimal_field(" 1000.50 ") == "1000.50"
    
    def test_negative_numbers(self):
        """Test that negative numbers are handled correctly."""
        assert normalize_decimal_field("-1000") == "-1000.00"
        assert normalize_decimal_field(-1000.5) == "-1000.50"
    
    def test_zero_values(self):
        """Test various representations of zero."""
        assert normalize_decimal_field("0") == "0.00"
        assert normalize_decimal_field(0) == "0.00"
        assert normalize_decimal_field("0.0") == "0.00"
        assert normalize_decimal_field(0.0) == "0.00"
    
    def test_invalid_string_raises_error(self):
        """Test that non-numeric strings raise ValueError."""
        with pytest.raises(ValueError, match="Cannot normalize decimal value"):
            normalize_decimal_field("abc")
        
        with pytest.raises(ValueError, match="Cannot normalize decimal value"):
            normalize_decimal_field("1000.00.00")
    
    def test_none_raises_error(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Cannot normalize decimal value"):
            normalize_decimal_field(None)
    
    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Cannot normalize decimal value"):
            normalize_decimal_field("")


class TestNormalizeTinField:
    """Test TIN field normalization."""
    
    def test_ein_without_hyphens_adds_hyphens(self):
        """Test that 9-digit EIN gets hyphens added."""
        assert normalize_tin_field("123456789", "EIN") == "12-3456789"
        assert normalize_tin_field("000000000", "EIN") == "00-0000000"
        assert normalize_tin_field("999999999", "EIN") == "99-9999999"
    
    def test_ein_with_hyphens_unchanged(self):
        """Test that properly formatted EIN remains unchanged."""
        assert normalize_tin_field("12-3456789", "EIN") == "12-3456789"
        assert normalize_tin_field("00-0000000", "EIN") == "00-0000000"
    
    def test_ssn_without_hyphens_adds_hyphens(self):
        """Test that 9-digit SSN gets hyphens added."""
        assert normalize_tin_field("987654321", "SSN") == "987-65-4321"
        assert normalize_tin_field("000000000", "SSN") == "000-00-0000"
        assert normalize_tin_field("999999999", "SSN") == "999-99-9999"
    
    def test_ssn_with_hyphens_unchanged(self):
        """Test that properly formatted SSN remains unchanged."""
        assert normalize_tin_field("987-65-4321", "SSN") == "987-65-4321"
        assert normalize_tin_field("000-00-0000", "SSN") == "000-00-0000"
    
    def test_whitespace_stripped(self):
        """Test that whitespace is stripped from TIN values."""
        assert normalize_tin_field(" 123456789 ", "EIN") == "12-3456789"
        assert normalize_tin_field(" 987654321 ", "SSN") == "987-65-4321"
    
    def test_mixed_format_normalized(self):
        """Test that TINs with spaces or partial hyphens are normalized."""
        assert normalize_tin_field("12 3456789", "EIN") == "12-3456789"
        assert normalize_tin_field("987 65 4321", "SSN") == "987-65-4321"
    
    def test_invalid_length_raises_error(self):
        """Test that TINs with incorrect length raise ValueError."""
        with pytest.raises(ValueError, match="TIN must be exactly 9 digits"):
            normalize_tin_field("12345678", "EIN")  # Too short
        
        with pytest.raises(ValueError, match="TIN must be exactly 9 digits"):
            normalize_tin_field("1234567890", "EIN")  # Too long
    
    def test_non_numeric_raises_error(self):
        """Test that TINs with non-numeric characters raise ValueError."""
        with pytest.raises(ValueError, match="TIN must be exactly 9 digits"):
            normalize_tin_field("12-34567AB", "EIN")
        
        with pytest.raises(ValueError, match="TIN must be exactly 9 digits"):
            normalize_tin_field("ABC-DE-FGHI", "SSN")
    
    def test_unknown_tin_type_raises_error(self):
        """Test that unknown TIN type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown TIN type"):
            normalize_tin_field("123456789", "ITIN")
        
        with pytest.raises(ValueError, match="Unknown TIN type"):
            normalize_tin_field("123456789", "")
    
    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="TIN must be exactly 9 digits"):
            normalize_tin_field("", "EIN")


class TestNormalizeFormData:
    """Test form data normalization."""
    
    def test_normalizes_decimal_fields(self):
        """Test that decimal fields are normalized."""
        form_data = {
            "totalOrdinaryDividends": "1000",
            "qualifiedDividends": 500,
            "recipientName": "John Doe"
        }
        
        result = normalize_form_data(form_data, "1099-DIV")
        
        assert result.normalized_data["totalOrdinaryDividends"] == "1000.00"
        assert result.normalized_data["qualifiedDividends"] == "500.00"
        assert result.normalized_data["recipientName"] == "John Doe"  # Unchanged
        
        # Check changes log
        assert len(result.changes) == 2
        assert ("totalOrdinaryDividends", "1000", "1000.00") in result.changes
        assert ("qualifiedDividends", "500", "500.00") in result.changes
    
    def test_normalizes_tin_fields(self):
        """Test that TIN fields are normalized."""
        form_data = {
            "payerTIN": "123456789",
            "recipientTIN": "987654321",
            "payerName": "Example Corp"
        }
        
        result = normalize_form_data(form_data, "1099-DIV")
        
        assert result.normalized_data["payerTIN"] == "12-3456789"
        assert result.normalized_data["recipientTIN"] == "987-65-4321"
        assert result.normalized_data["payerName"] == "Example Corp"  # Unchanged
        
        # Check changes log
        assert len(result.changes) == 2
        assert ("payerTIN", "123456789", "12-3456789") in result.changes
        assert ("recipientTIN", "987654321", "987-65-4321") in result.changes
    
    def test_no_changes_for_preformatted_data(self):
        """Test that pre-formatted data produces no changes."""
        form_data = {
            "totalOrdinaryDividends": "1000.00",
            "payerTIN": "12-3456789",
            "recipientTIN": "987-65-4321"
        }
        
        result = normalize_form_data(form_data, "1099-DIV")
        
        assert result.normalized_data == form_data
        assert len(result.changes) == 0
    
    def test_skips_none_values(self):
        """Test that None values are skipped."""
        form_data = {
            "totalOrdinaryDividends": "1000",
            "qualifiedDividends": None,
            "recipientName": "John Doe"
        }
        
        result = normalize_form_data(form_data, "1099-DIV")
        
        assert result.normalized_data["totalOrdinaryDividends"] == "1000.00"
        assert result.normalized_data["qualifiedDividends"] is None
        assert len(result.changes) == 1
    
    def test_skips_unknown_fields(self):
        """Test that fields not in metadata are skipped."""
        form_data = {
            "totalOrdinaryDividends": "1000",
            "unknownField": "some value"
        }
        
        result = normalize_form_data(form_data, "1099-DIV")
        
        assert result.normalized_data["totalOrdinaryDividends"] == "1000.00"
        assert result.normalized_data["unknownField"] == "some value"  # Unchanged
        assert len(result.changes) == 1
    
    def test_mixed_normalization(self):
        """Test form with both decimal and TIN fields."""
        form_data = {
            "totalOrdinaryDividends": "1000",
            "payerTIN": "123456789",
            "recipientName": "John Doe",
            "qualifiedDividends": "500.00",  # Already formatted
            "recipientTIN": "987-65-4321"  # Already formatted
        }
        
        result = normalize_form_data(form_data, "1099-DIV")
        
        assert result.normalized_data["totalOrdinaryDividends"] == "1000.00"
        assert result.normalized_data["payerTIN"] == "12-3456789"
        assert result.normalized_data["qualifiedDividends"] == "500.00"
        assert result.normalized_data["recipientTIN"] == "987-65-4321"
        
        # Only fields that changed should be in changes log
        assert len(result.changes) == 2
        assert ("totalOrdinaryDividends", "1000", "1000.00") in result.changes
        assert ("payerTIN", "123456789", "12-3456789") in result.changes
    
    def test_normalization_error_raises_with_context(self):
        """Test that normalization errors include field context."""
        form_data = {
            "totalOrdinaryDividends": "invalid"
        }
        
        with pytest.raises(ValueError, match="Normalization failed for field totalOrdinaryDividends"):
            normalize_form_data(form_data, "1099-DIV")
    
    def test_original_data_not_modified(self):
        """Test that original form_data dict is not modified."""
        form_data = {
            "totalOrdinaryDividends": "1000",
            "payerTIN": "123456789"
        }
        original_data = form_data.copy()
        
        result = normalize_form_data(form_data, "1099-DIV")
        
        # Original should be unchanged
        assert form_data == original_data
        # Result should have normalized values
        assert result.normalized_data["totalOrdinaryDividends"] == "1000.00"
        assert result.normalized_data["payerTIN"] == "12-3456789"


class TestNormalizationResult:
    """Test NormalizationResult dataclass."""
    
    def test_result_structure(self):
        """Test that NormalizationResult has correct structure."""
        normalized_data = {"field1": "value1"}
        changes = [("field1", "old", "new")]
        
        result = NormalizationResult(
            normalized_data=normalized_data,
            changes=changes
        )
        
        assert result.normalized_data == normalized_data
        assert result.changes == changes
    
    def test_empty_changes(self):
        """Test NormalizationResult with no changes."""
        normalized_data = {"field1": "value1"}
        changes = []
        
        result = NormalizationResult(
            normalized_data=normalized_data,
            changes=changes
        )
        
        assert result.normalized_data == normalized_data
        assert result.changes == []
        assert len(result.changes) == 0
