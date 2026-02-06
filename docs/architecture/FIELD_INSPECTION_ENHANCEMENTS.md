# Field Inspection Tool Enhancements

## Overview

The PDF field inspection tool (`inspect_pdf_fields.py`) has been enhanced with visual context features to better identify and analyze form fields in multi-copy tax forms like the 1099-DIV.

## New Features

### 1. Visual Location Classification

Fields are now classified by their visual position on the page:
- **top-left**: Upper left quadrant
- **top-right**: Upper right quadrant  
- **bottom-left**: Lower left quadrant
- **bottom-right**: Lower right quadrant
- **center**: Middle 20% of the page

**Implementation**: `classify_visual_location(x, y, page_width, page_height)`

**Example Output**:
```
Visual Location: top-left
```

### 2. Nearby Text Extraction

The tool now extracts text labels near each field (within 50 points radius) to help identify the field's purpose.

**Implementation**: `extract_nearby_text(page, field_rect, search_radius=50.0)`

**Example Output**:
```
Nearby Text: PAYER'S, name, Street, address, (including
             ... and 28 more
```

### 3. Form Copy Grouping

Fields are automatically grouped by which copy of the form they belong to:
- **Base**: Fields without copy indicators
- **Copy1**: First copy fields
- **Copy2**: Second copy fields
- **CopyB**: Copy B fields
- **CopyC**: Copy C fields

**Implementation**: `identify_form_copy(field_name)`

**Example Output**:
```
Form Copy: Copy1
```

### 4. Column Identification

Fields are identified by their column location in the form:
- **LeftCol**: Left column fields
- **RghtCol**: Right column fields
- **CopyHeader**: Header fields
- **(empty)**: Fields not in a specific column

**Implementation**: `identify_column(field_name)`

**Example Output**:
```
Column: LeftCol
```

## Enhanced FieldInfo Data Structure

The `FieldInfo` dataclass now includes:

```python
@dataclass
class FieldInfo:
    name: str                      # Full PDF field name
    page_num: int                  # Page number (0-indexed)
    rect: tuple                    # (x, y, width, height)
    field_type: str                # "text", "checkbox", etc.
    value: str                     # Current field value
    visual_location: str = ""      # Visual position on page
    nearby_text: List[str] = []    # Text labels near field
    form_copy: str = ""            # Form copy identifier
    column: str = ""               # Column identifier
```

## Enhanced Output Format

The inspection tool now displays:

1. **Summary Section**:
   - Total fields found
   - Total pages
   - Form copies found
   - Highlighted keywords

2. **Form Copy Summary**:
   - Count of fields per copy

3. **Detailed Field Information**:
   - Field name
   - Type
   - Position (x, y)
   - Dimensions (width, height)
   - **Visual Location** (NEW)
   - **Form Copy** (NEW)
   - **Column** (NEW)
   - Current value
   - **Nearby Text** (NEW)
   - Keyword highlighting

## Usage

```bash
python tax_document_generation/inspect_pdf_fields.py <pdf_path>
```

**Example**:
```bash
python tax_document_generation/inspect_pdf_fields.py samples/SAMPLE-1099-DIV-MULTI-COPY.pdf
```

## Test Results

Tested on `SAMPLE-1099-DIV-MULTI-COPY.pdf`:
- ✅ Successfully extracted 140 fields across 4 pages
- ✅ Identified 4 form copies: Base, Copy1, Copy2, CopyB
- ✅ Classified visual locations correctly
- ✅ Extracted nearby text for field identification
- ✅ Grouped fields by copy and column
- ✅ No diagnostic errors

## Benefits

1. **Better Field Identification**: Nearby text helps identify field purpose
2. **Multi-Copy Analysis**: Easy to compare corresponding fields across copies
3. **Visual Context**: Location classification helps understand form layout
4. **Debugging**: Enhanced output makes it easier to diagnose field mapping issues
5. **Documentation**: Comprehensive field metadata for mapping corrections

## Requirements Validated

This enhancement validates the following requirements:
- ✅ Requirement 1.1: Extract all field names, coordinates, and page numbers
- ✅ Requirement 1.2: Identify fields by position coordinates and visual location
- ✅ Requirement 1.4: Output field metadata including all required information
- ✅ Requirement 1.5: Identify corresponding fields across all copies

## Next Steps

The enhanced inspection tool can now be used to:
1. Identify correct PDF field names for payer TIN, recipient TIN, and recipient name
2. Verify field positions match IRS form specifications
3. Compare field mappings across form copies
4. Generate field mapping corrections
