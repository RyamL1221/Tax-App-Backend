"""
Property Test: Output S3 Key Pattern

Feature: tax-document-generation
Property 8: Output S3 Key Pattern

Tests that output S3 keys follow the pattern outputs/{userId}/{jobId}/{filename}.
**Validates: Requirements 4.2, 6.1**
"""

import pytest
import re
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch
from tax_document_generation.output_persister import store_output


@st.composite
def valid_identifiers(draw):
    """Generate valid user IDs and job IDs."""
    # Generate alphanumeric identifiers with hyphens (UUID-like)
    user_id = draw(st.text(
        min_size=8,
        max_size=36,
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-')
    ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-')))
    
    job_id = draw(st.text(
        min_size=8,
        max_size=36,
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-')
    ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-')))
    
    document_type = draw(st.sampled_from(["1040", "1099", "W2", "1040-EZ", "1040-SR"]))
    
    return user_id, job_id, document_type


@settings(max_examples=20)
@given(identifiers=valid_identifiers())
@patch('tax_document_generation.output_persister.boto3')
def test_output_s3_key_pattern(mock_boto3, identifiers):
    """
    Property: For any userId and jobId, the output S3 key should follow
    the pattern outputs/{userId}/{jobId}/form-{documentType}.pdf
    
    This ensures consistent organization of generated documents.
    """
    user_id, job_id, document_type = identifiers
    
    # Mock S3 client
    mock_s3_client = Mock()
    mock_boto3.client.return_value = mock_s3_client
    
    # Create test document
    test_document = b"test pdf content"
    bucket = "test-bucket"
    
    # Store the output
    result_key = store_output(bucket, user_id, job_id, test_document, document_type)
    
    # Verify the key follows the expected pattern
    expected_pattern = f"^outputs/{re.escape(user_id)}/{re.escape(job_id)}/form-{re.escape(document_type)}\\.pdf$"
    assert re.match(expected_pattern, result_key), f"Key '{result_key}' doesn't match pattern"
    
    # Verify the key components
    assert result_key.startswith("outputs/"), "Key should start with 'outputs/'"
    assert f"/{user_id}/" in result_key, "Key should contain user_id"
    assert f"/{job_id}/" in result_key, "Key should contain job_id"
    assert result_key.endswith(f"/form-{document_type}.pdf"), "Key should end with form filename"
    
    # Verify S3 client was called with correct parameters
    mock_s3_client.put_object.assert_called_once()
    call_args = mock_s3_client.put_object.call_args
    
    assert call_args[1]['Bucket'] == bucket
    assert call_args[1]['Key'] == result_key
    assert call_args[1]['Body'] == test_document
    assert call_args[1]['ContentType'] == 'application/pdf'


def test_output_key_structure_unit():
    """
    Unit test: Verify the S3 key structure for a specific example.
    """
    with patch('tax_document_generation.output_persister.boto3') as mock_boto3:
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client
        
        user_id = "user-123"
        job_id = "job-456"
        document_type = "1040"
        document = b"test content"
        bucket = "test-bucket"
        
        result_key = store_output(bucket, user_id, job_id, document, document_type)
        
        expected_key = "outputs/user-123/job-456/form-1040.pdf"
        assert result_key == expected_key


def test_user_scoped_prefix():
    """
    Unit test: Verify that all documents for a user share the same prefix.
    """
    with patch('tax_document_generation.output_persister.boto3') as mock_boto3:
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client
        
        user_id = "user-abc"
        bucket = "test-bucket"
        document = b"test"
        
        # Generate multiple documents for the same user
        keys = []
        for i in range(3):
            job_id = f"job-{i}"
            key = store_output(bucket, user_id, f"job-{i}", document, "1040")
            keys.append(key)
        
        # Verify all keys share the same user prefix
        expected_prefix = f"outputs/{user_id}/"
        for key in keys:
            assert key.startswith(expected_prefix), f"Key {key} should start with {expected_prefix}"


def test_special_characters_in_ids():
    """
    Unit test: Verify handling of special characters in user/job IDs.
    """
    with patch('tax_document_generation.output_persister.boto3') as mock_boto3:
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client
        
        # Test with UUIDs (common format)
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        job_id = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        document_type = "1040"
        
        result_key = store_output("bucket", user_id, job_id, b"test", document_type)
        
        expected_key = f"outputs/{user_id}/{job_id}/form-{document_type}.pdf"
        assert result_key == expected_key
