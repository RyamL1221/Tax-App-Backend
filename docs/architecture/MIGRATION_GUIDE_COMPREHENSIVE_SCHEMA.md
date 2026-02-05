# Migration Guide: Comprehensive 1099-DIV Schema Update

## Overview

This guide helps you migrate to the comprehensive 1099-DIV schema that includes all IRS-required fields. The update expands field coverage from approximately 25 fields to over 40 fields, adds support for multi-state tax reporting, and provides separate address component fields for better data structure and validation.

**Key Changes:**
- Separate address component fields (city, state, ZIP, country) for both payer and recipient
- Payer telephone number field
- Multi-state tax reporting (support for two states)
- Enhanced validation for state codes, ZIP codes, and phone numbers
- Backward compatibility with combined address format

**Backward Compatibility:** All existing API requests continue to work. The system automatically handles both old and new address formats.

## What Changed?

### 1. Payer Address Components (New Fields)

Previously, payer location information was often combined in the `payerCity` field. Now you can provide separate components:

**New Fields:**
- `payerState` - Two-letter state code (e.g., "NY", "CA")
- `payerCountry` - Country name (e.g., "USA", "Canada")
- `payerZip` - ZIP or postal code (e.g., "10001", "10001-1234")
- `payerTelephoneNumber` - Contact phone number (e.g., "(555) 123-4567")

### 2. Recipient Address Components (New Fields)

Similarly, recipient address information can now be provided as separate components:

**New Fields:**
- `recipientCity` - City or town name
- `recipientState` - Two-letter state code
- `recipientCountry` - Country name
- `recipientZip` - ZIP or postal code

### 3. Multi-State Tax Reporting (New Fields)

The IRS Form 1099-DIV supports reporting state tax information for up to two states. Previously, only one state was supported:

**New Fields:**
- `state2` - Second state name (Box 14, second row)
- `stateIdentificationNumber2` - Payer's state ID for second state (Box 15, second row)
- `stateTaxWithheld2` - State tax withheld for second state (Box 16, second row)


## Breaking Changes

**Good News: There are NO breaking changes!**

The comprehensive schema update maintains 100% backward compatibility with existing API requests. All existing field names continue to work, and the system automatically handles both old and new address formats.

### What This Means for You

- ✅ Existing API requests will continue to work without modification
- ✅ Combined address format ("City, State ZIP") is still supported
- ✅ No immediate action required
- ✅ You can migrate at your own pace

## New Fields Added

### Payer Information

| Field Name | Data Type | Max Length | Validation | Example |
|-----------|-----------|------------|------------|---------|
| `payerState` | string | 2 | Two-letter state code | `"NY"` |
| `payerCountry` | string | 50 | - | `"USA"` |
| `payerZip` | string | 10 | XXXXX or XXXXX-XXXX | `"10001"` |
| `payerTelephoneNumber` | string | 20 | Phone format | `"(555) 123-4567"` |

### Recipient Information

| Field Name | Data Type | Max Length | Validation | Example |
|-----------|-----------|------------|------------|---------|
| `recipientCity` | string | 50 | - | `"Los Angeles"` |
| `recipientState` | string | 2 | Two-letter state code | `"CA"` |
| `recipientCountry` | string | 50 | - | `"USA"` |
| `recipientZip` | string | 10 | XXXXX or XXXXX-XXXX | `"90001"` |

### Multi-State Tax Reporting

| Field Name | Data Type | IRS Box | Example |
|-----------|-----------|---------|---------|
| `state2` | string | 14 (row 2) | `"CA"` |
| `stateIdentificationNumber2` | string | 15 (row 2) | `"98-7654321"` |
| `stateTaxWithheld2` | decimal | 16 (row 2) | `"25.00"` |


## Address Field Migration

### Understanding the Change

**Old Format (Still Supported):**
Address components were combined in a single field:
```json
{
  "payerCity": "New York, NY 10001"
}
```

**New Format (Recommended):**
Address components are provided separately:
```json
{
  "payerCity": "New York",
  "payerState": "NY",
  "payerZip": "10001"
}
```

### Backward Compatibility

The system automatically detects and parses the old combined format:

1. **Detection:** If `payerCity` or `recipientCity` contains a comma, the system recognizes it as the old format
2. **Parsing:** The system extracts city, state, and ZIP components
3. **Mapping:** Components are mapped to the appropriate PDF fields
4. **Warning:** A deprecation warning is logged (visible in CloudWatch logs)

### Migration Examples

#### Example 1: Payer Address Migration

**Before (Old Format):**
```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "payerStreetAddress": "123 Main Street",
    "payerCity": "New York, NY 10001",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
  }
}
```

**After (New Format):**
```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "payerStreetAddress": "123 Main Street",
    "payerCity": "New York",
    "payerState": "NY",
    "payerZip": "10001",
    "payerTelephoneNumber": "(555) 123-4567",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
  }
}
```

#### Example 2: Complete Address Information

