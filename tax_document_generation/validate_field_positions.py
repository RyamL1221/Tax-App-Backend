#!/usr/bin/env python3
"""
Position Validation Tool for 1099-DIV Field Positions

This script validates that fields in generated 1099-DIV PDFs appear in their
expected positions according to IRS form specifications. It compares actual
field positions against expected positions with a configurable tolerance.

Usage:
    python validate_field_positions.py <generated_pdf_path>
    
Example:
    python validate_field_positions.py samples/test-output-1099-DIV.pdf

Requirements: 4.4, 4.5
"""

import sys
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is required. Install with: pip install PyMuPDF>=1.23.0")
    sys.exit(1)


# Position tolerance in points (±5 points as specified in requirements)
POSITION_TOLERANCE = 5.0


@dataclass
class FieldPosition:
    """Expected field position specification."""
    x: float                    # X-coordinate (left edge)
    y: float                    # Y-coordinate (top edge)
    width: float                # Field width
    height: float               # Field height
    purpose: str                # Field purpose (e.g., "payer_tin", "recipient_name")
    column: str                 # Column location ("LeftCol" or "RghtCol")
    
    def __str__(self) -> str:
        return f"({self.x:.1f}, {self.y:.1f}) [{self.width:.1f}×{self.height:.1f}]"


@dataclass
class ActualFieldInfo:
    """Actual field information from generated PDF."""
    name: str                   # PDF field name
    x: float                    # X-coordinate
    y: float                    # Y-coordinate
    width: float                # Field width
    height: float               # Field height
    value: str                  # Field value
    page_num: int               # Page number (0-indexed)
    
    def __str__(self) -> str:
        return f"({self.x:.1f}, {self.y:.1f}) [{self.width:.1f}×{self.height:.1f}]"


@dataclass
class FieldError:
    """Field position error details."""
    field_name: str
    purpose: str
    expected_position: FieldPosition
    actual_position: Optional[ActualFieldInfo]
    distance: float             # Distance from expected position
    error_type: str             # "position_mismatch" or "missing_field"
    
    def __str__(self) -> str:
        if self.error_type == "missing_field":
            return f"{self.purpose}: MISSING (expected at {self.expected_position})"
        else:
            return (f"{self.purpose}: Position mismatch - "
                   f"expected {self.expected_position}, "
                   f"actual {self.actual_position}, "
                   f"distance {self.distance:.1f} points")


@dataclass
class ValidationReport:
    """Field position validation results."""
    correct_fields: List[Tuple[str, str]] = field(default_factory=list)  # (field_name, purpose)
    incorrect_fields: List[FieldError] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)  # Field purposes
    total_fields: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate percentage of correct fields."""
        if self.total_fields == 0:
            return 0.0
        return (len(self.correct_fields) / self.total_fields) * 100


# IRS 1099-DIV Form Layout Specification (Copy1 - Page 3)
# These positions are based on the actual PDF template inspection
# Coordinates are for the Copy1 form (the base copy used in mappings)
IRS_1099_DIV_LAYOUT = {
    # Payer Information Fields (LeftCol)
    "payer_name": FieldPosition(
        x=52.4, y=56.0, width=242.1, height=76.0,
        purpose="payer_name",
        column="LeftCol"
    ),
    "payer_street_address": FieldPosition(
        x=50.4, y=142.0, width=122.4, height=38.0,
        purpose="payer_street_address",
        column="LeftCol"
    ),
    "payer_city": FieldPosition(
        x=172.8, y=142.0, width=122.4, height=38.0,
        purpose="payer_city",
        column="LeftCol"
    ),
    "payer_tin": FieldPosition(
        x=52.4, y=262.0, width=242.1, height=26.0,
        purpose="payer_tin",
        column="LeftCol"
    ),
    
    # Recipient Information Fields (LeftCol)
    "recipient_name": FieldPosition(
        x=52.4, y=190.0, width=242.1, height=26.0,
        purpose="recipient_name",
        column="LeftCol"
    ),
    "recipient_tin": FieldPosition(
        x=50.4, y=334.0, width=244.8, height=26.0,
        purpose="recipient_tin",
        column="LeftCol"
    ),
    
    # Box Values (RghtCol)
    "total_ordinary_dividends": FieldPosition(
        x=305.2, y=60.0, width=89.8, height=12.0,
        purpose="total_ordinary_dividends",
        column="RghtCol"
    ),
    "qualified_dividends": FieldPosition(
        x=305.2, y=96.0, width=89.8, height=12.0,
        purpose="qualified_dividends",
        column="RghtCol"
    ),
    "total_capital_gain_distributions": FieldPosition(
        x=305.2, y=120.0, width=89.8, height=12.0,
        purpose="total_capital_gain_distributions",
        column="RghtCol"
    ),
}


def calculate_distance(expected: FieldPosition, actual: ActualFieldInfo) -> float:
    """
    Calculate Euclidean distance between expected and actual field positions.
    
    Args:
        expected: Expected field position
        actual: Actual field position
        
    Returns:
        Distance in points
    """
    dx = expected.x - actual.x
    dy = expected.y - actual.y
    return (dx ** 2 + dy ** 2) ** 0.5


def positions_match(expected: FieldPosition, actual: ActualFieldInfo, 
                   tolerance: float = POSITION_TOLERANCE) -> bool:
    """
    Check if actual position matches expected position within tolerance.
    
    Args:
        expected: Expected field position
        actual: Actual field position
        tolerance: Maximum allowed distance in points
        
    Returns:
        True if positions match within tolerance
    """
    distance = calculate_distance(expected, actual)
    return distance <= tolerance


def extract_field_positions(pdf_path: str, page_num: int = 2) -> Dict[str, ActualFieldInfo]:
    """
    Extract field positions from a generated PDF.
    
    Args:
        pdf_path: Path to the PDF file
        page_num: Page number to extract fields from (0-indexed, default=2 for Copy1)
        
    Returns:
        Dictionary mapping field names to ActualFieldInfo objects
        
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
    
    if page_num >= len(doc):
        raise ValueError(f"Page {page_num + 1} does not exist in PDF (total pages: {len(doc)})")
    
    fields = {}
    page = doc[page_num]
    widgets = page.widgets()
    
    for widget in widgets:
        if widget.field_name:
            rect = widget.rect
            field_info = ActualFieldInfo(
                name=widget.field_name,
                x=rect.x0,
                y=rect.y0,
                width=rect.width,
                height=rect.height,
                value=str(widget.field_value or ""),
                page_num=page_num
            )
            fields[widget.field_name] = field_info
    
    doc.close()
    return fields


