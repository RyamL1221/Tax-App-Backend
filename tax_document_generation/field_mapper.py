"""
Field mapper for translating API field names to PDF form field names.

This module provides the FieldMapper class which translates user-friendly API
field names (e.g., 'payerName', 'totalOrdinaryDividends') to the cryptic PDF
form field names used in IRS templates (e.g., 'topmostSubform[0].Copy1[0]...').
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


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
            
        Requirements: 2.1, 2.2
        """
        if document_type not in self.SUPPORTED_TYPES:
            raise ValueError(
                f"Document type '{document_type}' is not supported. "
                f"Supported types: {self.SUPPORTED_TYPES}"
            )
        
        self.document_type = document_type
        self._mapping = self._load_mapping(document_type)
        
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
                from field_mappings.div_1099 import FIELD_MAPPING
                return FIELD_MAPPING
            except ImportError as e:
                raise ImportError(
                    f"No mapping configuration found for document type '{document_type}'"
                ) from e
        
        # This should never be reached due to validation in __init__
        raise ValueError(f"Unsupported document type: {document_type}")
    
    def map_field(self, api_field_name: str) -> Optional[str]:
        """
        Map an API field name to its PDF field name.
        
        Args:
            api_field_name: The user-friendly field name from the API
            
        Returns:
            The PDF form field name, or None if no mapping exists
            
        Requirements: 1.1, 1.3, 4.1
        """
        pdf_field_name = self._mapping.get(api_field_name)
        
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
        Map all fields in a form data dictionary.
        
        Args:
            form_data: Dictionary with API field names as keys
            
        Returns:
            Dictionary with PDF field names as keys, unmapped fields excluded
            
        Requirements: 1.2, 3.1, 4.3
        """
        if not form_data:
            logger.info("No form data provided, returning empty dictionary")
            return {}
        
        mapped_data = {}
        
        for api_field_name, value in form_data.items():
            pdf_field_name = self.map_field(api_field_name)
            
            if pdf_field_name is not None:
                mapped_data[pdf_field_name] = value
        
        logger.debug(
            f"Mapped {len(mapped_data)} out of {len(form_data)} fields "
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