**Before (Minimal):**
```json
{
  "payerCity": "Los Angeles, CA 90001",
  "recipientStreetAddress": "456 Oak Avenue"
}
```

**After (Complete):**
```json
{
  "payerCity": "Los Angeles",
  "payerState": "CA",
  "payerCountry": "USA",
  "payerZip": "90001",
  "payerTelephoneNumber": "(555) 987-6543",
  "recipientStreetAddress": "456 Oak Avenue",
  "recipientCity": "San Francisco",
  "recipientState": "CA",
  "recipientCountry": "USA",
  "recipientZip": "94102"
}
```


#### Example 3: International Addresses

**New Format with Country:**
```json
{
  "payerCity": "Toronto",
  "payerState": "ON",
  "payerCountry": "Canada",
  "payerZip": "M5H 2N2",
  "recipientCity": "London",
  "recipientCountry": "United Kingdom",
  "recipientZip": "SW1A 1AA"
}
```

### Deprecation Timeline

| Phase | Timeline | Status | Action Required |
|-------|----------|--------|-----------------|
| **Phase 1: Current** | Now | ✅ Active | None - both formats work |
| **Phase 2: Deprecation Warning** | 6 months | ⚠️ Warnings logged | Plan migration |
| **Phase 3: Deprecation Notice** | 12 months | ⚠️ Stronger warnings | Migrate to new format |
| **Phase 4: Removal** | 18 months | ❌ Old format removed | Must use new format |

**Recommendation:** Migrate to the new separate field format within the next 6 months to avoid deprecation warnings.


## Multi-State Tax Reporting

### Overview

The IRS Form 1099-DIV includes boxes 14-16 for state tax information, with space for **two states**. Previously, the API only supported one state. Now you can report tax information for up to two states.

### Field Naming Convention

Multi-state fields use numbered suffixes:

**First State (existing fields):**
- `state` - State name (Box 14, row 1)
- `stateIdentificationNumber` - Payer's state ID (Box 15, row 1)
- `stateTaxWithheld` - State tax withheld (Box 16, row 1)

**Second State (new fields):**
- `state2` - State name (Box 14, row 2)
- `stateIdentificationNumber2` - Payer's state ID (Box 15, row 2)
- `stateTaxWithheld2` - State tax withheld (Box 16, row 2)

### Examples

#### Example 1: Single State (Existing Behavior)

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00",
    "state": "NY",
    "stateIdentificationNumber": "12-3456789",
    "stateTaxWithheld": "50.00"
  }
}
```

#### Example 2: Two States (New Capability)

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00",
    "state": "NY",
    "stateIdentificationNumber": "12-3456789",
    "stateTaxWithheld": "50.00",
    "state2": "CA",
    "stateIdentificationNumber2": "98-7654321",
    "stateTaxWithheld2": "25.00"
  }
}
```

### Data Integrity

The system maintains the association between state name, state ID, and tax withheld for each state:

- **State 1:** `state`, `stateIdentificationNumber`, `stateTaxWithheld` are grouped together
- **State 2:** `state2`, `stateIdentificationNumber2`, `stateTaxWithheld2` are grouped together

Each group maps to a separate row on the PDF form.

### Validation Rules

- All three fields for a state must be provided together (state name, ID, and tax withheld)
- State codes must be valid two-letter abbreviations
- State tax withheld must be a valid decimal amount
- If only one state is needed, use the first state fields (without the "2" suffix)


## Migration Steps

Follow these steps to migrate your integration to the comprehensive schema:

### Step 1: Review New Fields

Review the [1099-DIV Field Reference](1099-DIV_FIELD_REFERENCE.md) to understand all available fields:

- Payer address components
- Recipient address components
- Multi-state tax reporting fields
- Validation rules for each field

### Step 2: Update Your Data Model

Update your application's data model to include the new fields:

```python
# Example: Python data model
class Form1099DIV:
    # Existing fields
    calendar_year: str
    payer_name: str
    payer_tin: str
    
    # New payer fields
    payer_city: str
    payer_state: str  # NEW
    payer_country: str  # NEW
    payer_zip: str  # NEW
    payer_telephone_number: str  # NEW
    
    # New recipient fields
    recipient_city: str  # NEW
    recipient_state: str  # NEW
    recipient_country: str  # NEW
    recipient_zip: str  # NEW
    
    # New multi-state fields
    state2: str  # NEW
    state_identification_number2: str  # NEW
    state_tax_withheld2: Decimal  # NEW
```

### Step 3: Update Address Parsing

If you currently combine address components, update your code to provide them separately:

**Before:**
```python
# Combining address components
payer_city = f"{city}, {state} {zip_code}"
```

**After:**
```python
# Separate address components
payer_city = city
payer_state = state
payer_zip = zip_code
```

### Step 4: Update API Requests

Update your API request payloads to use the new field structure:

**Before:**
```python
form_data = {
    "calendarYear": "2024",
    "payerName": "Example Corp",
    "payerTIN": "12-3456789",
    "payerStreetAddress": "123 Main St",
    "payerCity": "New York, NY 10001",  # Combined format
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
}
```

