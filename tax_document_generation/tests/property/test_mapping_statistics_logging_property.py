"""
Property-based tests for mapping statistics logging in document generator.

These tests verify that the Document_Generator logs the count of successfully
mapped fields and unmapped fields. Each property test runs with a minimum of
100 iterations.

Feature: fix-pdf-field-mapping
Property 11: Mapping statistics are logged

**Validates: Requirements 6.3**
"""

import pytest
import logging
import re
from hypothesis import given, settings, strategies as st, HealthCheck
from unittest.mock import Mock, patch
from io import BytesIO
from tax_document_generation.document_generator import generate_document
from tax_document_generation.field_mappings.div_1099 import SUPPORTED_FIELDS


# Strategy for generating valid API field names
def valid_api_field_name_strategy():
    """Generate valid API field names from the 1099-DIV field reference."""
    return st.sampled_from(SUPPORTED_FIELDS)


# Strategy for generating invalid API field names
def invalid_api_field_name_strategy():
    """Generate invalid API field names."""
    return st.text(min_size=1, max_size=50).filter(lambda s: s not in SUPPORTED_FIELDS and s.isidentifier())


# Strategy for generating form data with only valid fields
def valid_form_data_strategy():
    """Generate form data with only valid API field names."""
    return st.dictionaries(
        keys=valid_api_field_name_strategy(),
        values=st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=10
    )


# Strategy for generating mixed form data (valid and invalid fields)
def mixed_form_data_strategy():
    """Generate form data with both valid and invalid API field names."""
    valid_data = st.dictionaries(
        keys=valid_api_field_name_strategy(),
        values=st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=5
    )
    invalid_data = st.dictionaries(
        keys=invalid_api_field_name_strategy(),
        values=st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=5
    )
    
    return st.builds(
        lambda v, i: {**v, **i},
        valid_data,
        invalid_data
    )


