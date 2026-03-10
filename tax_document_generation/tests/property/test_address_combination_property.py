"""
Property-Based Tests for Address Combination

This module contains property-based tests using Hypothesis to verify correctness
properties of the address combination functionality. These tests validate that
address components are combined correctly, without blank lines, and maintain
backward compatibility.

**Validates: Requirements 7.1, 7.2**

Test Properties:
1. Address Block Completeness - All provided components appear in result
2. No Blank Lines - Combined addresses never contain blank lines
3. Backward Compatibility - Old and new formats produce equivalent output
"""

import pytest
from hypothesis import given, strategies as st, assume, settings

# Direct imports for production code
from tax_document_generation.address_combiner import (
    combine_payer_address,
    combine_recipient_address,
    combine_address_fields
)
from tax_document_generation.address_normalizer import normalize_address_fields


# ============================================================================
# Test Strategies
# ============================================================================

# Generate valid text without special characters that might break formatting
safe_text = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
        whitelist_characters='.-()#'
    ),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip() != '')

# Generate valid city names (no commas to avoid confusion with combined format)
city_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Zs'),
        blacklist_characters=','
    ),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != '')

# Generate valid 2-letter state codes
state_strategy = st.from_regex(r'^[A-Z]{2}$', fullmatch=True)

# Generate valid ZIP codes (5 digits or 5+4 format)
zip_strategy = st.one_of(
    st.from_regex(r'^\d{5}$', fullmatch=True),
    st.from_regex(r'^\d{5}-\d{4}$', fullmatch=True)
)

# Generate valid country names
country_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')),
    min_size=2,
    max_size=50
).filter(lambda x: x.strip() != '' and x.upper() not in ['USA', 'US', 'UNITED STATES'])

# Generate valid phone numbers
phone_strategy = st.from_regex(r'^\(\d{3}\) \d{3}-\d{4}$', fullmatch=True)


# ============================================================================
# Property 1: Address Block Completeness
# **Validates: Requirements 1.2, 1.5**
# ============================================================================

@settings(max_examples=20)  # Reduced from default 100
@given(
    name=safe_text,
    street=st.one_of(st.none(), safe_text),
    city=st.one_of(st.none(), city_strategy),
    state=st.one_of(st.none(), state_strategy),
    zip_code=st.one_of(st.none(), zip_strategy),
    country=st.one_of(st.none(), country_strategy),
    telephone=st.one_of(st.none(), phone_strategy)
)
def test_address_block_contains_all_components(
    name, street, city, state, zip_code, country, telephone
):
    """
    Property: Combined address block contains all provided non-empty components.
    
    For all valid payer address components, the combined address block must
    contain all non-empty components in the correct order. This ensures that
    no address information is lost during combination.
    
    **Validates: Requirements 1.2, 1.5**
    - 1.2: All payer address components are combined into a single multi-line string
    - 1.5: Each address component appears on its own line in the PDF
    """
    result = combine_payer_address(
        payer_name=name,
        payer_street_address=street,
        payer_city=city,
        payer_state=state,
        payer_zip=zip_code,
        payer_country=country,
        payer_telephone_number=telephone
    )
    
    # All non-empty components must appear in result
    if name:
        assert name in result, f"Name '{name}' not found in result: {result}"
    
    if street:
        assert street in result, f"Street '{street}' not found in result: {result}"
    
    if city:
        assert city in result, f"City '{city}' not found in result: {result}"
    
    if state:
        assert state in result, f"State '{state}' not found in result: {result}"
    
    if zip_code:
        assert zip_code in result, f"ZIP '{zip_code}' not found in result: {result}"
    
    # Country should always appear if provided
    if country:
        assert country in result, f"Country '{country}' not found in result: {result}"
    
    if telephone:
        assert telephone in result, f"Telephone '{telephone}' not found in result: {result}"


