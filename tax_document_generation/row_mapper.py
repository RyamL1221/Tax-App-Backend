"""Maps CSV row dictionaries to canonical 1099-DIV formData.

Converts raw string values from parsed CSV rows into properly typed
formData dictionaries suitable for the generation pipeline.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

from typing import Dict, Any

from field_mappings.field_metadata import FIELD_METADATA

# Derive typed field sets from FIELD_METADATA
DECIMAL_FIELDS = {
    name for name, meta in FIELD_METADATA.items()
    if meta.get("data_type") == "decimal"
}

BOOLEAN_FIELDS = {
    name for name, meta in FIELD_METADATA.items()
    if meta.get("data_type") == "boolean"
}

TRUTHY_VALUES = {"true", "yes", "1"}
FALSY_VALUES = {"false", "no", "0"}


def map_row_to_form_data(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert a single parsed CSV row into a formData dictionary.

    Rules:
      - Strip leading/trailing whitespace from all values.
      - Omit fields whose cell value is empty or whitespace-only.
      - Convert decimal fields to float.
      - Convert boolean fields to Python bool.
      - All other fields remain as stripped strings.

    Args:
        row: Dict mapping header names to raw cell strings.

    Returns:
        formData dict ready for Generation_Service.

    Raises:
        ValueError: If a decimal field contains a non-numeric value
                    or a boolean field contains an unrecognised value.
    """
    form_data: Dict[str, Any] = {}

    for key, raw_value in row.items():
        stripped = raw_value.strip()
        if not stripped:
            continue

        if key in DECIMAL_FIELDS:
            try:
                form_data[key] = float(stripped)
            except (ValueError, OverflowError):
                raise ValueError(
                    f"Invalid decimal value for field '{key}': '{stripped}'"
                )
        elif key in BOOLEAN_FIELDS:
            lower = stripped.lower()
            if lower in TRUTHY_VALUES:
                form_data[key] = True
            elif lower in FALSY_VALUES:
                form_data[key] = False
            else:
                raise ValueError(
                    f"Unrecognised boolean value for field '{key}': '{stripped}'"
                )
        else:
            form_data[key] = stripped

    return form_data
