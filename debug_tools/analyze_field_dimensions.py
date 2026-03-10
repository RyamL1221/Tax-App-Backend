#!/usr/bin/env python3
"""
Field Dimension Analysis Tool

This script extracts and analyzes field dimensions from the 1099-DIV PDF template
to identify optimal font sizes for different field types.

This tool:
1. Extracts all form field dimensions from the PDF template
2. Groups fields by column type (LeftCol, RghtCol, CopyHeader)
3. Calculates statistics (min, max, average dimensions)
4. Recommends font sizes based on field heights
5. Outputs detailed analysis for debugging rendering issues

Usage:
    python analyze_field_dimensions.py [template_path]

Requirements: 4.1, 4.2, 4.3
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

try:
    import fitz  # PyMuPDF
except ImportError as e:
    raise ImportError(
        "PyMuPDF is required for PDF analysis. "
        "Install with: pip install PyMuPDF>=1.23.0"
    ) from e


@dataclass
class FieldDimensions:
    """Dimensions and location of a PDF form field."""
    field_name: str
    width: float
    height: float
    x: float
    y: float
    page: int
    column: str = ""  # 'LeftCol', 'RghtCol', 'CopyHeader', etc.


@dataclass
class ColumnStats:
    """Statistics for a column of fields."""
    column_name: str
    field_count: int = 0
    min_height: float = float('inf')
    max_height: float = 0.0
    avg_height: float = 0.0
    min_width: float = float('inf')
    max_width: float = 0.0
    avg_width: float = 0.0
    fields: List[FieldDimensions] = field(default_factory=list)
    
    def add_field(self, field_dim: FieldDimensions):
        """Add a field to this column's statistics."""
        self.fields.append(field_dim)
        self.field_count += 1
        self.min_height = min(self.min_height, field_dim.height)
        self.max_height = max(self.max_height, field_dim.height)
        self.min_width = min(self.min_width, field_dim.width)
        self.max_width = max(self.max_width, field_dim.width)
    
    def calculate_averages(self):
        """Calculate average dimensions."""
        if self.field_count > 0:
            self.avg_height = sum(f.height for f in self.fields) / self.field_count
            self.avg_width = sum(f.width for f in self.fields) / self.field_count


def determine_column_type(field_name: str) -> str:
    """
    Determine the column type from the field name.
    
    Args:
        field_name: PDF field name
        
    Returns:
        Column type string ('LeftCol', 'RghtCol', 'CopyHeader', 'Other')
    """
    if 'LeftCol' in field_name:
        return 'LeftCol'
    elif 'RghtCol' in field_name:
        return 'RghtCol'
    elif 'CopyHeader' in field_name:
        return 'CopyHeader'
    else:
        return 'Other'