**After:**
```python
form_data = {
    "calendarYear": "2024",
    "payerName": "Example Corp",
    "payerTIN": "12-3456789",
    "payerStreetAddress": "123 Main St",
    "payerCity": "New York",  # Separate components
    "payerState": "NY",
    "payerZip": "10001",
    "payerTelephoneNumber": "(555) 123-4567",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "recipientCity": "Los Angeles",
    "recipientState": "CA",
    "recipientZip": "90001",
    "totalOrdinaryDividends": "1000.00"
}
```

### Step 5: Add Multi-State Support (If Needed)

If you need to report tax information for two states, add the second state fields:

```python
form_data = {
    # ... other fields ...
    "state": "NY",
    "stateIdentificationNumber": "12-3456789",
    "stateTaxWithheld": "50.00",
    "state2": "CA",  # Second state
    "stateIdentificationNumber2": "98-7654321",
    "stateTaxWithheld2": "25.00"
}
```

### Step 6: Update Validation Logic

Update your validation logic to handle the new fields:

```python
def validate_address_fields(form_data):
    """Validate address fields."""
    # State code validation
    if "payerState" in form_data:
        if not re.match(r'^[A-Z]{2}$', form_data["payerState"]):
            raise ValidationError("Invalid state code format")
    
    # ZIP code validation
    if "payerZip" in form_data:
        if not re.match(r'^\d{5}(-\d{4})?$', form_data["payerZip"]):
            raise ValidationError("Invalid ZIP code format")
    
    # Phone number validation
    if "payerTelephoneNumber" in form_data:
        if not re.match(r'^\+?[\d\s\-\(\)]+$', form_data["payerTelephoneNumber"]):
            raise ValidationError("Invalid phone number format")
```

### Step 7: Test Your Integration

Test your updated integration with various scenarios:

1. **Minimal data** - Required fields only
2. **Typical data** - Common fields including new address components
3. **Complete data** - All fields including multi-state reporting
4. **Backward compatibility** - Old combined address format (should still work)

### Step 8: Monitor Deprecation Warnings

Monitor your application logs for deprecation warnings:

```
WARNING: Deprecated field format detected: payerCity contains combined address.
Please use separate payerCity, payerState, and payerZip fields.
Combined format will be removed in a future version.
```

If you see these warnings, prioritize migrating to the new format.


## Validation Changes

### New Validation Rules

The comprehensive schema introduces enhanced validation for new fields:

#### State Code Validation

**Rule:** State codes must be valid two-letter abbreviations (uppercase)

**Valid Examples:**
- `"NY"` - New York
- `"CA"` - California
- `"TX"` - Texas

**Invalid Examples:**
- `"New York"` - Full state name (use "NY")
- `"ny"` - Lowercase (use "NY")
- `"N"` - Single letter

**Error Message:**
```json
{
  "error": "Validation failed",
  "details": {
    "field": "payerState",
    "message": "State code must be a two-letter abbreviation (e.g., 'NY', 'CA')"
  }
}
```

#### ZIP Code Validation

**Rule:** ZIP codes must be in format XXXXX or XXXXX-XXXX

**Valid Examples:**
- `"10001"` - 5-digit ZIP
- `"10001-1234"` - 9-digit ZIP with hyphen
- `"90210"` - 5-digit ZIP

**Invalid Examples:**
- `"1001"` - Too short
- `"100011"` - Too long
- `"10001 1234"` - Space instead of hyphen

**Error Message:**
```json
{
  "error": "Validation failed",
  "details": {
    "field": "payerZip",
    "message": "ZIP code must be in format XXXXX or XXXXX-XXXX"
  }
}
```

#### Telephone Number Validation

**Rule:** Phone numbers must contain only digits, spaces, hyphens, parentheses, and optional leading plus sign

**Valid Examples:**
- `"(555) 123-4567"` - Standard format
- `"555-123-4567"` - Hyphen format
- `"+1 555 123 4567"` - International format
- `"5551234567"` - No formatting

**Invalid Examples:**
- `"555.123.4567"` - Dots not allowed
- `"Call: 555-1234"` - Text not allowed
- `"555-CALL"` - Letters not allowed

**Error Message:**
```json
{
  "error": "Validation failed",
  "details": {
    "field": "payerTelephoneNumber",
    "message": "Phone number contains invalid characters"
  }
}
```

### Existing Validation Rules

All existing validation rules remain unchanged:

- **TIN Format:** XX-XXXXXXX (EIN) or XXX-XX-XXXX (SSN)
- **Numeric Fields:** Must be valid decimal numbers
- **Required Fields:** Must be present in all requests
- **Max Length:** Text fields have maximum length limits


## Code Examples

### Example 1: Basic Migration (Python)

