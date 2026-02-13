#!/usr/bin/env python3
"""
Checkbox Structure Analysis Script

This script analyzes checkbox fields in the IRS 1099-DIV template to document:
- Checkbox field properties
- Checkbox dimensions and positioning
- Checkbox field names for all copies (Copy 1, Copy B, Copy 2)
- Button states and appearance dictionaries

Usage:
    python analyze_checkbox_structure.py <pdf_path>
    
Example:
    python analyze_checkbox_structure.py templates/1099-DIV.pdf
"""

import sys
import os
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is required. Install with: pip install PyMuPDF>=1.23.0")
    sys.exit(1)


@dataclass
class CheckboxInfo:
    """Detailed information about a checkbox field."""
    name: str                      # Full PDF field name
    page_num: int                  # Page number (0-indexed)
    rect: tuple                    # (x0, y0, x1, y1)
    width: float                   # Width in points
    height: float                  # Height in points
    form_copy: str                 # "Copy1", "CopyB", "Copy2", or "Base"
    field_value: str               # Current value
    field_flags: int               # Field flags
    button_states: list            # Available button states
    on_state: str                  # The "on" state name
    has_appearance: bool           # Whether appearance dictionary exists
    nearby_text: List[str] = field(default_factory=list)  # Text labels near checkbox
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.name} (Page {self.page_num + 1}, {self.width:.1f}x{self.height:.1f}pt, Copy: {self.form_copy})"


def identify_form_copy(field_name: str) -> str:
    """
    Identify which form copy a field belongs to based on its name.
    
    Args:
        field_name: PDF field name
        
    Returns:
        Form copy identifier: "Copy1", "Copy2", "CopyB", or "Base"
    """
    field_lower = field_name.lower()
    
    if "copy1" in field_lower or "copy_1" in field_lower:
        return "Copy1"
    elif "copy2" in field_lower or "copy_2" in field_lower:
        return "Copy2"
    elif "copyb" in field_lower or "copy_b" in field_lower:
        return "CopyB"
    else:
        return "Base"


def extract_nearby_text(page: fitz.Page, field_rect: fitz.Rect, search_radius: float = 100.0) -> List[str]:
    """
    Extract text near a checkbox to identify labels.
    
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


def analyze_checkbox_fields(pdf_path: str) -> List[CheckboxInfo]:
    """
    Analyze all checkbox fields in a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of CheckboxInfo objects
        
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
    
    checkboxes = []
    
    # Iterate through all pages
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        
        # Extract information from each checkbox widget
        for widget in widgets:
            # Only process checkboxes
            if widget.field_type != fitz.PDF_WIDGET_TYPE_CHECKBOX:
                continue
            
            field_name = widget.field_name or "(unnamed)"
            rect = widget.rect
            
            # Get button states
            button_states = []
            on_state = ""
            try:
                button_states = widget.button_states() if hasattr(widget, 'button_states') else []
                on_state = widget.on_state() if hasattr(widget, 'on_state') else ""
            except Exception as e:
                print(f"Warning: Could not get button states for {field_name}: {e}")
            
            # Check for appearance dictionary
            has_appearance = False
            try:
                # Try to access appearance dictionary through xref
                xref = widget.xref
                if xref > 0:
                    ap_dict = doc.xref_get_key(xref, "AP")
                    has_appearance = ap_dict != ""
            except Exception:
                pass
            
            # Extract nearby text
            nearby_text = extract_nearby_text(page, rect)
            
            # Identify form copy
            form_copy = identify_form_copy(field_name)
            
            # Create CheckboxInfo object
            checkbox_info = CheckboxInfo(
                name=field_name,
                page_num=page_num,
                rect=(rect.x0, rect.y0, rect.x1, rect.y1),
                width=rect.width,
                height=rect.height,
                form_copy=form_copy,
                field_value=str(widget.field_value or ""),
                field_flags=widget.field_flags,
                button_states=button_states,
                on_state=on_state,
                has_appearance=has_appearance,
                nearby_text=nearby_text
            )
            checkboxes.append(checkbox_info)
    
    doc.close()
    return checkboxes


def group_checkboxes_by_copy(checkboxes: List[CheckboxInfo]) -> Dict[str, List[CheckboxInfo]]:
    """
    Group checkboxes by form copy.
    
    Args:
        checkboxes: List of CheckboxInfo objects
        
    Returns:
        Dictionary mapping form copy identifiers to lists of checkboxes
    """
    grouped = {}
    for checkbox in checkboxes:
        copy = checkbox.form_copy
        if copy not in grouped:
            grouped[copy] = []
        grouped[copy].append(checkbox)
    
    return grouped


def find_fatca_checkboxes(checkboxes: List[CheckboxInfo]) -> List[CheckboxInfo]:
    """
    Find FATCA-related checkboxes.
    
    Args:
        checkboxes: List of CheckboxInfo objects
        
    Returns:
        List of FATCA-related checkboxes
    """
    fatca_checkboxes = []
    for checkbox in checkboxes:
        # Check if field name or nearby text contains FATCA-related keywords
        name_lower = checkbox.name.lower()
        nearby_text_lower = " ".join(checkbox.nearby_text).lower()
        
        if "fatca" in name_lower or "fatca" in nearby_text_lower:
            fatca_checkboxes.append(checkbox)
    
    return fatca_checkboxes


