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


# Field-specific rendering configuration
# Different columns in the PDF have different size constraints
FIELD_RENDERING_CONFIG = {
    'LeftCol': {
        'default_font_size': 9.0,
        'min_font_size': 7.0,
        'max_font_size': 10.0,
    },
    'RghtCol': {
        'default_font_size': 7.0,  # Smaller for tight boxes
        'min_font_size': 6.0,
        'max_font_size': 8.0,
    },
    'CopyHeader': {
        'default_font_size': 10.0,
        'min_font_size': 8.0,
        'max_font_size': 12.0,
    }
}


def calculate_font_size(
    text: str,
    field_width: float,
    field_height: float,
    max_font_size: float = 10.0,
    min_font_size: float = 6.0
) -> float:
    """
    Calculate optimal font size for text to fit in field.
    
    This function estimates the appropriate font size based on:
    - Text length (number of characters)
    - Available field width and height
    - Configured min/max font size bounds
    
    The algorithm uses a simple character width estimation:
    - Average character width ≈ 0.6 × font_size (for Helvetica)
    - Text width ≈ char_count × 0.6 × font_size
    
    Args:
        text: Text content to render
        field_width: Available width in points
        field_height: Available height in points
        max_font_size: Maximum allowed font size (default: 10.0)
        min_font_size: Minimum allowed font size (default: 6.0)
        
    Returns:
        Font size in points that allows text to fit within bounds
        
    Requirements: 1.1, 2.1, 3.1
    """
    if not text:
        return max_font_size
    
    # Start with the maximum font size
    font_size = max_font_size
    
    # Constraint 1: Font size must fit within field height
    # Use 80% of field height to allow for padding and descenders
    height_based_size = field_height * 0.8
    font_size = min(font_size, height_based_size)
    
    # Constraint 2: Text width must fit within field width
    # Average character width for Helvetica ≈ 0.6 × font_size
    char_count = len(text)
    if char_count > 0:
        # Calculate maximum font size that allows text to fit
        # text_width = char_count × 0.6 × font_size
        # Solve for font_size: font_size = text_width / (char_count × 0.6)
        width_based_size = field_width / (char_count * 0.6)
        font_size = min(font_size, width_based_size)
    
    # Ensure font size is within configured bounds
    font_size = max(min_font_size, min(font_size, max_font_size))
    
    return font_size


