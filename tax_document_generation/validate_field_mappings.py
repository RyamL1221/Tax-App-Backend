#!/usr/bin/env python3
"""
Validation script to verify field mappings against actual PDF template.

This script:
1. Loads the 1099-DIV PDF template
2. Extracts all PDF field names from the template
3. Compares mapping configuration against actual PDF fields
4. Reports any mappings that point to non-existent fields
5. Reports any PDF fields that have no mapping

Usage:
    python validate_field_mappings.py

Requirements: 5.3
"""

import sys
import os
from pathlib import Path

try:
    from pypdf import PdfReader
    USING_PYPDF = True
except ImportError:
    from PyPDF2 import PdfReader
    USING_PYPDF = False

# Add parent directory to path to import field mappings
sys.path.insert(0, str(Path(__file__).parent.parent))

from tax_document_generation.field_mappings.div_1099 import FIELD_MAPPING


def load_pdf_template(template_path: str) -> PdfReader:
    """
    Load the PDF template and return a PdfReader object.
    
    Args:
        template_path: Path to the PDF template file
        
    Returns:
        PdfReader object
        
    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    with open(template_path, 'rb') as f:
        reader = PdfReader(f)
    
    return reader


def extract_pdf_field_names(reader: PdfReader) -> set:
    """
    Extract all field names from the PDF template.
    
    Args:
        reader: PdfReader object
        
    Returns:
        Set of PDF field names
    """
    fields = reader.get_fields()
    
    if not fields:
        return set()
    
    return set(fields.keys())


def validate_mappings(mapping: dict, pdf_fields: set) -> tuple:
    """
    Validate that all mappings point to real PDF fields.
    
    Args:
        mapping: Dictionary of API field name -> PDF field name
        pdf_fields: Set of actual PDF field names from template
        
    Returns:
        Tuple of (valid_mappings, invalid_mappings, unmapped_pdf_fields)
    """
    valid_mappings = []
    invalid_mappings = []
    
    for api_field, pdf_field in mapping.items():
        if pdf_field in pdf_fields:
            valid_mappings.append((api_field, pdf_field))
        else:
            invalid_mappings.append((api_field, pdf_field))
    
    # Find PDF fields that have no mapping
    mapped_pdf_fields = set(mapping.values())
    unmapped_pdf_fields = pdf_fields - mapped_pdf_fields
    
    return valid_mappings, invalid_mappings, unmapped_pdf_fields


def print_validation_report(valid_mappings: list, invalid_mappings: list, 
                           unmapped_pdf_fields: set, total_pdf_fields: int):
    """
    Print a validation report.
    
    Args:
        valid_mappings: List of valid (api_field, pdf_field) tuples
        invalid_mappings: List of invalid (api_field, pdf_field) tuples
        unmapped_pdf_fields: Set of PDF fields with no mapping
        total_pdf_fields: Total number of PDF fields in template
    """
    print("=" * 80)
    print("FIELD MAPPING VALIDATION REPORT")
    print("=" * 80)
    print()
    
    print(f"Total API field mappings: {len(FIELD_MAPPING)}")
    print(f"Total PDF fields in template: {total_pdf_fields}")
    print()
    
    # Valid mappings
    print(f"✓ Valid mappings: {len(valid_mappings)}")
    if valid_mappings:
        print("  Sample valid mappings:")
        for api_field, pdf_field in valid_mappings[:5]:
            print(f"    {api_field} -> {pdf_field}")
        if len(valid_mappings) > 5:
            print(f"    ... and {len(valid_mappings) - 5} more")
    print()
    
    # Invalid mappings
    if invalid_mappings:
        print(f"✗ Invalid mappings: {len(invalid_mappings)}")
        print("  These mappings point to non-existent PDF fields:")
        for api_field, pdf_field in invalid_mappings:
            print(f"    {api_field} -> {pdf_field} (NOT FOUND)")
        print()
    else:
        print("✓ No invalid mappings found")
        print()
    
    # Unmapped PDF fields
    if unmapped_pdf_fields:
        print(f"⚠ Unmapped PDF fields: {len(unmapped_pdf_fields)}")
        print("  These PDF fields have no API mapping:")
        for pdf_field in sorted(unmapped_pdf_fields)[:10]:
            print(f"    {pdf_field}")
        if len(unmapped_pdf_fields) > 10:
            print(f"    ... and {len(unmapped_pdf_fields) - 10} more")
        print()
    else:
        print("✓ All PDF fields have mappings")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if invalid_mappings:
        print("❌ VALIDATION FAILED")
        print(f"   {len(invalid_mappings)} mapping(s) point to non-existent PDF fields")
        return False
    else:
        print("✅ VALIDATION PASSED")
        print("   All mappings point to valid PDF fields")
        return True


def main():
    """
    Main validation function.
    """
    # Determine template path
    # Try multiple possible locations
    possible_paths = [
        "1099-DIV.pdf",  # Current directory
        "../1099-DIV.pdf",  # Parent directory
        "../../1099-DIV.pdf",  # Two levels up
        os.path.join(os.path.dirname(__file__), "..", "..", "1099-DIV.pdf"),  # Relative to script
    ]
    
    template_path = None
    for path in possible_paths:
        if os.path.exists(path):
            template_path = path
            break
    
    if not template_path:
        print("ERROR: Could not find 1099-DIV.pdf template file")
        print("Searched in:")
        for path in possible_paths:
            print(f"  - {os.path.abspath(path)}")
        print()
        print("Please ensure the 1099-DIV.pdf file is in the project root directory")
        sys.exit(1)
    
    print(f"Using template: {os.path.abspath(template_path)}")
    print(f"Using PDF library: {'pypdf' if USING_PYPDF else 'PyPDF2'}")
    print()
    
    try:
        # Load the PDF template
        reader = load_pdf_template(template_path)
        
        # Extract PDF field names
        pdf_fields = extract_pdf_field_names(reader)
        
        if not pdf_fields:
            print("WARNING: No form fields found in PDF template")
            print("This may indicate:")
            print("  - The PDF has no form fields")
            print("  - The PDF is corrupted")
            print("  - The PDF library cannot read the fields")
            sys.exit(1)
        
        # Validate mappings
        valid_mappings, invalid_mappings, unmapped_pdf_fields = validate_mappings(
            FIELD_MAPPING, pdf_fields
        )
        
        # Print report
        success = print_validation_report(
            valid_mappings, invalid_mappings, unmapped_pdf_fields, len(pdf_fields)
        )
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"ERROR: Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