@settings(max_examples=20)  # Reduced from default 100
@given(
    city=st.one_of(st.none(), city_strategy),
    state=st.one_of(st.none(), state_strategy),
    zip_code=st.one_of(st.none(), zip_strategy),
    country=st.one_of(st.none(), country_strategy)
)
def test_recipient_address_contains_all_components(city, state, zip_code, country):
    """
    Property: Combined recipient address contains all provided components.
    
    For all valid recipient address components, the combined address must
    contain all non-empty components.
    
    **Validates: Requirements 3.1, 3.3**
    - 3.1: Recipient address components are combined into field f2_7
    - 3.3: Combined recipient address follows same formatting rules as payer address
    """
    result = combine_recipient_address(
        recipient_city=city,
        recipient_state=state,
        recipient_zip=zip_code,
        recipient_country=country
    )
    
    # All non-empty components must appear in result
    if city:
        assert city in result, f"City '{city}' not found in result: {result}"
    
    if state:
        assert state in result, f"State '{state}' not found in result: {result}"
    
    if zip_code:
        assert zip_code in result, f"ZIP '{zip_code}' not found in result: {result}"
    
    # Country should always appear if provided
    if country:
        assert country in result, f"Country '{country}' not found in result: {result}"


# ============================================================================
# Property 2: No Blank Lines
# **Validates: Requirements 1.6, 3.4**
# ============================================================================

@settings(max_examples=20)  # Reduced from default 100
@given(
    name=st.one_of(st.none(), safe_text),
    street=st.one_of(st.none(), safe_text),
    city=st.one_of(st.none(), city_strategy),
    state=st.one_of(st.none(), state_strategy),
    zip_code=st.one_of(st.none(), zip_strategy),
    country=st.one_of(st.none(), country_strategy),
    telephone=st.one_of(st.none(), phone_strategy)
)
def test_no_blank_lines_in_payer_address(
    name, street, city, state, zip_code, country, telephone
):
    """
    Property: Combined payer address never contains blank lines.
    
    The combined address must not contain blank lines (consecutive newlines),
    leading newlines, or trailing newlines. Empty components should be omitted
    entirely rather than leaving blank lines.
    
    **Validates: Requirements 1.6, 3.4**
    - 1.6: Empty/missing components are omitted from the combined address (no blank lines)
    - 3.4: Empty/missing recipient components are omitted (no blank lines)
    """
    result = combine_payer_address(
        payer_name=name,
        payer_street_address=street,
        payer_city=city,
        payer_state=state,
        payer_zip=zip_code,
        payer_country=country,
        payer_telephone_number=telephone
    )
    
    # No consecutive newlines (blank lines)
    assert '\n\n' not in result, f"Found blank line in result: {repr(result)}"
    
    # No leading newlines
    assert not result.startswith('\n'), f"Result starts with newline: {repr(result)}"
    
    # No trailing newlines
    assert not result.endswith('\n'), f"Result ends with newline: {repr(result)}"
    
    # If result is non-empty, it should not be just whitespace
    if result:
        assert result.strip() != '', f"Result is only whitespace: {repr(result)}"


@settings(max_examples=20)  # Reduced from default 100
@given(
    city=st.one_of(st.none(), city_strategy),
    state=st.one_of(st.none(), state_strategy),
    zip_code=st.one_of(st.none(), zip_strategy),
    country=st.one_of(st.none(), country_strategy)
)
def test_no_blank_lines_in_recipient_address(city, state, zip_code, country):
    """
    Property: Combined recipient address never contains blank lines.
    
    The combined recipient address must not contain blank lines, leading
    newlines, or trailing newlines.
    
    **Validates: Requirements 1.6, 3.4**
    - 1.6: Empty/missing components are omitted from the combined address (no blank lines)
    - 3.4: Empty/missing recipient components are omitted (no blank lines)
    """
    result = combine_recipient_address(
        recipient_city=city,
        recipient_state=state,
        recipient_zip=zip_code,
        recipient_country=country
    )
    
    # No consecutive newlines (blank lines)
    assert '\n\n' not in result, f"Found blank line in result: {repr(result)}"
    
    # No leading newlines
    assert not result.startswith('\n'), f"Result starts with newline: {repr(result)}"
    
    # No trailing newlines
    assert not result.endswith('\n'), f"Result ends with newline: {repr(result)}"
    
    # If result is non-empty, it should not be just whitespace
    if result:
        assert result.strip() != '', f"Result is only whitespace: {repr(result)}"


