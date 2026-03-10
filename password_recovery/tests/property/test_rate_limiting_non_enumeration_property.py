"""
Property-based tests for rate limiting non-enumeration.

Feature: password-recovery
Property 6: Rate Limiting Non-Enumeration

**Validates: Requirements 2.3**

For any rate-limited request, the error response should not reveal whether 
the submitted email corresponds to a registered account.

Note: This test validates that the RateLimiter component doesn't leak information
about account existence. The actual non-enumeration response will be implemented
in the Lambda handler, which will return the same generic message regardless of
whether the email exists or the request is rate-limited.
"""

import pytest
from unittest.mock import Mock
from hypothesis import given, strategies as st, settings
from password_recovery.rate_limiter import RateLimiter


class TestRateLimitingNonEnumerationProperty:
    """Property-based tests for rate limiting non-enumeration."""
    
    def _create_mock_dynamodb(self, request_count=0):
        """Helper to create a mock DynamoDB client."""
        mock_dynamodb = Mock()
        
        # Mock query response
        items = []
        import time
        current_time = int(time.time())
        for i in range(request_count):
            items.append({
                'identifier': {'S': 'test-ip'},
                'timestamp': {'N': str(current_time - i * 60)},
                'request_id': {'S': f'test-ip#{current_time - i * 60}#abc{i}'}
            })
        
        mock_dynamodb.query.return_value = {
            'Count': request_count,
            'Items': items
        }
        
        mock_dynamodb.put_item.return_value = {}
        
        return mock_dynamodb
    
    @given(st.text(min_size=1, max_size=50), st.integers(min_value=5, max_value=20))
    @settings(max_examples=100)
    def test_rate_limit_response_independent_of_identifier(self, identifier, request_count):
        """
        Property: Rate limit responses should be consistent regardless of identifier.
        
        For any identifier that is rate-limited, the response format should be
        consistent and not reveal information about the identifier.
        """
        mock_dynamodb = self._create_mock_dynamodb(request_count)
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        allowed, retry_after = limiter.check_rate_limit(identifier)
        
        # All rate-limited responses should have the same structure
        assert allowed is False
        assert retry_after is not None
        assert isinstance(retry_after, int)
        assert retry_after > 0
    
    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_rate_limiter_does_not_expose_user_data(self, identifier):
        """
        Property: Rate limiter should not access or expose user data.
        
        For any identifier, the rate limiter should only track request counts
        and timestamps, not user account information.
        """
        mock_dynamodb = self._create_mock_dynamodb(0)
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        # Check rate limit
        allowed, retry_after = limiter.check_rate_limit(identifier)
        
        # Verify the query only uses identifier and timestamp
        call_args = mock_dynamodb.query.call_args
        assert call_args is not None
        
        # The query should only reference identifier and timestamp
        # It should NOT query user tables or access email/account data
        assert call_args[1]['TableName'] == 'TestTable'
        assert ':id' in call_args[1]['ExpressionAttributeValues']
        assert ':window_start' in call_args[1]['ExpressionAttributeValues']
        
        # Should not have any user-related fields
        assert 'email' not in str(call_args).lower()
        assert 'user' not in str(call_args).lower() or 'user' in 'TestTable'.lower()
    
    @given(st.integers(min_value=5, max_value=20))
    @settings(max_examples=100)
    def test_rate_limit_error_format_consistent(self, request_count):
        """
        Property: Rate limit errors should have consistent format.
        
        For any rate-limited request, the error response format should be
        consistent, making it impossible to distinguish between different
        types of rate-limited requests.
        """
        mock_dynamodb = self._create_mock_dynamodb(request_count)
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        # Test with different identifiers
        identifier1 = 'ip-address-1'
        identifier2 = 'ip-address-2'
        
        allowed1, retry_after1 = limiter.check_rate_limit(identifier1)
        allowed2, retry_after2 = limiter.check_rate_limit(identifier2)
        
        # Both should have the same response structure
        assert allowed1 is False
        assert allowed2 is False
        assert isinstance(retry_after1, int)
        assert isinstance(retry_after2, int)
        # Both should be positive
        assert retry_after1 > 0
        assert retry_after2 > 0
    
    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_record_request_does_not_store_sensitive_data(self, identifier):
        """
        Property: Request recording should not store sensitive user data.
        
        For any request recording, only the identifier, timestamp, and TTL
        should be stored - no email addresses or account information.
        """
        mock_dynamodb = Mock()
        mock_dynamodb.put_item.return_value = {}
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        limiter.record_request(identifier)
        
        # Verify put_item was called
        call_args = mock_dynamodb.put_item.call_args
        item = call_args[1]['Item']
        
        # Should only contain rate limiting data
        assert 'identifier' in item
        assert 'timestamp' in item
        assert 'ttl' in item
        assert 'request_id' in item
        
        # Should NOT contain user data
        assert 'email' not in item
        assert 'user_id' not in item
        assert 'password' not in item
        assert 'account' not in item
    
    @given(st.integers(min_value=0, max_value=4), st.integers(min_value=5, max_value=20))
    @settings(max_examples=100)
    def test_allowed_and_blocked_responses_distinguishable_only_by_status(
        self, allowed_count, blocked_count
    ):
        """
        Property: Allowed and blocked responses should differ only in allowed status.
        
        For any request, whether allowed or blocked, the response structure
        should be consistent - only the allowed boolean and retry_after presence
        should differ.
        """
        # Test allowed request
        mock_dynamodb_allowed = self._create_mock_dynamodb(allowed_count)
        limiter_allowed = RateLimiter(dynamodb_client=mock_dynamodb_allowed, table_name='TestTable')
        allowed1, retry_after1 = limiter_allowed.check_rate_limit('test-ip')
        
        # Test blocked request
        mock_dynamodb_blocked = self._create_mock_dynamodb(blocked_count)
        limiter_blocked = RateLimiter(dynamodb_client=mock_dynamodb_blocked, table_name='TestTable')
        allowed2, retry_after2 = limiter_blocked.check_rate_limit('test-ip')
        
        # Verify response structure
        assert allowed1 is True
        assert retry_after1 is None
        
        assert allowed2 is False
        assert retry_after2 is not None
        assert isinstance(retry_after2, int)
        
        # Both return tuples of (bool, Optional[int])
        assert isinstance(allowed1, bool)
        assert isinstance(allowed2, bool)
    
    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_rate_limiter_isolation_from_user_repository(self, identifier):
        """
        Property: Rate limiter should be isolated from user repository.
        
        For any rate limit check, the rate limiter should not interact with
        the user repository or access user account data.
        """
        mock_dynamodb = self._create_mock_dynamodb(0)
        limiter = RateLimiter(dynamodb_client=mock_dynamodb, table_name='TestTable')
        
        # Check rate limit
        limiter.check_rate_limit(identifier)
        
        # Verify only the rate limits table was queried
        call_args = mock_dynamodb.query.call_args
        assert call_args[1]['TableName'] == 'TestTable'
        
        # Should not query Users table or any other user-related table
        assert 'Users' not in call_args[1]['TableName']
        assert 'Accounts' not in call_args[1]['TableName']
