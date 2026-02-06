"""
Document Generator Module

This module handles the generation of completed tax documents by populating
IRS templates with user-supplied form data.
"""

from typing import Dict
import logging

# Import PyMuPDF - the sole PDF library for this module
try:
    import pymupdf as fitz
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
    },
    # Special config for very small fields (< 30 points wide)
    'SmallField': {
        'default_font_size': 6.0,
        'min_font_size': 5.0,
        'max_font_size': 7.0,
    }
}

# Threshold for small field detection (in points)
SMALL_FIELD_WIDTH_THRESHOLD = 30.0


def check_field_flags(widget: fitz.Widget) -> Dict[str, any]:
    """
    Check field flags and return status dictionary.
    
    This function examines the field_flags bitmask on a PDF widget to determine
    which flags are set. Common flags include:
    - Bit 0: READ-ONLY - Field cannot be modified
    - Bit 1: HIDDEN - Field is not visible
    - Bit 2: REQUIRED - Field must be filled
    
    Args:
        widget: PyMuPDF widget object representing a form field
        
    Returns:
        Dictionary with flag status:
        {
            'is_readonly': bool,  # True if READ-ONLY flag is set
            'is_hidden': bool,    # True if HIDDEN flag is set
            'is_required': bool,  # True if REQUIRED flag is set
            'flags_value': int    # Raw flags bitmask value
        }
        
    Requirements: 4.1, 4.2
    
    Example:
        >>> widget = page.widgets()[0]
        >>> flags = check_field_flags(widget)
        >>> if flags['is_readonly']:
        ...     print(f"Field is read-only, flags: {flags['flags_value']}")
    """
    flags_value = widget.field_flags
    
    return {
        'is_readonly': bool(flags_value & (1 << 0)),  # Bit 0
        'is_hidden': bool(flags_value & (1 << 1)),    # Bit 1
        'is_required': bool(flags_value & (1 << 2)),  # Bit 2
        'flags_value': flags_value
    }


def clear_readonly_flag(widget: fitz.Widget) -> bool:
    """
    Clear the READ-ONLY flag from a field widget.
    
    The READ-ONLY flag (bit 0 of field_flags) prevents modification of a field.
    This function clears that flag using bitwise AND with the complement of the
    READ-ONLY bit mask, then calls widget.update() to apply the change.
    
    Args:
        widget: PyMuPDF widget object representing a form field
        
    Returns:
        True if the READ-ONLY flag was cleared (it was previously set),
        False if no action was needed (flag was not set)
        
    Requirements: 6.1, 6.2
    
    Example:
        >>> widget = page.widgets()[0]
        >>> if widget.field_flags & (1 << 0):
        ...     print("Field is read-only")
        ...     cleared = clear_readonly_flag(widget)
        ...     print(f"Flag cleared: {cleared}")
    """
    # Check if READ-ONLY flag is set (bit 0)
    is_readonly = bool(widget.field_flags & (1 << 0))
    
    if is_readonly:
        # Clear READ-ONLY flag using bitwise AND with complement
        widget.field_flags = widget.field_flags & ~(1 << 0)
        widget.update()
        return True
    
    return False


def clear_hidden_flag(widget: fitz.Widget) -> bool:
    """
    Clear the HIDDEN flag from a field widget.
    
    The HIDDEN flag (bit 1 of field_flags) makes a field invisible.
    This function clears that flag using bitwise AND with the complement of the
    HIDDEN bit mask, then calls widget.update() to apply the change.
    
    Args:
        widget: PyMuPDF widget object representing a form field
        
    Returns:
        True if the HIDDEN flag was cleared (it was previously set),
        False if no action was needed (flag was not set)
        
    Requirements: 4.2
    
    Example:
        >>> widget = page.widgets()[0]
        >>> if widget.field_flags & (1 << 1):
        ...     print("Field is hidden")
        ...     cleared = clear_hidden_flag(widget)
        ...     print(f"Flag cleared: {cleared}")
    """
    # Check if HIDDEN flag is set (bit 1)
    is_hidden = bool(widget.field_flags & (1 << 1))
    
    if is_hidden:
        # Clear HIDDEN flag using bitwise AND with complement
        widget.field_flags = widget.field_flags & ~(1 << 1)
        widget.update()
        return True
    
    return False


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


