"""
Rate limiter utility for AlphaForge.
Manages API rate limiting to prevent hitting external service limits.
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from config import config

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API calls to various external services."""
    
    def __init__(self):
        """Initialize rate limiter with configured limits."""
        self.api_limits = config.get_api_config().get('rate_limits', {})
        self.last_request_times = defaultdict(list)
        self.request_counts = defaultdict(int)
        
        # Default limits if not configured
        self.default_limits = {
            'yfinance': 60,  # requests per minute
            'sec_edgar': 10,
            'fmp': 300,
            'alpha_vantage': 5,
            'openai': 60
        }
    
    def get_limit_for_service(self, service: str) -> int:
        """
        Get rate limit for a specific service.
        
        Args:
            service: Service name (e.g., 'yfinance', 'sec_edgar')
            
        Returns:
            Rate limit in requests per minute
        """
        return self.api_limits.get(service, self.default_limits.get(service, 60))
    
    def wait_if_needed(self, service: str):
        """
        Wait if necessary to respect rate limits for a service.
        
        Args:
            service: Service name to check rate limits for
        """
        current_time = datetime.now()
        limit = self.get_limit_for_service(service)
        
        # Clean up old requests (older than 1 minute)
        cutoff_time = current_time - timedelta(minutes=1)
        self.last_request_times[service] = [
            req_time for req_time in self.last_request_times[service]
            if req_time > cutoff_time
        ]
        
        # Check if we've hit the limit
        if len(self.last_request_times[service]) >= limit:
            # Calculate wait time until the oldest request expires
            oldest_request = min(self.last_request_times[service])
            wait_until = oldest_request + timedelta(minutes=1)
            
            if current_time < wait_until:
                wait_seconds = (wait_until - current_time).total_seconds()
                logger.info(f"Rate limit reached for {service}. Waiting {wait_seconds:.2f} seconds...")
                time.sleep(wait_seconds)
        
        # Record this request
        self.last_request_times[service].append(current_time)
        self.request_counts[service] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with statistics for each service
        """
        stats = {}
        current_time = datetime.now()
        
        for service, request_times in self.last_request_times.items():
            # Clean up old requests
            cutoff_time = current_time - timedelta(minutes=1)
            recent_requests = [
                req_time for req_time in request_times
                if req_time > cutoff_time
            ]
            
            stats[service] = {
                'requests_last_minute': len(recent_requests),
                'rate_limit': self.get_limit_for_service(service),
                'total_requests': self.request_counts[service],
                'utilization_percent': (len(recent_requests) / self.get_limit_for_service(service)) * 100
            }
        
        return stats
    
    def reset_stats(self):
        """Reset all rate limiter statistics."""
        self.last_request_times.clear()
        self.request_counts.clear()
        logger.info("Rate limiter statistics reset")
    
    def add_delay(self, service: str, extra_seconds: float = 0):
        """
        Add extra delay beyond rate limiting.
        
        Args:
            service: Service name
            extra_seconds: Additional seconds to wait
        """
        if extra_seconds > 0:
            logger.info(f"Adding {extra_seconds} second delay for {service}")
            time.sleep(extra_seconds)

class BatchRateLimiter:
    """Rate limiter for batch operations with progress tracking."""
    
    def __init__(self, rate_limiter: RateLimiter):
        """
        Initialize batch rate limiter.
        
        Args:
            rate_limiter: RateLimiter instance to use
        """
        self.rate_limiter = rate_limiter
        self.batch_start_time = None
        self.total_items = 0
        self.processed_items = 0
    
    def start_batch(self, total_items: int):
        """
        Start a batch operation.
        
        Args:
            total_items: Total number of items to process
        """
        self.batch_start_time = datetime.now()
        self.total_items = total_items
        self.processed_items = 0
        logger.info(f"Starting batch operation with {total_items} items")
    
    def process_item(self, service: str, item_name: Optional[str] = None):
        """
        Process a single item in the batch with rate limiting.
        
        Args:
            service: Service name for rate limiting
            item_name: Optional name of the item being processed
        """
        self.rate_limiter.wait_if_needed(service)
        self.processed_items += 1
        
        if item_name:
            logger.info(f"Processing item {self.processed_items}/{self.total_items}: {item_name}")
        else:
            logger.info(f"Processing item {self.processed_items}/{self.total_items}")
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get batch processing progress.
        
        Returns:
            Dictionary with progress information
        """
        if not self.batch_start_time:
            return {}
        
        elapsed_time = datetime.now() - self.batch_start_time
        progress_percent = (self.processed_items / self.total_items) * 100 if self.total_items > 0 else 0
        
        # Estimate time remaining
        if self.processed_items > 0:
            avg_time_per_item = elapsed_time.total_seconds() / self.processed_items
            remaining_items = self.total_items - self.processed_items
            estimated_remaining = timedelta(seconds=avg_time_per_item * remaining_items)
        else:
            estimated_remaining = timedelta(0)
        
        return {
            'processed_items': self.processed_items,
            'total_items': self.total_items,
            'progress_percent': progress_percent,
            'elapsed_time': elapsed_time,
            'estimated_remaining': estimated_remaining,
            'items_per_second': self.processed_items / elapsed_time.total_seconds() if elapsed_time.total_seconds() > 0 else 0
        }
    
    def finish_batch(self):
        """Finish the batch operation and log statistics."""
        if not self.batch_start_time:
            return
        
        elapsed_time = datetime.now() - self.batch_start_time
        items_per_second = self.processed_items / elapsed_time.total_seconds() if elapsed_time.total_seconds() > 0 else 0
        
        logger.info(f"Batch operation completed: {self.processed_items}/{self.total_items} items processed in {elapsed_time}")
        logger.info(f"Processing rate: {items_per_second:.2f} items/second")
        
        # Reset batch state
        self.batch_start_time = None
        self.total_items = 0
        self.processed_items = 0 