def identify_field_by_purpose(fields: Dict[str, ActualFieldInfo], 
                              purpose: str) -> Optional[ActualFieldInfo]:
    """
    Identify a field by its purpose based on field name patterns.
    
    Args:
        fields: Dictionary of field names to ActualFieldInfo
        purpose: Field purpose to search for
        
    Returns:
        ActualFieldInfo if found, None otherwise
    """
    # Map purposes to field name patterns
    purpose_patterns = {
        "payer_name": ["f2_2[0]"],
        "payer_street_address": ["f2_3[0]"],
        "payer_city": ["f2_4[0]"],
        "payer_tin": ["f2_7[0]"],
        "recipient_name": ["f2_5[0]"],
        "recipient_tin": ["f2_8[0]"],
        "total_ordinary_dividends": ["f2_9[0]"],
        "qualified_dividends": ["f2_10[0]"],
        "total_capital_gain_distributions": ["f2_11[0]"],
    }
    
    patterns = purpose_patterns.get(purpose, [])
    
    for field_name, field_info in fields.items():
        for pattern in patterns:
            if pattern in field_name:
                return field_info
    
    return None


def validate_field_positions(pdf_path: str, 
                            layout_spec: Dict[str, FieldPosition] = IRS_1099_DIV_LAYOUT,
                            tolerance: float = POSITION_TOLERANCE,
                            page_num: int = 2) -> ValidationReport:
    """
    Validate field positions in a generated PDF against expected layout.
    
    Args:
        pdf_path: Path to the generated PDF
        layout_spec: Expected field layout specification
        tolerance: Position tolerance in points
        page_num: Page number to validate (0-indexed, default=2 for Copy1)
        
    Returns:
        ValidationReport with validation results
        
    Requirements: 4.4, 4.5
    """
    report = ValidationReport()
    report.total_fields = len(layout_spec)
    
    # Extract actual field positions
    try:
        actual_fields = extract_field_positions(pdf_path, page_num)
    except Exception as e:
        print(f"Error extracting field positions: {e}")
        # Mark all fields as missing
        for purpose in layout_spec.keys():
            report.missing_fields.append(purpose)
        return report
    
    # Validate each expected field
    for purpose, expected_pos in layout_spec.items():
        # Find the actual field
        actual_field = identify_field_by_purpose(actual_fields, purpose)
        
        if actual_field is None:
            # Field is missing
            report.missing_fields.append(purpose)
            error = FieldError(
                field_name="",
                purpose=purpose,
                expected_position=expected_pos,
                actual_position=None,
                distance=0.0,
                error_type="missing_field"
            )
            report.incorrect_fields.append(error)
        else:
            # Check if position matches
            if positions_match(expected_pos, actual_field, tolerance):
                # Position is correct
                report.correct_fields.append((actual_field.name, purpose))
            else:
                # Position is incorrect
                distance = calculate_distance(expected_pos, actual_field)
                error = FieldError(
                    field_name=actual_field.name,
                    purpose=purpose,
                    expected_position=expected_pos,
                    actual_position=actual_field,
                    distance=distance,
                    error_type="position_mismatch"
                )
                report.incorrect_fields.append(error)
    
    return report


