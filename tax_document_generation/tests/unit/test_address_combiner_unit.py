"""
Unit tests for address combination functionality.

Tests the combination of individual address components into formatted multi-line
strings suitable for PDF form fields. Validates IRS-compliant formatting and
proper handling of missing/empty components.

Requirements: 7.1, 7.2
"""

import pytest
from tax_document_generation.address_combiner import (
    combine_payer_address,
    combine_recipient_address,
    combine_address_fields
)


class TestCombinePayerAddress:
    """Test the combine_payer_address function."""
    
    def test_all_components_present(self):
        """Test combining address with all components present."""
        result = combine_payer_address(
            payer_name="Example Investment Corporation",
            payer_street_address="123 Wall Street",
            payer_city="New York",
            payer_state="NY",
            payer_zip="10005",
            payer_country="USA",
            payer_telephone_number="(555) 123-4567"
        )
        
        expected = (
            "Example Investment Corporation\n"
            "123 Wall Street\n"
            "New York, NY 10005\n"
            "USA\n"
            "(555) 123-4567"
        )
        assert result == expected
    
    def test_missing_street_address(self):
        """Test combining address with missing street address."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="New York",
            payer_state="NY",
            payer_zip="10001"
        )
        
        expected = "Example Corp\nNew York, NY 10001"
        assert result == expected
    
    def test_missing_city(self):
        """Test combining address with missing city."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_street_address="123 Main St",
            payer_state="NY",
            payer_zip="10001"
        )
        
        expected = "Example Corp\n123 Main St\nNY 10001"
        assert result == expected
    
    def test_missing_state(self):
        """Test combining address with missing state."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="New York",
            payer_zip="10001"
        )
        
        expected = "Example Corp\nNew York 10001"
        assert result == expected
    
    def test_missing_zip(self):
        """Test combining address with missing ZIP code."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="New York",
            payer_state="NY"
        )
        
        expected = "Example Corp\nNew York, NY"
        assert result == expected
    
    def test_missing_telephone(self):
        """Test combining address with missing telephone number."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_street_address="123 Main St",
            payer_city="New York",
            payer_state="NY",
            payer_zip="10001"
        )
        
        expected = "Example Corp\n123 Main St\nNew York, NY 10001"
        assert result == expected
    
    def test_only_name_provided(self):
        """Test combining address with only name provided."""
        result = combine_payer_address(payer_name="Example Corp")
        
        assert result == "Example Corp"
    
    def test_empty_strings_treated_as_missing(self):
        """Test that empty strings are treated as missing components."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_street_address="",
            payer_city="New York",
            payer_state="",
            payer_zip="10001"
        )
        
        expected = "Example Corp\nNew York 10001"
        assert result == expected
    
    def test_none_values_treated_as_missing(self):
        """Test that None values are treated as missing components."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_street_address=None,
            payer_city="New York",
            payer_state=None,
            payer_zip="10001"
        )
        
        expected = "Example Corp\nNew York 10001"
        assert result == expected
    
    def test_city_state_zip_formatting(self):
        """Test proper formatting of city, state, ZIP line."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="Los Angeles",
            payer_state="CA",
            payer_zip="90001"
        )
        
        # Should be: "City, State ZIP" (comma after city, space between state and ZIP)
        assert "Los Angeles, CA 90001" in result
    
    def test_extended_zip_format(self):
        """Test handling of extended ZIP+4 format."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="New York",
            payer_state="NY",
            payer_zip="10001-1234"
        )
        
        assert "New York, NY 10001-1234" in result
    
    def test_multi_word_city(self):
        """Test handling of multi-word city names."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="San Francisco",
            payer_state="CA",
            payer_zip="94102"
        )
        
        assert "San Francisco, CA 94102" in result
    
    def test_non_usa_country_included(self):
        """Test that non-USA country is included in address."""
        result = combine_payer_address(
            payer_name="International Corp",
            payer_street_address="456 Main St",
            payer_city="Toronto",
            payer_state="ON",
            payer_zip="M5H 2N2",
            payer_country="Canada"
        )
        
        expected = (
            "International Corp\n"
            "456 Main St\n"
            "Toronto, ON M5H 2N2\n"
            "Canada"
        )
        assert result == expected
    
    def test_usa_country_included(self):
        """Test that USA country is included in address."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="New York",
            payer_state="NY",
            payer_zip="10001",
            payer_country="USA"
        )
        
        # USA should appear in result
        assert "USA" in result
        assert result == "Example Corp\nNew York, NY 10001\nUSA"
    
    def test_us_country_included(self):
        """Test that US country is included in address."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="New York",
            payer_state="NY",
            payer_zip="10001",
            payer_country="US"
        )
        
        # US should appear in result
        assert "US" in result
        assert result == "Example Corp\nNew York, NY 10001\nUS"
    
    def test_united_states_country_included(self):
        """Test that 'United States' country is included in address."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="New York",
            payer_state="NY",
            payer_zip="10001",
            payer_country="United States"
        )
        
        # United States should appear in result
        assert "United States" in result
        assert result == "Example Corp\nNew York, NY 10001\nUnited States"
    
    def test_no_blank_lines(self):
        """Test that result never contains blank lines (consecutive newlines)."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_street_address=None,  # Missing
            payer_city="New York",
            payer_state=None,  # Missing
            payer_zip="10001",
            payer_telephone_number=None  # Missing
        )
        
        # Should not have consecutive newlines
        assert "\n\n" not in result
    
    def test_no_leading_newline(self):
        """Test that result does not start with newline."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="New York",
            payer_state="NY"
        )
        
        assert not result.startswith("\n")
    
    def test_no_trailing_newline(self):
        """Test that result does not end with newline."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="New York",
            payer_state="NY"
        )
        
        assert not result.endswith("\n")
    
    def test_partial_city_state_zip_city_only(self):
        """Test handling when only city is provided."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_city="New York"
        )
        
        assert result == "Example Corp\nNew York"
    
    def test_partial_city_state_zip_state_only(self):
        """Test handling when only state is provided."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_state="NY"
        )
        
        assert result == "Example Corp\nNY"
    
    def test_partial_city_state_zip_zip_only(self):
        """Test handling when only ZIP is provided."""
        result = combine_payer_address(
            payer_name="Example Corp",
            payer_zip="10001"
        )
        
        assert result == "Example Corp\n10001"
    
    def test_all_components_missing(self):
        """Test handling when all components are missing."""
        result = combine_payer_address()
        
        assert result == ""
    
    def test_all_components_none(self):
        """Test handling when all components are None."""
        result = combine_payer_address(
            payer_name=None,
            payer_street_address=None,
            payer_city=None,
            payer_state=None,
            payer_zip=None,
            payer_country=None,
            payer_telephone_number=None
        )
        
        assert result == ""
    
    def test_all_components_empty_strings(self):
        """Test handling when all components are empty strings."""
        result = combine_payer_address(
            payer_name="",
            payer_street_address="",
            payer_city="",
            payer_state="",
            payer_zip="",
            payer_country="",
            payer_telephone_number=""
        )
        
        assert result == ""
    
    def test_very_long_address(self):
        """Test handling of very long address components."""
        result = combine_payer_address(
            payer_name="A" * 100,
            payer_street_address="B" * 100,
            payer_city="C" * 50,
            payer_state="NY",
            payer_zip="10001"
        )
        
        # Should contain all components
        assert "A" * 100 in result
        assert "B" * 100 in result
        assert "C" * 50 in result
    
    def test_special_characters_in_address(self):
        """Test handling of special characters in address components."""
        result = combine_payer_address(
            payer_name="O'Reilly & Associates, Inc.",
            payer_street_address="123 Main St., Suite #456",
            payer_city="St. Louis",
            payer_state="MO",
            payer_zip="63101"
        )
        
        # Should preserve special characters
        assert "O'Reilly & Associates, Inc." in result
        assert "123 Main St., Suite #456" in result
        assert "St. Louis" in result