def display_checkbox_analysis(checkboxes: List[CheckboxInfo]) -> None:
    """
    Display detailed checkbox analysis.
    
    Args:
        checkboxes: List of CheckboxInfo objects
    """
    if not checkboxes:
        print("No checkbox fields found in PDF.")
        return
    
    # Group by copy
    grouped_by_copy = group_checkboxes_by_copy(checkboxes)
    
    # Find FATCA checkboxes
    fatca_checkboxes = find_fatca_checkboxes(checkboxes)
    
    # Display summary
    print(f"\n{'='*80}")
    print(f"CHECKBOX STRUCTURE ANALYSIS")
    print(f"{'='*80}")
    print(f"Total checkboxes found: {len(checkboxes)}")
    print(f"Form copies found: {', '.join(sorted(grouped_by_copy.keys()))}")
    print(f"FATCA-related checkboxes: {len(fatca_checkboxes)}")
    print(f"{'='*80}\n")
    
    # Display copy summary
    print(f"\n{'─'*80}")
    print(f"CHECKBOX DISTRIBUTION BY COPY")
    print(f"{'─'*80}\n")
    for copy_name in sorted(grouped_by_copy.keys()):
        copy_checkboxes = grouped_by_copy[copy_name]
        print(f"  {copy_name}: {len(copy_checkboxes)} checkboxes")
    print()
    
    # Display FATCA checkboxes first
    if fatca_checkboxes:
        print(f"\n{'─'*80}")
        print(f"FATCA CHECKBOX DETAILS ({len(fatca_checkboxes)} checkboxes)")
        print(f"{'─'*80}\n")
        
        for checkbox in fatca_checkboxes:
            display_checkbox_details(checkbox, highlight=True)
    
    # Display all checkboxes grouped by copy
    print(f"\n{'─'*80}")
    print(f"ALL CHECKBOXES BY COPY")
    print(f"{'─'*80}\n")
    
    for copy_name in sorted(grouped_by_copy.keys()):
        copy_checkboxes = grouped_by_copy[copy_name]
        print(f"\n{'─'*40}")
        print(f"{copy_name} ({len(copy_checkboxes)} checkboxes)")
        print(f"{'─'*40}\n")
        
        for checkbox in copy_checkboxes:
            display_checkbox_details(checkbox, highlight=False)
    
    # Display dimension statistics
    print(f"\n{'─'*80}")
    print(f"CHECKBOX DIMENSION STATISTICS")
    print(f"{'─'*80}\n")
    
    widths = [cb.width for cb in checkboxes]
    heights = [cb.height for cb in checkboxes]
    
    print(f"  Width:  min={min(widths):.2f}pt, max={max(widths):.2f}pt, avg={sum(widths)/len(widths):.2f}pt")
    print(f"  Height: min={min(heights):.2f}pt, max={max(heights):.2f}pt, avg={sum(heights)/len(heights):.2f}pt")
    print()


def display_checkbox_details(checkbox: CheckboxInfo, highlight: bool = False) -> None:
    """
    Display detailed information about a checkbox.
    
    Args:
        checkbox: CheckboxInfo object
        highlight: Whether to highlight this checkbox
    """
    if highlight:
        print(f"  ★★★ FATCA CHECKBOX ★★★")
    
    print(f"  Field Name: {checkbox.name}")
    print(f"  Page: {checkbox.page_num + 1}")
    print(f"  Form Copy: {checkbox.form_copy}")
    print(f"  Position: ({checkbox.rect[0]:.1f}, {checkbox.rect[1]:.1f}) to ({checkbox.rect[2]:.1f}, {checkbox.rect[3]:.1f})")
    print(f"  Dimensions: {checkbox.width:.2f}pt × {checkbox.height:.2f}pt")
    print(f"  Current Value: '{checkbox.field_value}'")
    print(f"  Field Flags: {checkbox.field_flags}")
    
    if checkbox.button_states:
        print(f"  Button States: {checkbox.button_states}")
    
    if checkbox.on_state:
        print(f"  On State: '{checkbox.on_state}'")
    
    print(f"  Has Appearance Dictionary: {checkbox.has_appearance}")
    
    if checkbox.nearby_text:
        # Display first 10 nearby text items
        nearby_preview = checkbox.nearby_text[:10]
        print(f"  Nearby Text: {', '.join(nearby_preview)}")
        if len(checkbox.nearby_text) > 10:
            print(f"               ... and {len(checkbox.nearby_text) - 10} more")
    
    if highlight:
        print(f"  ★★★ END FATCA CHECKBOX ★★★")
    
    print()  # Blank line between checkboxes


def main():
    """Command-line interface."""
    if len(sys.argv) != 2:
        print("Usage: python analyze_checkbox_structure.py <pdf_path>")
        print("\nExample:")
        print("  python analyze_checkbox_structure.py templates/1099-DIV.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        print(f"Analyzing checkboxes in: {pdf_path}")
        
        # Analyze checkbox fields
        checkboxes = analyze_checkbox_fields(pdf_path)
        
        # Display analysis
        display_checkbox_analysis(checkboxes)
        
        print(f"\n{'='*80}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*80}\n")
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except fitz.FileDataError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
