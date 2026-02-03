"""
Unit tests for field dimension extraction functionality.

Tests verify that the analyze_field_dimensions module correctly extracts
and analyzes field dimensions from PDF templates.

Requirements: 4.1, 4.2, 4.3
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze_field_dimensions import (
    extract_field_dimensions,
    group_by_column,
    determine_column_type,
    recommend_font_size,
    FieldDimensions,
    ColumnStats
)


class TestDetermineColumnType:
    """Test column type determination from field names."""
    
    def test_leftcol_detection(self):
        """Test that LeftCol fields are correctly identified."""
        field_name = "topmostSubform[0].Copy1[0].LeftCol[0].f2_7[0]"
        assert determine_column_type(field_name) == 'LeftCol'
    
    def test_rghtcol_detection(self):
        """Test that RghtCol fields are correctly identified."""
        field_name = "topmostSubform[0].Copy1[0].RghtCol[0].f2_9[0]"
        assert determine_column_type(field_name) == 'RghtCol'
    
    def test_copyheader_detection(self):
        """Test that CopyHeader fields are correctly identified."""
        field_name = "topmostSubform[0].Copy1[0].CopyHeader[0].f2_1[0]"
        assert determine_column_type(field_name) == 'CopyHeader'
    
    def test_other_field_detection(self):
        """Test that unrecognized fields are marked as 'Other'."""
        field_name = "topmostSubform[0].SomeOtherField[0].f1_1[0]"
        assert determine_column_type(field_name) == 'Other'


class TestRecommendFontSize:
    """Test font size recommendations based on field height."""
    
    def test_very_small_field(self):
        """Test font size recommendation for very small fields (< 13pt)."""
        default, min_size, max_size = recommend_font_size(12.0)
        assert default == 7.0
        assert min_size == 6.0
        assert max_size == 8.0
    
    def test_small_field(self):
        """Test font size recommendation for small fields (13-20pt)."""
        default, min_size, max_size = recommend_font_size(15.0)
        assert default == 8.0
        assert min_size == 7.0
        assert max_size == 9.0
    
    def test_medium_field(self):
        """Test font size recommendation for medium fields (20-30pt)."""
        default, min_size, max_size = recommend_font_size(26.0)
        assert default == 9.0
        assert min_size == 8.0
        assert max_size == 10.0
    
    def test_large_field(self):
        """Test font size recommendation for large fields (> 30pt)."""
        default, min_size, max_size = recommend_font_size(40.0)
        assert default == 10.0
        assert min_size == 9.0
        assert max_size == 12.0
    
    def test_boundary_at_13(self):
        """Test boundary condition at 13pt."""
        default, min_size, max_size = recommend_font_size(13.0)
        assert default == 8.0  # Should be in small field range
    
    def test_boundary_at_20(self):
        """Test boundary condition at 20pt."""
        default, min_size, max_size = recommend_font_size(20.0)
        assert default == 9.0  # Should be in medium field range (20 <= height < 30)
    
    def test_boundary_at_30(self):
        """Test boundary condition at 30pt."""
        default, min_size, max_size = recommend_font_size(30.0)
        assert default == 10.0  # Should be in large field range (height >= 30)


class TestFieldDimensions:
    """Test FieldDimensions dataclass."""
    
    def test_field_dimensions_creation(self):
        """Test creating a FieldDimensions object."""
        field_dim = FieldDimensions(
            field_name="test_field",
            width=100.0,
            height=20.0,
            x=50.0,
            y=100.0,
            page=0,
            column="LeftCol"
        )
        
        assert field_dim.field_name == "test_field"
        assert field_dim.width == 100.0
        assert field_dim.height == 20.0
        assert field_dim.x == 50.0
        assert field_dim.y == 100.0
        assert field_dim.page == 0
        assert field_dim.column == "LeftCol"


class TestColumnStats:
    """Test ColumnStats dataclass and methods."""
    
    def test_column_stats_creation(self):
        """Test creating a ColumnStats object."""
        stats = ColumnStats(column_name="LeftCol")
        assert stats.column_name == "LeftCol"
        assert stats.field_count == 0
        assert stats.min_height == float('inf')
        assert stats.max_height == 0.0
    
    def test_add_field_updates_stats(self):
        """Test that adding fields updates statistics correctly."""
        stats = ColumnStats(column_name="LeftCol")
        
        field1 = FieldDimensions(
            field_name="field1",
            width=100.0,
            height=20.0,
            x=50.0,
            y=100.0,
            page=0,
            column="LeftCol"
        )
        
        field2 = FieldDimensions(
            field_name="field2",
            width=150.0,
            height=30.0,
            x=50.0,
            y=150.0,
            page=0,
            column="LeftCol"
        )
        
        stats.add_field(field1)
        assert stats.field_count == 1
        assert stats.min_height == 20.0
        assert stats.max_height == 20.0
        assert stats.min_width == 100.0
        assert stats.max_width == 100.0
        
        stats.add_field(field2)
        assert stats.field_count == 2
        assert stats.min_height == 20.0
        assert stats.max_height == 30.0
        assert stats.min_width == 100.0
        assert stats.max_width == 150.0
    
    def test_calculate_averages(self):
        """Test average calculation."""
        stats = ColumnStats(column_name="LeftCol")
        
        field1 = FieldDimensions(
            field_name="field1",
            width=100.0,
            height=20.0,
            x=50.0,
            y=100.0,
            page=0,
            column="LeftCol"
        )
        
        field2 = FieldDimensions(
            field_name="field2",
            width=200.0,
            height=40.0,
            x=50.0,
            y=150.0,
            page=0,
            column="LeftCol"
        )
        
        stats.add_field(field1)
        stats.add_field(field2)
        stats.calculate_averages()
        
        assert stats.avg_height == 30.0  # (20 + 40) / 2
        assert stats.avg_width == 150.0  # (100 + 200) / 2


class TestExtractFieldDimensions:
    """Test field dimension extraction from actual PDF."""
    
    def test_extract_from_valid_pdf(self):
        """Test extracting dimensions from the 1099-DIV template."""
        # Find the PDF template
        possible_paths = [
            "1099-DIV.pdf",
            "../1099-DIV.pdf",
            "../../1099-DIV.pdf",
        ]
        
        template_path = None
        for path in possible_paths:
            if os.path.exists(path):
                template_path = path
                break
        
        if not template_path:
            pytest.skip("1099-DIV.pdf template not found")
        
        dimensions = extract_field_dimensions(template_path)
        
        # Verify we extracted fields
        assert len(dimensions) > 0, "Should extract at least one field"
        
        # Verify all fields have required attributes
        for field_dim in dimensions:
            assert field_dim.field_name, "Field should have a name"
            assert field_dim.width > 0, "Field should have positive width"
            assert field_dim.height > 0, "Field should have positive height"
            assert field_dim.page >= 0, "Field should have valid page number"
            assert field_dim.column in ['LeftCol', 'RghtCol', 'CopyHeader', 'Other']
    
    def test_extract_from_nonexistent_pdf(self):
        """Test that extracting from nonexistent PDF raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            extract_field_dimensions("nonexistent.pdf")


