# Field Position Validation Guide

## Overview

The position validation tool (`validate_field_positions.py`) verifies that fields in generated 1099-DIV PDFs appear in their expected positions according to IRS form specifications. This ensures that field mappings are correct and that generated forms will display properly.

## Purpose

This tool addresses **Requirement 4.4** and **Requirement 4.5** from the fix-1099-div-field-positions specification:

- **4.4**: Compare generated PDF field positions against IRS 1099-DIV form layout specifications
- **4.5**: Report field name, expected position, and actual position when validation detects incorrect positioning

## Usage

### Basic Usage

```bash
python tax_document_generation/validate_field_positions.py <generated_pdf_path>
```

### Examples

```bash
# Validate a generated PDF
python tax_document_generation/validate_field_positions.py samples/test-output-1099-DIV.pdf

# Validate the template PDF
python tax_document_generation/validate_field_positions.py samples/SAMPLE-1099-DIV-MULTI-COPY.pdf

# Validate a freshly generated PDF
python tax_document_generation/validate_field_positions.py samples/fresh-generated-1099-DIV.pdf
```

## How It Works

### 1. Field Position Extraction

The tool extracts actual field positions from the generated PDF:
- Opens the PDF using PyMuPDF (fitz)
- Extracts field coordinates (x, y, width, height) from Copy1 (page 3)
- Stores field information for comparison

### 2. Position Comparison

Compares actual positions against IRS specifications:
- Uses predefined expected positions from `IRS_1099_DIV_LAYOUT`
- Calculates Euclidean distance between expected and actual positions
- Applies ±5 point tolerance for position matching

### 3. Report Generation

Generates a comprehensive validation report:
- **Correct fields**: Fields within tolerance
- **Incorrect fields**: Fields outside tolerance with distance details
- **Missing fields**: Expected fields not found in PDF
- **Success rate**: Percentage of correctly positioned fields

## IRS 1099-DIV Layout Specification

The tool uses the following expected field positions (based on Copy1):

### Payer Information (LeftCol)

| Field | X | Y | Width | Height | Purpose |
|-------|---|---|-------|--------|---------|
| payer_name | 52.4 | 56.0 | 242.1 | 76.0 | Payer's name |
| payer_street_address | 50.4 | 142.0 | 122.4 | 38.0 | Payer's street address |
| payer_city | 172.8 | 142.0 | 122.4 | 38.0 | Payer's city/state/ZIP |
| payer_tin | 52.4 | 262.0 | 242.1 | 26.0 | Payer's TIN |

### Recipient Information (LeftCol)

| Field | X | Y | Width | Height | Purpose |
|-------|---|---|-------|--------|---------|
| recipient_name | 52.4 | 190.0 | 242.1 | 26.0 | Recipient's name |
| recipient_tin | 50.4 | 334.0 | 244.8 | 26.0 | Recipient's TIN |

### Box Values (RghtCol)

| Field | X | Y | Width | Height | Purpose |
|-------|---|---|-------|--------|---------|
| total_ordinary_dividends | 305.2 | 60.0 | 89.8 | 12.0 | Box 1a |
| qualified_dividends | 305.2 | 96.0 | 89.8 | 12.0 | Box 1b |
| total_capital_gain_distributions | 305.2 | 120.0 | 89.8 | 12.0 | Box 2a |

## Position Tolerance

The tool uses a **±5 point tolerance** for position matching. This accounts for:
- Minor PDF rendering variations
- Floating-point precision differences
- Font rendering adjustments

A field is considered correctly positioned if its actual position is within 5 points of the expected position (Euclidean distance).

## Validation Report Format

### Success Example

```
================================================================================
FIELD POSITION VALIDATION REPORT
================================================================================
PDF: samples/test-output-1099-DIV.pdf
Tolerance: ±5.0 points
================================================================================

Total fields validated: 9
Correct positions: 9
Incorrect positions: 0
Missing fields: 0
Success rate: 100.0%

────────────────────────────────────────────────────────────────────────────────
✓ CORRECT POSITIONS (9 fields)
────────────────────────────────────────────────────────────────────────────────

  ✓ payer_name
    Field: topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]
  ✓ payer_tin
    Field: topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]
  ✓ recipient_name
    Field: topmostSubform[0].Copy1[0].LeftCol[0].f2_5[0]
  ✓ recipient_tin
    Field: topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]
  ✓ total_ordinary_dividends
    Field: topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]

================================================================================
VALIDATION RESULT
================================================================================

✅ VALIDATION PASSED
   All fields appear in correct positions
```

### Failure Example

