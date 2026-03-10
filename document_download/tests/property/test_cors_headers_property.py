"""
Property-Based Tests for CORS Headers

Tests that all responses include CORS headers.
**Validates: Requirements 1.1**
"""

import os
import pytest
from hypothesis import given, strategies as st

from document_download.response_formatter import pdf_response, error_response


def get_expected_cors_origin():
    """Get the expected CORS origin from environment or default."""
    return os.environ.get('CORS_ALLOWED_ORIGIN', '*')


class TestCORSHeadersProperty:
    """Property-based tests for CORS headers."""
    
    @given(
        status_code=st.integers(min_value=200, max_value=599),
        response_type=st.sampled_from(['pdf', 'error'])
    )
    def test_all_responses_include_cors_headers(self, status_code, response_type):
        """
        Property: All responses include CORS headers.
        
        For all possible responses (success or error), CORS headers
        must be present for frontend compatibility.
        """
        # Generate response based on type
        if response_type == 'pdf':
            response = pdf_response(b'fake pdf', 'test.pdf')
        else:
            response = error_response(status_code, 'TestError', 'Test message')
        
        # Verify CORS headers present
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
        
        # Verify CORS header values
        expected_origin = get_expected_cors_origin()
        assert response['headers']['Access-Control-Allow-Origin'] == expected_origin
        assert 'Authorization' in response['headers']['Access-Control-Allow-Headers']
        assert 'GET' in response['headers']['Access-Control-Allow-Methods']
    
    @given(pdf_content=st.binary(min_size=0, max_size=1000))
    def test_pdf_responses_always_have_cors_headers(self, pdf_content):
        """
        Property: PDF responses always have CORS headers.
        
        For any PDF content, the response must include CORS headers.
        """
        response = pdf_response(pdf_content, 'test.pdf')
        
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
    
    @given(
        status_code=st.integers(min_value=400, max_value=599),
        error_type=st.text(min_size=1, max_size=50),
        message=st.text(min_size=1, max_size=200)
    )
    def test_error_responses_always_have_cors_headers(self, status_code, error_type, message):
        """
        Property: Error responses always have CORS headers.
        
        For any error response, CORS headers must be present.
        """
        response = error_response(status_code, error_type, message)
        
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
    
    @given(
        filename=st.text(min_size=1, max_size=100).filter(lambda x: '/' not in x)
    )
    def test_cors_headers_consistent_across_filenames(self, filename):
        """
        Property: CORS headers are consistent regardless of filename.
        
        CORS headers should not vary based on the filename.
        """
        response = pdf_response(b'test', filename)
        
        # Verify standard CORS configuration
        expected_origin = get_expected_cors_origin()
        assert response['headers']['Access-Control-Allow-Origin'] == expected_origin
        assert 'Content-Type' in response['headers']['Access-Control-Allow-Headers']
        assert 'Authorization' in response['headers']['Access-Control-Allow-Headers']
        assert 'GET' in response['headers']['Access-Control-Allow-Methods']
        assert 'OPTIONS' in response['headers']['Access-Control-Allow-Methods']
    
    @given(
        status_code=st.sampled_from([400, 401, 403, 404, 500])
    )
    def test_cors_headers_consistent_across_error_types(self, status_code):
        """
        Property: CORS headers are consistent across error types.
        
        All error responses should have the same CORS configuration.
        """
        response = error_response(status_code, 'TestError', 'Test message')
        
        # Verify standard CORS configuration
        expected_origin = get_expected_cors_origin()
        assert response['headers']['Access-Control-Allow-Origin'] == expected_origin
        assert 'Content-Type' in response['headers']['Access-Control-Allow-Headers']
        assert 'Authorization' in response['headers']['Access-Control-Allow-Headers']
        assert 'GET' in response['headers']['Access-Control-Allow-Methods']
        assert 'OPTIONS' in response['headers']['Access-Control-Allow-Methods']
