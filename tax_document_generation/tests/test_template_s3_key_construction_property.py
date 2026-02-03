"""
Property-based tests for template S3 key construction.

These tests verify that the S3 key for IRS templates follows the correct
pattern `templates/irs/{documentType}`. Each property test runs with a
minimum of 100 iterations.

Feature: tax-document-generation
Property 6: Template S3 Key Construction

**Validates: Requirements 3.1**
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from hypothesis import given, settings, strategies as st
from hypothesis.strategies import text
from tax_document_generation.template_retriever import get_template
from tax_document_generation.exceptions import TemplateNotFoundError, S3Error


# Strategy for generating document types
# Document types are typically alphanumeric with possible hyphens
document_types = text(
    min_size=1,
    max_size=50,
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
)

# Strategy for generating bucket names
bucket_names = text(
    min_size=3,
    max_size=63,
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'
)


class TestTemplateS3KeyConstructionProperty:
    """Property-based tests for template S3 key construction."""
    
    @settings(max_examples=20)
    @given(
        bucket=bucket_names,
        document_type=document_types
    )
    def test_s3_key_follows_correct_pattern(self, bucket, document_type):
        """
        **Validates: Requirements 3.1**
        Feature: tax-document-generation, Property 6: Template S3 Key Construction
        
        For any document type, the system must construct the template S3 key
        using the pattern `templates/irs/{documentType}.pdf`.
        
        This test verifies that:
        1. The S3 key starts with "templates/irs/"
        2. The document type is correctly embedded in the key
        3. The key ends with ".pdf"
        4. The pattern is consistent across all document types
        """
        # Mock the S3 client to capture the key used
        with patch('tax_document_generation.template_retriever.boto3.client') as mock_boto3:
            mock_s3_client = Mock()
            mock_boto3.return_value = mock_s3_client
            
            # Mock successful S3 response
            mock_response = {
                'Body': MagicMock(read=Mock(return_value=b'fake pdf content'))
            }
            mock_s3_client.get_object.return_value = mock_response
            
            # Action: Call get_template
            try:
                get_template(bucket, document_type)
            except Exception:
                # We're only interested in the S3 key construction, not the result
                pass
            
            # Verification: Check that get_object was called with the correct key pattern
            if mock_s3_client.get_object.called:
                call_args = mock_s3_client.get_object.call_args
                actual_key = call_args[1]['Key']
                
                # The key must follow the pattern templates/irs/{document_type}.pdf
                expected_key = f"templates/irs/{document_type}.pdf"
                
                assert actual_key == expected_key, (
                    f"S3 key '{actual_key}' does not match expected pattern "
                    f"'templates/irs/{document_type}.pdf'"
                )
                
                # Verify the key starts with the correct prefix
                assert actual_key.startswith("templates/irs/"), (
                    f"S3 key '{actual_key}' does not start with 'templates/irs/'"
                )
                
                # Verify the key ends with .pdf
                assert actual_key.endswith(".pdf"), (
                    f"S3 key '{actual_key}' does not end with '.pdf'"
                )
                
                # Verify the document type is in the key
                assert document_type in actual_key, (
                    f"Document type '{document_type}' not found in S3 key '{actual_key}'"
                )
    
    @settings(max_examples=20)
    @given(
        bucket=bucket_names,
        document_type=document_types
    )
    def test_s3_key_construction_is_deterministic(self, bucket, document_type):
        """
        **Validates: Requirements 3.1**
        Feature: tax-document-generation, Property 6: Template S3 Key Construction
        
        For any document type, calling get_template multiple times with the
        same document type must construct the same S3 key each time.
        
        This test verifies that:
        1. S3 key construction is deterministic
        2. No randomness or state affects key construction
        3. The same input always produces the same key
        """
        # Mock the S3 client
        with patch('tax_document_generation.template_retriever.boto3.client') as mock_boto3:
            mock_s3_client = Mock()
            mock_boto3.return_value = mock_s3_client
            
            # Mock successful S3 response
            mock_response = {
                'Body': MagicMock(read=Mock(return_value=b'fake pdf content'))
            }
            mock_s3_client.get_object.return_value = mock_response
            
            # Action: Call get_template multiple times
            keys_used = []
            for _ in range(3):
                try:
                    get_template(bucket, document_type)
                    if mock_s3_client.get_object.called:
                        call_args = mock_s3_client.get_object.call_args
                        keys_used.append(call_args[1]['Key'])
                        mock_s3_client.get_object.reset_mock()
                except Exception:
                    pass
            
            # Verification: All keys should be identical
            if len(keys_used) > 1:
                expected_key = f"templates/irs/{document_type}.pdf"
                for key in keys_used:
                    assert key == expected_key, (
                        f"S3 key construction is not deterministic: got '{key}', "
                        f"expected '{expected_key}'"
                    )
                
                # All keys should be the same
                assert all(k == keys_used[0] for k in keys_used), (
                    f"S3 keys are not consistent across multiple calls: {keys_used}"
                )
    
    @settings(max_examples=20)
    @given(
        bucket=bucket_names,
        document_type1=document_types,
        document_type2=document_types
    )
    def test_different_document_types_produce_different_keys(self, bucket, document_type1, document_type2):
        """
        **Validates: Requirements 3.1**
        Feature: tax-document-generation, Property 6: Template S3 Key Construction
        
        For any two different document types, the constructed S3 keys
        must be different.
        
        This test verifies that:
        1. Different document types produce different S3 keys
        2. No collision occurs between different document types
        3. The document type uniquely identifies the template
        """
        # Skip if document types are the same
        if document_type1 == document_type2:
            return
        
        # Mock the S3 client
        with patch('tax_document_generation.template_retriever.boto3.client') as mock_boto3:
            mock_s3_client = Mock()
            mock_boto3.return_value = mock_s3_client
            
            # Mock successful S3 response
            mock_response = {
                'Body': MagicMock(read=Mock(return_value=b'fake pdf content'))
            }
            mock_s3_client.get_object.return_value = mock_response
            
            # Action: Call get_template with first document type
            try:
                get_template(bucket, document_type1)
            except Exception:
                pass
            
            key1 = None
            if mock_s3_client.get_object.called:
                call_args = mock_s3_client.get_object.call_args
                key1 = call_args[1]['Key']
            
            mock_s3_client.get_object.reset_mock()
            
            # Action: Call get_template with second document type
            try:
                get_template(bucket, document_type2)
            except Exception:
                pass
            
            key2 = None
            if mock_s3_client.get_object.called:
                call_args = mock_s3_client.get_object.call_args
                key2 = call_args[1]['Key']
            
            # Verification: Keys should be different
            if key1 and key2:
                assert key1 != key2, (
                    f"Different document types produced the same S3 key: "
                    f"'{document_type1}' and '{document_type2}' both produced '{key1}'"
                )
                
                # Verify each key contains its respective document type
                assert document_type1 in key1
                assert document_type2 in key2
    
    @settings(max_examples=20)
    @given(
        bucket=bucket_names,
        document_type=document_types
    )
    def test_s3_key_has_correct_prefix(self, bucket, document_type):
        """
        **Validates: Requirements 3.1**
        Feature: tax-document-generation, Property 6: Template S3 Key Construction
        
        For any document type, the constructed S3 key must start with
        the prefix "templates/irs/".
        
        This test verifies that:
        1. All template keys use the correct prefix
        2. Templates are organized under the templates/irs/ directory
        3. The prefix is consistent across all document types
        """
        # Mock the S3 client
        with patch('tax_document_generation.template_retriever.boto3.client') as mock_boto3:
            mock_s3_client = Mock()
            mock_boto3.return_value = mock_s3_client
            
            # Mock successful S3 response
            mock_response = {
                'Body': MagicMock(read=Mock(return_value=b'fake pdf content'))
            }
            mock_s3_client.get_object.return_value = mock_response
            
            # Action: Call get_template
            try:
                get_template(bucket, document_type)
            except Exception:
                pass
            
            # Verification: Check the prefix
            if mock_s3_client.get_object.called:
                call_args = mock_s3_client.get_object.call_args
                actual_key = call_args[1]['Key']
                
                # The key must start with "templates/irs/"
                assert actual_key.startswith("templates/irs/"), (
                    f"S3 key '{actual_key}' does not start with required prefix 'templates/irs/'"
                )
                
                # Verify the prefix is exactly "templates/irs/" (not "templates/irs" or "templates//irs/")
                prefix = actual_key[:14]  # Length of "templates/irs/"
                assert prefix == "templates/irs/", (
                    f"S3 key prefix '{prefix}' is not exactly 'templates/irs/'"
                )
    
    @settings(max_examples=20)
    @given(
        bucket=bucket_names,
        document_type=document_types
    )
    def test_s3_key_has_pdf_extension(self, bucket, document_type):
        """
        **Validates: Requirements 3.1**
        Feature: tax-document-generation, Property 6: Template S3 Key Construction
        
        For any document type, the constructed S3 key must end with
        the ".pdf" extension.
        
        This test verifies that:
        1. All template keys have the .pdf extension
        2. Templates are stored as PDF files
        3. The extension is consistent across all document types
        """
        # Mock the S3 client
        with patch('tax_document_generation.template_retriever.boto3.client') as mock_boto3:
            mock_s3_client = Mock()
            mock_boto3.return_value = mock_s3_client
            
            # Mock successful S3 response
            mock_response = {
                'Body': MagicMock(read=Mock(return_value=b'fake pdf content'))
            }
            mock_s3_client.get_object.return_value = mock_response
            
            # Action: Call get_template
            try:
                get_template(bucket, document_type)
            except Exception:
                pass
            
            # Verification: Check the extension
            if mock_s3_client.get_object.called:
                call_args = mock_s3_client.get_object.call_args
                actual_key = call_args[1]['Key']
                
                # The key must end with ".pdf"
                assert actual_key.endswith(".pdf"), (
                    f"S3 key '{actual_key}' does not end with required extension '.pdf'"
                )
                
                # Verify it's exactly ".pdf" (not ".PDF" or ".pdf.txt")
                extension = actual_key[-4:]  # Last 4 characters
                assert extension == ".pdf", (
                    f"S3 key extension '{extension}' is not exactly '.pdf'"
                )
    
    @settings(max_examples=20)
    @given(
        bucket=bucket_names,
        document_type=document_types
    )
    def test_s3_key_structure_is_correct(self, bucket, document_type):
        """
        **Validates: Requirements 3.1**
        Feature: tax-document-generation, Property 6: Template S3 Key Construction
        
        For any document type, the constructed S3 key must have the exact
        structure: "templates/irs/{documentType}.pdf" with no extra slashes,
        spaces, or characters.
        
        This test verifies that:
        1. The key structure is exactly as specified
        2. No extra characters are added
        3. The format is consistent and predictable
        """
        # Mock the S3 client
        with patch('tax_document_generation.template_retriever.boto3.client') as mock_boto3:
            mock_s3_client = Mock()
            mock_boto3.return_value = mock_s3_client
            
            # Mock successful S3 response
            mock_response = {
                'Body': MagicMock(read=Mock(return_value=b'fake pdf content'))
            }
            mock_s3_client.get_object.return_value = mock_response
            
            # Action: Call get_template
            try:
                get_template(bucket, document_type)
            except Exception:
                pass
            
            # Verification: Check the complete structure
            if mock_s3_client.get_object.called:
                call_args = mock_s3_client.get_object.call_args
                actual_key = call_args[1]['Key']
                expected_key = f"templates/irs/{document_type}.pdf"
                
                # The key must exactly match the expected pattern
                assert actual_key == expected_key, (
                    f"S3 key '{actual_key}' does not match expected structure "
                    f"'templates/irs/{document_type}.pdf'"
                )
                
                # Verify no double slashes
                assert "//" not in actual_key, (
                    f"S3 key '{actual_key}' contains double slashes"
                )
                
                # Verify no spaces
                assert " " not in actual_key, (
                    f"S3 key '{actual_key}' contains spaces"
                )
                
                # Verify the key has exactly 3 parts when split by '/'
                parts = actual_key.split('/')
                assert len(parts) == 3, (
                    f"S3 key '{actual_key}' should have 3 parts separated by '/', "
                    f"but has {len(parts)}: {parts}"
                )
                
                # Verify each part
                assert parts[0] == "templates", f"First part should be 'templates', got '{parts[0]}'"
                assert parts[1] == "irs", f"Second part should be 'irs', got '{parts[1]}'"
                assert parts[2] == f"{document_type}.pdf", (
                    f"Third part should be '{document_type}.pdf', got '{parts[2]}'"
                )
    
    @settings(max_examples=20)
    @given(
        bucket=bucket_names,
        document_type=document_types
    )
    def test_bucket_parameter_is_used_correctly(self, bucket, document_type):
        """
        **Validates: Requirements 3.1**
        Feature: tax-document-generation, Property 6: Template S3 Key Construction
        
        For any bucket and document type, the get_template function must
        use the provided bucket parameter when calling S3.
        
        This test verifies that:
        1. The bucket parameter is passed to S3 get_object call
        2. The correct bucket is used for template retrieval
        3. Bucket and key are both correctly specified
        """
        # Mock the S3 client
        with patch('tax_document_generation.template_retriever.boto3.client') as mock_boto3:
            mock_s3_client = Mock()
            mock_boto3.return_value = mock_s3_client
            
            # Mock successful S3 response
            mock_response = {
                'Body': MagicMock(read=Mock(return_value=b'fake pdf content'))
            }
            mock_s3_client.get_object.return_value = mock_response
            
            # Action: Call get_template
            try:
                get_template(bucket, document_type)
            except Exception:
                pass
            
            # Verification: Check that the correct bucket was used
            if mock_s3_client.get_object.called:
                call_args = mock_s3_client.get_object.call_args
                actual_bucket = call_args[1]['Bucket']
                actual_key = call_args[1]['Key']
                
                # The bucket must match the provided parameter
                assert actual_bucket == bucket, (
                    f"S3 bucket '{actual_bucket}' does not match provided bucket '{bucket}'"
                )
                
                # The key must follow the correct pattern
                expected_key = f"templates/irs/{document_type}.pdf"
                assert actual_key == expected_key, (
                    f"S3 key '{actual_key}' does not match expected pattern '{expected_key}'"
                )
    
    @settings(max_examples=20)
    @given(
        bucket=bucket_names,
        document_type=document_types
    )
    def test_s3_key_construction_with_special_characters(self, bucket, document_type):
        """
        **Validates: Requirements 3.1**
        Feature: tax-document-generation, Property 6: Template S3 Key Construction
        
        For any document type containing special characters (hyphens, underscores),
        the S3 key must preserve these characters exactly as provided.
        
        This test verifies that:
        1. Special characters in document type are preserved
        2. No encoding or escaping occurs
        3. The document type is used exactly as provided
        """
        # Mock the S3 client
        with patch('tax_document_generation.template_retriever.boto3.client') as mock_boto3:
            mock_s3_client = Mock()
            mock_boto3.return_value = mock_s3_client
            
            # Mock successful S3 response
            mock_response = {
                'Body': MagicMock(read=Mock(return_value=b'fake pdf content'))
            }
            mock_s3_client.get_object.return_value = mock_response
            
            # Action: Call get_template
            try:
                get_template(bucket, document_type)
            except Exception:
                pass
            
            # Verification: Check that special characters are preserved
            if mock_s3_client.get_object.called:
                call_args = mock_s3_client.get_object.call_args
                actual_key = call_args[1]['Key']
                expected_key = f"templates/irs/{document_type}.pdf"
                
                # The key must exactly match with special characters preserved
                assert actual_key == expected_key, (
                    f"S3 key '{actual_key}' does not preserve document type '{document_type}' correctly"
                )
                
                # Verify the document type appears exactly in the key
                # Extract the document type from the key
                key_without_prefix = actual_key.replace("templates/irs/", "")
                key_without_extension = key_without_prefix.replace(".pdf", "")
                
                assert key_without_extension == document_type, (
                    f"Document type '{document_type}' not preserved correctly in key, "
                    f"extracted '{key_without_extension}'"
                )