```
================================================================================
FIELD POSITION VALIDATION REPORT
================================================================================
PDF: samples/broken-1099-DIV.pdf
Tolerance: ±5.0 points
================================================================================

Total fields validated: 9
Correct positions: 6
Incorrect positions: 3
Missing fields: 0
Success rate: 66.7%

────────────────────────────────────────────────────────────────────────────────
✗ INCORRECT POSITIONS (3 fields)
────────────────────────────────────────────────────────────────────────────────

  ✗ recipient_name: POSITION MISMATCH
    Field: topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]
    Expected position: (52.4, 190.0) [242.1×26.0]
    Actual position: (406.0, 336.0) [89.8×12.0]
    Distance: 389.2 points (tolerance: ±5.0)
    Expected column: LeftCol

  ✗ payer_tin: POSITION MISMATCH
    Field: topmostSubform[0].Copy1[0].LeftCol[0].f2_4[0]
    Expected position: (52.4, 262.0) [242.1×26.0]
    Actual position: (172.8, 142.0) [122.4×38.0]
    Distance: 156.8 points (tolerance: ±5.0)
    Expected column: LeftCol

================================================================================
VALIDATION RESULT
================================================================================

⚠ VALIDATION PARTIALLY PASSED
   6/9 fields in correct positions
   3 field(s) need correction
```

## Exit Codes

- **0**: All fields in correct positions (validation passed)
- **1**: Some fields incorrect or missing (validation failed)
- **1**: Error during validation (exception occurred)

## Integration with Testing

### Unit Tests

The validation tool can be used in unit tests:

```python
from tax_document_generation.validate_field_positions import (
    validate_field_positions,
    POSITION_TOLERANCE
)

def test_generated_pdf_positions():
    """Test that generated PDF has correct field positions."""
    # Generate PDF
    pdf_bytes = generate_1099_div(test_data)
    
    # Save to file
    with open("test-output.pdf", "wb") as f:
        f.write(pdf_bytes)
    
    # Validate positions
    report = validate_field_positions("test-output.pdf")
    
    # Assert all fields correct
    assert len(report.correct_fields) == report.total_fields
    assert len(report.incorrect_fields) == 0
    assert len(report.missing_fields) == 0
```

### Integration Tests

Use in integration tests to verify end-to-end functionality:

```python
def test_field_mapping_correction_integration():
    """Test complete workflow: mapping correction → generation → validation."""
    # Generate PDF with corrected mappings
    pdf_bytes = generate_1099_div({
        "payerName": "Test Corp",
        "payerTIN": "12-3456789",
        "recipientName": "John Doe",
        "recipientTIN": "987-65-4321",
        "totalOrdinaryDividends": "1000.00"
    })
    
    # Save and validate
    with open("integration-test.pdf", "wb") as f:
        f.write(pdf_bytes)
    
    report = validate_field_positions("integration-test.pdf")
    
    # Verify critical fields
    critical_fields = ["payer_tin", "recipient_tin", "recipient_name"]
    for field_name, purpose in report.correct_fields:
        if purpose in critical_fields:
            critical_fields.remove(purpose)
    
    assert len(critical_fields) == 0, f"Missing critical fields: {critical_fields}"
```

## Troubleshooting

### "PDF file not found"

Ensure the PDF path is correct:
```bash
ls -la samples/test-output-1099-DIV.pdf
```

### "Page 3 does not exist in PDF"

The tool validates Copy1 (page 3, 0-indexed as page 2). Ensure your PDF has at least 3 pages:
```bash
python -c "import fitz; doc = fitz.open('samples/test.pdf'); print(f'Pages: {len(doc)}')"
```

### "No form fields found"

The PDF may not have form fields. Verify with:
```bash
python tax_document_generation/inspect_pdf_fields.py samples/test.pdf
```

### All fields showing as "MISSING"

The field identification patterns may need updating. Check the `identify_field_by_purpose()` function in the script.

## Extending the Tool

### Adding New Fields

To validate additional fields, add them to `IRS_1099_DIV_LAYOUT`:

```python
IRS_1099_DIV_LAYOUT = {
    # ... existing fields ...
    
    "new_field": FieldPosition(
        x=100.0, y=200.0, width=150.0, height=20.0,
        purpose="new_field",
        column="LeftCol"
    ),
}
```

And add the field pattern to `identify_field_by_purpose()`:

```python
purpose_patterns = {
    # ... existing patterns ...
    "new_field": ["f2_99[0]"],
}
```

### Adjusting Tolerance

To change the position tolerance, modify the constant:

```python
POSITION_TOLERANCE = 10.0  # Increase to 10 points
```

### Validating Different Pages

To validate a different page (e.g., Copy2 on page 6):

```python
report = validate_field_positions(pdf_path, page_num=5)  # 0-indexed
```

## Related Tools

- **inspect_pdf_fields.py**: Inspect all fields in a PDF template
- **validate_field_mappings.py**: Validate field mappings against template
- **visual_field_mapper.py**: Map fields to their visual purpose

## Requirements Validation

This tool validates the following requirements:

- ✅ **Requirement 4.4**: Compares generated PDF field positions against IRS 1099-DIV form layout specifications
- ✅ **Requirement 4.5**: Reports field name, expected position, and actual position when validation detects incorrect positioning

## References

- IRS Form 1099-DIV: https://www.irs.gov/forms-pubs/about-form-1099-div
- Field inspection findings: `FIELD_INSPECTION_FINDINGS.md`
- Field mapping corrections: `FIELD_MAPPING_CORRECTIONS.md`
- Recipient name inspection: `RECIPIENT_NAME_FIELD_INSPECTION_REPORT.md`
