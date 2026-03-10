"""
Integration tests for visual field mapper.

This module tests the visual field mapper's ability to identify field purposes
based on position, dimensions, and context in real PDF forms.

Requirements: 1.3
"""

import pytest
from typing import List, Tuple

from visual_field_mapper import (
    VisualFieldMapper,
    FieldInfo,
    FieldPurpose,
    FormLayoutSpec
)


class TestVisualFieldMapperIntegration:
    """Integration tests for VisualFieldMapper."""
    
    @pytest.fixture
    def mapper(self):
        """Create a visual field mapper instance."""
        return VisualFieldMapper()
    
    @pytest.fixture
    def form_layout(self):
        """Create a form layout specification."""
        return FormLayoutSpec()
    
    def test_identify_payer_tin_in_left_column(self, mapper):
        """
        Test that payer TIN field is correctly identified in left column.
        
        Based on actual 1099-DIV inspection findings:
        - Field: f2_7[0]
        - Location: LeftCol at position (52.4, 262.0)
        - Dimensions: 242.1 × 26.0
        """
        field = FieldInfo(
            name="topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]",
            page_num=2,
            rect=(52.4, 262.0, 242.1, 26.0),
            field_type="text",
            column="LeftCol",
            nearby_text=["PAYER'S", "TIN"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        assert purpose == FieldPurpose.PAYER_TIN
    
    def test_identify_recipient_tin_in_left_column(self, mapper):
        """
        Test that recipient TIN field is correctly identified in left column.
        
        Based on actual 1099-DIV inspection findings:
        - Field: f2_8[0]
        - Location: LeftCol at position (50.4, 334.0)
        - Dimensions: 244.8 × 26.0
        """
        field = FieldInfo(
            name="topmostSubform[0].Copy1[0].LeftCol[0].f2_8[0]",
            page_num=2,
            rect=(50.4, 334.0, 244.8, 26.0),
            field_type="text",
            column="LeftCol",
            nearby_text=["RECIPIENT'S", "TIN"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        assert purpose == FieldPurpose.RECIPIENT_TIN
    
    def test_identify_payer_name_in_left_column(self, mapper):
        """
        Test that payer name field is correctly identified in left column.
        
        Based on actual 1099-DIV inspection findings:
        - Field: f2_2[0]
        - Location: LeftCol at position (52.4, 56.0)
        - Dimensions: 242.1 × 76.0 (large field)
        """
        field = FieldInfo(
            name="topmostSubform[0].Copy1[0].LeftCol[0].f2_2[0]",
            page_num=2,
            rect=(52.4, 56.0, 242.1, 76.0),
            field_type="text",
            column="LeftCol",
            nearby_text=["PAYER'S", "name"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        assert purpose == FieldPurpose.PAYER_NAME
    
    def test_identify_box_field_in_right_column(self, mapper):
        """
        Test that box value fields are correctly identified in right column.
        
        Based on actual 1099-DIV inspection findings:
        - Field: f2_9[0] (Box 1a - Total ordinary dividends)
        - Location: RghtCol at position (305.2, 60.0)
        - Dimensions: 89.8 × 12.0 (small field)
        """
        field = FieldInfo(
            name="topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]",
            page_num=2,
            rect=(305.2, 60.0, 89.8, 12.0),
            field_type="text",
            column="RghtCol",
            nearby_text=["1a", "Total", "ordinary", "dividends"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        assert purpose == FieldPurpose.BOX_1A_ORDINARY_DIVIDENDS
    
    def test_identify_questionable_recipient_name_in_right_column(self, mapper):
        """
        Test identification of recipient name field in right column.
        
        Based on actual 1099-DIV inspection findings:
        - Field: f2_31[0]
        - Location: RghtCol at position (406.0, 336.0)
        - Dimensions: 89.8 × 12.0 (small, typical of box fields)
        
        This field is questionable because:
        - It's in the right column (box values section)
        - It has small dimensions typical of amount fields
        - Recipient info is typically in left column
        """
        field = FieldInfo(
            name="topmostSubform[0].Copy1[0].RghtCol[0].f2_31[0]",
            page_num=2,
            rect=(406.0, 336.0, 89.8, 12.0),
            field_type="text",
            column="RghtCol",
            nearby_text=["RECIPIENT'S", "name"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        # The mapper should identify this as recipient name based on nearby text
        # even though the position and dimensions are unusual
        assert purpose == FieldPurpose.RECIPIENT_NAME
    
    def test_identify_calendar_year_in_header(self, mapper):
        """
        Test that calendar year field is correctly identified in header.
        """
        field = FieldInfo(
            name="topmostSubform[0].Copy1[0].CopyHeader[0].CalendarYear[0].f2_1[0]",
            page_num=2,
            rect=(100.0, 20.0, 50.0, 15.0),
            field_type="text",
            column="CopyHeader",
            nearby_text=["Calendar", "Year", "2024"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        assert purpose == FieldPurpose.CALENDAR_YEAR
    
    def test_identify_payer_city_field(self, mapper):
        """
        Test that payer city field is correctly identified.
        
        Based on actual 1099-DIV inspection findings:
        - Field: f2_4[0]
        - Location: LeftCol at position (172.8, 142.0)
        - Dimensions: 122.4 × 38.0
        """
        field = FieldInfo(
            name="topmostSubform[0].Copy1[0].LeftCol[0].f2_4[0]",
            page_num=2,
            rect=(172.8, 142.0, 122.4, 38.0),
            field_type="text",
            column="LeftCol",
            nearby_text=["City", "or", "town"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        assert purpose == FieldPurpose.PAYER_CITY
    
    def test_identify_account_number_in_right_column(self, mapper):
        """
        Test that account number field is correctly identified.
        
        Based on actual 1099-DIV inspection findings:
        - Field: f2_39[0]
        - Location: RghtCol
        """
        field = FieldInfo(
            name="topmostSubform[0].Copy1[0].RghtCol[0].f2_39[0]",
            page_num=2,
            rect=(305.2, 350.0, 89.8, 12.0),
            field_type="text",
            column="RghtCol",
            nearby_text=["Account", "number"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        assert purpose == FieldPurpose.ACCOUNT_NUMBER
    
    def test_identify_multiple_fields(self, mapper):
        """
        Test identifying purposes for multiple fields at once.
        """
        fields = [
            FieldInfo(
                name="f2_7[0]",
                page_num=2,
                rect=(52.4, 262.0, 242.1, 26.0),
                field_type="text",
                column="LeftCol",
                nearby_text=["PAYER'S", "TIN"]
            ),
            FieldInfo(
                name="f2_8[0]",
                page_num=2,
                rect=(50.4, 334.0, 244.8, 26.0),
                field_type="text",
                column="LeftCol",
                nearby_text=["RECIPIENT'S", "TIN"]
            ),
            FieldInfo(
                name="f2_9[0]",
                page_num=2,
                rect=(305.2, 60.0, 89.8, 12.0),
                field_type="text",
                column="RghtCol",
                nearby_text=["1a", "Total", "ordinary", "dividends"]
            ),
        ]
        
        results = mapper.identify_all_fields(fields)
        
        assert len(results) == 3
        assert results["f2_7[0]"] == FieldPurpose.PAYER_TIN
        assert results["f2_8[0]"] == FieldPurpose.RECIPIENT_TIN
        assert results["f2_9[0]"] == FieldPurpose.BOX_1A_ORDINARY_DIVIDENDS
    
    def test_handle_ambiguous_field_with_left_column_preference(self, mapper):
        """
        Test that ambiguous fields in left column are resolved correctly.
        """
        field = FieldInfo(
            name="ambiguous_field",
            page_num=2,
            rect=(100.0, 280.0, 200.0, 25.0),
            field_type="text",
            column="LeftCol",
            nearby_text=[]  # No nearby text to help
        )
        
        candidates = [FieldPurpose.PAYER_TIN, FieldPurpose.BOX_1A_ORDINARY_DIVIDENDS]
        
        result = mapper.handle_ambiguous_field(field, candidates)
        
        # Should prefer payer TIN because it's in left column
        assert result == FieldPurpose.PAYER_TIN
    
    def test_handle_ambiguous_field_with_right_column_preference(self, mapper):
        """
        Test that ambiguous fields in right column are resolved correctly.
        """
        field = FieldInfo(
            name="ambiguous_field",
            page_num=2,
            rect=(350.0, 100.0, 90.0, 12.0),
            field_type="text",
            column="RghtCol",
            nearby_text=[]  # No nearby text to help
        )
        
        candidates = [FieldPurpose.PAYER_TIN, FieldPurpose.BOX_1A_ORDINARY_DIVIDENDS]
        
        result = mapper.handle_ambiguous_field(field, candidates)
        
        # Should prefer box field because it's in right column
        assert result == FieldPurpose.BOX_1A_ORDINARY_DIVIDENDS
    
    def test_identify_field_without_column_info(self, mapper):
        """
        Test that fields can be identified even without column information.
        
        This tests the fallback dimension-based identification.
        """
        # Large field in payer section (should be identified as payer name)
        field = FieldInfo(
            name="unknown_field",
            page_num=2,
            rect=(50.0, 80.0, 250.0, 30.0),
            field_type="text",
            column="",  # No column info
            nearby_text=[]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        # Should identify as payer name based on dimensions and Y position
        assert purpose == FieldPurpose.PAYER_NAME
    
    def test_identify_small_field_as_box_value(self, mapper):
        """
        Test that small fields are identified as box values.
        """
        field = FieldInfo(
            name="small_field",
            page_num=2,
            rect=(350.0, 150.0, 85.0, 10.0),
            field_type="text",
            column="",  # No column info
            nearby_text=[]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        # Should identify as unknown box field based on small dimensions
        # (without nearby text, we can't determine which specific box)
        assert purpose == FieldPurpose.UNKNOWN
    
    def test_identify_box_1b_qualified_dividends(self, mapper):
        """
        Test identification of Box 1b (Qualified dividends).
        """
        field = FieldInfo(
            name="f2_10[0]",
            page_num=2,
            rect=(305.2, 96.0, 89.8, 12.0),
            field_type="text",
            column="RghtCol",
            nearby_text=["1b", "Qualified", "dividends"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        assert purpose == FieldPurpose.BOX_1B_QUALIFIED_DIVIDENDS
    
    def test_identify_box_4_federal_tax(self, mapper):
        """
        Test identification of Box 4 (Federal income tax withheld).
        """
        field = FieldInfo(
            name="f2_18[0]",
            page_num=2,
            rect=(305.2, 180.0, 89.8, 12.0),
            field_type="text",
            column="RghtCol",
            nearby_text=["4", "Federal", "income", "tax", "withheld"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        assert purpose == FieldPurpose.BOX_4_FEDERAL_TAX
    
    def test_identify_payer_tin_by_position_without_keywords(self, mapper):
        """
        Test that payer TIN can be identified by position even without keywords.
        
        This tests the position-based heuristic for fields at y > 250 in left column.
        """
        field = FieldInfo(
            name="f2_7[0]",
            page_num=2,
            rect=(52.4, 262.0, 242.1, 26.0),
            field_type="text",
            column="LeftCol",
            nearby_text=[]  # No keywords
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        # Should still identify as payer TIN based on position
        assert purpose == FieldPurpose.PAYER_TIN
    
    def test_identify_recipient_tin_by_position(self, mapper):
        """
        Test that recipient TIN can be identified by position.
        
        This tests the position-based heuristic for fields at y > 320 in left column.
        """
        field = FieldInfo(
            name="f2_8[0]",
            page_num=2,
            rect=(50.4, 334.0, 244.8, 26.0),
            field_type="text",
            column="LeftCol",
            nearby_text=[]  # No keywords
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        # Should identify as recipient TIN based on position
        assert purpose == FieldPurpose.RECIPIENT_TIN
    
    def test_custom_form_layout(self):
        """
        Test that custom form layout specifications can be used.
        """
        custom_layout = FormLayoutSpec()
        custom_layout.LEFT_COLUMN_MAX_X = 350.0  # Wider left column
        
        mapper = VisualFieldMapper(form_layout=custom_layout)
        
        # Field that would be in right column with default layout
        # but in left column with custom layout
        field = FieldInfo(
            name="test_field",
            page_num=2,
            rect=(320.0, 100.0, 200.0, 25.0),
            field_type="text",
            column="",
            nearby_text=["PAYER'S", "name"]
        )
        
        purpose = mapper.identify_field_purpose(field)
        
        # Should identify as payer name because it's in left column with custom layout
        assert purpose == FieldPurpose.PAYER_NAME


class TestFieldPurposeEnum:
    """Tests for FieldPurpose enumeration."""
    
    def test_field_purpose_values(self):
        """Test that all expected field purposes are defined."""
        expected_purposes = [
            "payer_name", "payer_tin", "recipient_name", "recipient_tin",
            "box_1a_ordinary_dividends", "box_1b_qualified_dividends",
            "calendar_year", "account_number", "unknown"
        ]
        
        actual_values = [p.value for p in FieldPurpose]
        
        for expected in expected_purposes:
            assert expected in actual_values
    
    def test_field_purpose_uniqueness(self):
        """Test that all field purpose values are unique."""
        values = [p.value for p in FieldPurpose]
        assert len(values) == len(set(values))


class TestFormLayoutSpec:
    """Tests for FormLayoutSpec dataclass."""
    
    def test_default_layout_values(self):
        """Test that default layout values are reasonable."""
        layout = FormLayoutSpec()
        
        assert layout.PAGE_WIDTH == 612.0  # Letter width
        assert layout.PAGE_HEIGHT == 792.0  # Letter height
        assert layout.LEFT_COLUMN_MAX_X < layout.RIGHT_COLUMN_MIN_X
        assert layout.NAME_FIELD_MIN_WIDTH > 0
        assert layout.TIN_FIELD_MIN_WIDTH > 0
        assert layout.BOX_FIELD_MAX_WIDTH < layout.NAME_FIELD_MIN_WIDTH
    
    def test_section_boundaries(self):
        """Test that section boundaries are logical."""
        layout = FormLayoutSpec()
        
        # Payer section should be above recipient section
        assert layout.PAYER_SECTION_Y_MIN < layout.PAYER_SECTION_Y_MAX
        assert layout.RECIPIENT_SECTION_Y_MIN < layout.RECIPIENT_SECTION_Y_MAX
        assert layout.PAYER_SECTION_Y_MAX <= layout.RECIPIENT_SECTION_Y_MIN