class TestGroupByColumn:
    """Test grouping fields by column type."""
    
    def test_group_empty_list(self):
        """Test grouping an empty list of dimensions."""
        columns = group_by_column([])
        assert len(columns) == 0
    
    def test_group_single_column(self):
        """Test grouping fields from a single column."""
        field1 = FieldDimensions(
            field_name="field1",
            width=100.0,
            height=20.0,
            x=50.0,
            y=100.0,
            page=0,
            column="LeftCol"
        )
        
        field2 = FieldDimensions(
            field_name="field2",
            width=150.0,
            height=30.0,
            x=50.0,
            y=150.0,
            page=0,
            column="LeftCol"
        )
        
        columns = group_by_column([field1, field2])
        
        assert len(columns) == 1
        assert "LeftCol" in columns
        assert columns["LeftCol"].field_count == 2
        assert columns["LeftCol"].min_height == 20.0
        assert columns["LeftCol"].max_height == 30.0
    
    def test_group_multiple_columns(self):
        """Test grouping fields from multiple columns."""
        field1 = FieldDimensions(
            field_name="field1",
            width=100.0,
            height=20.0,
            x=50.0,
            y=100.0,
            page=0,
            column="LeftCol"
        )
        
        field2 = FieldDimensions(
            field_name="field2",
            width=90.0,
            height=12.0,
            x=300.0,
            y=100.0,
            page=0,
            column="RghtCol"
        )
        
        field3 = FieldDimensions(
            field_name="field3",
            width=30.0,
            height=10.0,
            x=400.0,
            y=50.0,
            page=0,
            column="CopyHeader"
        )
        
        columns = group_by_column([field1, field2, field3])
        
        assert len(columns) == 3
        assert "LeftCol" in columns
        assert "RghtCol" in columns
        assert "CopyHeader" in columns
        assert columns["LeftCol"].field_count == 1
        assert columns["RghtCol"].field_count == 1
        assert columns["CopyHeader"].field_count == 1
    
    def test_averages_calculated(self):
        """Test that averages are calculated when grouping."""
        field1 = FieldDimensions(
            field_name="field1",
            width=100.0,
            height=20.0,
            x=50.0,
            y=100.0,
            page=0,
            column="LeftCol"
        )
        
        field2 = FieldDimensions(
            field_name="field2",
            width=200.0,
            height=40.0,
            x=50.0,
            y=150.0,
            page=0,
            column="LeftCol"
        )
        
        columns = group_by_column([field1, field2])
        
        assert columns["LeftCol"].avg_height == 30.0
        assert columns["LeftCol"].avg_width == 150.0


