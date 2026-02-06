"""
Unit tests for address normalization functionality.

Tests the parsing of combined address formats and normalization of address
fields to support backward compatibility.

Requirements: 6.1, 6.2
"""

import pytest
from tax_document_generation.address_normalizer import (
    parse_combined_address,
    normalize_address_fields,
    _normalize_address_group
)


class TestParseCombinedAddress:
    """Test the parse_combined_address function."""
    
    def test_parse_standard_format(self):
        """Test parsing standard combined address format."""
        result = parse_combined_address("New York, NY 10001")
        assert result == ("New York", "NY", "10001")
    
    def test_parse_extended_zip(self):
        """Test parsing address with extended ZIP+4 format."""
        result = parse_combined_address("Los Angeles, CA 90001-1234")
        assert result == ("Los Angeles", "CA", "90001-1234")
    
    def test_parse_multi_word_city(self):
        """Test parsing city names with multiple words."""
        result = parse_combined_address("San Francisco, CA 94102")
        assert result == ("San Francisco", "CA", "94102")
    
    def test_parse_city_with_extra_spaces(self):
        """Test parsing with extra whitespace."""
        result = parse_combined_address("New York,  NY  10001")
        assert result == ("New York", "NY", "10001")
    
    def test_parse_leading_trailing_spaces(self):
        """Test parsing with leading/trailing spaces."""
        result = parse_combined_address("  New York, NY 10001  ")
        assert result == ("New York", "NY", "10001")
    
    def test_parse_missing_zip(self):
        """Test that addresses without ZIP return None."""
        result = parse_combined_address("New York, NY")
        assert result is None
    
    def test_parse_missing_state(self):
        """Test that addresses without state return None."""
        result = parse_combined_address("New York 10001")
        assert result is None
    
    def test_parse_missing_comma(self):
        """Test that addresses without comma return None."""
        result = parse_combined_address("New York NY 10001")
        assert result is None
    
    def test_parse_invalid_state_code(self):
        """Test that addresses with invalid state codes return None."""
        result = parse_combined_address("New York, ABC 10001")
        assert result is None
    
    def test_parse_invalid_zip_format(self):
        """Test that addresses with invalid ZIP format return None."""
        result = parse_combined_address("New York, NY 1234")
        assert result is None
    
    def test_parse_non_string_input(self):
        """Test that non-string inputs return None."""
        assert parse_combined_address(None) is None
        assert parse_combined_address(12345) is None
        assert parse_combined_address([]) is None
    
    def test_parse_empty_string(self):
        """Test that empty string returns None."""
        result = parse_combined_address("")
        assert result is None
    
    def test_parse_city_only(self):
        """Test that city-only string returns None."""
        result = parse_combined_address("New York")
        assert result is None


class TestNormalizeAddressGroup:
    """Test the _normalize_address_group function."""
    
    def test_normalize_combined_format(self):
        """Test normalizing combined address format."""
        form_data = {"payerCity": "New York, NY 10001"}
        result = _normalize_address_group(
            form_data,
            city_field="payerCity",
            state_field="payerState",
            zip_field="payerZip"
        )
        
        assert result["payerCity"] == "New York"
        assert result["payerState"] == "NY"
        assert result["payerZip"] == "10001"
    
    def test_normalize_separate_format_unchanged(self):
        """Test that separate format is not modified."""
        form_data = {
            "payerCity": "New York",
            "payerState": "NY",
            "payerZip": "10001"
        }
        result = _normalize_address_group(
            form_data,
            city_field="payerCity",
            state_field="payerState",
            zip_field="payerZip"
        )
        
        assert result["payerCity"] == "New York"
        assert result["payerState"] == "NY"
        assert result["payerZip"] == "10001"
    
    def test_explicit_values_take_precedence(self):
        """Test that explicit state/ZIP values override parsed values."""
        form_data = {
            "payerCity": "New York, NY 10001",
            "payerState": "CA",  # Explicit value should win
            "payerZip": "90001"  # Explicit value should win
        }
        result = _normalize_address_group(
            form_data,
            city_field="payerCity",
            state_field="payerState",
            zip_field="payerZip"
        )
        
        assert result["payerCity"] == "New York"
        assert result["payerState"] == "CA"  # Should keep explicit value
        assert result["payerZip"] == "90001"  # Should keep explicit value
    
    def test_missing_city_field(self):
        """Test handling when city field is not present."""
        form_data = {"payerState": "NY"}
        result = _normalize_address_group(
            form_data,
            city_field="payerCity",
            state_field="payerState",
            zip_field="payerZip"
        )
        
        assert "payerCity" not in result
        assert result["payerState"] == "NY"
    
    def test_non_string_city_value(self):
        """Test handling when city value is not a string."""
        form_data = {"payerCity": 12345}
        result = _normalize_address_group(
            form_data,
            city_field="payerCity",
            state_field="payerState",
            zip_field="payerZip"
        )
        
        assert result["payerCity"] == 12345
        assert "payerState" not in result
        assert "payerZip" not in result
    
    def test_invalid_combined_format(self):
        """Test handling when city value doesn't match combined format."""
        form_data = {"payerCity": "Just a city name"}
        result = _normalize_address_group(
            form_data,
            city_field="payerCity",
            state_field="payerState",
            zip_field="payerZip"
        )
        
        assert result["payerCity"] == "Just a city name"
        assert "payerState" not in result
        assert "payerZip" not in result


