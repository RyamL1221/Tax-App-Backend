#!/usr/bin/env python3
"""
PDF Field Inspection Script

This script inspects PDF form fields and displays detailed information about each field,
including name, page number, position, type, current value, visual location, nearby text,
and form copy grouping. It helps identify correct field names for mapping purposes.

Usage:
    python inspect_pdf_fields.py <pdf_path>
    
Example:
    python inspect_pdf_fields.py templates/1099-DIV.pdf
"""

import sys
import os
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is required. Install with: pip install PyMuPDF>=1.23.0")
    sys.exit(1)


@dataclass
class FieldInfo:
    """Information about a PDF form field with visual context."""
    name: str                      # Full PDF field name
    page_num: int                  # Page number (0-indexed)
    rect: tuple                    # (x, y, width, height)
    field_type: str                # "text", "checkbox", etc.
    value: str                     # Current field value
    visual_location: str = ""      # "top-left", "top-right", "bottom-left", "bottom-right", "center"
    nearby_text: List[str] = field(default_factory=list)  # Text labels near the field
    form_copy: str = ""            # "Copy1", "Copy2", "CopyB", or "Base"
    column: str = ""               # "LeftCol", "RghtCol", "CopyHeader", or ""
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.name} (Page {self.page_num + 1}, {self.field_type}, {self.visual_location})"


def classify_visual_location(x: float, y: float, page_width: float, page_height: float) -> str:
    """
    Classify the visual location of a field on the page.
    
    Args:
        x: X-coordinate of the field
        y: Y-coordinate of the field
        page_width: Width of the page
        page_height: Height of the page
        
    Returns:
        Visual location: "top-left", "top-right", "bottom-left", "bottom-right", or "center"
    """
    # Define thresholds for center region (middle 20% of page)
    center_x_min = page_width * 0.4
    center_x_max = page_width * 0.6
    center_y_min = page_height * 0.4
    center_y_max = page_height * 0.6
    
    # Check if in center region
    if center_x_min <= x <= center_x_max and center_y_min <= y <= center_y_max:
        return "center"
    
    # Determine horizontal position
    is_left = x < page_width / 2
    
    # Determine vertical position
    is_top = y < page_height / 2
    
    # Combine to get location
    if is_top and is_left:
        return "top-left"
    elif is_top and not is_left:
        return "top-right"
    elif not is_top and is_left:
        return "bottom-left"
    else:
        return "bottom-right"


def extract_nearby_text(page: fitz.Page, field_rect: fitz.Rect, search_radius: float = 50.0) -> List[str]:
    """
    Extract text near a field to identify labels.
    
    Args:
        page: PyMuPDF page object
        field_rect: Rectangle of the field
        search_radius: Radius in points to search for text
        
    Returns:
        List of nearby text strings
    """
    # Expand the field rectangle to search for nearby text
    search_rect = fitz.Rect(
        field_rect.x0 - search_radius,
        field_rect.y0 - search_radius,
        field_rect.x1 + search_radius,
        field_rect.y1 + search_radius
    )
    
    # Extract text from the search area
    text_instances = page.get_text("words", clip=search_rect)
    
    # Filter and clean text
    nearby_text = []
    for inst in text_instances:
        # inst is (x0, y0, x1, y1, "word", block_no, line_no, word_no)
        if len(inst) >= 5:
            word = inst[4].strip()
            if word and len(word) > 1:  # Skip single characters
                nearby_text.append(word)
    
    return nearby_text


def identify_form_copy(field_name: str) -> str:
    """
    Identify which form copy a field belongs to based on its name.
    
    Args:
        field_name: PDF field name
        
    Returns:
        Form copy identifier: "Copy1", "Copy2", "CopyB", "CopyC", or "Base"
    """
    # Check for copy indicators in field name
    if "Copy1" in field_name or "Copy_1" in field_name or "copy1" in field_name:
        return "Copy1"
    elif "Copy2" in field_name or "Copy_2" in field_name or "copy2" in field_name:
        return "Copy2"
    elif "CopyB" in field_name or "Copy_B" in field_name or "copyb" in field_name:
        return "CopyB"
    elif "CopyC" in field_name or "Copy_C" in field_name or "copyc" in field_name:
        return "CopyC"
    else:
        return "Base"


def identify_column(field_name: str) -> str:
    """
    Identify which column a field belongs to based on its name.
    
    Args:
        field_name: PDF field name
        
    Returns:
        Column identifier: "LeftCol", "RghtCol", "CopyHeader", or ""
    """
    if "LeftCol" in field_name or "leftcol" in field_name:
        return "LeftCol"
    elif "RghtCol" in field_name or "rghtcol" in field_name or "RightCol" in field_name:
        return "RghtCol"
    elif "CopyHeader" in field_name or "copyheader" in field_name:
        return "CopyHeader"
    else:
        return ""


