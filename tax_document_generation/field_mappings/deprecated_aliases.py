"""
Deprecated field name aliases for IRS Form 1099-DIV.

This module maintains backward compatibility by mapping old/deprecated
field names to their canonical replacements. When a deprecated field name
is used, the system will log a warning and automatically resolve it to
the canonical name.

Requirements: 4.3, 8.1, 8.4
"""

from typing import Dict

# Mapping from deprecated field names to canonical field names
# Format: {"old_field_name": "canonicalFieldName"}
#
# Example entries (for reference):
# {
#     "payer_tin": "payerTIN",           # If we ever change naming convention
#     "recipient_ssn": "recipientTIN",   # If we rename for clarity
#     "ordinary_dividends": "totalOrdinaryDividends",  # If we standardize names
# }
#
# Currently, no field names are deprecated. This structure is ready for
# future use when field names need to be changed while maintaining
# backward compatibility.
#
# When adding deprecated aliases:
# 1. Add the mapping: "oldName": "newCanonicalName"
# 2. Update MIGRATION_GUIDE.md with the deprecation notice
# 3. Set a timeline for eventual removal (e.g., 6 months)
# 4. Ensure FieldMapper.resolve_field_name() logs appropriate warnings
#
# Requirements: 4.3, 8.1, 8.4
DEPRECATED_ALIASES: Dict[str, str] = {
    # No deprecated aliases currently defined
    # This dictionary will be populated as field names evolve
}