**Before:**
```python
import requests

# Old format with combined address
payload = {
    "documentType": "1099-DIV",
    "formData": {
        "calendarYear": "2024",
        "payerName": "Example Corporation",
        "payerTIN": "12-3456789",
        "payerStreetAddress": "123 Main Street",
        "payerCity": "New York, NY 10001",
        "recipientName": "John Doe",
        "recipientTIN": "123-45-6789",
        "recipientStreetAddress": "456 Oak Avenue",
        "totalOrdinaryDividends": "1000.00"
    }
}

response = requests.post(
    "https://api.example.com/generate",
    json=payload,
    headers={"Authorization": f"Bearer {token}"}
)
```

**After:**
```python
import requests

# New format with separate address components
payload = {
    "documentType": "1099-DIV",
    "formData": {
        "calendarYear": "2024",
        "payerName": "Example Corporation",
        "payerTIN": "12-3456789",
        "payerStreetAddress": "123 Main Street",
        "payerCity": "New York",
        "payerState": "NY",
        "payerZip": "10001",
        "payerTelephoneNumber": "(555) 123-4567",
        "recipientName": "John Doe",
        "recipientTIN": "123-45-6789",
        "recipientStreetAddress": "456 Oak Avenue",
        "recipientCity": "Los Angeles",
        "recipientState": "CA",
        "recipientZip": "90001",
        "totalOrdinaryDividends": "1000.00"
    }
}

response = requests.post(
    "https://api.example.com/generate",
    json=payload,
    headers={"Authorization": f"Bearer {token}"}
)
```

### Example 2: Multi-State Reporting (JavaScript)

```javascript
// Generate 1099-DIV with two states
const formData = {
  documentType: "1099-DIV",
  formData: {
    calendarYear: "2024",
    payerName: "Example Investment Corp",
    payerTIN: "12-3456789",
    payerStreetAddress: "123 Wall Street",
    payerCity: "New York",
    payerState: "NY",
    payerZip: "10005",
    payerTelephoneNumber: "(555) 123-4567",
    
    recipientName: "Jane Smith",
    recipientTIN: "987-65-4321",
    recipientStreetAddress: "789 Market Street",
    recipientCity: "San Francisco",
    recipientState: "CA",
    recipientZip: "94102",
    
    totalOrdinaryDividends: "2500.00",
    qualifiedDividends: "2000.00",
    federalIncomeTaxWithheld: "375.00",
    
    // First state
    state: "NY",
    stateIdentificationNumber: "12-3456789",
    stateTaxWithheld: "125.00",
    
    // Second state (NEW)
    state2: "CA",
    stateIdentificationNumber2: "98-7654321",
    stateTaxWithheld2: "100.00"
  }
};

const response = await fetch("https://api.example.com/generate", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  },
  body: JSON.stringify(formData)
});

const result = await response.json();
console.log("Document generated:", result.jobId);
```

### Example 3: Address Parser Helper (Python)

If you need to support both formats in your application:

```python
def parse_address_field(combined_address: str) -> dict:
    """
    Parse combined address format into separate components.
    
    Args:
        combined_address: Address in format "City, State ZIP"
        
    Returns:
        Dictionary with city, state, and zip components
        
    Example:
        >>> parse_address_field("New York, NY 10001")
        {'city': 'New York', 'state': 'NY', 'zip': '10001'}
    """
    if "," not in combined_address:
        # Already in new format or just city
        return {"city": combined_address, "state": None, "zip": None}
    
    parts = combined_address.split(",")
    city = parts[0].strip()
    
    if len(parts) < 2:
        return {"city": city, "state": None, "zip": None}
    
    state_zip = parts[1].strip().split()
    state = state_zip[0] if len(state_zip) > 0 else None
    zip_code = state_zip[1] if len(state_zip) > 1 else None
    
    return {"city": city, "state": state, "zip": zip_code}


def migrate_form_data(old_format: dict) -> dict:
    """
    Migrate form data from old to new format.
    
    Args:
        old_format: Form data with combined address fields
        
    Returns:
        Form data with separate address components
    """
    new_format = old_format.copy()
    
    # Migrate payer address
    if "payerCity" in new_format and "," in new_format["payerCity"]:
        parsed = parse_address_field(new_format["payerCity"])
        new_format["payerCity"] = parsed["city"]
        if parsed["state"]:
            new_format["payerState"] = parsed["state"]
        if parsed["zip"]:
            new_format["payerZip"] = parsed["zip"]
    
    # Migrate recipient address
    if "recipientCity" in new_format and "," in new_format["recipientCity"]:
        parsed = parse_address_field(new_format["recipientCity"])
        new_format["recipientCity"] = parsed["city"]
        if parsed["state"]:
            new_format["recipientState"] = parsed["state"]
        if parsed["zip"]:
            new_format["recipientZip"] = parsed["zip"]
    
    return new_format


# Usage
old_data = {
    "calendarYear": "2024",
    "payerName": "Example Corp",
    "payerCity": "New York, NY 10001",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
}

new_data = migrate_form_data(old_data)
print(new_data)
# Output: {
#   "calendarYear": "2024",
#   "payerName": "Example Corp",
#   "payerCity": "New York",
#   "payerState": "NY",
#   "payerZip": "10001",
#   "recipientName": "John Doe",
#   "recipientTIN": "123-45-6789",
#   "totalOrdinaryDividends": "1000.00"
# }
```


