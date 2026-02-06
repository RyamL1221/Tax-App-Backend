"""
Validation script for field mapping standardization.

This script validates that:
1. All mappings point to valid PDF field names
2. No duplicate mappings exist
3. All required fields have mappings
4. Metadata is complete for all fields

Requirements: 9.1, 9.2, 9.3
"""

import logging
from field_mapper import FieldMapper
from field_mappings.canonical_div_1099 import CANONICAL_FIELD_MAPPING
from field_mappings.field_metadata import FIELD_METADATA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_no_duplicate_mappings():
    """Validate that no two API fields map to the same PDF field."""
    logger.info("Validating no duplicate PDF field mappings...")
    
    pdf_fields = {}
    duplicates = []
    
    for api_field, pdf_field in CANONICAL_FIELD_MAPPING.items():
        if pdf_field in pdf_fields:
            duplicates.append({
                'pdf_field': pdf_field,
                'api_fields': [pdf_fields[pdf_field], api_field]
            })
        else:
            pdf_fields[pdf_field] = api_field
    
    if duplicates:
        logger.error(f"Found {len(duplicates)} duplicate mappings:")
        for dup in duplicates:
            logger.error(f"  PDF field '{dup['pdf_field']}' mapped by: {dup['api_fields']}")
        return False
    
    logger.info(f"✓ No duplicate mappings found ({len(CANONICAL_FIELD_MAPPING)} unique mappings)")
    return True


def validate_all_fields_have_metadata():
    """Validate that all fields in CANONICAL_FIELD_MAPPING have metadata."""
    logger.info("Validating metadata completeness...")
    
    missing_metadata = []
    
    for field_name in CANONICAL_FIELD_MAPPING.keys():
        if field_name not in FIELD_METADATA:
            missing_metadata.append(field_name)
    
    if missing_metadata:
        logger.error(f"Found {len(missing_metadata)} fields without metadata:")
        for field in missing_metadata:
            logger.error(f"  - {field}")
        return False
    
    logger.info(f"✓ All {len(CANONICAL_FIELD_MAPPING)} fields have metadata")
    return True


def validate_required_fields_have_mappings():
    """Validate that all required fields have mappings."""
    logger.info("Validating required field mappings...")
    
    required_fields = [
        field_name for field_name, metadata in FIELD_METADATA.items()
        if metadata["required"]
    ]
    
    missing_mappings = []
    
    for field_name in required_fields:
        if field_name not in CANONICAL_FIELD_MAPPING:
            missing_mappings.append(field_name)
    
    if missing_mappings:
        logger.error(f"Found {len(missing_mappings)} required fields without mappings:")
        for field in missing_mappings:
            logger.error(f"  - {field}")
        return False
    
    logger.info(f"✓ All {len(required_fields)} required fields have mappings")
    return True


def validate_pdf_field_name_format():
    """Validate that all PDF field names follow the expected format."""
    logger.info("Validating PDF field name format...")
    
    invalid_fields = []
    
    for api_field, pdf_field in CANONICAL_FIELD_MAPPING.items():
        # Check that field starts with topmostSubform[0]
        if not pdf_field.startswith("topmostSubform[0]"):
            invalid_fields.append({
                'api_field': api_field,
                'pdf_field': pdf_field,
                'reason': 'Does not start with topmostSubform[0]'
            })
        
        # Check that field contains Copy1[0]
        if "Copy1[0]" not in pdf_field:
            invalid_fields.append({
                'api_field': api_field,
                'pdf_field': pdf_field,
                'reason': 'Does not contain Copy1[0]'
            })
    
    if invalid_fields:
        logger.error(f"Found {len(invalid_fields)} fields with invalid format:")
        for field in invalid_fields:
            logger.error(f"  - {field['api_field']}: {field['reason']}")
            logger.error(f"    PDF field: {field['pdf_field']}")
        return False
    
    logger.info(f"✓ All {len(CANONICAL_FIELD_MAPPING)} PDF field names follow correct format")
    return True


def validate_field_mapper_integration():
    """Validate that FieldMapper works with the new configuration."""
    logger.info("Validating FieldMapper integration...")
    
    try:
        mapper = FieldMapper("1099-DIV")
        
        # Test basic mapping
        pdf_field = mapper.map_field("payerName")
        if pdf_field is None:
            logger.error("Failed to map payerName")
            return False
        
        # Test validation
        form_data = {
            "calendarYear": "2024",
            "payerName": "Test Corp",
            "payerTIN": "12-3456789",
            "recipientName": "John Doe",
            "recipientTIN": "123-45-6789",
            "totalOrdinaryDividends": "1000.00"
        }
        
        missing = mapper.validate_required_fields(form_data)
        if len(missing) != 0:
            logger.error(f"Validation failed: {missing}")
            return False
        
        # Test multi-copy mapping
        mapped = mapper.map_all_fields(form_data)
        if len(mapped) != 18:  # 6 fields × 3 copies
            logger.error(f"Expected 18 mapped fields, got {len(mapped)}")
            return False
        
        logger.info("✓ FieldMapper integration working correctly")
        return True
        
    except Exception as e:
        logger.error(f"FieldMapper integration failed: {e}")
        return False


def main():
    """Run all validation checks."""
    logger.info("=" * 70)
    logger.info("Field Mapping Standardization Validation")
    logger.info("=" * 70)
    
    results = {
        "No duplicate mappings": validate_no_duplicate_mappings(),
        "Metadata completeness": validate_all_fields_have_metadata(),
        "Required field mappings": validate_required_fields_have_mappings(),
        "PDF field name format": validate_pdf_field_name_format(),
        "FieldMapper integration": validate_field_mapper_integration()
    }
    
    logger.info("=" * 70)
    logger.info("Validation Results:")
    logger.info("=" * 70)
    
    all_passed = True
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {check}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 70)
    
    if all_passed:
        logger.info("✓ All validation checks passed!")
        logger.info(f"  - {len(CANONICAL_FIELD_MAPPING)} field mappings validated")
        logger.info(f"  - {len(FIELD_METADATA)} field metadata entries validated")
        logger.info(f"  - {len([m for m in FIELD_METADATA.values() if m['required']])} required fields validated")
        return 0
    else:
        logger.error("✗ Some validation checks failed")
        return 1


if __name__ == "__main__":
    exit(main())
