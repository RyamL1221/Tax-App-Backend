"""
Property-Based Tests for Download Headers

Tests that PDF responses have correct download headers.
**Validates: Requirements 1.1**
"""

import pytest
import base64
from hypothesis import given, strategies as st

from document_download.response_formatter import pdf_response


class TestDownloadHeadersProperty:
    """Property-based tests for download headers."""
    
    @given(
        filename=st.text(min_size=1, max_size=100).filter(lambda x: '/' not in x and '\\' not in x)
    )
    def test_pdf_response_has_download_headers(self, filename):
        """
        Property: PDF responses have proper download headers.
        
        For all valid filenames, PDF responses must include:
        - Content-Type: application/pdf
        - Content-Disposition with attachment and filename
        - isBase64Encoded: True
        """
        response = pdf_response(b'fake pdf', filename)
        
        # Verify Content-Type
        assert response['headers']['Content-Type'] == 'application/pdf'
        
        # Verify Content-Disposition
        assert 'attachment' in response['headers']['Content-Disposition']
        assert filename in response['headers']['Content-Disposition']
        
        # Verify base64 encoding flag
        assert response['isBase64Encoded'] is True
    
    @given(
        pdf_content=st.binary(min_size=0, max_size=10000),
        filename=st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x)
    )
    def test_pdf_content_properly_encoded(self, pdf_content, filename):
        """
        Property: PDF content is properly base64 encoded.
        
        For any PDF content, the response body must be valid base64
        that decodes back to the original content.
        """
        response = pdf_response(pdf_content, filename)
        
        # Verify can decode
        decoded = base64.b64decode(response['body'])
        assert decoded == pdf_content
        
        # Verify encoding flag is set
        assert response['isBase64Encoded'] is True
    
    @given(
        filename=st.text(min_size=1, max_size=100).filter(
            lambda x: '/' not in x and '\\' not in x and x.endswith('.pdf')
        )
    )
    def test_content_disposition_format(self, filename):
        """
        Property: Content-Disposition header has correct format.
        
        The Content-Disposition header must follow the format:
        attachment; filename="<filename>"
        """
        response = pdf_response(b'test', filename)
        
        disposition = response['headers']['Content-Disposition']
        assert disposition.startswith('attachment')
        assert 'filename=' in disposition
        assert filename in disposition
    
    @given(pdf_content=st.binary(min_size=1, max_size=1000))
    def test_status_code_always_200_for_pdf(self, pdf_content):
        """
        Property: PDF responses always have 200 status code.
        
        For any successful PDF response, status code must be 200.
        """
        response = pdf_response(pdf_content, 'test.pdf')
        
        assert response['statusCode'] == 200
    
    @given(
        document_type=st.sampled_from(['1099-DIV', '1099-INT', '1099-MISC', 'W-2'])
    )
    def test_filename_format_for_tax_forms(self, document_type):
        """
        Property: Tax form filenames follow expected format.
        
        Tax form filenames should follow the pattern: form-{documentType}.pdf
        """
        filename = f'form-{document_type}.pdf'
        response = pdf_response(b'test', filename)
        
        disposition = response['headers']['Content-Disposition']
        assert filename in disposition
        assert document_type in disposition
    
    @given(
        pdf_size=st.integers(min_value=0, max_value=10000)
    )
    def test_pdf_response_handles_various_sizes(self, pdf_size):
        """
        Property: PDF responses handle various content sizes.
        
        For any PDF size, the response should be properly formatted.
        """
        pdf_content = b'X' * pdf_size
        response = pdf_response(pdf_content, 'test.pdf')
        
        # Verify response structure
        assert 'statusCode' in response
        assert 'headers' in response
        assert 'body' in response
        assert 'isBase64Encoded' in response
        
        # Verify content can be decoded
        decoded = base64.b64decode(response['body'])
        assert len(decoded) == pdf_size
    
    @given(
        filename=st.text(min_size=1, max_size=100).filter(lambda x: '/' not in x)
    )
    def test_special_characters_in_filename(self, filename):
        """
        Property: Filenames with special characters are handled correctly.
        
        Filenames may contain spaces, hyphens, parentheses, etc.
        """
        response = pdf_response(b'test', filename)
        
        # Verify filename is in Content-Disposition
        disposition = response['headers']['Content-Disposition']
        assert filename in disposition or filename.replace('"', '\\"') in disposition