def extract_field_info(pdf_path: str) -> List[FieldInfo]:
    """
    Extract all form field information from a PDF with visual context.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of FieldInfo objects containing field details with visual context
        
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
    
    fields = []
    
    # Iterate through all pages
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        widgets = page.widgets()
        
        # Extract information from each widget (form field)
        for widget in widgets:
            field_name = widget.field_name or "(unnamed)"
            field_type = widget.field_type_string or "unknown"
            field_value = widget.field_value or ""
            rect = widget.rect
            
            # Calculate visual location
            visual_location = classify_visual_location(
                rect.x0, rect.y0, page_width, page_height
            )
            
            # Extract nearby text
            nearby_text = extract_nearby_text(page, rect)
            
            # Identify form copy
            form_copy = identify_form_copy(field_name)
            
            # Identify column
            column = identify_column(field_name)
            
            # Create FieldInfo object with visual context
            field_info = FieldInfo(
                name=field_name,
                page_num=page_num,
                rect=(rect.x0, rect.y0, rect.width, rect.height),
                field_type=field_type,
                value=str(field_value),
                visual_location=visual_location,
                nearby_text=nearby_text,
                form_copy=form_copy,
                column=column
            )
            fields.append(field_info)
    
    doc.close()
    return fields


def group_fields_by_page(fields: List[FieldInfo]) -> Dict[int, List[FieldInfo]]:
    """
    Group fields by page number.
    
    Args:
        fields: List of FieldInfo objects
        
    Returns:
        Dictionary mapping page numbers to lists of fields
    """
    grouped = {}
    for field in fields:
        page_num = field.page_num
        if page_num not in grouped:
            grouped[page_num] = []
        grouped[page_num].append(field)
    
    return grouped


def group_fields_by_copy(fields: List[FieldInfo]) -> Dict[str, List[FieldInfo]]:
    """
    Group fields by form copy.
    
    Args:
        fields: List of FieldInfo objects
        
    Returns:
        Dictionary mapping form copy identifiers to lists of fields
    """
    grouped = {}
    for field in fields:
        copy = field.form_copy
        if copy not in grouped:
            grouped[copy] = []
        grouped[copy].append(field)
    
    return grouped


def contains_keyword(field_name: str, keywords: List[str]) -> bool:
    """
    Check if field name contains any of the specified keywords (case-insensitive).
    
    Args:
        field_name: Field name to check
        keywords: List of keywords to search for
        
    Returns:
        True if any keyword is found in the field name
    """
    field_name_lower = field_name.lower()
    return any(keyword.lower() in field_name_lower for keyword in keywords)


def display_field_info(fields: List[FieldInfo], highlight_keywords: List[str] = None) -> None:
    """
    Display field information grouped by page with visual context and optional keyword highlighting.
    
    Args:
        fields: List of FieldInfo objects
        highlight_keywords: Optional list of keywords to highlight
    """
    if not fields:
        print("No form fields found in PDF.")
        return
    
    # Default keywords to highlight
    if highlight_keywords is None:
        highlight_keywords = ["TIN", "Name", "City", "Account"]
    
    # Group fields by page
    grouped_by_page = group_fields_by_page(fields)
    
    # Group fields by copy
    grouped_by_copy = group_fields_by_copy(fields)
    
    # Display summary
    print(f"\n{'='*80}")
    print(f"PDF FIELD INSPECTION SUMMARY")
    print(f"{'='*80}")
    print(f"Total fields found: {len(fields)}")
    print(f"Total pages: {len(grouped_by_page)}")
    print(f"Form copies found: {', '.join(sorted(grouped_by_copy.keys()))}")
    print(f"Highlighting fields containing: {', '.join(highlight_keywords)}")
    print(f"{'='*80}\n")
    
    # Display copy summary
    print(f"\n{'─'*80}")
    print(f"FORM COPY SUMMARY")
    print(f"{'─'*80}\n")
    for copy_name in sorted(grouped_by_copy.keys()):
        copy_fields = grouped_by_copy[copy_name]
        print(f"  {copy_name}: {len(copy_fields)} fields")
    print()
    
    # Display fields grouped by page
    for page_num in sorted(grouped_by_page.keys()):
        page_fields = grouped_by_page[page_num]
        print(f"\n{'─'*80}")
        print(f"PAGE {page_num + 1} ({len(page_fields)} fields)")
        print(f"{'─'*80}\n")
        
        for field in page_fields:
            # Check if field should be highlighted
            is_highlighted = contains_keyword(field.name, highlight_keywords)
            
            # Display field information
            if is_highlighted:
                print(f"  ★ HIGHLIGHTED FIELD ★")
            
            print(f"  Field Name: {field.name}")
            print(f"  Type: {field.field_type}")
            print(f"  Position: x={field.rect[0]:.1f}, y={field.rect[1]:.1f}")
            print(f"  Dimensions: width={field.rect[2]:.1f}, height={field.rect[3]:.1f}")
            print(f"  Visual Location: {field.visual_location}")
            print(f"  Form Copy: {field.form_copy}")
            
            if field.column:
                print(f"  Column: {field.column}")
            
            if field.value:
                print(f"  Current Value: {field.value}")
            
            if field.nearby_text:
                # Display first 5 nearby text items
                nearby_preview = field.nearby_text[:5]
                print(f"  Nearby Text: {', '.join(nearby_preview)}")
                if len(field.nearby_text) > 5:
                    print(f"               ... and {len(field.nearby_text) - 5} more")
            
            if is_highlighted:
                print(f"  ★ Contains keyword(s): {[kw for kw in highlight_keywords if kw.lower() in field.name.lower()]}")
            
            print()  # Blank line between fields


def inspect_pdf_fields(pdf_path: str) -> None:
    """
    Main function to inspect PDF fields and display information.
    
    Args:
        pdf_path: Path to the PDF file
    """
    try:
        print(f"Inspecting PDF: {pdf_path}")
        
        # Extract field information
        fields = extract_field_info(pdf_path)
        
        # Display field information with keyword highlighting
        display_field_info(fields)
        
        print(f"\n{'='*80}")
        print("INSPECTION COMPLETE")
        print(f"{'='*80}\n")
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except fitz.FileDataError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


def main():
    """Command-line interface."""
    if len(sys.argv) != 2:
        print("Usage: python inspect_pdf_fields.py <pdf_path>")
        print("\nExample:")
        print("  python inspect_pdf_fields.py templates/1099-DIV.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    inspect_pdf_fields(pdf_path)


if __name__ == "__main__":
    main()