class TestCombineRecipientAddress:
    """Test the combine_recipient_address function."""
    
    def test_all_components_present(self):
        """Test combining recipient address with all components present."""
        result = combine_recipient_address(
            recipient_city="Los Angeles",
            recipient_state="CA",
            recipient_zip="90001",
            recipient_country="USA"
        )
        
        # USA should be included
        assert result == "Los Angeles, CA 90001\nUSA"
    
    def test_missing_country(self):
        """Test combining recipient address with missing country (USA default)."""
        result = combine_recipient_address(
            recipient_city="Los Angeles",
            recipient_state="CA",
            recipient_zip="90001"
        )
        
        assert result == "Los Angeles, CA 90001"
    
    def test_non_usa_country(self):
        """Test combining recipient address with non-USA country."""
        result = combine_recipient_address(
            recipient_city="Toronto",
            recipient_state="ON",
            recipient_zip="M5H 2N2",
            recipient_country="Canada"
        )
        
        expected = "Toronto, ON M5H 2N2\nCanada"
        assert result == expected
    
    def test_partial_city_state(self):
        """Test combining with only city and state."""
        result = combine_recipient_address(
            recipient_city="Boston",
            recipient_state="MA"
        )
        
        assert result == "Boston, MA"
    
    def test_partial_city_zip(self):
        """Test combining with only city and ZIP."""
        result = combine_recipient_address(
            recipient_city="Boston",
            recipient_zip="02101"
        )
        
        assert result == "Boston 02101"
    
    def test_partial_state_zip(self):
        """Test combining with only state and ZIP."""
        result = combine_recipient_address(
            recipient_state="MA",
            recipient_zip="02101"
        )
        
        assert result == "MA 02101"
    
    def test_only_city(self):
        """Test combining with only city."""
        result = combine_recipient_address(recipient_city="Boston")
        
        assert result == "Boston"
    
    def test_only_state(self):
        """Test combining with only state."""
        result = combine_recipient_address(recipient_state="MA")
        
        assert result == "MA"
    
    def test_only_zip(self):
        """Test combining with only ZIP."""
        result = combine_recipient_address(recipient_zip="02101")
        
        assert result == "02101"
    
    def test_empty_inputs(self):
        """Test combining with all empty inputs."""
        result = combine_recipient_address()
        
        assert result == ""
    
    def test_all_none_values(self):
        """Test combining with all None values."""
        result = combine_recipient_address(
            recipient_city=None,
            recipient_state=None,
            recipient_zip=None,
            recipient_country=None
        )
        
        assert result == ""
    
    def test_all_empty_strings(self):
        """Test combining with all empty strings."""
        result = combine_recipient_address(
            recipient_city="",
            recipient_state="",
            recipient_zip="",
            recipient_country=""
        )
        
        assert result == ""
    
    def test_city_state_zip_formatting(self):
        """Test proper formatting of city, state, ZIP line."""
        result = combine_recipient_address(
            recipient_city="Los Angeles",
            recipient_state="CA",
            recipient_zip="90001"
        )
        
        # Should be: "City, State ZIP" (comma after city, space between state and ZIP)
        assert result == "Los Angeles, CA 90001"
    
    def test_extended_zip_format(self):
        """Test handling of extended ZIP+4 format."""
        result = combine_recipient_address(
            recipient_city="New York",
            recipient_state="NY",
            recipient_zip="10001-1234"
        )
        
        assert result == "New York, NY 10001-1234"
    
    def test_multi_word_city(self):
        """Test handling of multi-word city names."""
        result = combine_recipient_address(
            recipient_city="San Francisco",
            recipient_state="CA",
            recipient_zip="94102"
        )
        
        assert result == "San Francisco, CA 94102"
    
    def test_no_blank_lines(self):
        """Test that result never contains blank lines."""
        result = combine_recipient_address(
            recipient_city="Toronto",
            recipient_state="ON",
            recipient_zip="M5H 2N2",
            recipient_country="Canada"
        )
        
        # Should not have consecutive newlines
        assert "\n\n" not in result
    
    def test_no_leading_newline(self):
        """Test that result does not start with newline."""
        result = combine_recipient_address(
            recipient_city="Boston",
            recipient_state="MA"
        )
        
        assert not result.startswith("\n")
    
    def test_no_trailing_newline(self):
        """Test that result does not end with newline."""
        result = combine_recipient_address(
            recipient_city="Boston",
            recipient_state="MA"
        )
        
        assert not result.endswith("\n")


