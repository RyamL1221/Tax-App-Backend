"""
Field mapper for translating API field names to PDF form field names.

This module provides the FieldMapper class which translates user-friendly API
field names (e.g., 'payerName', 'totalOrdinaryDividends') to the cryptic PDF
form field names used in IRS templates (e.g., 'topmostSubform[0].Copy1[0]...').
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# Import the new canonical configuration
try:
    from field_mappings.canonical_div_1099 import CANONICAL_FIELD_MAPPING
    from field_mappings.field_metadata import FIELD_METADATA, FieldMetadata
    from field_mappings.deprecated_aliases import DEPRECATED_ALIASES
    _USE_CANONICAL = True
except ImportError:
    # Fallback to old configuration if new one doesn't exist
    _USE_CANONICAL = False
    logger.warning("Canonical field mapping not found, using legacy configuration")


class FieldMapper:
    """
    Translates API field names to PDF form field names.
    
    Each IRS form has different internal field names in the PDF.
    This class maintains mappings between user-friendly API names
    and the cryptic PDF field names.
    """
    
    # Supported document types
    SUPPORTED_TYPES = ["1099-DIV"]
    
    def __init__(self, document_type: str):
        """
        Initialize the field mapper for a specific document type.
        
        Args:
            document_type: The IRS form type (e.g., "1099-DIV")
            
        Raises:
            ValueError: If document_type is not supported
            
        Requirements: 1.1, 2.1
        """
        if document_type not in self.SUPPORTED_TYPES:
            raise ValueError(
                f"Document type '{document_type}' is not supported. "
                f"Supported types: {self.SUPPORTED_TYPES}"
            )
        
        self.document_type = document_type
        self._mapping = self._load_mapping(document_type)
        
        # Load metadata and aliases if using canonical configuration
        if _USE_CANONICAL and document_type == "1099-DIV":
            self._metadata = FIELD_METADATA
            self._aliases = DEPRECATED_ALIASES
            required_count = len([m for m in self._metadata.values() if m["required"]])
            logger.info(
                f"Initialized FieldMapper for document type '{document_type}' "
                f"with {len(self._mapping)} field mappings, {required_count} required fields"
            )
        else:
            self._metadata = {}
            self._aliases = {}
            logger.info(
                f"Initialized FieldMapper for document type '{document_type}' "
                f"with {len(self._mapping)} field mappings"
            )
    
    def _load_mapping(self, document_type: str) -> Dict[str, str]:
        """
        Load the field mapping configuration for a document type.
        
        Args:
            document_type: The IRS form type
            
        Returns:
            Dictionary mapping API field names to PDF field names
            
        Raises:
            ImportError: If mapping configuration doesn't exist
        """
        if document_type == "1099-DIV":
            try:
                # Try to load canonical mapping first
                if _USE_CANONICAL:
                    return CANONICAL_FIELD_MAPPING
                else:
                    # Fallback to legacy mapping
                    from field_mappings.div_1099 import FIELD_MAPPING
                    return FIELD_MAPPING
            except ImportError as e:
                raise ImportError(
                    f"No mapping configuration found for document type '{document_type}'"
                ) from e
        
        # This should never be reached due to validation in __init__
        raise ValueError(f"Unsupported document type: {document_type}")
    
    def _generate_copy_variants(self, pdf_field_name: str) -> List[str]:
        """
        Generate field name variants for all form copies.
        
        Takes a Copy1 PDF field name and generates corresponding field names
        for CopyA, Copy2, and CopyB by replacing the copy prefix and field
        type prefixes. CopyA uses different field name patterns (f1_ instead
        of f2_, c1_ instead of c2_) which are handled automatically.
        
        Args:
            pdf_field_name: The Copy1 PDF field name
            
        Returns:
            List of field names for CopyA, Copy1, Copy2, and CopyB (in that order).
            If the field name doesn't contain "Copy1[0]", returns a list with only
            the original field name.
            
        Requirements: 1.1, 1.2, 1.4, 2.1, 2.2, 2.3, 2.4
        """
        # Check if the field name contains the Copy1 pattern
        if "Copy1[0]" not in pdf_field_name:
            logger.warning(
                f"Field name '{pdf_field_name}' does not contain 'Copy1[0]' pattern. "
                f"Returning original field name only."
            )
            return [pdf_field_name]
        
        # Generate Copy1, Copy2, CopyB variants (existing logic)
        copy1_name = pdf_field_name
        copy2_name = pdf_field_name.replace("Copy1[0]", "Copy2[0]")
        copyb_name = pdf_field_name.replace("Copy1[0]", "CopyB[0]")
        
        # Generate CopyA variant (new logic)
        # Replace Copy1[0] with CopyA[0] and f2_ with f1_
        copyA_name = pdf_field_name.replace("Copy1[0]", "CopyA[0]")
        copyA_name = copyA_name.replace("f2_", "f1_")  # Text field prefix
        copyA_name = copyA_name.replace("c2_", "c1_")  # Checkbox field prefix
        
        logger.debug(
            f"Generated copy variants for field: "
            f"CopyA='{copyA_name}', Copy1='{copy1_name}', Copy2='{copy2_name}', CopyB='{copyb_name}'"
        )
        
        return [copyA_name, copy1_name, copy2_name, copyb_name]
    
    def map_field(self, api_field_name: str) -> Optional[str]:
        """
        Map an API field name to its PDF field name.
        
        Resolves deprecated field names before mapping.
        
        Args:
            api_field_name: The user-friendly field name from the API
            
        Returns:
            The PDF form field name, or None if no mapping exists
            
        Requirements: 1.1, 1.3, 4.1, 4.4, 8.2
        """
        # Resolve deprecated aliases
        canonical_name = self.resolve_field_name(api_field_name)
        
        pdf_field_name = self._mapping.get(canonical_name)
        
        if pdf_field_name is not None:
            logger.debug(
                f"Mapped field '{api_field_name}' -> '{pdf_field_name}' "
                f"for document type '{self.document_type}'"
            )
        else:
            logger.warning(
                f"Field '{api_field_name}' has no mapping for document type "
                f"'{self.document_type}'"
            )
        
        return pdf_field_name
    
    def map_all_fields(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map all fields in a form data dictionary to multiple copies.
        
        For each API field, generates mappings for Copy1, Copy2, and CopyB.
        All three copies receive the same value from the form data.
        Resolves deprecated field names before mapping.
        
        Args:
            form_data: Dictionary with API field names as keys
            
        Returns:
            Dictionary with PDF field names as keys (includes all copies),
            unmapped fields excluded
            
        Requirements: 1.1, 1.2, 1.3, 3.1, 4.3, 4.4, 5.1, 5.3, 8.2
        """
        if not form_data:
            logger.info("No form data provided, returning empty dictionary")
            return {}
        
        mapped_data = {}
        total_copies_generated = 0
        
        for api_field_name, value in form_data.items():
            # Resolve deprecated aliases before mapping
            canonical_name = self.resolve_field_name(api_field_name)
            pdf_field_name = self._mapping.get(canonical_name)
            
            if pdf_field_name is not None:
                # Generate field name variants for all copies
                copy_variants = self._generate_copy_variants(pdf_field_name)
                
                # Map each copy variant to the same value
                for variant in copy_variants:
                    mapped_data[variant] = value
                
                total_copies_generated += len(copy_variants)
        
        logger.info(
            f"Mapped {len(form_data)} API fields to {len(mapped_data)} PDF fields "
            f"({total_copies_generated} total copies generated) "
            f"for document type '{self.document_type}'"
        )
        
        return mapped_data
    
    def get_unmapped_fields(self, form_data: Dict[str, Any]) -> List[str]:
        """
        Get list of fields that have no mapping.
        
        Args:
            form_data: Dictionary with API field names as keys
            
        Returns:
            List of API field names that couldn't be mapped
            
        Requirements: 4.2, 6.2
        """
        unmapped = []
        
        for api_field_name in form_data.keys():
            if self._mapping.get(api_field_name) is None:
                unmapped.append(api_field_name)
        
        if unmapped:
            logger.debug(
                f"Found {len(unmapped)} unmapped fields for document type "
                f"'{self.document_type}': {unmapped}"
            )
        
        return unmapped
    
    def resolve_field_name(self, field_name: str) -> str:
        """
        Resolve a field name, handling deprecated aliases.
        
        If the field name is in the deprecated aliases dictionary,
        logs a warning and returns the canonical field name. Otherwise,
        returns the field name unchanged.
        
        Args:
            field_name: The API field name (possibly deprecated)
            
        Returns:
            The canonical field name
            
        Requirements: 4.4, 8.2, 8.3
        """
        if field_name in self._aliases:
            canonical_name = self._aliases[field_name]
            logger.warning(
                f"Field name '{field_name}' is deprecated. "
                f"Use '{canonical_name}' instead."
            )
            return canonical_name
        return field_name
    
    def get_field_metadata(self, field_name: str) -> Optional[FieldMetadata]:
        """
        Get metadata for a field.
        
        Resolves deprecated field names before looking up metadata.
        
        Args:
            field_name: The API field name (possibly deprecated)
            
        Returns:
            Field metadata dictionary, or None if field not found
            
        Requirements: 2.1, 2.4
        """
        canonical_name = self.resolve_field_name(field_name)
        return self._metadata.get(canonical_name)
    
    def is_required_field(self, field_name: str) -> bool:
        """
        Check if a field is required.
        
        Args:
            field_name: The API field name (possibly deprecated)
            
        Returns:
            True if the field is required, False otherwise
            
        Requirements: 2.1, 2.5
        """
        metadata = self.get_field_metadata(field_name)
        return metadata["required"] if metadata else False
    
    def validate_required_fields(self, form_data: Dict[str, Any]) -> List[str]:
        """
        Validate that all required fields are present.
        
        Returns a list of missing required fields using canonical names only.
        Accepts both canonical and deprecated field names in form_data.
        
        Args:
            form_data: Dictionary with API field names as keys
            
        Returns:
            List of missing required field names (canonical names only)
            
        Requirements: 2.5, 8.5
        """
        missing_fields = []
        
        # Resolve all field names in form_data to canonical names
        canonical_form_data = {
            self.resolve_field_name(field_name): value
            for field_name, value in form_data.items()
        }
        
        # Check each required field
        for field_name, metadata in self._metadata.items():
            if metadata["required"] and field_name not in canonical_form_data:
                missing_fields.append(field_name)
        
        return missing_fields
