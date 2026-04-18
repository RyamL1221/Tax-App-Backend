"""CSV parsing and header validation for 1099-DIV import.

This module parses uploaded CSV content, validates headers against
required fields, detects duplicates, filters blank rows, and returns
a list of row dictionaries ready for downstream mapping.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8
"""

import csv
import io
from typing import List, Dict

from exceptions import ValidationError

REQUIRED_HEADERS = [
    "payerName",
    "payerTIN",
    "recipientName",
    "recipientTIN",
    "totalOrdinaryDividends",
]


def parse_csv(csv_content: str) -> List[Dict[str, str]]:
    """
    Parse CSV content into a list of row dictionaries.

    Validates:
      - Header row is present
      - All required headers exist (case-sensitive)
      - No duplicate headers
      - At least one non-blank data row exists
      - Blank rows (all cells empty/whitespace) are skipped

    Args:
        csv_content: Decoded CSV string (may include BOM prefix).

    Returns:
        List of dicts mapping header names to cell values.

    Raises:
        ValidationError: On missing headers, duplicates, or no data rows.
    """
    # Strip BOM if present
    if csv_content.startswith("\ufeff"):
        csv_content = csv_content[1:]

    reader = csv.reader(io.StringIO(csv_content))

    # Parse header row
    try:
        headers = next(reader)
    except StopIteration:
        raise ValidationError("CSV file is empty")

    # Detect duplicate headers
    seen = set()
    duplicates = set()
    for header in headers:
        if header in seen:
            duplicates.add(header)
        seen.add(header)

    if duplicates:
        sorted_dupes = sorted(duplicates)
        raise ValidationError(
            f"Duplicate CSV headers: {', '.join(sorted_dupes)}"
        )

    # Validate required headers (case-sensitive)
    header_set = set(headers)
    missing = [h for h in REQUIRED_HEADERS if h not in header_set]
    if missing:
        raise ValidationError(
            f"Missing required CSV headers: {', '.join(missing)}"
        )

    # Parse data rows, filtering blank rows
    rows: List[Dict[str, str]] = []
    for raw_row in reader:
        # Skip blank rows: every cell is empty or whitespace-only
        if all(cell.strip() == "" for cell in raw_row):
            continue
        row_dict = dict(zip(headers, raw_row))
        rows.append(row_dict)

    if not rows:
        raise ValidationError("CSV file contains no data rows")

    return rows
