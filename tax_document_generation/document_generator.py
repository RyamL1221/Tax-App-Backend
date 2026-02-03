"""
Document Generator Module

This module handles the generation of completed tax documents by populating
IRS templates with user-supplied form data.
"""

from typing import Dict
import logging

# Import PyMuPDF (fitz) - the sole PDF library for this module
try:
    import fitz  # PyMuPDF
except ImportError as e:
    raise ImportError(
        "PyMuPDF is required for PDF generation. "
        "Install with: pip install PyMuPDF>=1.23.0"
    ) from e

from exceptions import GenerationError
from field_mapper import FieldMapper

# Configure logging
logger = logging.getLogger(__name__)


def generate_document(template: bytes, form_data: Dict, document_type: str) -> bytes:
    """
    Generates a completed tax document by populating a template with form data.
    
    This function:
    1. Loads the PDF template
    2. Translates API field names to PDF field names using FieldMapper
    3. Populates form fields with provided data
    4. Returns the generated PDF as bytes
    
    Args:
        template: Raw template file content (PDF bytes)
        form_data: Dictionary of form field values (API field names -> values)
        document_type: The IRS form type (e.g., "1099-DIV")
        
    Returns:
        bytes: Generated document content (PDF)
        
    Raises:
        GenerationError: If document generation fails
        
    Requirements: 2.1, 2.2, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 6.2, 6.3
    """
    try:
        logger.info(f"Starting document generation for type: {document_type}")
        logger.info("Using library: PyMuPDF (fitz)")
        
        # Initialize field mapper for this document type
        mapper = FieldMapper(document_type)
        
        # Translate API field names to PDF field names
        mapped_data = mapper.map_all_fields(form_data)
        unmapped_fields = mapper.get_unmapped_fields(form_data)
        
        # Log mapping results
        logger.info(f"Mapped {len(mapped_data)} fields successfully")
        if unmapped_fields:
            logger.warning(f"Unmapped fields: {unmapped_fields}")
            for field in unmapped_fields:
                logger.warning(f"Field '{field}' has no mapping for document type '{document_type}'")
        
        # Log completion status
        if unmapped_fields:
            logger.info(f"Document generation completed with {len(unmapped_fields)} unmapped field(s)")
        else:
            logger.info("Document generation completed - all fields mapped successfully")
        
        # Open PDF with PyMuPDF
        doc = fitz.open(stream=template, filetype="pdf")
        
        logger.info(f"Template has {len(doc)} page(s)")
        
        # ============================================
        # PDF FLATTENING APPROACH
        # ============================================
        # Adobe Reader requires proper appearance streams to display form field values.
        # The IRS PDF templates don't have appearance streams, causing values to be invisible.
        # Solution: Flatten the PDF by converting form fields to static text.
        # Trade-off: Fields become non-editable, but values are guaranteed to be visible.
        # ============================================
        
        logger.info("Flattening PDF form fields to static text for Adobe Reader compatibility")
        logger.info("Note: Fields will be non-editable but visible in all PDF viewers")
        
        # Step 1: Collect field data (position, value, properties)
        fields_to_flatten = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = list(page.widgets())
            
            for widget in widgets:
                field_name = widget.field_name
                if field_name in mapped_data:
                    try:
                        value = str(mapped_data[field_name])
                        rect = widget.rect
                        
                        # Get text properties
                        try:
                            font_name = widget.text_font or "helv"
                            font_size = widget.text_fontsize or 10
                            text_color = widget.text_color or (0, 0, 0)
                        except:
                            font_name = "helv"
                            font_size = 10
                            text_color = (0, 0, 0)
                        
                        fields_to_flatten.append({
                            'page_num': page_num,
                            'value': value,
                            'rect': rect,
                            'font_name': font_name,
                            'font_size': font_size,
                            'text_color': text_color,
                            'field_name': field_name
                        })
                        
                        logger.debug(f"Prepared field '{field_name}' for flattening: value='{value}'")
                    except Exception as e:
                        logger.warning(f"Failed to prepare field '{field_name}' for flattening: {str(e)}")
        
        logger.info(f"Prepared {len(fields_to_flatten)} fields for flattening")
        
        # Step 2: Insert static text at field locations using built-in Helvetica font
        populated_count = 0
        failed_fields = []
        
        # Track statistics per copy for multi-copy operations
        copy_stats = {
            'Copy1': {'success': 0, 'failed': []},
            'Copy2': {'success': 0, 'failed': []},
            'CopyB': {'success': 0, 'failed': []}
        }
        
        for field_data in fields_to_flatten:
            try:
                page = doc[field_data['page_num']]
                field_name = field_data['field_name']
                
                # Determine which copy this field belongs to
                copy_id = None
                if 'Copy1[0]' in field_name:
                    copy_id = 'Copy1'
                elif 'Copy2[0]' in field_name:
                    copy_id = 'Copy2'
                elif 'CopyB[0]' in field_name:
                    copy_id = 'CopyB'
                
                # Insert text as static content
                # Use "helv" (Helvetica) - a PDF base-14 font that's always available
                # This avoids "need font file or buffer" errors
                rc = page.insert_textbox(
                    field_data['rect'],
                    field_data['value'],
                    fontsize=field_data['font_size'],
                    fontname="helv",
                    color=field_data['text_color'],
                    align=fitz.TEXT_ALIGN_LEFT
                )
                
                if rc >= 0:  # Success
                    populated_count += 1
                    if copy_id:
                        copy_stats[copy_id]['success'] += 1
                        logger.debug(f"Successfully populated {copy_id} field '{field_name}' with value '{field_data['value']}'")
                    else:
                        logger.debug(f"Flattened field '{field_name}' with value '{field_data['value']}'")
                else:
                    if copy_id:
                        copy_stats[copy_id]['failed'].append(field_name)
                        logger.warning(f"Failed to populate {copy_id} field '{field_name}' (rc={rc})")
                    else:
                        logger.warning(f"Failed to insert text for field '{field_name}' (rc={rc})")
                    failed_fields.append(field_name)
                    
            except Exception as e:
                field_name = field_data['field_name']
                
                # Determine which copy this field belongs to
                copy_id = None
                if 'Copy1[0]' in field_name:
                    copy_id = 'Copy1'
                elif 'Copy2[0]' in field_name:
                    copy_id = 'Copy2'
                elif 'CopyB[0]' in field_name:
                    copy_id = 'CopyB'
                
                if copy_id:
                    copy_stats[copy_id]['failed'].append(field_name)
                    logger.warning(f"Failed to populate {copy_id} field '{field_name}': {str(e)}")
                else:
                    logger.warning(f"Failed to flatten field '{field_name}': {str(e)}")
                failed_fields.append(field_name)
        
        # Step 3: Remove form field widgets (convert to static content)
        logger.info("Removing form field widgets (converting to static content)...")
        removed_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = list(page.widgets())
            
            for widget in widgets:
                if widget.field_name in mapped_data:
                    try:
                        widget.delete()
                        removed_count += 1
                    except Exception as e:
                        logger.debug(f"Could not delete widget '{widget.field_name}': {str(e)}")
        
        logger.info(f"Removed {removed_count} form field widgets")
        logger.info(f"Successfully flattened {populated_count} fields")
        if failed_fields:
            logger.warning(f"Failed to flatten {len(failed_fields)} field(s): {failed_fields}")
        
        # Log summary statistics per copy for multi-copy operations
        has_multi_copy = any(copy_stats[copy]['success'] > 0 or copy_stats[copy]['failed'] 
                            for copy in copy_stats)
        if has_multi_copy:
            logger.info("Multi-copy field population summary:")
            for copy_id in ['Copy1', 'Copy2', 'CopyB']:
                success_count = copy_stats[copy_id]['success']
                failed_count = len(copy_stats[copy_id]['failed'])
                total = success_count + failed_count
                
                if total > 0:
                    logger.info(f"  {copy_id}: {success_count}/{total} fields populated successfully")
                    if failed_count > 0:
                        logger.warning(f"  {copy_id}: {failed_count} field(s) failed: {copy_stats[copy_id]['failed']}")

        
        # Save to bytes
        output_bytes = doc.tobytes()
        doc.close()
        
        if not output_bytes:
            raise GenerationError("Generated document is empty")
        
        logger.info(f"Document generated successfully, size: {len(output_bytes)} bytes")
        return output_bytes
        
    except GenerationError:
        raise
    except Exception as e:
        logger.error(f"Document generation failed: {str(e)}", exc_info=True)
        raise GenerationError(f"Failed to generate document: {str(e)}")