def flatten_checkbox(
    page: fitz.Page,
    widget: fitz.Widget,
    value: str
) -> None:
    """
    Flatten checkbox to static graphic for visibility in all PDF viewers.
    
    This function converts a checkbox form field into a static graphic by:
    1. Drawing a checkbox border (empty box)
    2. Drawing a checkmark if the checkbox is checked
    3. Using proportional sizing based on the checkbox dimensions
    
    The function is necessary because PyMuPDF 1.26.7 does not support
    widget.update_appearance(), and setting field_value alone does not
    create visible checkmarks in PDF viewers.
    
    Based on research findings:
    - All checkboxes in IRS 1099-DIV are uniformly 9×9 points
    - On state is '1' or '2' (not 'Yes')
    - Checkmark uses proportional coordinates for scalability
    
    Args:
        page: PyMuPDF page object where the checkbox is located
        widget: PyMuPDF widget object representing the checkbox
        value: Checkbox value - on_state value (e.g., '1', '2') for checked,
               'Off' for unchecked
    
    Returns:
        None - modifies the page in place
        
    Raises:
        Exception: Logs but does not raise exceptions to allow graceful degradation
        
    Requirements: 1.1, 1.2, 2.1, 2.2
    
    Example:
        >>> widget = page.widgets()[0]
        >>> on_state = widget.on_state() if hasattr(widget, 'on_state') else '1'
        >>> flatten_checkbox(page, widget, on_state)
    """
    try:
        rect = widget.rect
        
        # Validate rect exists
        if rect is None:
            logger.error("Cannot flatten checkbox: widget.rect is None")
            return
        
        # Draw checkbox border (empty box)
        # Use 0.5pt line width for clean appearance
        page.draw_rect(rect, color=(0, 0, 0), width=0.5)
        
        # Determine if checkbox is checked
        # Value is checked if it matches the on_state (not 'Off')
        is_checked = value != "Off"
        
        # If checked, draw checkmark
        if is_checked:
            # Extract rectangle coordinates
            x0, y0, x1, y1 = rect
            width = x1 - x0
            height = y1 - y0
            
            # Calculate proportional checkmark coordinates
            # Checkmark consists of two strokes forming a check shape:
            # - Left stroke: from bottom-left to middle
            # - Right stroke: from middle to top-right
            
            # Left stroke: from bottom-left to middle
            p1 = fitz.Point(x0 + width * 0.2, y0 + height * 0.5)
            p2 = fitz.Point(x0 + width * 0.4, y0 + height * 0.7)
            
            # Right stroke: from middle to top-right
            p3 = fitz.Point(x0 + width * 0.4, y0 + height * 0.7)
            p4 = fitz.Point(x0 + width * 0.8, y0 + height * 0.3)
            
            # Draw checkmark strokes
            # Use 1.5pt line width for visibility
            page.draw_line(p1, p2, color=(0, 0, 0), width=1.5)
            page.draw_line(p3, p4, color=(0, 0, 0), width=1.5)
            
            logger.debug(
                f"Drew checkmark in checkbox at ({x0:.1f}, {y0:.1f}) "
                f"with dimensions {width:.1f}×{height:.1f}pt"
            )
        else:
            logger.debug(
                f"Drew empty checkbox at ({rect.x0:.1f}, {rect.y0:.1f}) "
                f"with dimensions {rect.width:.1f}×{rect.height:.1f}pt"
            )
            
    except Exception as e:
        # Log error but don't raise - allow document generation to continue
        logger.error(
            f"Failed to flatten checkbox at ({rect.x0:.1f}, {rect.y0:.1f}): "
            f"{type(e).__name__}: {str(e)}"
        )


