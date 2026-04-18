#!/usr/bin/env python3
"""
Generate CSV templates for 1099-DIV data import.

Reads field definitions from FIELD_METADATA to ensure CSV headers
stay in sync with the canonical field metadata.

Usage:
    python scripts/generate_csv_templates.py [--output-dir DIR]
"""

import argparse
import csv
import os
import sys

# Add project root to path so we can import field_metadata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tax_document_generation.field_mappings.field_metadata import FIELD_METADATA


SIMPLE_FIELDS = [
    "payerName",
    "payerTIN",
    "recipientName",
    "recipientTIN",
    "totalOrdinaryDividends",
    "totalCapitalGainsDistributions",
]

# Alias map: requirements use plural "Gains" but FIELD_METADATA uses singular "Gain"
FIELD_ALIASES = {
    "totalCapitalGainsDistributions": "totalCapitalGainDistributions",
}


def resolve_field(field_name: str) -> str:
    """Resolve a field name to its FIELD_METADATA key, handling known aliases."""
    return FIELD_ALIASES.get(field_name, field_name)


def generate_csv(fields: list, metadata: dict, output_path: str) -> None:
    """Generate a CSV template with a header row and one example data row."""
    headers = fields
    example_row = [metadata[resolve_field(f)]["example_value"] for f in fields]

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerow(example_row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 1099-DIV CSV templates")
    parser.add_argument(
        "--output-dir",
        default="templates/csv/1099-DIV/",
        help="Output directory for CSV templates (default: templates/csv/1099-DIV/)",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Generate simple template (6 fields)
    simple_path = os.path.join(args.output_dir, "simple-template.csv")
    generate_csv(SIMPLE_FIELDS, FIELD_METADATA, simple_path)
    print(f"Generated {simple_path}")

    # Generate full template (all FIELD_METADATA keys)
    full_fields = list(FIELD_METADATA.keys())
    full_path = os.path.join(args.output_dir, "full-template.csv")
    generate_csv(full_fields, FIELD_METADATA, full_path)
    print(f"Generated {full_path}")


if __name__ == "__main__":
    main()