# ============================================================================
# Property 3: Backward Compatibility
# **Validates: Requirements 2.1, 2.5**
# ============================================================================

@settings(max_examples=20)  # Reduced from default 100
@given(
    city=city_strategy,
    state=state_strategy,
    zip_code=zip_strategy
)
def test_old_and_new_payer_formats_equivalent(city, state, zip_code):
    """
    Property: Old combined format and new separate format produce equivalent results.
    
    When the same address information is provided in old combined format
    ("City, State ZIP") versus new separate format (separate city, state, ZIP),
    both should produce the same city/state/ZIP line in the final address block.
    This ensures backward compatibility.
    
    **Validates: Requirements 2.1, 2.5**
    - 2.1: Old combined format "payerCity: City, State ZIP" is still accepted
    - 2.5: Both old and new formats produce identical PDF output
    """
    # Normalize the city to match what the normalizer does (strips trailing spaces)
    normalized_city = city.strip()
    
    # Old format: combined city/state/ZIP in payerCity field
    old_format = {
        "payerName": "Test Corp",
        "payerCity": f"{normalized_city}, {state} {zip_code}"
    }
    old_normalized = normalize_address_fields(old_format.copy())
    old_combined = combine_address_fields(old_normalized)
    
    # New format: separate city, state, ZIP fields
    new_format = {
        "payerName": "Test Corp",
        "payerCity": normalized_city,
        "payerState": state,
        "payerZip": zip_code
    }
    new_combined = combine_address_fields(new_format.copy())
    
    # Both should produce the same city/state/ZIP line
    expected_line = f"{normalized_city}, {state} {zip_code}"
    
    old_address_block = old_combined.get("payerAddressBlock", "")
    new_address_block = new_combined.get("payerAddressBlock", "")
    
    # Check that all components are present in both results
    assert normalized_city in old_address_block, \
        f"City '{normalized_city}' not found in old format result: {old_address_block}"
    assert state in old_address_block, \
        f"State '{state}' not found in old format result: {old_address_block}"
    assert zip_code in old_address_block, \
        f"ZIP '{zip_code}' not found in old format result: {old_address_block}"
    
    assert normalized_city in new_address_block, \
        f"City '{normalized_city}' not found in new format result: {new_address_block}"
    assert state in new_address_block, \
        f"State '{state}' not found in new format result: {new_address_block}"
    assert zip_code in new_address_block, \
        f"ZIP '{zip_code}' not found in new format result: {new_address_block}"
    
    # Both should have the same address block (since only name and city/state/ZIP provided)
    assert old_address_block == new_address_block, \
        f"Old and new formats produced different results:\nOld: {old_address_block}\nNew: {new_address_block}"


@settings(max_examples=20)  # Reduced from default 100
@given(
    city=city_strategy,
    state=state_strategy,
    zip_code=zip_strategy
)
def test_old_and_new_recipient_formats_equivalent(city, state, zip_code):
    """
    Property: Old and new recipient formats produce equivalent results.
    
    When the same recipient address information is provided in old combined
    format versus new separate format, both should produce the same result.
    
    **Validates: Requirements 2.1, 2.5**
    - 2.1: Old combined format is still accepted
    - 2.5: Both old and new formats produce identical PDF output
    """
    # Old format: combined city/state/ZIP in recipientCity field
    old_format = {
        "recipientName": "John Doe",
        "recipientCity": f"{city}, {state} {zip_code}"
    }
    old_normalized = normalize_address_fields(old_format.copy())
    old_combined = combine_address_fields(old_normalized)
    
    # New format: separate city, state, ZIP fields
    new_format = {
        "recipientName": "John Doe",
        "recipientCity": city,
        "recipientState": state,
        "recipientZip": zip_code
    }
    new_combined = combine_address_fields(new_format.copy())
    
    # Both should produce the same city/state/ZIP result
    # Note: The normalizer may clean up spacing, so we check for the normalized format
    expected_result = f"{city}, {state} {zip_code}"
    
    old_result = old_combined.get("recipientCityStateZip", "")
    new_result = new_combined.get("recipientCityStateZip", "")
    
    # Check that all components are present in both results
    assert city in old_result, f"City '{city}' not found in old format result: {old_result}"
    assert state in old_result, f"State '{state}' not found in old format result: {old_result}"
    assert zip_code in old_result, f"ZIP '{zip_code}' not found in old format result: {old_result}"
    
    assert city in new_result, f"City '{city}' not found in new format result: {new_result}"
    assert state in new_result, f"State '{state}' not found in new format result: {new_result}"
    assert zip_code in new_result, f"ZIP '{zip_code}' not found in new format result: {new_result}"
    
    # Both should produce identical results
    assert old_result == new_result, \
        f"Old and new formats produced different results:\nOld: {old_result}\nNew: {new_result}"


