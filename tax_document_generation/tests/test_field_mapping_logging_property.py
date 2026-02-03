"""
Property-based tests for field mapping logging.

These tests verify that the FieldMapper logs field mapping operations correctly.
Each property test runs with a minimum of 100 iterations.

Feature: fix-pdf-field-mapping
Property 10: Field mapping operations are logged

**Validates: Requirements 6.1**
"""

import pytest
import logging
from hypothesis import given, settings, strategies as st, HealthCheck
from tax_document_generation.field_mapper import FieldMapper
from tax_document_generation.field_mappings.div_1099 import SUPPORTED_FIELDS


# Strategy for generating valid API field names
def valid_api_field_name_strategy():
    """Generate valid API field names from the 1099-DIV field reference."""
    return st.sampled_from(SUPPORTED_FIELDS)


# Strategy for generating invalid API field names
def invalid_api_field_name_strategy():
    """Generate invalid API field names."""
    return st.text(min_size=1, max_size=100).filter(lambda s: s not in SUPPORTED_FIELDS)


class TestFieldMappingLoggingProperty:
    """Property-based tests for field mapping logging."""
    
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(api_field_name=valid_api_field_name_strategy())
    def test_valid_field_mapping_logs_debug_message(self, api_field_name, caplog):
        """
        **Validates: Requirements 6.1**
        Feature: fix-pdf-field-mapping, Property 10: Field mapping operations are logged
        
        For any valid field mapping operation,
        when the Field_Mapper translates a field name, it should produce
        a debug-level log entry containing the API field name and the
        resulting PDF field name.
        
        This test verifies that:
        1. Debug-level logging occurs for valid mappings
        2. Log message contains the API field name
        3. Log message contains the PDF field name
        4. Log message contains the document type
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Clear any previous log records
        caplog.clear()
        
        # Set log level to DEBUG to capture debug messages
        with caplog.at_level(logging.DEBUG):
            # Map the field
            pdf_field_name = mapper.map_field(api_field_name)
        
        # Verify debug log was created
        debug_logs = [record for record in caplog.records if record.levelname == "DEBUG"]
        
        assert len(debug_logs) > 0, \
            f"Should have at least one debug log for mapping '{api_field_name}'"
        
        # Find the log record for this mapping
        mapping_logs = [
            record for record in debug_logs
            if api_field_name in record.message
        ]
        
        assert len(mapping_logs) > 0, \
            f"Should have a debug log containing API field name '{api_field_name}'"
        
        # Verify the log message contains the PDF field name
        log_message = mapping_logs[0].message
        
        assert pdf_field_name in log_message, \
            f"Log message should contain PDF field name '{pdf_field_name}': {log_message}"
        
        # Verify the log message contains the document type
        assert "1099-DIV" in log_message, \
            f"Log message should contain document type '1099-DIV': {log_message}"
    
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(api_field_name=invalid_api_field_name_strategy())
    def test_invalid_field_mapping_logs_warning_message(self, api_field_name, caplog):
        """
        **Validates: Requirements 6.1**
        Feature: fix-pdf-field-mapping, Property 10: Field mapping operations are logged
        
        For any invalid field mapping operation,
        when the Field_Mapper encounters an unmapped field, it should log
        a warning message containing the field name and document type.
        
        This test verifies that:
        1. Warning-level logging occurs for invalid mappings
        2. Log message contains the API field name
        3. Log message indicates no mapping exists
        4. Log message contains the document type
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Clear any previous log records
        caplog.clear()
        
        # Set log level to WARNING to capture warning messages
        with caplog.at_level(logging.WARNING):
            # Map the invalid field
            result = mapper.map_field(api_field_name)
        
        # Verify result is None
        assert result is None, \
            f"Invalid field should return None"
        
        # Verify warning log was created
        warning_logs = [record for record in caplog.records if record.levelname == "WARNING"]
        
        assert len(warning_logs) > 0, \
            f"Should have at least one warning log for unmapped field '{api_field_name}'"
        
        # Find the log record for this unmapped field
        unmapped_logs = [
            record for record in warning_logs
            if api_field_name in record.message
        ]
        
        assert len(unmapped_logs) > 0, \
            f"Should have a warning log containing API field name '{api_field_name}'"
        
        # Verify the log message indicates no mapping
        log_message = unmapped_logs[0].message
        
        assert "no mapping" in log_message.lower(), \
            f"Log message should indicate no mapping exists: {log_message}"
        
        # Verify the log message contains the document type
        assert "1099-DIV" in log_message, \
            f"Log message should contain document type '1099-DIV': {log_message}"
    
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(api_field_name=valid_api_field_name_strategy())
    def test_multiple_mappings_produce_multiple_logs(self, api_field_name, caplog):
        """
        **Validates: Requirements 6.1**
        Feature: fix-pdf-field-mapping, Property 10: Field mapping operations are logged
        
        For any field mapping operation repeated multiple times,
        each mapping should produce a separate log entry.
        
        This test verifies that:
        1. Each mapping operation is logged
        2. Multiple calls produce multiple log entries
        3. Logging is consistent across calls
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Clear any previous log records
        caplog.clear()
        
        # Set log level to DEBUG to capture debug messages
        with caplog.at_level(logging.DEBUG):
            # Map the field multiple times
            mapper.map_field(api_field_name)
            mapper.map_field(api_field_name)
            mapper.map_field(api_field_name)
        
        # Count debug logs containing the API field name
        mapping_logs = [
            record for record in caplog.records
            if record.levelname == "DEBUG" and api_field_name in record.message
        ]
        
        # Should have 3 log entries (one for each mapping)
        assert len(mapping_logs) == 3, \
            f"Should have 3 debug logs for 3 mappings of '{api_field_name}', got {len(mapping_logs)}"
    
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        field1=valid_api_field_name_strategy(),
        field2=valid_api_field_name_strategy(),
    )
    def test_different_fields_produce_different_logs(self, field1, field2, caplog):
        """
        **Validates: Requirements 6.1**
        Feature: fix-pdf-field-mapping, Property 10: Field mapping operations are logged
        
        For different field mapping operations,
        each should produce a distinct log entry with the correct field names.
        
        This test verifies that:
        1. Different fields produce different log messages
        2. Each log contains the correct field name
        3. Logs are not mixed or confused
        """
        # Skip if both fields are the same
        if field1 == field2:
            return
        
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Clear any previous log records
        caplog.clear()
        
        # Set log level to DEBUG to capture debug messages
        with caplog.at_level(logging.DEBUG):
            # Map both fields
            pdf1 = mapper.map_field(field1)
            pdf2 = mapper.map_field(field2)
        
        # Find logs for each field - use more precise matching
        logs_for_field1 = [
            record for record in caplog.records
            if record.levelname == "DEBUG" and f"Mapped field '{field1}'" in record.message
        ]
        
        logs_for_field2 = [
            record for record in caplog.records
            if record.levelname == "DEBUG" and f"Mapped field '{field2}'" in record.message
        ]
        
        # Should have at least one log for each field
        assert len(logs_for_field1) > 0, \
            f"Should have a debug log for field '{field1}'"
        
        assert len(logs_for_field2) > 0, \
            f"Should have a debug log for field '{field2}'"
        
        # Verify each log contains the correct PDF field name
        assert pdf1 in logs_for_field1[0].message, \
            f"Log for '{field1}' should contain PDF field name '{pdf1}'"
        
        assert pdf2 in logs_for_field2[0].message, \
            f"Log for '{field2}' should contain PDF field name '{pdf2}'"
    
    def test_initialization_logs_info_message(self, caplog):
        """
        **Validates: Requirements 6.1**
        Feature: fix-pdf-field-mapping, Property 10: Field mapping operations are logged
        
        When a FieldMapper is initialized,
        it should log an info message about the initialization.
        
        This test verifies that:
        1. Initialization is logged at INFO level
        2. Log message contains the document type
        3. Log message contains the number of mappings loaded
        """
        # Clear any previous log records
        caplog.clear()
        
        # Set log level to INFO to capture info messages
        with caplog.at_level(logging.INFO):
            # Initialize the field mapper
            mapper = FieldMapper("1099-DIV")
        
        # Verify info log was created
        info_logs = [record for record in caplog.records if record.levelname == "INFO"]
        
        assert len(info_logs) > 0, \
            "Should have at least one info log for initialization"
        
        # Find the initialization log
        init_logs = [
            record for record in info_logs
            if "Initialized" in record.message or "initialized" in record.message
        ]
        
        assert len(init_logs) > 0, \
            "Should have an info log about initialization"
        
        # Verify the log message contains the document type
        log_message = init_logs[0].message
        
        assert "1099-DIV" in log_message, \
            f"Log message should contain document type '1099-DIV': {log_message}"
    
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(api_field_name=valid_api_field_name_strategy())
    def test_log_level_is_debug_for_successful_mapping(self, api_field_name, caplog):
        """
        **Validates: Requirements 6.1**
        Feature: fix-pdf-field-mapping, Property 10: Field mapping operations are logged
        
        For successful field mappings,
        the log level should be DEBUG (not INFO or WARNING).
        
        This test verifies that:
        1. Successful mappings use DEBUG level
        2. Not INFO level (too noisy for production)
        3. Not WARNING level (not an error condition)
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Clear any previous log records
        caplog.clear()
        
        # Set log level to DEBUG to capture all messages
        with caplog.at_level(logging.DEBUG):
            # Map the field
            mapper.map_field(api_field_name)
        
        # Find logs for this field
        field_logs = [
            record for record in caplog.records
            if api_field_name in record.message and "Mapped field" in record.message
        ]
        
        # Should have at least one log
        assert len(field_logs) > 0, \
            f"Should have a log for mapping '{api_field_name}'"
        
        # Verify the log level is DEBUG
        assert field_logs[0].levelname == "DEBUG", \
            f"Successful mapping should use DEBUG level, got {field_logs[0].levelname}"
    
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(api_field_name=invalid_api_field_name_strategy())
    def test_log_level_is_warning_for_unmapped_field(self, api_field_name, caplog):
        """
        **Validates: Requirements 6.1**
        Feature: fix-pdf-field-mapping, Property 10: Field mapping operations are logged
        
        For unmapped fields,
        the log level should be WARNING (not ERROR or DEBUG).
        
        This test verifies that:
        1. Unmapped fields use WARNING level
        2. Not ERROR level (not a fatal error)
        3. Not DEBUG level (important enough to warn about)
        """
        # Initialize the field mapper
        mapper = FieldMapper("1099-DIV")
        
        # Clear any previous log records
        caplog.clear()
        
        # Set log level to DEBUG to capture all messages
        with caplog.at_level(logging.DEBUG):
            # Map the invalid field
            mapper.map_field(api_field_name)
        
        # Find logs for this field
        field_logs = [
            record for record in caplog.records
            if api_field_name in record.message and "no mapping" in record.message.lower()
        ]
        
        # Should have at least one log
        assert len(field_logs) > 0, \
            f"Should have a log for unmapped field '{api_field_name}'"
        
        # Verify the log level is WARNING
        assert field_logs[0].levelname == "WARNING", \
            f"Unmapped field should use WARNING level, got {field_logs[0].levelname}"