### Example 4: Validation Helper (TypeScript)

```typescript
interface ValidationResult {
  valid: boolean;
  errors: string[];
}

function validateStateCode(stateCode: string): ValidationResult {
  const errors: string[] = [];
  
  if (!stateCode) {
    return { valid: true, errors: [] }; // Optional field
  }
  
  if (!/^[A-Z]{2}$/.test(stateCode)) {
    errors.push("State code must be a two-letter abbreviation (e.g., 'NY', 'CA')");
  }
  
  return { valid: errors.length === 0, errors };
}

function validateZipCode(zipCode: string): ValidationResult {
  const errors: string[] = [];
  
  if (!zipCode) {
    return { valid: true, errors: [] }; // Optional field
  }
  
  if (!/^\d{5}(-\d{4})?$/.test(zipCode)) {
    errors.push("ZIP code must be in format XXXXX or XXXXX-XXXX");
  }
  
  return { valid: errors.length === 0, errors };
}

function validatePhoneNumber(phoneNumber: string): ValidationResult {
  const errors: string[] = [];
  
  if (!phoneNumber) {
    return { valid: true, errors: [] }; // Optional field
  }
  
  if (!/^\+?[\d\s\-\(\)]+$/.test(phoneNumber)) {
    errors.push("Phone number contains invalid characters");
  }
  
  return { valid: errors.length === 0, errors };
}

function validateFormData(formData: any): ValidationResult {
  const errors: string[] = [];
  
  // Validate payer address components
  const payerStateResult = validateStateCode(formData.payerState);
  errors.push(...payerStateResult.errors);
  
  const payerZipResult = validateZipCode(formData.payerZip);
  errors.push(...payerZipResult.errors);
  
  const payerPhoneResult = validatePhoneNumber(formData.payerTelephoneNumber);
  errors.push(...payerPhoneResult.errors);
  
  // Validate recipient address components
  const recipientStateResult = validateStateCode(formData.recipientState);
  errors.push(...recipientStateResult.errors);
  
  const recipientZipResult = validateZipCode(formData.recipientZip);
  errors.push(...recipientZipResult.errors);
  
  // Validate multi-state fields
  const state2Result = validateStateCode(formData.state2);
  errors.push(...state2Result.errors);
  
  return { valid: errors.length === 0, errors };
}

// Usage
const formData = {
  calendarYear: "2024",
  payerName: "Example Corp",
  payerTIN: "12-3456789",
  payerCity: "New York",
  payerState: "NY",
  payerZip: "10001",
  payerTelephoneNumber: "(555) 123-4567",
  recipientName: "John Doe",
  recipientTIN: "123-45-6789",
  totalOrdinaryDividends: "1000.00"
};

const result = validateFormData(formData);
if (!result.valid) {
  console.error("Validation errors:", result.errors);
} else {
  console.log("Form data is valid");
}
```


## Timeline

### Phase 1: Current (Now - 6 Months)

**Status:** ✅ Active

**What's Available:**
- All new fields are available and fully functional
- Both old and new address formats work
- Multi-state tax reporting is supported
- No breaking changes

**Action Required:**
- None - existing integrations continue to work
- Optional: Begin planning migration to new format

**Recommendations:**
- Review the new fields and determine which ones you need
- Test the new fields in a development environment
- Plan your migration timeline

### Phase 2: Transition Period (6-12 Months)

**Status:** ⚠️ Deprecation Warnings

**What Changes:**
- Deprecation warnings logged for combined address format
- Warnings visible in CloudWatch logs
- No functional changes - both formats still work

**Action Required:**
- Monitor logs for deprecation warnings
- Begin migrating to new separate address format
- Update documentation and internal guides

**Recommendations:**
- Migrate high-traffic integrations first
- Test thoroughly in staging environment
- Update API documentation

### Phase 3: Deprecation Notice (12-18 Months)

**Status:** ⚠️ Stronger Warnings

**What Changes:**
- More prominent deprecation warnings
- Documentation updated to show new format only
- Old format still functional but discouraged

**Action Required:**
- Complete migration to new format
- Remove any code that generates combined address format
- Verify all integrations use new format

**Recommendations:**
- Set internal deadline for migration completion
- Audit all systems using the API
- Update all documentation and examples

### Phase 4: Removal (After 18 Months)

**Status:** ❌ Breaking Change

**What Changes:**
- Combined address format no longer supported
- Requests with combined format will fail validation
- Only new separate field format accepted

**Action Required:**
- Must use new format for all requests
- Update any remaining legacy code
- Ensure all integrations are migrated

**Recommendations:**
- Complete migration well before this phase
- Have rollback plan ready
- Monitor error rates closely after cutover

### Timeline Summary

