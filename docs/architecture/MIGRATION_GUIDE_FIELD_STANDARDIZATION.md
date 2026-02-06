# Migration Guide: Field Mapping Standardization

## Overview

This guide helps you migrate to the standardized 1099-DIV field mapping configuration. The standardization improves code organization, documentation, and maintainability while maintaining 100% backward compatibility.

## What Changed?

### New Configuration Structure

The field mapping configuration has been reorganized into three separate modules:

1. **canonical_div_1099.py** - Clean, well-organized field mappings
2. **field_metadata.py** - Comprehensive metadata for all fields
3. **deprecated_aliases.py** - Backward compatibility mappings

### New FieldMapper Methods

The `FieldMapper` class now includes additional methods:

- `resolve_field_name(field_name)` - Resolves deprecated field names
- `get_field_metadata(field_name)` - Returns field metadata
- `is_required_field(field_name)` - Checks if field is required
- `validate_required_fields(form_data)` - Validates required fields

### Enhanced Documentation

- **1099-DIV_FIELD_REFERENCE.md** - Comprehensive field reference
- **MIGRATION_GUIDE_FIELD_STANDARDIZATION.md** - This guide
- Improved inline documentation in code

## Backward Compatibility Guarantee

**All existing API field names continue to work without any changes.**

- No breaking changes to the FieldMapper API
- All existing field names are supported
- Existing integrations will continue to function
- No immediate action required

## Migration Timeline

### Phase 1: Current (Immediate)
- New configuration is available
- Old configuration still works
- Both configurations coexist

### Phase 2: Transition (Next 6 Months)
- Update your code to use new methods (optional but recommended)
- Test with new configuration
- Update documentation references

### Phase 3: Deprecation (After 6 Months)
- Old configuration marked as deprecated
- Deprecation warnings logged
- Old configuration still functional

### Phase 4: Removal (After 12 Months)
- Old configuration removed
- Only new configuration supported

## How to Migrate

### Step 1: Update Imports (Optional)

If you're directly importing field mappings, update your imports:

**Before:**
```python
from field_mappings.div_1099 import FIELD_MAPPING
```

**After:**
```python
from field_mappings.canonical_div_1099 import CANONICAL_FIELD_MAPPING
from field_mappings.field_metadata import FIELD_METADATA
```

**Note:** If you're only using the `FieldMapper` class, no import changes are needed.

### Step 2: Use New Validation Methods (Recommended)

Take advantage of the new validation methods:

**Before:**
```python
mapper = FieldMapper("1099-DIV")

# Manual validation
required_fields = ["calendarYear", "payerName", "payerTIN", 
                   "recipientName", "recipientTIN", "totalOrdinaryDividends"]
missing = [f for f in required_fields if f not in form_data]
if missing:
    raise ValidationError(f"Missing required fields: {missing}")
```

**After:**
```python
mapper = FieldMapper("1099-DIV")

# Automatic validation
missing = mapper.validate_required_fields(form_data)
if missing:
    raise ValidationError(f"Missing required fields: {missing}")
```

### Step 3: Use Metadata for Dynamic Behavior (Recommended)

Use field metadata for dynamic validation and documentation:

**Before:**
```python
# Hardcoded field information
if field_name == "payerTIN":
    max_length = 11
    pattern = r"^\d{2}-?\d{7}$"
```

**After:**
```python
# Dynamic field information
metadata = mapper.get_field_metadata(field_name)
if metadata:
    max_length = metadata["max_length"]
    pattern = metadata["validation_pattern"]
```

### Step 4: Update Documentation References

Update any documentation that references field mappings:

- Point to `1099-DIV_FIELD_REFERENCE.md` for field information
- Update API documentation to reference new field metadata
- Update developer guides to use new validation methods

### Step 5: Test Your Integration

Run your existing tests to verify backward compatibility:

```bash
# Run your test suite
pytest tests/

# Verify all tests pass
```

## Code Examples

### Example 1: Basic Form Validation

