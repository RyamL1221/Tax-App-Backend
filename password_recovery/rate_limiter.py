"""
Rate limiter for password recovery.

This module implements rate limiting using DynamoDB with a sliding window algorithm
to prevent abuse of the password recovery endpoints.
"""

import os
import logging
import time
from typing import Tuple, Optional
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter using DynamoDB with sliding window algorithm.
    
    Enforces a limit of 5 requests per 15 minutes per IP address.
    """
    
    # Rate limit configuration
    MAX_REQUESTS = 5
    WINDOW_SECONDS = 15 * 60  # 15 minutes
    
    def __init__(self, dynamodb_client=None, table_name=None):
        """
        Initialize the rate limiter.
        
        Args:
            dynamodb_client: Optional boto3 DynamoDB client (for testing)
            table_name: Optional table name (defaults to env var RATE_LIMITS_TABLE)
        """
        self.dynamodb = dynamodb_client or boto3.client('dynamodb')
        self.table_name = table_name or os.environ.get('RATE_LIMITS_TABLE', 'RateLimits')
        logger.debug(f"RateLimiter initialized with table: {self.table_name}")
    
    def check_rate_limit(self, identifier: str) -> Tuple[bool, Optional[int]]:
        """
        Checks if a request should be allowed based on rate limits.
        
        Args:
            identifier: IP address or other identifier
            
        Returns:
            tuple containing:
            - allowed: True if request is within limits
            - retry_after: Seconds until next request allowed (if blocked)
            
        Rate limit: 5 requests per 15 minutes per IP address
        
        Examples:
            >>> limiter = RateLimiter()
            >>> allowed, retry_after = limiter.check_rate_limit("192.168.1.1")
            >>> if allowed:
            ...     print("Request allowed")
            ... else:
            ...     print(f"Rate limited. Retry after {retry_after} seconds")
        """
        try:
            current_time = int(time.time())
            window_start = current_time - self.WINDOW_SECONDS
            
            # Query for requests from this identifier in the current window
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='identifier = :id AND #ts >= :window_start',
                ExpressionAttributeNames={
                    '#ts': 'timestamp'
                },
                ExpressionAttributeValues={
                    ':id': {'S': identifier},
                    ':window_start': {'N': str(window_start)}
                }
            )
            
            request_count = response.get('Count', 0)
            
            if request_count >= self.MAX_REQUESTS:
                # Rate limit exceeded
                # Calculate retry_after based on oldest request in window
                if response.get('Items'):
                    # Get the oldest timestamp
                    oldest_timestamp = min(
                        int(item['timestamp']['N']) 
                        for item in response['Items']
                    )
                    # Retry after the window expires for the oldest request
                    retry_after = (oldest_timestamp + self.WINDOW_SECONDS) - current_time
                    retry_after = max(1, retry_after)  # At least 1 second
                else:
                    retry_after = self.WINDOW_SECONDS
                
                logger.info(f"Rate limit exceeded for {identifier}: {request_count} requests in window")
                return False, retry_after
            
            # Within limits
            logger.debug(f"Rate limit check passed for {identifier}: {request_count}/{self.MAX_REQUESTS}")
            return True, None
            
        except ClientError as e:
            logger.error(f"DynamoDB error checking rate limit: {e}")
            # On error, allow the request (fail open for availability)
            # In production, you might want to fail closed for security
            return True, None
        except Exception as e:
            logger.error(f"Unexpected error checking rate limit: {e}")
            return True, None
    
    def record_request(self, identifier: str) -> None:
        """
        Records a request for rate limiting purposes.
        
        Args:
            identifier: IP address or other identifier
            
        Stores the request timestamp in DynamoDB with TTL for automatic cleanup.
        
        Examples:
            >>> limiter = RateLimiter()
            >>> limiter.record_request("192.168.1.1")
        """
        try:
            current_time = int(time.time())
            # TTL is set to window duration + some buffer for cleanup
            ttl = current_time + self.WINDOW_SECONDS + 3600  # +1 hour buffer
            
            # Generate a unique request ID (identifier + timestamp)
            request_id = f"{identifier}#{current_time}#{os.urandom(4).hex()}"
            
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    'identifier': {'S': identifier},
                    'timestamp': {'N': str(current_time)},
                    'request_id': {'S': request_id},
                    'ttl': {'N': str(ttl)}
                }
            )
            
            logger.debug(f"Recorded request for {identifier} at {current_time}")
            
        except ClientError as e:
            logger.error(f"DynamoDB error recording request: {e}")
            # Don't raise - recording failure shouldn't block the request
        except Exception as e:
            logger.error(f"Unexpected error recording request: {e}")
            # Don't raise - recording failure shouldn't block the request
    
    def is_rate_limited(self, identifier: str) -> bool:
        """
        Convenience method to check if an identifier is currently rate limited.
        
        Args:
            identifier: IP address or other identifier
            
        Returns:
            True if rate limited, False otherwise
            
        Examples:
            >>> limiter = RateLimiter()
            >>> if limiter.is_rate_limited("192.168.1.1"):
            ...     print("Too many requests")
        """
        allowed, _ = self.check_rate_limit(identifier)
        return not allowed
