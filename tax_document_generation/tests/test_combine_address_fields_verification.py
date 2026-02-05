"""
Quick verification test for combine_address_fields() function.

This test verifies that the combine_address_fields() function works correctly
for task 1.4 implementation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from address_combiner import combine_address_fields


def test_combine_address_fields_basic():
    """Test basic address combination functionality."""
    form_data = {
        "payerName": "Example Corp",
        "payerStreetAddress": "123 Main St",
        "payerCity": "New York",
        "payerState": "NY",
        "payerZip": "10001",
        "payerTelephoneNumber": "(555) 123-4567",
        "recipientName": "John Doe",
        "recipientStreetAddress": "456 Oak Ave",
        "recipientCity": "Los Angeles",
        "recipientState": "CA",
        "recipientZip": "90001"
    }
    
    result = combine_address_fields(form_data)
    
    # Verify combined fields were added
    assert "payerAddressBlock" in result
    assert "recipientCityStateZip" in result
    
    # Verify payerAddressBlock contains all components
    payer_block = result["payerAddressBlock"]
    assert "Example Corp" in payer_block
    assert "123 Main St" in payer_block
    assert "New York, NY 10001" in payer_block
    assert "(555) 123-4567" in payer_block
    
    # Verify recipientCityStateZip is correct
    assert result["recipientCityStateZip"] == "Los Angeles, CA 90001"
    
    # Verify individual components were removed
    assert "payerStreetAddress" not in result
    assert "payerCity" not in result
    assert "payerState" not in result
    assert "payerZip" not in result
    assert "payerTelephoneNumber" not in result
    assert "recipientCity" not in result
    assert "recipientState" not in result
    assert "recipientZip" not in result
    
    # Verify required fields were kept
    assert "payerName" in result
    assert "recipientName" in result
    assert "recipientStreetAddress" in result
    
    print("✅ Basic address combination test passed")


def test_combine_address_fields_minimal():
    """Test with minimal data."""
    form_data = {
        "payerName": "Example Corp"
    }
    
    result = combine_address_fields(form_data)
    
    # Should have payerAddressBlock with just the name
    assert "payerAddressBlock" in result
    assert result["payerAddressBlock"] == "Example Corp"
    
    # payerName should still be present
    assert "payerName" in result
    
    print("✅ Minimal data test passed")


def test_combine_address_fields_partial():
    """Test with partial address data."""
    form_data = {
        "payerName": "Example Corp",
        "payerCity": "Boston",
        "payerState": "MA",
        "recipientCity": "Seattle",
        "recipientState": "WA"
    }
    
    result = combine_address_fields(form_data)
    
    # Verify partial payer address
    assert "payerAddressBlock" in result
    payer_block = result["payerAddressBlock"]
    assert "Example Corp" in payer_block
    assert "Boston, MA" in payer_block
    
    # Verify partial recipient address
    assert "recipientCityStateZip" in result
    assert result["recipientCityStateZip"] == "Seattle, WA"
    
    # Verify components removed
    assert "payerCity" not in result
    assert "payerState" not in result
    assert "recipientCity" not in result
    assert "recipientState" not in result
    
    print("✅ Partial data test passed")


def test_combine_address_fields_empty():
    """Test with empty form_data."""
    form_data = {}
    
    result = combine_address_fields(form_data)
    
    # Should return the same empty dict (no combined fields added)
    assert result == {}
    
    print("✅ Empty data test passed")


if __name__ == "__main__":
    test_combine_address_fields_basic()
    test_combine_address_fields_minimal()
    test_combine_address_fields_partial()
    test_combine_address_fields_empty()
    print("\n✅ All verification tests passed!")
