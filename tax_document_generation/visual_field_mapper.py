"""
Visual Field Mapper for IRS 1099-DIV Form

This module provides functionality to identify the purpose of PDF form fields
based on their visual position, dimensions, and context. It implements the
IRS 1099-DIV form layout specification and matches fields to their intended
purposes (payer_tin, recipient_tin, recipient_name, etc.).

The visual field mapper uses multiple strategies to identify field purposes:
1. Position-based matching: Compare field coordinates to known IRS form layout
2. Dimension-based matching: Use field size to distinguish field types
3. Context-based matching: Analyze nearby text labels
4. Column-based matching: Use column location (LeftCol vs RghtCol)

Requirements: 1.3
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FieldPurpose(Enum):
    """Enumeration of possible field purposes in 1099-DIV form."""
    PAYER_NAME = "payer_name"
    PAYER_TIN = "payer_tin"
    PAYER_STREET_ADDRESS = "payer_street_address"
    PAYER_CITY = "payer_city"
    PAYER_STATE = "payer_state"
    PAYER_ZIP = "payer_zip"
    PAYER_COUNTRY = "payer_country"
    PAYER_PHONE = "payer_phone"
    
    RECIPIENT_NAME = "recipient_name"
    RECIPIENT_TIN = "recipient_tin"
    RECIPIENT_STREET_ADDRESS = "recipient_street_address"
    RECIPIENT_CITY = "recipient_city"
    RECIPIENT_STATE = "recipient_state"
    RECIPIENT_ZIP = "recipient_zip"
    RECIPIENT_COUNTRY = "recipient_country"
    
    ACCOUNT_NUMBER = "account_number"
    CALENDAR_YEAR = "calendar_year"
    
    # Box fields (amounts)
    BOX_1A_ORDINARY_DIVIDENDS = "box_1a_ordinary_dividends"
    BOX_1B_QUALIFIED_DIVIDENDS = "box_1b_qualified_dividends"
    BOX_2A_CAPITAL_GAIN = "box_2a_capital_gain"
    BOX_2B_UNRECAPTURED_1250 = "box_2b_unrecaptured_1250"
    BOX_2C_SECTION_1202 = "box_2c_section_1202"
    BOX_2D_COLLECTIBLES = "box_2d_collectibles"
    BOX_2E_SECTION_897_ORDINARY = "box_2e_section_897_ordinary"
    BOX_2F_SECTION_897_CAPITAL = "box_2f_section_897_capital"
    BOX_3_NONDIVIDEND = "box_3_nondividend"
    BOX_4_FEDERAL_TAX = "box_4_federal_tax"
    BOX_5_SECTION_199A = "box_5_section_199a"
    BOX_6_INVESTMENT_EXPENSES = "box_6_investment_expenses"
    BOX_7_FOREIGN_TAX = "box_7_foreign_tax"
    BOX_8_FOREIGN_COUNTRY = "box_8_foreign_country"
    BOX_9_CASH_LIQUIDATION = "box_9_cash_liquidation"
    BOX_10_NONCASH_LIQUIDATION = "box_10_noncash_liquidation"
    BOX_11_FATCA = "box_11_fatca"
    BOX_12_EXEMPT_INTEREST = "box_12_exempt_interest"
    BOX_13_PRIVATE_ACTIVITY = "box_13_private_activity"
    BOX_14_STATE = "box_14_state"
    BOX_15_STATE_ID = "box_15_state_id"
    BOX_16_STATE_TAX = "box_16_state_tax"
    
    UNKNOWN = "unknown"


@dataclass
class FormLayoutSpec:
    """
    IRS 1099-DIV form layout specification.
    
    Defines expected positions and dimensions for fields based on
    IRS form specifications. Coordinates are in PDF points (1/72 inch).
    
    Standard letter size: 612 × 792 points (8.5" × 11")
    """
    
    # Page dimensions
    PAGE_WIDTH: float = 612.0
    PAGE_HEIGHT: float = 792.0
    
    # Column boundaries (approximate)
    LEFT_COLUMN_MAX_X: float = 299.0  # Left column ends around x=299
    RIGHT_COLUMN_MIN_X: float = 300.0  # Right column starts around x=300
    
    # Field dimension thresholds
    NAME_FIELD_MIN_WIDTH: float = 150.0  # Name fields are typically wide
    NAME_FIELD_MIN_HEIGHT: float = 20.0  # Name fields are typically tall
    
    TIN_FIELD_MIN_WIDTH: float = 150.0  # TIN fields are typically wide
    TIN_FIELD_MIN_HEIGHT: float = 20.0  # TIN fields are typically tall
    
    BOX_FIELD_MAX_WIDTH: float = 120.0  # Box value fields are narrow
    BOX_FIELD_MAX_HEIGHT: float = 20.0  # Box value fields are short
    
    # Y-coordinate ranges for different sections (approximate)
    PAYER_SECTION_Y_MIN: float = 50.0
    PAYER_SECTION_Y_MAX: float = 300.0
    
    RECIPIENT_SECTION_Y_MIN: float = 300.0
    RECIPIENT_SECTION_Y_MAX: float = 400.0
    
    BOX_SECTION_Y_MIN: float = 50.0
    BOX_SECTION_Y_MAX: float = 400.0


@dataclass
class FieldInfo:
    """Information about a PDF form field."""
    name: str
    page_num: int
    rect: Tuple[float, float, float, float]  # (x, y, width, height)
    field_type: str
    column: str  # "LeftCol", "RghtCol", "CopyHeader", or ""
    nearby_text: List[str]


class VisualFieldMapper:
    """
    Maps PDF fields to their purposes based on visual characteristics.
    
    This class implements the IRS 1099-DIV form layout specification and
    uses multiple strategies to identify field purposes:
    - Position-based matching
    - Dimension-based matching
    - Context-based matching (nearby text)
    - Column-based matching
    
    Requirements: 1.3
    """
    
    def __init__(self, form_layout: Optional[FormLayoutSpec] = None):
        """
        Initialize the visual field mapper.
        
        Args:
            form_layout: Form layout specification (uses default if None)
        """
        self.form_layout = form_layout or FormLayoutSpec()
        logger.info("Initialized VisualFieldMapper with IRS 1099-DIV layout specification")
    
    def identify_field_purpose(self, field_info: FieldInfo) -> FieldPurpose:
        """
        Identify the purpose of a field based on its visual characteristics.
        
        This method uses multiple strategies to determine field purpose:
        1. Check column location (LeftCol vs RghtCol)
        2. Check field dimensions (name/TIN fields vs box fields)
        3. Check Y-coordinate position (payer section vs recipient section)
        4. Analyze nearby text for keywords
        5. Apply heuristics for ambiguous cases
        
        Args:
            field_info: Field metadata including position, dimensions, and context
            
        Returns:
            FieldPurpose enum value indicating the identified purpose
            
        Requirements: 1.3
        """
        x, y, width, height = field_info.rect
        column = field_info.column
        nearby_text = field_info.nearby_text
        
        logger.debug(
            f"Identifying purpose for field '{field_info.name}': "
            f"column={column}, pos=({x:.1f}, {y:.1f}), "
            f"size=({width:.1f} × {height:.1f})"
        )
        
        # Strategy 1: Check if field is in header (calendar year)
        if column == "CopyHeader" or "CopyHeader" in field_info.name:
            if self._contains_keywords(nearby_text, ["year", "calendar"]):
                logger.debug(f"Field '{field_info.name}' identified as CALENDAR_YEAR (header)")
                return FieldPurpose.CALENDAR_YEAR
        
        # Strategy 2: Check if field is in left column (payer/recipient info)
        if column == "LeftCol" or x < self.form_layout.LEFT_COLUMN_MAX_X:
            return self._identify_left_column_field(field_info)
        
        # Strategy 3: Check if field is in right column (box values)
        if column == "RghtCol" or x >= self.form_layout.RIGHT_COLUMN_MIN_X:
            return self._identify_right_column_field(field_info)
        
        # Strategy 4: If column is ambiguous, use dimensions and position
        logger.warning(
            f"Field '{field_info.name}' has ambiguous column location, "
            f"using dimension-based identification"
        )
        return self._identify_by_dimensions(field_info)
    
    def _identify_left_column_field(self, field_info: FieldInfo) -> FieldPurpose:
        """
        Identify field purpose for fields in the left column.
        
        Left column contains payer and recipient information fields.
        
        Args:
            field_info: Field metadata
            
        Returns:
            FieldPurpose for left column fields
        """
        x, y, width, height = field_info.rect
        nearby_text = field_info.nearby_text
        
        # Check if field is in payer section (top of left column)
        if y < self.form_layout.PAYER_SECTION_Y_MAX:
            return self._identify_payer_field(field_info)
        
        # Check if field is in recipient section (bottom of left column)
        if y >= self.form_layout.RECIPIENT_SECTION_Y_MIN:
            return self._identify_recipient_field(field_info)
        
        logger.warning(
            f"Field '{field_info.name}' in left column but outside "
            f"known sections (y={y:.1f})"
        )
        return FieldPurpose.UNKNOWN
    
    def _identify_payer_field(self, field_info: FieldInfo) -> FieldPurpose:
        """
        Identify payer field purpose based on position and context.
        
        Args:
            field_info: Field metadata
            
        Returns:
            FieldPurpose for payer fields
        """
        x, y, width, height = field_info.rect
        nearby_text = field_info.nearby_text
        
        # Check for TIN field (typically below address fields)
        if self._contains_keywords(nearby_text, ["tin", "identification", "number"]):
            if width >= self.form_layout.TIN_FIELD_MIN_WIDTH:
                logger.debug(f"Field '{field_info.name}' identified as PAYER_TIN")
                return FieldPurpose.PAYER_TIN
        
        # Check for name field (typically at top, large dimensions)
        if self._contains_keywords(nearby_text, ["payer", "name"]):
            if width >= self.form_layout.NAME_FIELD_MIN_WIDTH:
                logger.debug(f"Field '{field_info.name}' identified as PAYER_NAME")
                return FieldPurpose.PAYER_NAME
        
        # Check for address fields
        if self._contains_keywords(nearby_text, ["street", "address"]):
            logger.debug(f"Field '{field_info.name}' identified as PAYER_STREET_ADDRESS")
            return FieldPurpose.PAYER_STREET_ADDRESS
        
        if self._contains_keywords(nearby_text, ["city"]):
            logger.debug(f"Field '{field_info.name}' identified as PAYER_CITY")
            return FieldPurpose.PAYER_CITY
        
        if self._contains_keywords(nearby_text, ["state"]):
            logger.debug(f"Field '{field_info.name}' identified as PAYER_STATE")
            return FieldPurpose.PAYER_STATE
        
        if self._contains_keywords(nearby_text, ["zip", "postal"]):
            logger.debug(f"Field '{field_info.name}' identified as PAYER_ZIP")
            return FieldPurpose.PAYER_ZIP
        
        if self._contains_keywords(nearby_text, ["country"]):
            logger.debug(f"Field '{field_info.name}' identified as PAYER_COUNTRY")
            return FieldPurpose.PAYER_COUNTRY
        
        if self._contains_keywords(nearby_text, ["phone", "telephone"]):
            logger.debug(f"Field '{field_info.name}' identified as PAYER_PHONE")
            return FieldPurpose.PAYER_PHONE
        
        # Position-based heuristics for payer section
        # Typically: name (top) → address → city → state → zip → TIN (bottom)
        if y < 100:  # Top of payer section
            if height > self.form_layout.NAME_FIELD_MIN_HEIGHT:
                logger.debug(f"Field '{field_info.name}' identified as PAYER_NAME (position)")
                return FieldPurpose.PAYER_NAME
        elif y > 250:  # Bottom of payer section
            if width >= self.form_layout.TIN_FIELD_MIN_WIDTH:
                logger.debug(f"Field '{field_info.name}' identified as PAYER_TIN (position)")
                return FieldPurpose.PAYER_TIN
        
        logger.warning(f"Could not identify payer field '{field_info.name}'")
        return FieldPurpose.UNKNOWN
    
    def _identify_recipient_field(self, field_info: FieldInfo) -> FieldPurpose:
        """
        Identify recipient field purpose based on position and context.
        
        Args:
            field_info: Field metadata
            
        Returns:
            FieldPurpose for recipient fields
        """
        x, y, width, height = field_info.rect
        nearby_text = field_info.nearby_text
        
        # Check for TIN field
        if self._contains_keywords(nearby_text, ["tin", "identification", "number", "recipient"]):
            if width >= self.form_layout.TIN_FIELD_MIN_WIDTH:
                logger.debug(f"Field '{field_info.name}' identified as RECIPIENT_TIN")
                return FieldPurpose.RECIPIENT_TIN
        
        # Check for name field
        if self._contains_keywords(nearby_text, ["recipient", "name"]):
            if width >= self.form_layout.NAME_FIELD_MIN_WIDTH:
                logger.debug(f"Field '{field_info.name}' identified as RECIPIENT_NAME")
                return FieldPurpose.RECIPIENT_NAME
        
        # Position-based heuristic: recipient TIN is typically at bottom of left column
        if y > 320:  # Bottom of left column
            if width >= self.form_layout.TIN_FIELD_MIN_WIDTH:
                logger.debug(f"Field '{field_info.name}' identified as RECIPIENT_TIN (position)")
                return FieldPurpose.RECIPIENT_TIN
        
        logger.warning(f"Could not identify recipient field '{field_info.name}'")
        return FieldPurpose.UNKNOWN
    
    def _identify_right_column_field(self, field_info: FieldInfo) -> FieldPurpose:
        """
        Identify field purpose for fields in the right column.
        
        Right column contains box values (amounts) and some recipient address fields.
        
        Args:
            field_info: Field metadata
            
        Returns:
            FieldPurpose for right column fields
        """
        x, y, width, height = field_info.rect
        nearby_text = field_info.nearby_text
        
        # Check for specific non-box fields first (before checking dimensions)
        # These checks should happen before the box field check because
        # recipient name and account number might have box-like dimensions
        
        if self._contains_keywords(nearby_text, ["recipient", "name"]):
            logger.debug(f"Field '{field_info.name}' identified as RECIPIENT_NAME (right column)")
            return FieldPurpose.RECIPIENT_NAME
        
        if self._contains_keywords(nearby_text, ["account", "number"]):
            logger.debug(f"Field '{field_info.name}' identified as ACCOUNT_NUMBER")
            return FieldPurpose.ACCOUNT_NUMBER
        
        if self._contains_keywords(nearby_text, ["recipient", "street", "address"]):
            logger.debug(f"Field '{field_info.name}' identified as RECIPIENT_STREET_ADDRESS")
            return FieldPurpose.RECIPIENT_STREET_ADDRESS
        
        if self._contains_keywords(nearby_text, ["recipient", "city"]):
            logger.debug(f"Field '{field_info.name}' identified as RECIPIENT_CITY")
            return FieldPurpose.RECIPIENT_CITY
        
        if self._contains_keywords(nearby_text, ["recipient", "state"]):
            logger.debug(f"Field '{field_info.name}' identified as RECIPIENT_STATE")
            return FieldPurpose.RECIPIENT_STATE
        
        if self._contains_keywords(nearby_text, ["recipient", "zip"]):
            logger.debug(f"Field '{field_info.name}' identified as RECIPIENT_ZIP")
            return FieldPurpose.RECIPIENT_ZIP
        
        # Check if field is a small box value field
        is_box_field = (
            width <= self.form_layout.BOX_FIELD_MAX_WIDTH and
            height <= self.form_layout.BOX_FIELD_MAX_HEIGHT
        )
        
        if is_box_field:
            return self._identify_box_field(field_info)
        
        logger.warning(
            f"Field '{field_info.name}' in right column but not identified "
            f"(size: {width:.1f} × {height:.1f})"
        )
        return FieldPurpose.UNKNOWN
    
    def _identify_box_field(self, field_info: FieldInfo) -> FieldPurpose:
        """
        Identify which box a field belongs to based on position and nearby text.
        
        Args:
            field_info: Field metadata
            
        Returns:
            FieldPurpose for box fields
        """
        x, y, width, height = field_info.rect
        nearby_text = field_info.nearby_text
        
        # Map box numbers to purposes
        box_mapping = {
            "1a": FieldPurpose.BOX_1A_ORDINARY_DIVIDENDS,
            "1b": FieldPurpose.BOX_1B_QUALIFIED_DIVIDENDS,
            "2a": FieldPurpose.BOX_2A_CAPITAL_GAIN,
            "2b": FieldPurpose.BOX_2B_UNRECAPTURED_1250,
            "2c": FieldPurpose.BOX_2C_SECTION_1202,
            "2d": FieldPurpose.BOX_2D_COLLECTIBLES,
            "2e": FieldPurpose.BOX_2E_SECTION_897_ORDINARY,
            "2f": FieldPurpose.BOX_2F_SECTION_897_CAPITAL,
            "3": FieldPurpose.BOX_3_NONDIVIDEND,
            "4": FieldPurpose.BOX_4_FEDERAL_TAX,
            "5": FieldPurpose.BOX_5_SECTION_199A,
            "6": FieldPurpose.BOX_6_INVESTMENT_EXPENSES,
            "7": FieldPurpose.BOX_7_FOREIGN_TAX,
            "8": FieldPurpose.BOX_8_FOREIGN_COUNTRY,
            "9": FieldPurpose.BOX_9_CASH_LIQUIDATION,
            "10": FieldPurpose.BOX_10_NONCASH_LIQUIDATION,
            "11": FieldPurpose.BOX_11_FATCA,
            "12": FieldPurpose.BOX_12_EXEMPT_INTEREST,
            "13": FieldPurpose.BOX_13_PRIVATE_ACTIVITY,
            "14": FieldPurpose.BOX_14_STATE,
            "15": FieldPurpose.BOX_15_STATE_ID,
            "16": FieldPurpose.BOX_16_STATE_TAX,
        }
        
        # Check nearby text for box numbers
        # Need to check more specific patterns first (e.g., "1b" before "1a")
        nearby_text_lower = " ".join(nearby_text).lower()
        
        # Sort box numbers by length (descending) to match "1b" before "1"
        sorted_boxes = sorted(box_mapping.items(), key=lambda x: len(x[0]), reverse=True)
        
        for box_num, purpose in sorted_boxes:
            # Check for various patterns
            if (f"box {box_num}" in nearby_text_lower or 
                f"{box_num}." in nearby_text_lower or
                f"{box_num} " in nearby_text_lower or
                nearby_text_lower.startswith(box_num)):
                logger.debug(f"Field '{field_info.name}' identified as {purpose.value}")
                return purpose
        
        # Check for specific keywords (fallback if box number not found)
        if self._contains_keywords(nearby_text, ["qualified", "dividend"]):
            logger.debug(f"Field '{field_info.name}' identified as BOX_1B_QUALIFIED_DIVIDENDS")
            return FieldPurpose.BOX_1B_QUALIFIED_DIVIDENDS
        
        if self._contains_keywords(nearby_text, ["ordinary", "dividend"]):
            logger.debug(f"Field '{field_info.name}' identified as BOX_1A_ORDINARY_DIVIDENDS")
            return FieldPurpose.BOX_1A_ORDINARY_DIVIDENDS
        
        if self._contains_keywords(nearby_text, ["capital", "gain"]):
            logger.debug(f"Field '{field_info.name}' identified as BOX_2A_CAPITAL_GAIN")
            return FieldPurpose.BOX_2A_CAPITAL_GAIN
        
        if self._contains_keywords(nearby_text, ["federal", "tax", "withheld"]):
            logger.debug(f"Field '{field_info.name}' identified as BOX_4_FEDERAL_TAX")
            return FieldPurpose.BOX_4_FEDERAL_TAX
        
        if self._contains_keywords(nearby_text, ["foreign", "tax"]):
            logger.debug(f"Field '{field_info.name}' identified as BOX_7_FOREIGN_TAX")
            return FieldPurpose.BOX_7_FOREIGN_TAX
        
        if self._contains_keywords(nearby_text, ["state", "tax"]):
            logger.debug(f"Field '{field_info.name}' identified as BOX_16_STATE_TAX")
            return FieldPurpose.BOX_16_STATE_TAX
        
        logger.warning(f"Could not identify box field '{field_info.name}'")
        return FieldPurpose.UNKNOWN
    
    def _identify_by_dimensions(self, field_info: FieldInfo) -> FieldPurpose:
        """
        Identify field purpose based primarily on dimensions.
        
        This is a fallback method when column location is ambiguous.
        
        Args:
            field_info: Field metadata
            
        Returns:
            FieldPurpose based on dimensions
        """
        x, y, width, height = field_info.rect
        
        # Large fields are likely name or TIN fields
        if width >= self.form_layout.NAME_FIELD_MIN_WIDTH:
            if height >= self.form_layout.NAME_FIELD_MIN_HEIGHT:
                logger.debug(
                    f"Field '{field_info.name}' identified as name/TIN field "
                    f"based on dimensions"
                )
                # Use Y position to distinguish payer vs recipient
                if y < self.form_layout.PAYER_SECTION_Y_MAX:
                    return FieldPurpose.PAYER_NAME
                else:
                    return FieldPurpose.RECIPIENT_NAME
        
        # Small fields are likely box value fields
        if (width <= self.form_layout.BOX_FIELD_MAX_WIDTH and
            height <= self.form_layout.BOX_FIELD_MAX_HEIGHT):
            logger.debug(
                f"Field '{field_info.name}' identified as box field "
                f"based on dimensions"
            )
            return self._identify_box_field(field_info)
        
        logger.warning(
            f"Could not identify field '{field_info.name}' by dimensions "
            f"(size: {width:.1f} × {height:.1f})"
        )
        return FieldPurpose.UNKNOWN
    
    def _contains_keywords(self, text_list: List[str], keywords: List[str]) -> bool:
        """
        Check if any text in the list contains any of the keywords (case-insensitive).
        
        Args:
            text_list: List of text strings to search
            keywords: List of keywords to search for
            
        Returns:
            True if any keyword is found in any text
        """
        if not text_list:
            return False
        
        combined_text = " ".join(text_list).lower()
        return any(keyword.lower() in combined_text for keyword in keywords)
    
    def identify_all_fields(self, fields: List[FieldInfo]) -> Dict[str, FieldPurpose]:
        """
        Identify purposes for all fields in a list.
        
        Args:
            fields: List of FieldInfo objects
            
        Returns:
            Dictionary mapping field names to their identified purposes
        """
        results = {}
        
        for field in fields:
            purpose = self.identify_field_purpose(field)
            results[field.name] = purpose
        
        logger.info(
            f"Identified purposes for {len(results)} fields: "
            f"{sum(1 for p in results.values() if p != FieldPurpose.UNKNOWN)} identified, "
            f"{sum(1 for p in results.values() if p == FieldPurpose.UNKNOWN)} unknown"
        )
        
        return results
    
    def handle_ambiguous_field(
        self,
        field_info: FieldInfo,
        candidate_purposes: List[FieldPurpose]
    ) -> FieldPurpose:
        """
        Handle edge cases where a field could have multiple purposes.
        
        This method applies additional heuristics to resolve ambiguity:
        - Prefer fields in expected columns (LeftCol for payer/recipient)
        - Prefer fields with matching nearby text
        - Prefer fields with appropriate dimensions
        
        Args:
            field_info: Field metadata
            candidate_purposes: List of possible purposes
            
        Returns:
            Most likely FieldPurpose
        """
        if not candidate_purposes:
            logger.warning(f"No candidate purposes for field '{field_info.name}'")
            return FieldPurpose.UNKNOWN
        
        if len(candidate_purposes) == 1:
            return candidate_purposes[0]
        
        logger.info(
            f"Resolving ambiguity for field '{field_info.name}': "
            f"candidates={[p.value for p in candidate_purposes]}"
        )
        
        # Heuristic 1: Prefer fields in left column for payer/recipient info
        if field_info.column == "LeftCol":
            payer_recipient_purposes = [
                p for p in candidate_purposes
                if "payer" in p.value or "recipient" in p.value
            ]
            if payer_recipient_purposes:
                logger.debug(f"Resolved to {payer_recipient_purposes[0].value} (left column)")
                return payer_recipient_purposes[0]
        
        # Heuristic 2: Prefer fields in right column for box values
        if field_info.column == "RghtCol":
            box_purposes = [
                p for p in candidate_purposes
                if "box" in p.value
            ]
            if box_purposes:
                logger.debug(f"Resolved to {box_purposes[0].value} (right column)")
                return box_purposes[0]
        
        # Heuristic 3: Use nearby text to disambiguate
        nearby_text_lower = " ".join(field_info.nearby_text).lower()
        for purpose in candidate_purposes:
            if purpose.value.replace("_", " ") in nearby_text_lower:
                logger.debug(f"Resolved to {purpose.value} (nearby text match)")
                return purpose
        
        # Default: return first candidate
        logger.warning(
            f"Could not resolve ambiguity for field '{field_info.name}', "
            f"using first candidate: {candidate_purposes[0].value}"
        )
        return candidate_purposes[0]