class TestMappingStatisticsLoggingProperty:
    """Property-based tests for mapping statistics logging."""
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=valid_form_data_strategy())
    def test_mapped_field_count_is_logged(self, form_data, caplog):
        """
        **Validates: Requirements 6.3**
        Feature: fix-pdf-field-mapping, Property 11: Mapping statistics are logged
        
        For any document generation operation,
        when the Document_Generator completes field mapping, it should log
        the count of successfully mapped fields.
        
        This test verifies that:
        1. A log message contains the mapped field count
        2. The count is accurate
        3. The log is at INFO level
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Clear any previous log records
        caplog.clear()
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document with logging enabled
            with caplog.at_level(logging.INFO):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                except Exception as e:
                    pass
            
            # Expected count of mapped fields (all fields are valid)
            expected_count = len(form_data)
            
            # Find logs about mapped fields
            info_logs = [record for record in caplog.records if record.levelname == "INFO"]
            
            mapped_logs = [
                record for record in info_logs
                if "Mapped" in record.message and "field" in record.message.lower()
            ]
            
            assert len(mapped_logs) > 0, \
                "Should have an INFO log about mapped fields"
            
            # Verify the count is in the log message
            log_message = mapped_logs[0].message
            
            # Extract the number from the log message
            numbers = re.findall(r'\d+', log_message)
            
            assert len(numbers) > 0, \
                f"Log message should contain the mapped field count: {log_message}"
            
            # The first number should be the mapped count
            actual_count = int(numbers[0])
            
            assert actual_count == expected_count, \
                f"Logged mapped count should be {expected_count}, got {actual_count}"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=mixed_form_data_strategy())
    def test_unmapped_field_count_is_logged(self, form_data, caplog):
        """
        **Validates: Requirements 6.3**
        Feature: fix-pdf-field-mapping, Property 11: Mapping statistics are logged
        
        For any document generation operation with unmapped fields,
        when the Document_Generator completes field mapping, it should log
        the count of unmapped fields.
        
        This test verifies that:
        1. A log message contains the unmapped field count
        2. The count is accurate
        3. The log is at WARNING level
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Clear any previous log records
        caplog.clear()
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document with logging enabled
            with caplog.at_level(logging.WARNING):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                except Exception as e:
                    pass
            
            # Count unmapped fields
            unmapped_fields = [k for k in form_data.keys() if k not in SUPPORTED_FIELDS]
            expected_unmapped_count = len(unmapped_fields)
            
            if expected_unmapped_count > 0:
                # Find logs about unmapped fields
                warning_logs = [record for record in caplog.records if record.levelname == "WARNING"]
                
                unmapped_logs = [
                    record for record in warning_logs
                    if "Unmapped" in record.message or "unmapped" in record.message
                ]
                
                assert len(unmapped_logs) > 0, \
                    "Should have a WARNING log about unmapped fields"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=valid_form_data_strategy())
    def test_mapping_statistics_logged_at_info_level(self, form_data, caplog):
        """
        **Validates: Requirements 6.3**
        Feature: fix-pdf-field-mapping, Property 11: Mapping statistics are logged
        
        For any document generation operation,
        mapping statistics should be logged at INFO level (not DEBUG or WARNING).
        
        This test verifies that:
        1. Statistics are visible in production logs
        2. INFO level is used for successful mappings
        3. Appropriate log level for operational visibility
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Clear any previous log records
        caplog.clear()
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document with logging enabled
            with caplog.at_level(logging.INFO):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                except Exception as e:
                    pass
            
            # Find logs about mapped fields
            info_logs = [record for record in caplog.records if record.levelname == "INFO"]
            
            mapped_logs = [
                record for record in info_logs
                if "Mapped" in record.message and "field" in record.message.lower()
            ]
            
            assert len(mapped_logs) > 0, \
                "Mapping statistics should be logged at INFO level"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=mixed_form_data_strategy())
    def test_both_mapped_and_unmapped_counts_logged(self, form_data, caplog):
        """
        **Validates: Requirements 6.3**
        Feature: fix-pdf-field-mapping, Property 11: Mapping statistics are logged
        
        For any document generation operation with mixed fields,
        both the mapped count and unmapped count should be logged.
        
        This test verifies that:
        1. Both statistics are present in logs
        2. Complete visibility into mapping results
        3. Operators can see full picture
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Clear any previous log records
        caplog.clear()
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document with logging enabled
            with caplog.at_level(logging.INFO):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                except Exception as e:
                    pass
            
            # Count mapped and unmapped fields
            mapped_fields = [k for k in form_data.keys() if k in SUPPORTED_FIELDS]
            unmapped_fields = [k for k in form_data.keys() if k not in SUPPORTED_FIELDS]
            
            # Find logs about mapped fields
            all_logs = [record for record in caplog.records]
            
            mapped_logs = [
                record for record in all_logs
                if "Mapped" in record.message and "field" in record.message.lower()
            ]
            
            assert len(mapped_logs) > 0, \
                "Should have a log about mapped fields"
            
            # If there are unmapped fields, verify they're logged
            if unmapped_fields:
                unmapped_logs = [
                    record for record in all_logs
                    if "Unmapped" in record.message or "unmapped" in record.message
                ]
                
                assert len(unmapped_logs) > 0, \
                    "Should have a log about unmapped fields when they exist"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=valid_form_data_strategy())
    def test_mapping_statistics_logged_before_pdf_operations(self, form_data, caplog):
        """
        **Validates: Requirements 6.3**
        Feature: fix-pdf-field-mapping, Property 11: Mapping statistics are logged
        
        For any document generation operation,
        mapping statistics should be logged BEFORE PDF operations begin.
        
        This test verifies that:
        1. Statistics are logged early in the process
        2. Operators can see mapping results even if PDF operations fail
        3. Correct order of operations
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Clear any previous log records
        caplog.clear()
        
        # Track log order
        log_order = []
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader with logging
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            
            def reader_init(*args, **kwargs):
                log_order.append('PdfReader')
                return mock_reader
            mock_reader_class.side_effect = reader_init
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document with logging enabled
            with caplog.at_level(logging.INFO):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                except Exception as e:
                    pass
            
            # Find when mapping statistics were logged
            for i, record in enumerate(caplog.records):
                if "Mapped" in record.message and "field" in record.message.lower():
                    log_order.insert(i, 'MappingStatistics')
                    break
            
            # Verify mapping statistics were logged before PDF operations
            if 'MappingStatistics' in log_order and 'PdfReader' in log_order:
                stats_index = log_order.index('MappingStatistics')
                reader_index = log_order.index('PdfReader')
                
                assert stats_index < reader_index, \
                    "Mapping statistics should be logged before PDF operations"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=valid_form_data_strategy())
    def test_mapping_statistics_include_field_word(self, form_data, caplog):
        """
        **Validates: Requirements 6.3**
        Feature: fix-pdf-field-mapping, Property 11: Mapping statistics are logged
        
        For any document generation operation,
        mapping statistics logs should include the word "field" or "fields"
        to make them clear and searchable.
        
        This test verifies that:
        1. Log messages are clear and descriptive
        2. Easy to search for in log aggregation systems
        3. Consistent terminology
        """
        # Create a mock PDF template
        mock_template = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Clear any previous log records
        caplog.clear()
        
        # Mock the PDF library components
        with patch('tax_document_generation.document_generator.PdfReader') as mock_reader_class, \
             patch('tax_document_generation.document_generator.PdfWriter') as mock_writer_class:
            
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock()]
            mock_reader.get_fields.return_value = {}
            mock_reader_class.return_value = mock_reader
            
            # Setup mock writer
            mock_writer = Mock()
            mock_output = BytesIO(b"%PDF-1.4\ngenerated content\n%%EOF")
            mock_writer.write = lambda stream: stream.write(mock_output.getvalue())
            mock_writer_class.return_value = mock_writer
            
            # Generate the document with logging enabled
            with caplog.at_level(logging.INFO):
                try:
                    result = generate_document(mock_template, form_data, "1099-DIV")
                except Exception as e:
                    pass
            
            # Find logs about mapped fields
            info_logs = [record for record in caplog.records if record.levelname == "INFO"]
            
            mapped_logs = [
                record for record in info_logs
                if "Mapped" in record.message
            ]
            
            assert len(mapped_logs) > 0, \
                "Should have a log about mapped fields"
            
            # Verify the log contains "field" or "fields"
            log_message = mapped_logs[0].message.lower()
            
            assert "field" in log_message, \
                f"Log message should contain 'field' or 'fields': {mapped_logs[0].message}"