def print_validation_report(report: ValidationReport, pdf_path: str) -> None:
    """
    Print a detailed validation report.
    
    Args:
        report: ValidationReport object
        pdf_path: Path to the validated PDF
        
    Requirements: 4.5
    """
    print(f"\n{'='*80}")
    print(f"FIELD POSITION VALIDATION REPORT")
    print(f"{'='*80}")
    print(f"PDF: {pdf_path}")
    print(f"Tolerance: ±{POSITION_TOLERANCE} points")
    print(f"{'='*80}\n")
    
    # Summary statistics
    print(f"Total fields validated: {report.total_fields}")
    print(f"Correct positions: {len(report.correct_fields)}")
    print(f"Incorrect positions: {len(report.incorrect_fields)}")
    print(f"Missing fields: {len(report.missing_fields)}")
    print(f"Success rate: {report.success_rate:.1f}%")
    print()
    
    # Correct fields
    if report.correct_fields:
        print(f"{'─'*80}")
        print(f"✓ CORRECT POSITIONS ({len(report.correct_fields)} fields)")
        print(f"{'─'*80}\n")
        for field_name, purpose in report.correct_fields:
            print(f"  ✓ {purpose}")
            print(f"    Field: {field_name}")
        print()
    
    # Incorrect fields
    if report.incorrect_fields:
        print(f"{'─'*80}")
        print(f"✗ INCORRECT POSITIONS ({len(report.incorrect_fields)} fields)")
        print(f"{'─'*80}\n")
        for error in report.incorrect_fields:
            if error.error_type == "missing_field":
                print(f"  ✗ {error.purpose}: MISSING")
                print(f"    Expected position: {error.expected_position}")
                print(f"    Expected column: {error.expected_position.column}")
            else:
                print(f"  ✗ {error.purpose}: POSITION MISMATCH")
                print(f"    Field: {error.field_name}")
                print(f"    Expected position: {error.expected_position}")
                print(f"    Actual position: {error.actual_position}")
                print(f"    Distance: {error.distance:.1f} points (tolerance: ±{POSITION_TOLERANCE})")
                print(f"    Expected column: {error.expected_position.column}")
            print()
    
    # Missing fields
    if report.missing_fields:
        print(f"{'─'*80}")
        print(f"⚠ MISSING FIELDS ({len(report.missing_fields)} fields)")
        print(f"{'─'*80}\n")
        for purpose in report.missing_fields:
            expected_pos = IRS_1099_DIV_LAYOUT.get(purpose)
            if expected_pos:
                print(f"  ⚠ {purpose}")
                print(f"    Expected at: {expected_pos}")
                print(f"    Expected column: {expected_pos.column}")
        print()
    
    # Final verdict
    print(f"{'='*80}")
    print(f"VALIDATION RESULT")
    print(f"{'='*80}\n")
    
    if len(report.correct_fields) == report.total_fields:
        print("✅ VALIDATION PASSED")
        print("   All fields appear in correct positions")
    elif len(report.correct_fields) > 0:
        print("⚠ VALIDATION PARTIALLY PASSED")
        print(f"   {len(report.correct_fields)}/{report.total_fields} fields in correct positions")
        print(f"   {len(report.incorrect_fields)} field(s) need correction")
    else:
        print("❌ VALIDATION FAILED")
        print("   No fields found in correct positions")
    
    print()


def main():
    """Command-line interface."""
    if len(sys.argv) != 2:
        print("Usage: python validate_field_positions.py <generated_pdf_path>")
        print("\nExample:")
        print("  python validate_field_positions.py samples/test-output-1099-DIV.pdf")
        print("\nThis script validates that fields in a generated 1099-DIV PDF appear")
        print("in their expected positions according to IRS form specifications.")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    try:
        # Validate field positions
        report = validate_field_positions(pdf_path)
        
        # Print report
        print_validation_report(report, pdf_path)
        
        # Exit with appropriate code
        if len(report.correct_fields) == report.total_fields:
            sys.exit(0)  # All fields correct
        else:
            sys.exit(1)  # Some fields incorrect or missing
            
    except Exception as e:
        print(f"Error: Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