class TestCombineAddressFields:
    """Test the combine_address_fields function."""
    
    def test_payer_components_combined_correctly(self):
        """Test that payer address components are combined correctly."""
        form_data = {
            "payerName": "Example Corp",
            "payerStreetAddress": "123 Main St",
            "payerCity": "New York",
            "payerState": "NY",
            "payerZip": "10001",
            "payerTelephoneNumber": "(555) 123-4567"
        }
        
        result = combine_address_fields(form_data)
        
        assert "payerAddressBlock" in result
        expected_block = (
            "Example Corp\n"
            "123 Main St\n"
            "New York, NY 10001\n"
            "(555) 123-4567"
        )
        assert result["payerAddressBlock"] == expected_block
    
    def test_recipient_components_combined_correctly(self):
        """Test that recipient address components are combined correctly."""
        form_data = {
            "recipientCity": "Los Angeles",
            "recipientState": "CA",
            "recipientZip": "90001"
        }
        
        result = combine_address_fields(form_data)
        
        assert "recipientCityStateZip" in result
        assert result["recipientCityStateZip"] == "Los Angeles, CA 90001"
    
    def test_individual_components_removed(self):
        """Test that individual address components are removed from form_data."""
        form_data = {
            "payerName": "Example Corp",
            "payerStreetAddress": "123 Main St",
            "payerCity": "New York",
            "payerState": "NY",
            "payerZip": "10001",
            "payerCountry": "USA",
            "payerTelephoneNumber": "(555) 123-4567",
            "recipientCity": "Los Angeles",
            "recipientState": "CA",
            "recipientZip": "90001",
            "recipientCountry": "USA"
        }
        
        result = combine_address_fields(form_data)
        
        # Individual payer components should be removed
        assert "payerStreetAddress" not in result
        assert "payerCity" not in result
        assert "payerState" not in result
        assert "payerZip" not in result
        assert "payerCountry" not in result
        assert "payerTelephoneNumber" not in result
        
        # Individual recipient components should be removed
        assert "recipientCity" not in result
        assert "recipientState" not in result
        assert "recipientZip" not in result
        assert "recipientCountry" not in result
    
    def test_required_fields_preserved(self):
        """Test that required fields with their own PDF mappings are preserved."""
        form_data = {
            "payerName": "Example Corp",
            "payerCity": "New York",
            "payerState": "NY",
            "recipientName": "John Doe",
            "recipientStreetAddress": "456 Oak Ave",
            "recipientCity": "Los Angeles",
            "recipientState": "CA"
        }
        
        result = combine_address_fields(form_data)
        
        # These fields should be preserved (they have their own PDF mappings)
        assert "payerName" in result
        assert result["payerName"] == "Example Corp"
        assert "recipientName" in result
        assert result["recipientName"] == "John Doe"
        assert "recipientStreetAddress" in result
        assert result["recipientStreetAddress"] == "456 Oak Ave"
    
    def test_empty_form_data(self):
        """Test handling of empty form data."""
        form_data = {}
        
        result = combine_address_fields(form_data)
        
        assert result == {}
    
    def test_mixed_present_missing_fields(self):
        """Test handling with mixed present and missing fields."""
        form_data = {
            "payerName": "Example Corp",
            "payerCity": "New York",
            # Missing: payerState, payerZip, payerStreetAddress, etc.
            "recipientCity": "Los Angeles",
            "recipientZip": "90001"
            # Missing: recipientState
        }
        
        result = combine_address_fields(form_data)
        
        # Should create combined fields with available components
        assert "payerAddressBlock" in result
        assert "Example Corp" in result["payerAddressBlock"]
        assert "New York" in result["payerAddressBlock"]
        
        assert "recipientCityStateZip" in result
        assert "Los Angeles" in result["recipientCityStateZip"]
        assert "90001" in result["recipientCityStateZip"]
    
    def test_preserves_other_fields(self):
        """Test that non-address fields are preserved unchanged."""
        form_data = {
            "payerName": "Example Corp",
            "payerCity": "New York",
            "payerState": "NY",
            "payerTIN": "12-3456789",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00",
            "calendarYear": "2023"
        }
        
        result = combine_address_fields(form_data)
        
        # Non-address fields should be preserved
        assert result["payerTIN"] == "12-3456789"
        assert result["recipientTIN"] == "123-45-6789"
        assert result["totalOrdinaryDividends"] == "1000.00"
        assert result["calendarYear"] == "2023"
    
    def test_only_payer_address(self):
        """Test combining when only payer address is present."""
        form_data = {
            "payerName": "Example Corp",
            "payerCity": "New York",
            "payerState": "NY"
        }
        
        result = combine_address_fields(form_data)
        
        assert "payerAddressBlock" in result
        assert "recipientCityStateZip" not in result
    
    def test_only_recipient_address(self):
        """Test combining when only recipient address is present."""
        form_data = {
            "recipientCity": "Los Angeles",
            "recipientState": "CA",
            "recipientZip": "90001"
        }
        
        result = combine_address_fields(form_data)
        
        assert "recipientCityStateZip" in result
        assert "payerAddressBlock" not in result
    
    def test_complete_form_data(self):
        """Test combining with complete form data including all address fields."""
        form_data = {
            "payerName": "Example Investment Corporation",
            "payerStreetAddress": "123 Wall Street",
            "payerCity": "New York",
            "payerState": "NY",
            "payerZip": "10005",
            "payerCountry": "USA",
            "payerTelephoneNumber": "(555) 123-4567",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientStreetAddress": "456 Oak Avenue",
            "recipientCity": "Los Angeles",
            "recipientState": "CA",
            "recipientZip": "90001",
            "recipientCountry": "USA",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00"
        }
        
        result = combine_address_fields(form_data)
        
        # Combined fields should be present
        assert "payerAddressBlock" in result
        assert "recipientCityStateZip" in result
        
        # Individual components should be removed
        assert "payerStreetAddress" not in result
        assert "payerCity" not in result
        assert "recipientCity" not in result
        
        # Fields with own mappings should be preserved
        assert "payerName" in result
        assert "recipientName" in result
        assert "recipientStreetAddress" in result
        
        # Other fields should be preserved
        assert "payerTIN" in result
        assert "recipientTIN" in result
        assert "totalOrdinaryDividends" in result
