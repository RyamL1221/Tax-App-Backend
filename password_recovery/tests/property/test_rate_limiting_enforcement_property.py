"""
Property-based tests for rate limiting enforcement.

Feature: password-recovery
Property 5: Rate Limiting Enforcement

**Validates: Requirements 2.1**

For any IP address making password reset requests, when the request frequency 
exceeds the configured limit (5 requests per 15 minutes), subsequent requests 
should be rejected with a 429 status code.

Note: This test validates the RateLimiter component's enforcement logic.
The actual HTTP status code (429) will be set by the Lambda handler.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock
from hypothesis import given, strategies as st, settings
from password_recovery.rate_limiter import RateLimiter


class TestRateLimitingEnforcementProperty:
    """Property-based tests for rate limiting enforcement."""
    
    def _create_mock_dynamodb(self, request_count=0):
        """Helper to create a mock DynamoDB client."""
        mock_dynamodb = Mock()
        
        # Mock query response
        items = []
        current_time = int(time.time())
        for i in range(request_count):
            items.append({
                'identifier': {'S': 'test-ip'},
                'timestamp': {'N': str(current_time - i * 60)},  # Spread over time
                'request_id': {'S': f'test-ip#{current_time - i * 60}#abc{i}'}
            })
        
        mock_dynamodb.query.return_value = {
            'Count': request_count,
            'Items': items
        }
        
        mock_dynamodb.put_item.return_value = {}
        
        return mock_dynamodb
    
    @given(st.integers(min_value=0, max_value=4))
    @settings(max_examples=100)
    def test_requests_within_limit_allowed(self, request_count):
        """
        Property: Requests within the rate limit should be allowed.
        
        For any number of requests less than the maximum (5), the rate limiter
        should allow the request.
        """
        mock_dynamodb = self._create_mock_dynamodb(request_count)
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        allowed, retry_after = limiter.check_rate_limit('test-ip')
        
        assert allowed is True, f"Request should be allowed with {request_count} prior requests"
        assert retry_after is None
    
    @given(st.integers(min_value=5, max_value=20))
    @settings(max_examples=100)
    def test_requests_exceeding_limit_rejected(self, request_count):
        """
        Property: Requests exceeding the rate limit should be rejected.
        
        For any number of requests equal to or greater than the maximum (5),
        the rate limiter should reject the request and provide a retry_after value.
        """
        mock_dynamodb = self._create_mock_dynamodb(request_count)
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        allowed, retry_after = limiter.check_rate_limit('test-ip')
        
        assert allowed is False, f"Request should be rejected with {request_count} prior requests"
        assert retry_after is not None
        assert isinstance(retry_after, int)
        assert retry_after > 0
        # Retry after should be reasonable (within the window duration)
        assert retry_after <= limiter.WINDOW_SECONDS
    
    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_different_identifiers_tracked_separately(self, identifier):
        """
        Property: Different identifiers should have independent rate limits.
        
        For any identifier, the rate limit should be tracked independently
        from other identifiers.
        """
        # Mock with 0 requests for this identifier
        mock_dynamodb = self._create_mock_dynamodb(0)
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        allowed, retry_after = limiter.check_rate_limit(identifier)
        
        # Should be allowed since this identifier has no prior requests
        assert allowed is True
        assert retry_after is None
        
        # Verify query was called with the correct identifier
        mock_dynamodb.query.assert_called_once()
        call_args = mock_dynamodb.query.call_args
        assert call_args[1]['ExpressionAttributeValues'][':id']['S'] == identifier
    
    @given(st.integers(min_value=0, max_value=10))
    @settings(max_examples=100)
    def test_record_request_stores_timestamp(self, _):
        """
        Property: Recording a request should store it in DynamoDB with timestamp.
        
        For any request recording, the rate limiter should store the identifier,
        timestamp, and TTL in DynamoDB.
        """
        mock_dynamodb = Mock()
        mock_dynamodb.put_item.return_value = {}
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        identifier = 'test-ip-123'
        limiter.record_request(identifier)
        
        # Verify put_item was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args
        
        # Verify the item structure
        item = call_args[1]['Item']
        assert 'identifier' in item
        assert item['identifier']['S'] == identifier
        assert 'timestamp' in item
        assert 'N' in item['timestamp']
        assert 'ttl' in item
        assert 'N' in item['ttl']
        assert 'request_id' in item
    
    @given(st.integers(min_value=0, max_value=4))
    @settings(max_examples=100)
    def test_is_rate_limited_convenience_method(self, request_count):
        """
        Property: is_rate_limited() should return correct boolean status.
        
        For any request count, is_rate_limited() should return True if and only if
        the request count is at or above the limit.
        """
        mock_dynamodb = self._create_mock_dynamodb(request_count)
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        is_limited = limiter.is_rate_limited('test-ip')
        
        # Should not be limited if under the limit
        assert is_limited is False
    
    @given(st.integers(min_value=5, max_value=20))
    @settings(max_examples=100)
    def test_is_rate_limited_when_over_limit(self, request_count):
        """
        Property: is_rate_limited() should return True when over limit.
        
        For any request count at or above the limit, is_rate_limited() should
        return True.
        """
        mock_dynamodb = self._create_mock_dynamodb(request_count)
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        is_limited = limiter.is_rate_limited('test-ip')
        
        # Should be limited if at or over the limit
        assert is_limited is True
    
    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_dynamodb_error_fails_open(self, identifier):
        """
        Property: DynamoDB errors should fail open (allow requests).
        
        For any DynamoDB error during rate limit check, the system should
        allow the request to maintain availability.
        """
        mock_dynamodb = Mock()
        # Simulate DynamoDB error
        from botocore.exceptions import ClientError
        mock_dynamodb.query.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'Query'
        )
        
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        allowed, retry_after = limiter.check_rate_limit(identifier)
        
        # Should fail open (allow request) on error
        assert allowed is True
        assert retry_after is None
    
    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_record_request_error_does_not_raise(self, identifier):
        """
        Property: Errors during request recording should not raise exceptions.
        
        For any error during request recording, the rate limiter should log
        the error but not raise an exception that would block the request.
        """
        mock_dynamodb = Mock()
        # Simulate DynamoDB error
        from botocore.exceptions import ClientError
        mock_dynamodb.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'PutItem'
        )
        
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        # Should not raise an exception
        try:
            limiter.record_request(identifier)
            # If we get here, the test passes
            assert True
        except Exception as e:
            pytest.fail(f"record_request raised an exception: {e}")
    
    @given(st.integers(min_value=5, max_value=10))
    @settings(max_examples=100)
    def test_retry_after_is_reasonable(self, request_count):
        """
        Property: retry_after should be a reasonable value within the window.
        
        For any rate-limited request, the retry_after value should be positive
        and not exceed the window duration.
        """
        mock_dynamodb = self._create_mock_dynamodb(request_count)
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        allowed, retry_after = limiter.check_rate_limit('test-ip')
        
        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0
        assert retry_after <= limiter.WINDOW_SECONDS
        # Should be at least 1 second
        assert retry_after >= 1