class TestIntegrationWithActualPDF:
    """Integration tests using the actual 1099-DIV template."""
    
    def test_full_analysis_workflow(self):
        """Test the complete analysis workflow on actual PDF."""
        # Find the PDF template
        possible_paths = [
            "1099-DIV.pdf",
            "../1099-DIV.pdf",
            "../../1099-DIV.pdf",
        ]
        
        template_path = None
        for path in possible_paths:
            if os.path.exists(path):
                template_path = path
                break
        
        if not template_path:
            pytest.skip("1099-DIV.pdf template not found")
        
        # Extract dimensions
        dimensions = extract_field_dimensions(template_path)
        assert len(dimensions) > 0
        
        # Group by column
        columns = group_by_column(dimensions)
        assert len(columns) > 0
        
        # Verify expected columns exist
        assert "LeftCol" in columns or "RghtCol" in columns or "CopyHeader" in columns
        
        # Verify statistics are reasonable
        for column_name, stats in columns.items():
            assert stats.field_count > 0
            assert stats.min_height > 0
            assert stats.max_height >= stats.min_height
            assert stats.min_width > 0
            assert stats.max_width >= stats.min_width
            assert stats.avg_height > 0
            assert stats.avg_width > 0
    
    def test_rghtcol_has_small_fields(self):
        """Test that RghtCol fields are identified as small (< 13pt height)."""
        # Find the PDF template
        possible_paths = [
            "1099-DIV.pdf",
            "../1099-DIV.pdf",
            "../../1099-DIV.pdf",
        ]
        
        template_path = None
        for path in possible_paths:
            if os.path.exists(path):
                template_path = path
                break
        
        if not template_path:
            pytest.skip("1099-DIV.pdf template not found")
        
        # Extract and group dimensions
        dimensions = extract_field_dimensions(template_path)
        columns = group_by_column(dimensions)
        
        # RghtCol should have small fields
        if "RghtCol" in columns:
            rghtcol_stats = columns["RghtCol"]
            # Based on the analysis output, RghtCol min height is 9.0
            assert rghtcol_stats.min_height < 13.0, "RghtCol should have small fields"
            
            # Verify font size recommendation is appropriate
            default, min_size, max_size = recommend_font_size(rghtcol_stats.min_height)
            assert max_size <= 8.0, "RghtCol should recommend small font sizes"