def generate_document(template: bytes, form_data: Dict, document_type: str) -> bytes:
    """
    Generates a completed tax document by populating a template with form data.
    
    This function:
    1. Loads the PDF template
    2. Normalizes address fields (handles backward compatibility)
    3. Combines address components into multi-line blocks for PDF fields
    4. Translates API field names to PDF field names using FieldMapper
    5. Populates form fields with provided data
    6. Returns the generated PDF as bytes
    
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
        
        # Step 1: Normalize address fields (handles backward compatibility with old combined format)
        from address_normalizer import normalize_address_fields
        logger.info("Normalizing address fields for backward compatibility")
        form_data = normalize_address_fields(form_data)
        
        # Step 2: Combine address components into multi-line blocks for PDF fields
        from address_combiner import combine_address_fields
        logger.info("Combining address components into PDF-ready fields")
        form_data = combine_address_fields(form_data)
        
        # Step 3: Initialize field mapper for this document type
        mapper = FieldMapper(document_type)
        
        # Check for mutual exclusivity warning (VOIDED and CORRECTED both true)
        if form_data.get('voided') and form_data.get('corrected'):
            logger.warning(
                "Both 'voided' and 'corrected' are set to true. "
                "This may not be valid according to IRS guidelines. "
                "The PDF will be generated with both checkboxes checked."
            )
        
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
        
        # Print all PDF fields for debugging
        print("\n" + "="*80)
        print("ALL PDF FIELDS IN TEMPLATE:")
        print("="*80)
        all_fields = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = list(page.widgets())
            for widget in widgets:
                field_name = widget.field_name
                if field_name:
                    all_fields.append(field_name)
                    print(f"Page {page_num + 1}: {field_name}")
        print(f"\nTotal fields found: {len(all_fields)}")
        print("="*80 + "\n")
        
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
        
        # Step 1: Check and clear field flags that prevent modification
        logger.info("Checking and clearing field flags that prevent modification...")
        flags_cleared_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = list(page.widgets())
            
            for widget in widgets:
                field_name = widget.field_name
                if field_name in mapped_data:
                    # Check field flags
                    flags = check_field_flags(widget)
                    
                    # Log calendar year fields specifically
                    if "CalendarYear[0]" in field_name:
                        logger.info(f"Processing calendar year field '{field_name}'")
                        logger.info(f"  Dimensions: {widget.rect.width:.1f}x{widget.rect.height:.1f} points")
                        logger.info(f"  Field flags: {flags['flags_value']}")
                        logger.info(f"  Is READ-ONLY: {flags['is_readonly']}")
                        logger.info(f"  Is HIDDEN: {flags['is_hidden']}")
                    
                    # Clear READ-ONLY flag if present
                    if flags['is_readonly']:
                        logger.warning(f"Field '{field_name}' is READ-ONLY, clearing flag")
                        if clear_readonly_flag(widget):
                            flags_cleared_count += 1
                            logger.info(f"  Cleared READ-ONLY flag, new flags value: {widget.field_flags}")
                    
                    # Clear HIDDEN flag if present
                    if flags['is_hidden']:
                        logger.warning(f"Field '{field_name}' is HIDDEN, clearing flag")
                        if clear_hidden_flag(widget):
                            flags_cleared_count += 1
                            logger.info(f"  Cleared HIDDEN flag, new flags value: {widget.field_flags}")
        
        if flags_cleared_count > 0:
            logger.info(f"Cleared flags on {flags_cleared_count} field(s)")
        else:
            logger.info("No problematic field flags found")
        
        # Step 2: Set checkbox values and collect text field data
        fields_to_flatten = []
        checkbox_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = list(page.widgets())
            
            for widget in widgets:
                field_name = widget.field_name
                if field_name in mapped_data:
                    try:
                        value = mapped_data[field_name]
                        rect = widget.rect
                        field_type = widget.field_type
                        
                        # Handle checkboxes differently from text fields
                        if field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                            # For checkboxes, convert boolean to appropriate value
                            checkbox_value = "Off"
                            if isinstance(value, bool):
                                checkbox_value = "Yes" if value else "Off"
                            elif isinstance(value, str):
                                checkbox_value = "Yes" if value.lower() in ['true', 'yes', '1'] else "Off"
                            
                            # Set the checkbox value
                            widget.field_value = checkbox_value
                            widget.update()
                            
                            # Flatten checkbox to static graphic for visibility
                            # PyMuPDF 1.26.7 does not support widget.update_appearance()
                            # Flattening ensures checkbox is visible in all PDF viewers
                            flatten_checkbox(page, widget, checkbox_value)
                            checkbox_count += 1
                            
                            logger.info(f"Flattened checkbox '{field_name}' to static graphic (value: {checkbox_value})")
                        else:
                            # For text fields, convert to string and collect for later flattening
                            value = str(value)
                            
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
                            
                            logger.debug(f"Prepared text field '{field_name}' for flattening: value='{value}'")
                    except Exception as e:
                        logger.warning(f"Failed to process field '{field_name}': {str(e)}")
        
        logger.info(f"Set {checkbox_count} checkbox(es) and prepared {len(fields_to_flatten)} text fields for flattening")
        
        # Step 3: Insert static text at field locations using built-in Helvetica font
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
                
                # Enhanced logging for calendar year fields
                if "CalendarYear[0]" in field_name:
                    logger.info(f"Filling calendar year field '{field_name}' with value '{value}'")
                
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
                
                # Check if this is a small field (< 30 points wide)
                if rect.width < SMALL_FIELD_WIDTH_THRESHOLD:
                    logger.info(f"Small field detected ({rect.width:.1f}x{rect.height:.1f}), using SmallField config")
                    column_type = 'SmallField'
                
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
                    
                    # Enhanced logging for calendar year fields
                    if "CalendarYear[0]" in field_name:
                        logger.info(f"  ✅ Successfully filled calendar year field '{field_name}'")
                else:
                    if copy_id:
                        copy_stats[copy_id]['failed'].append(field_name)
                        logger.warning(f"Failed to populate {copy_id} field '{field_name}'")
                    else:
                        logger.warning(f"Failed to insert text for field '{field_name}'")
                    failed_fields.append(field_name)
                    
                    # Enhanced logging for calendar year fields
                    if "CalendarYear[0]" in field_name:
                        logger.error(f"  ❌ Failed to fill calendar year field '{field_name}'")
                    
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
        
        # Step 4: Remove form field widgets (convert to static content)
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