| Milestone | Date | Combined Format | New Format | Action |
|-----------|------|-----------------|------------|--------|
| **Release** | Now | ✅ Supported | ✅ Supported | None required |
| **Warnings Start** | +6 months | ⚠️ Warnings logged | ✅ Recommended | Plan migration |
| **Strong Warnings** | +12 months | ⚠️ Discouraged | ✅ Required | Complete migration |
| **Removal** | +18 months | ❌ Not supported | ✅ Only option | Must be migrated |


## Testing Recommendations

### Test Scenarios

Test your migration with these scenarios to ensure compatibility:

#### Scenario 1: Minimal Required Fields

Test with only required fields to ensure basic functionality:

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
  }
}
```

**Expected Result:** ✅ Success - PDF generated with required fields only

#### Scenario 2: New Address Fields

Test with new separate address components:

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "payerCity": "New York",
    "payerState": "NY",
    "payerZip": "10001",
    "payerTelephoneNumber": "(555) 123-4567",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "recipientCity": "Los Angeles",
    "recipientState": "CA",
    "recipientZip": "90001",
    "totalOrdinaryDividends": "1000.00"
  }
}
```

**Expected Result:** ✅ Success - PDF generated with all address components filled

#### Scenario 3: Multi-State Reporting

Test with two states:

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00",
    "state": "NY",
    "stateIdentificationNumber": "12-3456789",
    "stateTaxWithheld": "50.00",
    "state2": "CA",
    "stateIdentificationNumber2": "98-7654321",
    "stateTaxWithheld2": "25.00"
  }
}
```

**Expected Result:** ✅ Success - PDF generated with both states filled

#### Scenario 4: Backward Compatibility (Old Format)

Test with old combined address format:

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "payerCity": "New York, NY 10001",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
  }
}
```

**Expected Result:** ✅ Success - PDF generated, deprecation warning logged

#### Scenario 5: Invalid State Code

Test validation with invalid state code:

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "payerState": "New York",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
  }
}
```

**Expected Result:** ❌ Validation error - "State code must be a two-letter abbreviation"

#### Scenario 6: Invalid ZIP Code

Test validation with invalid ZIP code:

```json
{
  "documentType": "1099-DIV",
  "formData": {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "payerZip": "1001",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
  }
}
```

**Expected Result:** ❌ Validation error - "ZIP code must be in format XXXXX or XXXXX-XXXX"

### Automated Testing

Consider adding automated tests for the migration:

```python
import pytest
import requests

BASE_URL = "https://api.example.com"
TOKEN = "your-jwt-token"

