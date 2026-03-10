"""
Unit tests for deprecation warning logging.

Tests that deprecation warnings are logged when old combined address format
is detected, with appropriate migration guidance.

Requirements: 6.3
"""

import logging
import pytest
from tax_document_generation.address_normalizer import (
    normalize_address_fields,
    _normalize_address_group
)


class TestDeprecationWarningLogging:
    """Test deprecation warning logging for combined address format."""
    
    def test_payer_combined_format_logs_warning(self, caplog):
        """Test that combined payer address format logs deprecation warning."""
        with caplog.at_level(logging.WARNING):
            form_data = {"payerCity": "New York, NY 10001"}
            normalize_address_fields(form_data)
        
        # Verify warning was logged
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        
        # Verify warning message content
        warning_message = caplog.records[0].message
        assert "Deprecated field format detected" in warning_message
        assert "payerCity" in warning_message
        assert "New York, NY 10001" in warning_message
        assert "Please use separate" in warning_message
        assert "payerState" in warning_message
        assert "payerZip" in warning_message
        assert "Combined format will be removed in a future version" in warning_message
    
    def test_recipient_combined_format_logs_warning(self, caplog):
        """Test that combined recipient address format logs deprecation warning."""
        with caplog.at_level(logging.WARNING):
            form_data = {"recipientCity": "Los Angeles, CA 90001"}
            normalize_address_fields(form_data)
        
        # Verify warning was logged
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        
        # Verify warning message content
        warning_message = caplog.records[0].message
        assert "Deprecated field format detected" in warning_message
        assert "recipientCity" in warning_message
        assert "Los Angeles, CA 90001" in warning_message
        assert "recipientState" in warning_message
        assert "recipientZip" in warning_message
    
    def test_both_combined_formats_log_two_warnings(self, caplog):
        """Test that both payer and recipient combined formats log separate warnings."""
        with caplog.at_level(logging.WARNING):
            form_data = {
                "payerCity": "New York, NY 10001",
                "recipientCity": "Los Angeles, CA 90001"
            }
            normalize_address_fields(form_data)
        
        # Verify two warnings were logged
        assert len(caplog.records) == 2
        assert all(record.levelname == "WARNING" for record in caplog.records)
        
        # Verify both warnings are present
        messages = [record.message for record in caplog.records]
        assert any("payerCity" in msg for msg in messages)
        assert any("recipientCity" in msg for msg in messages)
    
    def test_separate_format_no_warning(self, caplog):
        """Test that separate address format does not log warning."""
        with caplog.at_level(logging.WARNING):
            form_data = {
                "payerCity": "New York",
                "payerState": "NY",
                "payerZip": "10001"
            }
            normalize_address_fields(form_data)
        
        # Verify no warnings were logged
        warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_records) == 0
    
    def test_invalid_format_no_warning(self, caplog):
        """Test that invalid address format does not log warning."""
        with caplog.at_level(logging.WARNING):
            form_data = {"payerCity": "Just a city name"}
            normalize_address_fields(form_data)
        
        # Verify no warnings were logged
        warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_records) == 0
    
    def test_warning_includes_migration_guidance(self, caplog):
        """Test that warning message includes clear migration guidance."""
        with caplog.at_level(logging.WARNING):
            form_data = {"payerCity": "San Francisco, CA 94102"}
            normalize_address_fields(form_data)
        
        warning_message = caplog.records[0].message
        
        # Verify migration guidance is present
        assert "Please use separate" in warning_message
        assert "payerCity" in warning_message
        assert "payerState" in warning_message
        assert "payerZip" in warning_message
        
        # Verify deprecation timeline is mentioned
        assert "future version" in warning_message
    
    def test_warning_includes_actual_value(self, caplog):
        """Test that warning message includes the actual combined value."""
        combined_address = "Boston, MA 02101"
        with caplog.at_level(logging.WARNING):
            form_data = {"payerCity": combined_address}
            normalize_address_fields(form_data)
        
        warning_message = caplog.records[0].message
        
        # Verify actual value is included in warning
        assert combined_address in warning_message
    
    def test_normalize_address_group_logs_warning(self, caplog):
        """Test that _normalize_address_group logs deprecation warning."""
        with caplog.at_level(logging.WARNING):
            form_data = {"testCity": "Chicago, IL 60601"}
            _normalize_address_group(
                form_data,
                city_field="testCity",
                state_field="testState",
                zip_field="testZip"
            )
        
        # Verify warning was logged
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        
        # Verify custom field names are in warning
        warning_message = caplog.records[0].message
        assert "testCity" in warning_message
        assert "testState" in warning_message
        assert "testZip" in warning_message
    
    def test_explicit_values_still_log_warning(self, caplog):
        """Test that warning is logged even when explicit values override parsed values."""
        with caplog.at_level(logging.WARNING):
            form_data = {
                "payerCity": "New York, NY 10001",
                "payerState": "CA",  # Explicit override
                "payerZip": "90001"  # Explicit override
            }
            normalize_address_fields(form_data)
        
        # Verify warning was still logged
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert "Deprecated field format detected" in caplog.records[0].message
    
    def test_warning_message_format(self, caplog):
        """Test that warning message follows expected format."""
        with caplog.at_level(logging.WARNING):
            form_data = {"payerCity": "Seattle, WA 98101"}
            normalize_address_fields(form_data)
        
        warning_message = caplog.records[0].message
        
        # Verify message structure
        assert warning_message.startswith("Deprecated field format detected:")
        assert "contains combined address" in warning_message
        assert "Please use separate" in warning_message
        assert "fields." in warning_message
        assert "Combined format will be removed" in warning_message


class TestDeprecationWarningContent:
    """Test the content and quality of deprecation warning messages."""
    
    def test_warning_is_actionable(self, caplog):
        """Test that warning provides actionable guidance."""
        with caplog.at_level(logging.WARNING):
            form_data = {"payerCity": "Denver, CO 80201"}
            normalize_address_fields(form_data)
        
        warning_message = caplog.records[0].message
        
        # Verify message tells user what to do
        assert "Please use" in warning_message
        
        # Verify message specifies the correct field names
        assert "payerCity" in warning_message
        assert "payerState" in warning_message
        assert "payerZip" in warning_message
    
    def test_warning_explains_deprecation_timeline(self, caplog):
        """Test that warning explains when the format will be removed."""
        with caplog.at_level(logging.WARNING):
            form_data = {"recipientCity": "Austin, TX 78701"}
            normalize_address_fields(form_data)
        
        warning_message = caplog.records[0].message
        
        # Verify timeline is mentioned
        assert "future version" in warning_message or "will be removed" in warning_message
    
    def test_warning_identifies_problematic_field(self, caplog):
        """Test that warning clearly identifies which field has the issue."""
        with caplog.at_level(logging.WARNING):
            form_data = {"payerCity": "Portland, OR 97201"}
            normalize_address_fields(form_data)
        
        warning_message = caplog.records[0].message
        
        # Verify field name is prominently mentioned
        assert "payerCity" in warning_message
        assert "contains combined address" in warning_message
    
    def test_warning_shows_detected_value(self, caplog):
        """Test that warning shows the actual value that was detected."""
        test_value = "Miami, FL 33101"
        with caplog.at_level(logging.WARNING):
            form_data = {"recipientCity": test_value}
            normalize_address_fields(form_data)
        
        warning_message = caplog.records[0].message
        
        # Verify the actual value is shown
        assert test_value in warning_message