def extract_field_dimensions(pdf_path: str) -> List[FieldDimensions]:
    """
    Extract dimensions for all form fields in the PDF.
    
    Args:
        pdf_path: Path to PDF template
        
    Returns:
        List of FieldDimensions objects
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    dimensions = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        
        if widgets:
            for widget in widgets:
                if widget.field_name:
                    rect = widget.rect
                    column = determine_column_type(widget.field_name)
                    
                    field_dim = FieldDimensions(
                        field_name=widget.field_name,
                        width=rect.width,
                        height=rect.height,
                        x=rect.x0,
                        y=rect.y0,
                        page=page_num,
                        column=column
                    )
                    dimensions.append(field_dim)
    
    doc.close()
    return dimensions


def group_by_column(dimensions: List[FieldDimensions]) -> Dict[str, ColumnStats]:
    """
    Group field dimensions by column type and calculate statistics.
    
    Args:
        dimensions: List of FieldDimensions objects
        
    Returns:
        Dictionary mapping column names to ColumnStats objects
    """
    columns = {}
    
    for field_dim in dimensions:
        column_name = field_dim.column
        
        if column_name not in columns:
            columns[column_name] = ColumnStats(column_name=column_name)
        
        columns[column_name].add_field(field_dim)
    
    # Calculate averages for each column
    for column_stats in columns.values():
        column_stats.calculate_averages()
    
    return columns


def recommend_font_size(height: float) -> Tuple[float, float, float]:
    """
    Recommend font sizes based on field height.
    
    Args:
        height: Field height in points
        
    Returns:
        Tuple of (default_font_size, min_font_size, max_font_size)
    """
    # General rule: font size should be about 70-80% of field height
    # to allow for descenders and padding
    
    if height < 13:
        # Very small fields (like RghtCol)
        return (7.0, 6.0, 8.0)
    elif height < 20:
        # Small fields
        return (8.0, 7.0, 9.0)
    elif height < 30:
        # Medium fields (like LeftCol)
        return (9.0, 8.0, 10.0)
    else:
        # Large fields
        return (10.0, 9.0, 12.0)


def print_analysis_report(columns: Dict[str, ColumnStats], total_fields: int):
    """
    Print a detailed analysis report.
    
    Args:
        columns: Dictionary of column statistics
        total_fields: Total number of fields analyzed
    """
    print("=" * 80)
    print("FIELD DIMENSION ANALYSIS REPORT")
    print("=" * 80)
    print()
    print(f"Total fields analyzed: {total_fields}")
    print(f"Column types found: {len(columns)}")
    print()
    
    # Sort columns by name for consistent output
    sorted_columns = sorted(columns.items(), key=lambda x: x[0])
    
    for column_name, stats in sorted_columns:
        print("=" * 80)
        print(f"COLUMN: {column_name}")
        print("=" * 80)
        print()
        print(f"Field count: {stats.field_count}")
        print()
        
        print("Dimension Statistics:")
        print(f"  Height: min={stats.min_height:.2f}, max={stats.max_height:.2f}, avg={stats.avg_height:.2f}")
        print(f"  Width:  min={stats.min_width:.2f}, max={stats.max_width:.2f}, avg={stats.avg_width:.2f}")
        print()
        
        # Recommend font sizes based on minimum height
        default_font, min_font, max_font = recommend_font_size(stats.min_height)
        print("Recommended Font Sizes (based on minimum height):")
        print(f"  Default: {default_font}pt")
        print(f"  Minimum: {min_font}pt")
        print(f"  Maximum: {max_font}pt")
        print()
        
        # Show sample fields
        print("Sample fields (first 5):")
        for field_dim in stats.fields[:5]:
            print(f"  {field_dim.field_name}")
            print(f"    Dimensions: {field_dim.width:.2f} x {field_dim.height:.2f}")
            print(f"    Position: ({field_dim.x:.2f}, {field_dim.y:.2f})")
            print(f"    Page: {field_dim.page}")
            print()
        
        if stats.field_count > 5:
            print(f"  ... and {stats.field_count - 5} more fields")
            print()
    
    # Summary recommendations
    print("=" * 80)
    print("SUMMARY RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    print("Suggested FIELD_RENDERING_CONFIG:")
    print()
    print("FIELD_RENDERING_CONFIG = {")
    
    for column_name, stats in sorted_columns:
        if stats.field_count > 0:
            default_font, min_font, max_font = recommend_font_size(stats.min_height)
            print(f"    '{column_name}': {{")
            print(f"        'default_font_size': {default_font},")
            print(f"        'min_font_size': {min_font},")
            print(f"        'max_font_size': {max_font},")
            print(f"    }},")
    
    print("}")
    print()
    
    # Identify problematic fields
    print("=" * 80)
    print("POTENTIAL RENDERING ISSUES")
    print("=" * 80)
    print()
    
    small_fields = []
    for column_name, stats in sorted_columns:
        for field_dim in stats.fields:
            if field_dim.height < 13:
                small_fields.append(field_dim)
    
    if small_fields:
        print(f"Found {len(small_fields)} fields with height < 13pt (may have rendering issues):")
        print()
        for field_dim in small_fields[:10]:
            print(f"  {field_dim.field_name}")
            print(f"    Height: {field_dim.height:.2f}pt")
            print(f"    Recommended max font size: {recommend_font_size(field_dim.height)[2]}pt")
            print()
        
        if len(small_fields) > 10:
            print(f"  ... and {len(small_fields) - 10} more small fields")
            print()
    else:
        print("No fields with potential rendering issues found.")
        print()


def main():
    """
    Main analysis function.
    """
    # Determine template path
    if len(sys.argv) > 1:
        template_path = sys.argv[1]
    else:
        # Try multiple possible locations
        possible_paths = [
            "1099-DIV.pdf",  # Current directory
            "../1099-DIV.pdf",  # Parent directory
            "../../1099-DIV.pdf",  # Two levels up
            os.path.join(os.path.dirname(__file__), "..", "1099-DIV.pdf"),  # Relative to script
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
            print("Usage: python analyze_field_dimensions.py [template_path]")
            sys.exit(1)
    
    print(f"Analyzing template: {os.path.abspath(template_path)}")
    print(f"Using PDF library: PyMuPDF (fitz)")
    print()
    
    try:
        # Extract field dimensions
        dimensions = extract_field_dimensions(template_path)
        
        if not dimensions:
            print("WARNING: No form fields found in PDF template")
            print("This may indicate:")
            print("  - The PDF has no form fields")
            print("  - The PDF is corrupted")
            print("  - The PDF library cannot read the fields")
            sys.exit(1)
        
        # Group by column and calculate statistics
        columns = group_by_column(dimensions)
        
        # Print analysis report
        print_analysis_report(columns, len(dimensions))
        
        print("=" * 80)
        print("Analysis complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"ERROR: Analysis failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