def insert_text_with_fallback(
    page: fitz.Page,
    rect: fitz.Rect,
    text: str,
    field_name: str,
    default_font_size: float = 10.0,
    min_font_size: float = 6.0,
    text_color: tuple = (0, 0, 0)
) -> bool:
    """
    Insert text into PDF field with adaptive sizing and fallback.
    
    This function attempts to insert text into a PDF field with retry logic:
    1. Attempts insertion with the calculated/default font size
    2. If insertion fails (rc < 0), reduces font size by 1pt and retries
    3. Repeats up to 3 times before giving up
    4. Logs success/failure with details
    
    Args:
        page: PyMuPDF page object
        rect: Field rectangle (position and dimensions)
        text: Text to insert
        field_name: Field name for logging purposes
        default_font_size: Starting font size (default: 10.0)
        min_font_size: Minimum allowed font size (default: 6.0)
        text_color: RGB color tuple (default: black)
        
    Returns:
        True if text was successfully inserted, False otherwise
        
    Requirements: 1.2, 2.2, 3.2
    """
    max_attempts = 3
    current_font_size = default_font_size
    
    for attempt in range(1, max_attempts + 1):
        # Ensure font size doesn't go below minimum
        if current_font_size < min_font_size:
            logger.warning(
                f"Text too large for field '{field_name}' even at minimum font size {min_font_size}pt. "
                f"Text length: {len(text)}, Field dimensions: {rect.width:.1f}x{rect.height:.1f}. "
                f"Consider truncating text or increasing field size."
            )
            return False
        
        # Attempt to insert text
        rc = page.insert_textbox(
            rect,
            text,
            fontsize=current_font_size,
            fontname="helv",  # Use built-in Helvetica font
            color=text_color,
            align=fitz.TEXT_ALIGN_LEFT
        )
        
        # Check if insertion was successful
        if rc >= 0:
            # Log success with complete details
            if attempt > 1:
                logger.info(
                    f"Successfully rendered field '{field_name}' with reduced font size {current_font_size:.1f}pt "
                    f"(default was {default_font_size:.1f}pt) after {attempt} attempt(s). "
                    f"Text length: {len(text)}, Field dimensions: {rect.width:.1f}x{rect.height:.1f}"
                )
            else:
                logger.info(
                    f"Successfully rendered field '{field_name}' with font size {current_font_size:.1f}pt. "
                    f"Text length: {len(text)}, Field dimensions: {rect.width:.1f}x{rect.height:.1f}"
                )
            return True
        
        # Insertion failed - log and prepare for retry
        logger.debug(
            f"Attempt {attempt}/{max_attempts}: Text doesn't fit in field '{field_name}' "
            f"at font size {current_font_size:.1f}pt (rc={rc}). "
            f"Field dimensions: {rect.width:.1f}x{rect.height:.1f}, Text length: {len(text)}"
        )
        
        # Reduce font size for next attempt
        current_font_size -= 1.0
    
    # All attempts failed
    logger.error(
        f"Failed to render field '{field_name}' after {max_attempts} attempts. "
        f"Field name: '{field_name}', Text length: {len(text)}, "
        f"Field dimensions: {rect.width:.1f}x{rect.height:.1f}, "
        f"Final font size attempted: {current_font_size + 1.0:.1f}pt, "
        f"Minimum font size: {min_font_size:.1f}pt"
    )
    return False


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
                rect = field_data['rect']
                value = field_data['value']
                
                # Determine which copy this field belongs to
                copy_id = None
                if 'Copy1[0]' in field_name:
                    copy_id = 'Copy1'
                elif 'Copy2[0]' in field_name:
                    copy_id = 'Copy2'
                elif 'CopyB[0]' in field_name:
                    copy_id = 'CopyB'
                
                # Determine field column from field name to get appropriate rendering config
                column_type = 'LeftCol'  # Default
                if 'LeftCol' in field_name:
                    column_type = 'LeftCol'
                elif 'RghtCol' in field_name:
                    column_type = 'RghtCol'
                elif 'CopyHeader' in field_name:
                    column_type = 'CopyHeader'
                
                # Look up rendering config for this column
                config = FIELD_RENDERING_CONFIG.get(column_type, FIELD_RENDERING_CONFIG['LeftCol'])
                
                # Calculate adaptive font size based on field dimensions and text content
                calculated_font_size = calculate_font_size(
                    text=value,
                    field_width=rect.width,
                    field_height=rect.height,
                    max_font_size=config['max_font_size'],
                    min_font_size=config['min_font_size']
                )
                
                # Use insert_text_with_fallback for better error handling and retry logic
                success = insert_text_with_fallback(
                    page=page,
                    rect=rect,
                    text=value,
                    field_name=field_name,
                    default_font_size=calculated_font_size,
                    min_font_size=config['min_font_size'],
                    text_color=field_data['text_color']
                )
                
                if success:
                    populated_count += 1
                    if copy_id:
                        copy_stats[copy_id]['success'] += 1
                        logger.debug(f"Successfully populated {copy_id} field '{field_name}' with value '{value}'")
                    else:
                        logger.debug(f"Flattened field '{field_name}' with value '{value}'")
                else:
                    if copy_id:
                        copy_stats[copy_id]['failed'].append(field_name)
                        logger.warning(f"Failed to populate {copy_id} field '{field_name}'")
                    else:
                        logger.warning(f"Failed to insert text for field '{field_name}'")
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