def test_new_address_format():
    """Test new separate address format."""
    payload = {
        "documentType": "1099-DIV",
        "formData": {
            "calendarYear": "2024",
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "payerCity": "New York",
            "payerState": "NY",
            "payerZip": "10001",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/generate",
        json=payload,
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    
    assert response.status_code == 200
    assert "jobId" in response.json()

def test_multi_state_reporting():
    """Test multi-state tax reporting."""
    payload = {
        "documentType": "1099-DIV",
        "formData": {
            "calendarYear": "2024",
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00",
            "state": "NY",
            "stateIdentificationNumber": "12-3456789",
            "stateTaxWithheld": "50.00",
            "state2": "CA",
            "stateIdentificationNumber2": "98-7654321",
            "stateTaxWithheld2": "25.00"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/generate",
        json=payload,
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    
    assert response.status_code == 200
    assert "jobId" in response.json()

def test_backward_compatibility():
    """Test old combined address format still works."""
    payload = {
        "documentType": "1099-DIV",
        "formData": {
            "calendarYear": "2024",
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "payerCity": "New York, NY 10001",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/generate",
        json=payload,
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    
    assert response.status_code == 200
    assert "jobId" in response.json()
```


## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Validation Error - Invalid State Code

**Error Message:**
```json
{
  "error": "Validation failed",
  "details": {
    "field": "payerState",
    "message": "State code must be a two-letter abbreviation (e.g., 'NY', 'CA')"
  }
}
```

**Cause:** State code is not in the correct format (must be two uppercase letters)

**Solution:**
```python
# ❌ Wrong
"payerState": "New York"
"payerState": "ny"
"payerState": "N"

# ✅ Correct
"payerState": "NY"
```

#### Issue 2: Validation Error - Invalid ZIP Code

**Error Message:**
```json
{
  "error": "Validation failed",
  "details": {
    "field": "payerZip",
    "message": "ZIP code must be in format XXXXX or XXXXX-XXXX"
  }
}
```

**Cause:** ZIP code is not in the correct format

**Solution:**
```python
# ❌ Wrong
"payerZip": "1001"          # Too short
"payerZip": "100011"        # Too long
"payerZip": "10001 1234"    # Space instead of hyphen

# ✅ Correct
"payerZip": "10001"         # 5-digit format
"payerZip": "10001-1234"    # 9-digit format with hyphen
```

#### Issue 3: Deprecation Warnings in Logs

**Warning Message:**
```
WARNING: Deprecated field format detected: payerCity contains combined address.
Please use separate payerCity, payerState, and payerZip fields.
Combined format will be removed in a future version.
```

**Cause:** Using old combined address format

**Solution:** Migrate to separate address fields:
```python
# ❌ Old format (triggers warning)
"payerCity": "New York, NY 10001"

# ✅ New format (no warning)
"payerCity": "New York"
"payerState": "NY"
"payerZip": "10001"
```

#### Issue 4: Multi-State Fields Not Appearing

**Problem:** Second state information not showing on PDF

**Possible Causes:**
1. Missing one or more of the three required fields (state2, stateIdentificationNumber2, stateTaxWithheld2)
2. Field names misspelled
3. Values not provided

**Solution:** Ensure all three fields are provided together:
```python
# ❌ Incomplete (missing stateTaxWithheld2)
"state2": "CA"
"stateIdentificationNumber2": "98-7654321"

# ✅ Complete
"state2": "CA"
"stateIdentificationNumber2": "98-7654321"
"stateTaxWithheld2": "25.00"
```

#### Issue 5: Phone Number Validation Error

**Error Message:**
```json
{
  "error": "Validation failed",
  "details": {
    "field": "payerTelephoneNumber",
    "message": "Phone number contains invalid characters"
  }
}
```

**Cause:** Phone number contains invalid characters

**Solution:**
```python
# ❌ Wrong
"payerTelephoneNumber": "555.123.4567"      # Dots not allowed
"payerTelephoneNumber": "Call: 555-1234"    # Text not allowed
"payerTelephoneNumber": "555-CALL"          # Letters not allowed

# ✅ Correct
"payerTelephoneNumber": "(555) 123-4567"
"payerTelephoneNumber": "555-123-4567"
"payerTelephoneNumber": "+1 555 123 4567"
"payerTelephoneNumber": "5551234567"
```

#### Issue 6: Mixed Old and New Format

**Problem:** Using both old and new format in the same request

**Example:**
```python
# ⚠️ Confusing - mixed format
"payerCity": "New York, NY 10001"  # Old format
"payerState": "NY"                  # New format
"payerZip": "10001"                 # New format
```

**Solution:** Use one format consistently:
```python
# ✅ Better - new format only
"payerCity": "New York"
"payerState": "NY"
"payerZip": "10001"
```

**Note:** If both formats are provided, the new format takes precedence.


## Frequently Asked Questions

### General Questions

**Q: Do I need to update my integration immediately?**

A: No. The comprehensive schema update maintains 100% backward compatibility. Your existing integrations will continue to work without any changes. However, we recommend migrating to the new format within the next 6 months to take advantage of the improvements and avoid future deprecation warnings.

**Q: Will my existing API requests break?**

A: No. All existing field names and formats continue to work. The system automatically handles both old and new address formats.

**Q: What happens if I don't migrate?**

A: Your integration will continue to work during the transition period (18 months). After that, the old combined address format will no longer be supported, and requests using it will fail validation.

**Q: Can I use both old and new formats in the same request?**

A: Yes, but it's not recommended. If both formats are provided, the new format takes precedence. For clarity and consistency, use one format throughout your request.

### Address Field Questions

**Q: What's the difference between the old and new address formats?**

A: The old format combined city, state, and ZIP in a single field (e.g., "New York, NY 10001"). The new format provides separate fields for each component (payerCity, payerState, payerZip), which allows for better validation and data structure.

**Q: Do I need to provide all address components?**

A: No. All address component fields are optional. You can provide as many or as few as you need. However, if you provide a state code, it must be in the correct two-letter format.

**Q: What about international addresses?**

A: Use the `payerCountry` and `recipientCountry` fields for international addresses. State codes are optional for international addresses, and ZIP codes can be in any format for non-US addresses.

**Q: Can I still use the combined address format?**

A: Yes, during the transition period (18 months). However, deprecation warnings will be logged, and the format will eventually be removed. We recommend migrating to the new format as soon as possible.

### Multi-State Questions

**Q: How many states can I report?**

A: The IRS Form 1099-DIV supports up to two states. Use the first state fields (state, stateIdentificationNumber, stateTaxWithheld) for the first state, and the second state fields (state2, stateIdentificationNumber2, stateTaxWithheld2) for the second state.

**Q: What if I only need to report one state?**

A: Use only the first state fields (without the "2" suffix). The second state fields are optional.

**Q: Do I need to provide all three fields for each state?**

A: Yes. If you provide any state field, you should provide all three fields for that state (state name, state ID, and tax withheld) to ensure data integrity.

**Q: Can I report more than two states?**

A: No. The IRS Form 1099-DIV only has space for two states. If you need to report more than two states, you may need to file multiple forms or consult with a tax professional.

### Validation Questions

**Q: What state codes are valid?**

A: Valid state codes are two-letter uppercase abbreviations (e.g., "NY", "CA", "TX"). See the [USPS state abbreviations list](https://pe.usps.com/text/pub28/28apb.htm) for a complete list.

**Q: What ZIP code formats are accepted?**

A: Two formats are accepted: 5-digit (e.g., "10001") and 9-digit with hyphen (e.g., "10001-1234"). Spaces are not allowed.

**Q: What phone number formats are accepted?**

A: Phone numbers can contain digits, spaces, hyphens, parentheses, and an optional leading plus sign. Common formats like "(555) 123-4567", "555-123-4567", and "+1 555 123 4567" are all valid.

**Q: Are the new fields required?**

A: No. All new fields are optional. The only required fields remain: calendarYear, payerName, payerTIN, recipientName, recipientTIN, and totalOrdinaryDividends.

### Technical Questions

**Q: How does the system detect the old address format?**

A: The system checks if the payerCity or recipientCity field contains a comma. If it does, the system assumes it's in the old combined format and automatically parses it into separate components.

**Q: What happens if I provide both old and new formats?**

A: If both formats are provided (e.g., both "payerCity": "New York, NY 10001" and "payerState": "NY"), the new format takes precedence. The system will use the explicitly provided payerState and payerZip values.

**Q: Will the API version change?**

A: No. This is a backward-compatible enhancement to the existing API. The API version remains the same.

**Q: How can I test the new fields?**

A: Use the example JSON payloads in the [examples directory](../examples/) or refer to the test scenarios in this guide. You can test in your development environment before deploying to production.


## Getting Help

### Documentation Resources

- **[1099-DIV Field Reference](1099-DIV_FIELD_REFERENCE.md)** - Complete field documentation with descriptions, validation rules, and examples
- **[Example JSON Payloads](../examples/)** - Sample requests showing minimal, typical, and complete data
- **[Field Standardization Guide](MIGRATION_GUIDE_FIELD_STANDARDIZATION.md)** - Previous migration guide for field mapping standardization

### Support Channels

If you encounter issues during migration:

1. **Review this guide** - Check the troubleshooting section and FAQ
2. **Check the field reference** - Verify field names, types, and validation rules
3. **Test with examples** - Use the provided example JSON payloads
4. **Review logs** - Check CloudWatch logs for detailed error messages
5. **Contact support** - Reach out to the development team for assistance

### Reporting Issues

When reporting issues, please include:

- **Request payload** - The JSON payload you're sending (sanitize sensitive data)
- **Error message** - The complete error response from the API
- **Expected behavior** - What you expected to happen
- **Actual behavior** - What actually happened
- **Environment** - Development, staging, or production
- **Timestamp** - When the issue occurred (for log correlation)

### Feedback

We welcome feedback on this migration guide and the comprehensive schema update:

- **Suggestions** - Ideas for improving the migration process
- **Documentation** - Requests for additional examples or clarification
- **Features** - Requests for additional fields or functionality

## Summary

The comprehensive 1099-DIV schema update provides:

✅ **Complete IRS Compliance** - All IRS-defined fields are now supported

✅ **Better Data Structure** - Separate address components for improved validation and data quality

✅ **Multi-State Support** - Report state tax information for up to two states

✅ **Enhanced Validation** - Proper validation for state codes, ZIP codes, and phone numbers

✅ **Backward Compatibility** - Existing integrations continue to work without changes

✅ **Smooth Migration Path** - 18-month transition period with clear milestones

### Key Takeaways

1. **No immediate action required** - Your existing integrations will continue to work
2. **Plan your migration** - Review the new fields and plan your migration timeline
3. **Test thoroughly** - Use the provided test scenarios to validate your migration
4. **Migrate within 6 months** - Avoid deprecation warnings by migrating early
5. **Complete by 18 months** - Old format will be removed after 18 months

### Next Steps

1. ✅ Review the [1099-DIV Field Reference](1099-DIV_FIELD_REFERENCE.md)
2. ✅ Examine the [example JSON payloads](../examples/)
3. ✅ Test the new fields in your development environment
4. ✅ Update your data models and API requests
5. ✅ Deploy to staging and test thoroughly
6. ✅ Deploy to production
7. ✅ Monitor logs for deprecation warnings
8. ✅ Complete migration within 6 months

### Migration Checklist

Use this checklist to track your migration progress:

- [ ] Reviewed new field documentation
- [ ] Identified which new fields are needed
- [ ] Updated data models to include new fields
- [ ] Updated address parsing logic (if applicable)
- [ ] Updated API request payloads
- [ ] Added validation for new field formats
- [ ] Tested with minimal data set
- [ ] Tested with typical data set
- [ ] Tested with complete data set
- [ ] Tested multi-state reporting (if needed)
- [ ] Tested backward compatibility
- [ ] Updated internal documentation
- [ ] Deployed to staging environment
- [ ] Verified in staging
- [ ] Deployed to production
- [ ] Monitored production logs
- [ ] Confirmed no deprecation warnings

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Related Documents:**
- [1099-DIV Field Reference](1099-DIV_FIELD_REFERENCE.md)
- [Field Standardization Migration Guide](MIGRATION_GUIDE_FIELD_STANDARDIZATION.md)
- [Example JSON Payloads](../examples/)

For questions or assistance, please contact the development team.