class TestNormalizeAddressFields:
    """Test the normalize_address_fields function."""
    
    def test_normalize_payer_address(self):
        """Test normalizing payer address fields."""
        form_data = {"payerCity": "New York, NY 10001"}
        result = normalize_address_fields(form_data)
        
        assert result["payerCity"] == "New York"
        assert result["payerState"] == "NY"
        assert result["payerZip"] == "10001"
    
    def test_normalize_recipient_address(self):
        """Test normalizing recipient address fields."""
        form_data = {"recipientCity": "Los Angeles, CA 90001"}
        result = normalize_address_fields(form_data)
        
        assert result["recipientCity"] == "Los Angeles"
        assert result["recipientState"] == "CA"
        assert result["recipientZip"] == "90001"
    
    def test_normalize_both_addresses(self):
        """Test normalizing both payer and recipient addresses."""
        form_data = {
            "payerCity": "New York, NY 10001",
            "recipientCity": "Los Angeles, CA 90001"
        }
        result = normalize_address_fields(form_data)
        
        assert result["payerCity"] == "New York"
        assert result["payerState"] == "NY"
        assert result["payerZip"] == "10001"
        assert result["recipientCity"] == "Los Angeles"
        assert result["recipientState"] == "CA"
        assert result["recipientZip"] == "90001"
    
    def test_normalize_mixed_formats(self):
        """Test normalizing with mixed old and new formats."""
        form_data = {
            "payerCity": "New York, NY 10001",  # Old format
            "recipientCity": "Los Angeles",      # New format
            "recipientState": "CA",
            "recipientZip": "90001"
        }
        result = normalize_address_fields(form_data)
        
        assert result["payerCity"] == "New York"
        assert result["payerState"] == "NY"
        assert result["payerZip"] == "10001"
        assert result["recipientCity"] == "Los Angeles"
        assert result["recipientState"] == "CA"
        assert result["recipientZip"] == "90001"
    
    def test_normalize_empty_form_data(self):
        """Test normalizing empty form data."""
        form_data = {}
        result = normalize_address_fields(form_data)
        
        assert result == {}
    
    def test_normalize_preserves_other_fields(self):
        """Test that normalization preserves non-address fields."""
        form_data = {
            "payerCity": "New York, NY 10001",
            "payerName": "Test Corporation",
            "payerTIN": "12-3456789",
            "totalOrdinaryDividends": "1000.00"
        }
        result = normalize_address_fields(form_data)
        
        assert result["payerCity"] == "New York"
        assert result["payerState"] == "NY"
        assert result["payerZip"] == "10001"
        assert result["payerName"] == "Test Corporation"
        assert result["payerTIN"] == "12-3456789"
        assert result["totalOrdinaryDividends"] == "1000.00"
    
    def test_normalize_does_not_modify_original(self):
        """Test that normalization does not modify the original form data."""
        original = {"payerCity": "New York, NY 10001"}
        result = normalize_address_fields(original)
        
        # Original should be unchanged
        assert original == {"payerCity": "New York, NY 10001"}
        
        # Result should be normalized
        assert result["payerCity"] == "New York"
        assert result["payerState"] == "NY"
        assert result["payerZip"] == "10001"
