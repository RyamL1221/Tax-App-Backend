"""
Edge case tests for combine_address_fields() function.

This test verifies edge cases and special scenarios for task 1.4.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from address_combiner import combine_address_fields


def test_with_country_non_usa():
    """Test with non-USA country."""
    form_data = {
        "payerName": "International Corp",
        "payerStreetAddress": "456 Main St",
        "payerCity": "Toronto",
        "payerState": "ON",
        "payerZip": "M5H 2N2",
        "payerCountry": "Canada",
        "recipientCity": "Vancouver",
        "recipientState": "BC",
        "recipientZip": "V6B 1A1",
        "recipientCountry": "Canada"
    }
    
    result = combine_address_fields(form_data)
    
    # Verify country appears in payer address
    assert "Canada" in result["payerAddressBlock"]
    
    # Verify country appears in recipient address
    assert "Canada" in result["recipientCityStateZip"]
    
    print("✅ Non-USA country test passed")


def test_with_usa_country_omitted():
    """Test that USA country is omitted."""
    form_data = {
        "payerName": "Example Corp",
        "payerCity": "New York",
        "payerState": "NY",
        "payerZip": "10001",
        "payerCountry": "USA",
        "recipientCity": "Boston",
        "recipientState": "MA",
        "recipientZip": "02101",
        "recipientCountry": "United States"
    }
    
    result = combine_address_fields(form_data)
    
    # Verify USA is not in the address blocks
    assert "USA" not in result["payerAddressBlock"]
    assert "United States" not in result["recipientCityStateZip"]
    
    print("✅ USA country omission test passed")


def test_only_payer_components():
    """Test with only payer components, no recipient."""
    form_data = {
        "payerName": "Example Corp",
        "payerCity": "Boston",
        "payerState": "MA"
    }
    
    result = combine_address_fields(form_data)
    
    # Should have payer address block
    assert "payerAddressBlock" in result
    
    # Should not have recipient address (no components provided)
    assert "recipientCityStateZip" not in result
    
    print("✅ Only payer components test passed")


def test_only_recipient_components():
    """Test with only recipient components, no payer."""
    form_data = {
        "recipientCity": "Seattle",
        "recipientState": "WA",
        "recipientZip": "98101"
    }
    
    result = combine_address_fields(form_data)
    
    # Should not have payer address block (no components provided)
    assert "payerAddressBlock" not in result
    
    # Should have recipient address
    assert "recipientCityStateZip" in result
    assert result["recipientCityStateZip"] == "Seattle, WA 98101"
    
    print("✅ Only recipient components test passed")


def test_preserves_non_address_fields():
    """Test that non-address fields are preserved."""
    form_data = {
        "payerName": "Example Corp",
        "payerCity": "Boston",
        "payerState": "MA",
        "payerTIN": "12-3456789",
        "recipientName": "John Doe",
        "recipientTIN": "123-45-6789",
        "totalOrdinaryDividends": "1000.00",
        "calendarYear": "2023"
    }
    
    result = combine_address_fields(form_data)
    
    # Verify non-address fields are preserved
    assert result["payerTIN"] == "12-3456789"
    assert result["recipientTIN"] == "123-45-6789"
    assert result["totalOrdinaryDividends"] == "1000.00"
    assert result["calendarYear"] == "2023"
    
    # Verify address fields were processed
    assert "payerAddressBlock" in result
    assert "payerCity" not in result
    assert "payerState" not in result
    
    print("✅ Non-address field preservation test passed")


def test_with_extended_zip():
    """Test with extended ZIP code format."""
    form_data = {
        "payerName": "Example Corp",
        "payerCity": "New York",
        "payerState": "NY",
        "payerZip": "10001-1234",
        "recipientCity": "Boston",
        "recipientState": "MA",
        "recipientZip": "02101-5678"
    }
    
    result = combine_address_fields(form_data)
    
    # Verify extended ZIP is preserved
    assert "10001-1234" in result["payerAddressBlock"]
    assert "02101-5678" in result["recipientCityStateZip"]
    
    print("✅ Extended ZIP code test passed")


def test_with_special_characters():
    """Test with special characters in address."""
    form_data = {
        "payerName": "O'Reilly & Associates, Inc.",
        "payerStreetAddress": "123 Main St., Suite #456",
        "payerCity": "St. Louis",
        "payerState": "MO",
        "payerZip": "63101"
    }
    
    result = combine_address_fields(form_data)
    
    # Verify special characters are preserved
    assert "O'Reilly & Associates, Inc." in result["payerAddressBlock"]
    assert "123 Main St., Suite #456" in result["payerAddressBlock"]
    assert "St. Louis" in result["payerAddressBlock"]
    
    print("✅ Special characters test passed")


def test_modifies_dict_in_place():
    """Test that the function modifies the dict in place."""
    form_data = {
        "payerName": "Example Corp",
        "payerCity": "Boston",
        "payerState": "MA"
    }
    
    original_id = id(form_data)
    result = combine_address_fields(form_data)
    
    # Should return the same dict object
    assert id(result) == original_id
    
    # Original dict should be modified
    assert "payerAddressBlock" in form_data
    assert "payerCity" not in form_data
    
    print("✅ In-place modification test passed")


if __name__ == "__main__":
    test_with_country_non_usa()
    test_with_usa_country_omitted()
    test_only_payer_components()
    test_only_recipient_components()
    test_preserves_non_address_fields()
    test_with_extended_zip()
    test_with_special_characters()
    test_modifies_dict_in_place()
    print("\n✅ All edge case tests passed!")
