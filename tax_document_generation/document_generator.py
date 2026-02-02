"""
Document Generator Module

This module handles the generation of completed tax documents by populating
IRS templates with user-supplied form data.
"""

from typing import Dict
import logging

try:
    from pypdf import PdfReader, PdfWriter
    USING_PYPDF = True
except ImportError:
    from PyPDF2 import PdfReader, PdfWriter
    USING_PYPDF = False

from io import BytesIO
from exceptions import GenerationError

# Configure logging
logger = logging.getLogger(__name__)


def generate_document(template: bytes, form_data: Dict, document_type: str) -> bytes:
    """
    Generates a completed tax document by populating a template with form data.
    
    This function:
    1. Loads the PDF template
    2. Populates form fields with provided data
    3. Flattens the form to create a static document
    4. Returns the generated PDF as bytes
    
    Args:
        template: Raw template file content (PDF bytes)
        form_data: Dictionary of form field values (field_name -> value)
        document_type: The IRS form type (e.g., "1099-DIV")
        
    Returns:
        bytes: Generated document content (PDF)
        
    Raises:
        GenerationError: If document generation fails
        
    Requirements: 2.1, 2.2, 2.4, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4
    """
    try:
        logger.info(f"Starting document generation for type: {document_type}")
        logger.info(f"Using library: {'pypdf' if USING_PYPDF else 'PyPDF2'}")
        
        # Read the template PDF
        template_stream = BytesIO(template)
        reader = PdfReader(template_stream)
        writer = PdfWriter()
        
        # Log template information
        logger.info(f"Template has {len(reader.pages)} page(s)")
        
        # Clone the document to preserve form structure
        writer.clone_reader_document_root(reader)
        
        # Check if the PDF has form fields
        fields = reader.get_fields()
        if fields:
            logger.info(f"Template has {len(fields)} form field(s)")
            logger.debug(f"Available fields: {list(fields.keys())}")
            
            # Log which fields we're trying to populate
            logger.debug(f"Form data keys: {list(form_data.keys())}")
            
            # Populate form fields with flattening
            # The flatten=True parameter converts form fields to static content
            # Note: auto_regenerate parameter may not be available in all versions
            # Update all pages to ensure all form fields are populated
            try:
                writer.update_page_form_field_values(
                    None,  # None means update all pages
                    form_data,
                    auto_regenerate=False,
                    flatten=True
                )
            except TypeError:
                # Fallback for older versions that don't support auto_regenerate
                writer.update_page_form_field_values(
                    None,  # None means update all pages
                    form_data,
                    flatten=True
                )
            
            logger.info("Form fields populated and flattened successfully")
        else:
            logger.warning("Template has no form fields - generating static copy")
        
        # Write the output to bytes
        output_stream = BytesIO()
        writer.write(output_stream)
        output_bytes = output_stream.getvalue()
        
        if not output_bytes:
            raise GenerationError("Generated document is empty")
        
        logger.info(f"Document generated successfully, size: {len(output_bytes)} bytes")
        return output_bytes
        
    except GenerationError:
        raise
    except Exception as e:
        # Log the full exception for debugging
        logger.error(f"Document generation failed: {str(e)}", exc_info=True)
        raise GenerationError(f"Failed to generate document: {str(e)}")