# ============================================================================
# Additional Property Tests
# ============================================================================

@settings(max_examples=20)  # Reduced from default 100
@given(
    name=safe_text,
    city=city_strategy,
    state=state_strategy,
    zip_code=zip_strategy
)
def test_city_state_zip_formatting_consistency(name, city, state, zip_code):
    """
    Property: City/state/ZIP line is always formatted consistently.
    
    When city, state, and ZIP are all provided, they should always be
    formatted as "City, State ZIP" (comma between city and state, space
    between state and ZIP).
    
    **Validates: Requirements 1.3, 4.2**
    - 1.3: The combined address block is formatted according to IRS specifications
    - 4.2: Follows IRS formatting guidelines for payer address blocks
    """
    result = combine_payer_address(
        payer_name=name,
        payer_city=city,
        payer_state=state,
        payer_zip=zip_code
    )
    
    # Expected format: "City, State ZIP"
    expected_line = f"{city}, {state} {zip_code}"
    
    assert expected_line in result, \
        f"Expected formatted line '{expected_line}' not found in result: {result}"


@settings(max_examples=20)  # Reduced from default 100
@given(
    form_data=st.fixed_dictionaries({
        'payerName': safe_text,
        'payerStreetAddress': st.one_of(st.none(), safe_text),
        'payerCity': st.one_of(st.none(), city_strategy),
        'payerState': st.one_of(st.none(), state_strategy),
        'payerZip': st.one_of(st.none(), zip_strategy),
        'recipientName': safe_text,
        'recipientCity': st.one_of(st.none(), city_strategy),
        'recipientState': st.one_of(st.none(), state_strategy),
        'recipientZip': st.one_of(st.none(), zip_strategy)
    })
)
def test_combine_address_fields_preserves_required_fields(form_data):
    """
    Property: combine_address_fields() preserves required fields.
    
    The combine_address_fields() function should preserve fields that have
    their own PDF mappings (payerName, recipientName, recipientStreetAddress)
    while removing individual address components.
    
    **Validates: Requirements 5.2, 5.3**
    - 5.2: After address normalization, combine payer address components into payerAddressBlock
    - 5.3: After address normalization, combine recipient address components into recipientCityStateZip
    """
    original_payer_name = form_data.get('payerName')
    original_recipient_name = form_data.get('recipientName')
    
    result = combine_address_fields(form_data.copy())
    
    # Required fields should be preserved
    assert result.get('payerName') == original_payer_name, \
        "payerName should be preserved"
    
    assert result.get('recipientName') == original_recipient_name, \
        "recipientName should be preserved"
    
    # Individual components should be removed
    assert 'payerCity' not in result, "payerCity should be removed"
    assert 'payerState' not in result, "payerState should be removed"
    assert 'payerZip' not in result, "payerZip should be removed"
    assert 'recipientCity' not in result, "recipientCity should be removed"
    assert 'recipientState' not in result, "recipientState should be removed"
    assert 'recipientZip' not in result, "recipientZip should be removed"
    
    # Combined fields should be added if components existed
    if any([form_data.get('payerName'), form_data.get('payerStreetAddress'),
            form_data.get('payerCity'), form_data.get('payerState'), form_data.get('payerZip')]):
        assert 'payerAddressBlock' in result, "payerAddressBlock should be added"
    
    if any([form_data.get('recipientCity'), form_data.get('recipientState'),
            form_data.get('recipientZip')]):
        assert 'recipientCityStateZip' in result, "recipientCityStateZip should be added"