```python
from tax_document_generation.field_mapper import FieldMapper

mapper = FieldMapper("1099-DIV")

form_data = {
    "calendarYear": "2024",
    "payerName": "Example Corporation",
    "payerTIN": "12-3456789",
    "recipientName": "John Doe",
    "recipientTIN": "123-45-6789",
    "totalOrdinaryDividends": "1000.00"
}

# Validate required fields
missing = mapper.validate_required_fields(form_data)
if missing:
    print(f"Missing required fields: {missing}")
else:
    print("All required fields present")

# Map to PDF fields
mapped = mapper.map_all_fields(form_data)
print(f"Mapped {len(form_data)} API fields to {len(mapped)} PDF fields")
```

### Example 2: Dynamic Field Validation

```python
from tax_document_generation.field_mapper import FieldMapper
import re

mapper = FieldMapper("1099-DIV")

def validate_field(field_name, value):
    """Validate a field using its metadata."""
    metadata = mapper.get_field_metadata(field_name)
    
    if not metadata:
        return False, "Unknown field"
    
    # Check max length
    if metadata["max_length"] and len(str(value)) > metadata["max_length"]:
        return False, f"Exceeds maximum length of {metadata['max_length']}"
    
    # Check validation pattern
    if metadata["validation_pattern"]:
        if not re.match(metadata["validation_pattern"], str(value)):
            return False, f"Does not match required pattern"
    
    return True, "Valid"

# Validate a field
is_valid, message = validate_field("payerTIN", "12-3456789")
print(f"payerTIN validation: {message}")
```

### Example 3: Generating API Documentation

```python
from tax_document_generation.field_mapper import FieldMapper

mapper = FieldMapper("1099-DIV")

# Generate field documentation
for field_name, metadata in mapper._metadata.items():
    required_str = "Required" if metadata["required"] else "Optional"
    irs_box = metadata["irs_box"] or "N/A"
    
    print(f"{field_name}:")
    print(f"  Status: {required_str}")
    print(f"  IRS Box: {irs_box}")
    print(f"  Description: {metadata['description']}")
    print(f"  Example: {metadata['example_value']}")
    print()
```

## Deprecated Field Names

Currently, no field names are deprecated. All existing field names continue to work.

If field names are deprecated in the future, they will be listed here with their canonical replacements.

### Future Deprecation Format

When field names are deprecated, they will be documented as follows:

| Deprecated Name | Canonical Name | Deprecation Date | Removal Date |
|----------------|----------------|------------------|--------------|
| (none yet) | - | - | - |

## Troubleshooting

### Issue: Tests Failing After Update

**Solution:** Ensure you're using the latest version of the FieldMapper class. The new methods are backward compatible.

### Issue: Missing Metadata

**Solution:** Verify that the canonical configuration files are present:
- `field_mappings/canonical_div_1099.py`
- `field_mappings/field_metadata.py`
- `field_mappings/deprecated_aliases.py`

### Issue: Import Errors

**Solution:** Check your import statements. If you're importing field mappings directly, update to use the new module names.

## Getting Help

If you encounter issues during migration:

1. Check this migration guide
2. Review the `1099-DIV_FIELD_REFERENCE.md` documentation
3. Run the test suite to verify compatibility
4. Contact the development team for assistance

## Benefits of Migrating

### Improved Code Quality
- Cleaner, more organized configuration
- Better separation of concerns
- Easier to maintain and update

### Better Documentation
- Comprehensive field reference
- Inline metadata for all fields
- Clear validation rules

### Enhanced Validation
- Automatic required field validation
- Metadata-driven validation rules
- Consistent error messages

### Future-Proof
- Ready for new IRS form types
- Extensible metadata structure
- Support for field deprecation

## Summary

The field mapping standardization improves code organization and documentation while maintaining 100% backward compatibility. No immediate action is required, but we recommend migrating to the new methods and documentation over the next 6 months to take advantage of the improvements.

For questions or assistance, please contact the development team.
