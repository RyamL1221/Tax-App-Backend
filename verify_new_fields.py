#!/usr/bin/env python3
"""
Verification script for Task 4 checkpoint.
Verifies that all new fields added in Tasks 1-3 are properly mapped and have metadata.
"""

from tax_document_generation.field_mappings.canonical_div_1099 import CANONICAL_FIELD_MAPPING
from tax_document_generation.field_mappings.field_metadata import FIELD_METADATA

# New fields that should have been added in Tasks 2-3
NEW_PAYER_FIELDS = [
    "payerState",
    "payerCountry",
    "payerZip",
    "payerTelephoneNumber"
]

NEW_RECIPIENT_FIELDS = [
    "recipientCity",
    "recipientState",
    "recipientCountry",
    "recipientZip"
]

NEW_STATE_FIELDS = [
    "state2",
    "stateIdentificationNumber2",
    "stateTaxWithheld2"
]

ALL_NEW_FIELDS = NEW_PAYER_FIELDS + NEW_RECIPIENT_FIELDS + NEW_STATE_FIELDS

def verify_field_mappings():
    """Verify all new fields have mappings."""
    print("=" * 70)
    print("VERIFYING FIELD MAPPINGS")
    print("=" * 70)
    
    missing_mappings = []
    for field in ALL_NEW_FIELDS:
        if field in CANONICAL_FIELD_MAPPING:
            pdf_field = CANONICAL_FIELD_MAPPING[field]
            print(f"✓ {field:30s} → {pdf_field}")
        else:
            print(f"✗ {field:30s} → MISSING")
            missing_mappings.append(field)
    
    print()
    if missing_mappings:
        print(f"❌ FAILED: {len(missing_mappings)} fields missing mappings:")
        for field in missing_mappings:
            print(f"   - {field}")
        return False
    else:
        print(f"✅ PASSED: All {len(ALL_NEW_FIELDS)} new fields have mappings")
        return True

def verify_field_metadata():
    """Verify all new fields have metadata."""
    print("\n" + "=" * 70)
    print("VERIFYING FIELD METADATA")
    print("=" * 70)
    
    missing_metadata = []
    incomplete_metadata = []
    
    required_attributes = [
        'required', 'irs_box', 'description', 'section',
        'data_type', 'max_length', 'validation_pattern', 'example_value'
    ]
    
    for field in ALL_NEW_FIELDS:
        if field not in FIELD_METADATA:
            print(f"✗ {field:30s} → MISSING METADATA")
            missing_metadata.append(field)
        else:
            metadata = FIELD_METADATA[field]
            missing_attrs = [attr for attr in required_attributes if attr not in metadata]
            
            if missing_attrs:
                print(f"⚠ {field:30s} → INCOMPLETE (missing: {', '.join(missing_attrs)})")
                incomplete_metadata.append((field, missing_attrs))
            else:
                print(f"✓ {field:30s} → Complete metadata")
    
    print()
    if missing_metadata or incomplete_metadata:
        if missing_metadata:
            print(f"❌ {len(missing_metadata)} fields missing metadata:")
            for field in missing_metadata:
                print(f"   - {field}")
        if incomplete_metadata:
            print(f"⚠️  {len(incomplete_metadata)} fields have incomplete metadata:")
            for field, attrs in incomplete_metadata:
                print(f"   - {field}: missing {', '.join(attrs)}")
        return False
    else:
        print(f"✅ PASSED: All {len(ALL_NEW_FIELDS)} new fields have complete metadata")
        return True

def verify_metadata_quality():
    """Verify metadata quality for new fields."""
    print("\n" + "=" * 70)
    print("VERIFYING METADATA QUALITY")
    print("=" * 70)
    
    issues = []
    
    for field in ALL_NEW_FIELDS:
        if field not in FIELD_METADATA:
            continue
            
        metadata = FIELD_METADATA[field]
        
        # Check description is not empty
        if not metadata.get('description') or len(metadata['description']) < 10:
            issues.append(f"{field}: description too short or empty")
        
        # Check example value is not empty
        if not metadata.get('example_value'):
            issues.append(f"{field}: example_value is empty")
        
        # Check data type is valid
        valid_types = ['string', 'decimal', 'boolean']
        if metadata.get('data_type') not in valid_types:
            issues.append(f"{field}: invalid data_type '{metadata.get('data_type')}'")
        
        # Check section is valid
        valid_sections = ['metadata', 'payer', 'recipient', 'dividends', 'capital_gains', 
                         'distributions', 'taxes', 'other', 'account']
        if metadata.get('section') not in valid_sections:
            issues.append(f"{field}: invalid section '{metadata.get('section')}'")
        
        print(f"✓ {field:30s} → Quality checks passed")
    
    print()
    if issues:
        print(f"⚠️  Found {len(issues)} quality issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print(f"✅ PASSED: All metadata quality checks passed")
        return True

def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("TASK 4 CHECKPOINT: FIELD MAPPINGS AND METADATA VERIFICATION")
    print("=" * 70)
    print(f"\nVerifying {len(ALL_NEW_FIELDS)} new fields added in Tasks 1-3:")
    print(f"  - {len(NEW_PAYER_FIELDS)} new payer fields")
    print(f"  - {len(NEW_RECIPIENT_FIELDS)} new recipient fields")
    print(f"  - {len(NEW_STATE_FIELDS)} new state tax fields")
    print()
    
    results = []
    results.append(("Field Mappings", verify_field_mappings()))
    results.append(("Field Metadata", verify_field_metadata()))
    results.append(("Metadata Quality", verify_metadata_quality()))
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for check_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{check_name:30s} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Field mappings and metadata are correct!")
    else:
        print("❌ SOME CHECKS FAILED - Please review the issues above")
    print("=" * 70)
    print()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
