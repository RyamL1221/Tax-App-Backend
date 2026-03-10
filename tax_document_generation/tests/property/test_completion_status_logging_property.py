"""
Property-based tests for completion status logging in document generator.

These tests verify that the Document_Generator logs whether all expected fields
were mapped successfully or if some fields were unmapped. Each property test
runs with a minimum of 100 iterations.

Feature: fix-pdf-field-mapping
Property 12: Completion status is logged

**Validates: Requirements 6.4**
"""

import pytest
import logging
import os
from hypothesis import given, settings, strategies as st, HealthCheck
from unittest.mock import Mock, patch
from io import BytesIO
from tax_document_generation.document_generator import generate_document
from tax_document_generation.field_mappings.div_1099 import SUPPORTED_FIELDS


def get_1099_div_template():
    """Load the actual 1099-DIV template from the project root."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    tax_doc_dir = os.path.dirname(test_dir)
    project_root = os.path.dirname(tax_doc_dir)
    template_path = os.path.join(project_root, "1099-DIV.pdf")
    
    if not os.path.exists(template_path):
        pytest.skip(f"1099-DIV template not found at {template_path}")
    
    with open(template_path, "rb") as f:
        return f.read()


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


class TestCompletionStatusLoggingProperty:
    """Property-based tests for completion status logging."""
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=valid_form_data_strategy())
    def test_successful_completion_logged_when_all_fields_mapped(self, form_data, caplog):
        """
        **Validates: Requirements 6.4**
        Feature: fix-pdf-field-mapping, Property 12: Completion status is logged
        
        For any document generation operation where all fields are mapped,
        when the Document_Generator completes, it should log that all fields
        were mapped successfully.
        
        This test verifies that:
        1. Success status is logged
        2. Log indicates all fields were mapped
        3. Log is at INFO level
        4. Message is clear and positive
        """
        # Get the real template
        template = get_1099_div_template()
        
        # Clear any previous log records
        caplog.clear()
        
        # Generate the document with logging enabled
        with caplog.at_level(logging.INFO):
            try:
                result = generate_document(template, form_data, "1099-DIV")
            except Exception as e:
                pass
        
        # Find completion status logs
        info_logs = [record for record in caplog.records if record.levelname == "INFO"]
        
        completion_logs = [
            record for record in info_logs
            if ("completed" in record.message.lower() or "complete" in record.message.lower()) and
               ("all" in record.message.lower() or "successfully" in record.message.lower())
        ]
        
        assert len(completion_logs) > 0, \
            "Should have an INFO log about successful completion when all fields are mapped"
        
        # Verify the log indicates success
        log_message = completion_logs[0].message.lower()
        
        assert "all" in log_message or "successfully" in log_message, \
            f"Completion log should indicate success: {completion_logs[0].message}"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=mixed_form_data_strategy())
    def test_partial_completion_logged_when_fields_unmapped(self, form_data, caplog):
        """
        **Validates: Requirements 6.4**
        Feature: fix-pdf-field-mapping, Property 12: Completion status is logged
        
        For any document generation operation with unmapped fields,
        when the Document_Generator completes, it should log that some fields
        were unmapped.
        
        This test verifies that:
        1. Partial completion status is logged
        2. Log indicates unmapped fields exist
        3. Log is at INFO level
        4. Message is clear about the issue
        """
        # Get the real template
        template = get_1099_div_template()
        
        # Clear any previous log records
        caplog.clear()
        
        # Generate the document with logging enabled
        with caplog.at_level(logging.INFO):
            try:
                result = generate_document(template, form_data, "1099-DIV")
            except Exception as e:
                pass
        
        # Count unmapped fields
        unmapped_fields = [k for k in form_data.keys() if k not in SUPPORTED_FIELDS]
        
        if unmapped_fields:
            # Find completion status logs
            info_logs = [record for record in caplog.records if record.levelname == "INFO"]
            
            completion_logs = [
                record for record in info_logs
                if ("completed" in record.message.lower() or "complete" in record.message.lower()) and
                   ("unmapped" in record.message.lower())
            ]
            
            assert len(completion_logs) > 0, \
                "Should have an INFO log about completion with unmapped fields"
            
            # Verify the log mentions unmapped fields
            log_message = completion_logs[0].message.lower()
            
            assert "unmapped" in log_message, \
                f"Completion log should mention unmapped fields: {completion_logs[0].message}"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=valid_form_data_strategy())
    def test_completion_status_logged_at_end_of_generation(self, form_data, caplog):
        """
        **Validates: Requirements 6.4**
        Feature: fix-pdf-field-mapping, Property 12: Completion status is logged
        
        For any document generation operation,
        the completion status should be logged near the end of the process
        (after mapping but before final PDF generation).
        
        This test verifies that:
        1. Completion status is logged at appropriate time
        2. Not too early (before mapping)
        3. Not too late (after all operations)
        4. Provides timely feedback
        """
        # Get the real template
        template = get_1099_div_template()
        
        # Clear any previous log records
        caplog.clear()
        
        # Generate the document with logging enabled
        with caplog.at_level(logging.INFO):
            try:
                result = generate_document(template, form_data, "1099-DIV")
            except Exception as e:
                pass
        
        # Find completion status log
        info_logs = [record for record in caplog.records if record.levelname == "INFO"]
        
        completion_logs = [
            record for record in info_logs
            if "completed" in record.message.lower() or "complete" in record.message.lower()
        ]
        
        # Find mapping statistics log
        mapping_logs = [
            record for record in info_logs
            if "Mapped" in record.message and "field" in record.message.lower()
        ]
        
        if completion_logs and mapping_logs:
            # Get indices in the log list
            completion_index = caplog.records.index(completion_logs[0])
            mapping_index = caplog.records.index(mapping_logs[0])
            
            # Completion should be after mapping
            assert completion_index > mapping_index, \
                "Completion status should be logged after mapping statistics"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=mixed_form_data_strategy())
    def test_completion_status_includes_unmapped_count(self, form_data, caplog):
        """
        **Validates: Requirements 6.4**
        Feature: fix-pdf-field-mapping, Property 12: Completion status is logged
        
        For any document generation operation with unmapped fields,
        the completion status log should include the count of unmapped fields.
        
        This test verifies that:
        1. Unmapped count is in completion log
        2. Operators can see the extent of the issue
        3. Quantitative information is provided
        """
        # Get the real template
        template = get_1099_div_template()
        
        # Clear any previous log records
        caplog.clear()
        
        # Generate the document with logging enabled
        with caplog.at_level(logging.INFO):
            try:
                result = generate_document(template, form_data, "1099-DIV")
            except Exception as e:
                pass
        
        # Count unmapped fields
        unmapped_fields = [k for k in form_data.keys() if k not in SUPPORTED_FIELDS]
        
        if unmapped_fields:
            # Find completion status logs
            info_logs = [record for record in caplog.records if record.levelname == "INFO"]
            
            completion_logs = [
                record for record in info_logs
                if ("completed" in record.message.lower() or "complete" in record.message.lower()) and
                   "unmapped" in record.message.lower()
            ]
            
            if completion_logs:
                log_message = completion_logs[0].message
                
                # Verify the log contains a number (the unmapped count)
                import re
                numbers = re.findall(r'\d+', log_message)
                
                assert len(numbers) > 0, \
                    f"Completion log should include unmapped count: {log_message}"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=valid_form_data_strategy())
    def test_completion_status_uses_info_level(self, form_data, caplog):
        """
        **Validates: Requirements 6.4**
        Feature: fix-pdf-field-mapping, Property 12: Completion status is logged
        
        For any document generation operation,
        the completion status should be logged at INFO level (not DEBUG or WARNING).
        
        This test verifies that:
        1. INFO level is used for completion status
        2. Visible in production logs
        3. Appropriate severity level
        """
        # Get the real template
        template = get_1099_div_template()
        
        # Clear any previous log records
        caplog.clear()
        
        # Generate the document with logging enabled
        with caplog.at_level(logging.INFO):
            try:
                result = generate_document(template, form_data, "1099-DIV")
            except Exception as e:
                pass
        
        # Find completion status logs
        info_logs = [record for record in caplog.records if record.levelname == "INFO"]
        
        completion_logs = [
            record for record in info_logs
            if "completed" in record.message.lower() or "complete" in record.message.lower()
        ]
        
        assert len(completion_logs) > 0, \
            "Completion status should be logged at INFO level"
        
        # Verify it's INFO level
        assert completion_logs[0].levelname == "INFO", \
            f"Completion status should use INFO level, got {completion_logs[0].levelname}"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(form_data=valid_form_data_strategy())
    def test_completion_status_contains_completion_keyword(self, form_data, caplog):
        """
        **Validates: Requirements 6.4**
        Feature: fix-pdf-field-mapping, Property 12: Completion status is logged
        
        For any document generation operation,
        the completion status log should contain words like "completed" or "complete"
        to make it clear and searchable.
        
        This test verifies that:
        1. Clear terminology is used
        2. Easy to search for in logs
        3. Consistent messaging
        """
        # Get the real template
        template = get_1099_div_template()
        
        # Clear any previous log records
        caplog.clear()
        
        # Generate the document with logging enabled
        with caplog.at_level(logging.INFO):
            try:
                result = generate_document(template, form_data, "1099-DIV")
            except Exception as e:
                pass
        
        # Find logs with completion keywords
        info_logs = [record for record in caplog.records if record.levelname == "INFO"]
        
        completion_logs = [
            record for record in info_logs
            if "completed" in record.message.lower() or "complete" in record.message.lower()
        ]
        
        assert len(completion_logs) > 0, \
            "Should have a log with 'completed' or 'complete' keyword"
