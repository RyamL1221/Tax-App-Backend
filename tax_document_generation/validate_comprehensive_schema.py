#!/usr/bin/env python3
"""
Validation script for 1099-DIV comprehensive schema field mappings.

This script verifies that all field mappings in canonical_div_1099.py
correspond to actual fields in the PDF template.

Usage:
    python tax_document_generation/validate_comprehensive_schema.py

Requirements: 8.1, 8.3
"""

import sys
import os
from typing import Set, Dict, List, Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is required. Install with: pip install PyMuPDF>=1.23.0")
    sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tax_document_generation.field_mappings.canonical_div_1099 import CANONICAL_FIELD_MAPPING


def extract_pdf_fields(pdf_path: str) -> Set[str]:
    """
    Extract all field names from PDF template.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Set of all field names found in the PDF
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        fitz.FileDataError: If PDF cannot be opened
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise fitz.FileDataError(f"Cannot open PDF: {str(e)}")
    
    field_names = set()
    
    # Iterate through all pages
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        
        # Extract field names from each widget
        for widget in widgets:
            field_name = widget.field_name
            if field_name:
                field_names.add(field_name)
    
    doc.close()
    return field_names


def load_canonical_mappings() -> Dict[str, str]:
    """
    Load canonical field mappings.
    
    Returns:
        Dictionary mapping API field names to PDF field names
    """
    return CANONICAL_FIELD_MAPPING.copy()


def validate_mappings(pdf_fields: Set[str], mappings: Dict[str, str]) -> Dict:
    """
    Validate that all mappings correspond to PDF fields.
    
    Args:
        pdf_fields: Set of field names from PDF template
        mappings: Dictionary of canonical field mappings
        
    Returns:
        Dictionary containing validation results:
        - valid_mappings: List of (api_field, pdf_field) tuples that are valid
        - invalid_mappings: List of (api_field, pdf_field) tuples that are invalid
        - unmapped_fields: List of PDF fields not mapped to any API field
        - total_pdf_fields: Total number of fields in PDF
        - total_mappings: Total number of canonical mappings
    """
    valid_mappings = []
    invalid_mappings = []
    mapped_pdf_fields = set()
    
    # Check each mapping
    for api_field, pdf_field in mappings.items():
        if pdf_field in pdf_fields:
            valid_mappings.append((api_field, pdf_field))
            mapped_pdf_fields.add(pdf_field)
        else:
            invalid_mappings.append((api_field, pdf_field))
    
    # Find unmapped PDF fields
    unmapped_fields = pdf_fields - mapped_pdf_fields
    
    return {
        'valid_mappings': valid_mappings,
        'invalid_mappings': invalid_mappings,
        'unmapped_fields': sorted(unmapped_fields),
        'total_pdf_fields': len(pdf_fields),
        'total_mappings': len(mappings)
    }


def generate_report(validation_results: Dict, pdf_path: str) -> int:
    """
    Generate validation report.
    
    Args:
        validation_results: Dictionary containing validation results
        pdf_path: Path to the PDF template
        
    Returns:
        Exit code: 0 if all mappings valid, 1 if issues found
    """
    print(f"\n{'='*80}")
    print("1099-DIV FIELD MAPPING VALIDATION")
    print(f"{'='*80}\n")
    
    print(f"PDF Template: {pdf_path}")
    print(f"Total PDF Fields: {validation_results['total_pdf_fields']}")
    print(f"Total Canonical Mappings: {validation_results['total_mappings']}")
    print()
    
    # Summary
    print("Validation Results:")
    print(f"  ✓ Valid Mappings: {len(validation_results['valid_mappings'])}")
    print(f"  ✗ Invalid Mappings: {len(validation_results['invalid_mappings'])}")
    print(f"  ⚠ Unmapped PDF Fields: {len(validation_results['unmapped_fields'])}")
    print()
    
    # Show invalid mappings if any
    if validation_results['invalid_mappings']:
        print(f"{'─'*80}")
        print("INVALID MAPPINGS (mapped to non-existent PDF fields):")
        print(f"{'─'*80}\n")
        
        for api_field, pdf_field in validation_results['invalid_mappings']:
            print(f"  API Field: {api_field}")
            print(f"  PDF Field: {pdf_field}")
            print(f"  Issue: PDF field does not exist in template")
            print()
    
    # Show unmapped fields if any
    if validation_results['unmapped_fields']:
        print(f"{'─'*80}")
        print("UNMAPPED PDF FIELDS (fields in PDF but not in canonical mapping):")
        print(f"{'─'*80}\n")
        
        # Group by copy for better readability
        copy1_fields = [f for f in validation_results['unmapped_fields'] if 'Copy1' in f]
        copy2_fields = [f for f in validation_results['unmapped_fields'] if 'Copy2' in f]
        copy3_fields = [f for f in validation_results['unmapped_fields'] if 'Copy3' in f]
        other_fields = [f for f in validation_results['unmapped_fields'] 
                       if f not in copy1_fields and f not in copy2_fields and f not in copy3_fields]
        
        if copy1_fields:
            print(f"  Copy1 Fields ({len(copy1_fields)}):")
            for field in copy1_fields[:10]:  # Show first 10
                print(f"    - {field}")
            if len(copy1_fields) > 10:
                print(f"    ... and {len(copy1_fields) - 10} more")
            print()
        
        if copy2_fields:
            print(f"  Copy2 Fields ({len(copy2_fields)}):")
            for field in copy2_fields[:10]:  # Show first 10
                print(f"    - {field}")
            if len(copy2_fields) > 10:
                print(f"    ... and {len(copy2_fields) - 10} more")
            print()
        
        if copy3_fields:
            print(f"  Copy3 Fields ({len(copy3_fields)}):")
            for field in copy3_fields[:10]:  # Show first 10
                print(f"    - {field}")
            if len(copy3_fields) > 10:
                print(f"    ... and {len(copy3_fields) - 10} more")
            print()
        
        if other_fields:
            print(f"  Other Fields ({len(other_fields)}):")
            for field in other_fields[:10]:  # Show first 10
                print(f"    - {field}")
            if len(other_fields) > 10:
                print(f"    ... and {len(other_fields) - 10} more")
            print()
    
    # Final status
    print(f"{'='*80}")
    if validation_results['invalid_mappings']:
        print("Status: FAIL - Invalid mappings detected")
        print(f"{'='*80}\n")
        return 1
    else:
        print("Status: PASS - All mappings are valid")
        print(f"{'='*80}\n")
        return 0


def main() -> int:
    """
    Main validation function.
    
    Returns:
        Exit code: 0 if all mappings valid, 1 if issues found
    """
    # Default PDF path
    pdf_path = "samples/1099-DIV.pdf"
    
    # Allow override from command line
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    try:
        print("Starting validation...")
        print(f"Loading PDF template: {pdf_path}")
        
        # Extract PDF fields
        pdf_fields = extract_pdf_fields(pdf_path)
        print(f"Found {len(pdf_fields)} fields in PDF template")
        
        # Load canonical mappings
        mappings = load_canonical_mappings()
        print(f"Loaded {len(mappings)} canonical field mappings")
        
        # Validate mappings
        print("Validating mappings...")
        validation_results = validate_mappings(pdf_fields, mappings)
        
        # Generate report
        exit_code = generate_report(validation_results, pdf_path)
        
        return exit_code
        
    except FileNotFoundError as e:
        print(f"\nError: {str(e)}")
        return 1
    except fitz.FileDataError as e:
        print(f"\nError: {str(e)}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
