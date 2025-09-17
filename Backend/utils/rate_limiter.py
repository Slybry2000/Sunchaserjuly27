import logging
import os
import time
from collections import defaultdict
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """Simple sliding window rate limiter using in-memory storage."""

    def __init__(self, window_seconds: int = 60, max_requests: int = 100):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        # Store timestamps for each key
        self._requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for the given key."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests outside the window
        self._requests[key] = [
            timestamp for timestamp in self._requests[key] if timestamp > window_start
        ]

        # Check if under limit
        if len(self._requests[key]) < self.max_requests:
            self._requests[key].append(now)
            return True

        logger.warning(f"Rate limit exceeded for key: {key}")
        return False

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests allowed in current window."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        self._requests[key] = [
            timestamp for timestamp in self._requests[key] if timestamp > window_start
        ]

        return max(0, self.max_requests - len(self._requests[key]))

    def get_reset_time(self, key: str) -> float:
        """Get time until rate limit resets (next request allowed)."""
        if not self._requests[key]:
            return 0.0

        now = time.time()
        window_start = now - self.window_seconds
        oldest_request = min(self._requests[key])

        if oldest_request <= window_start:
            return 0.0

        return oldest_request - window_start


# Global rate limiter instance
_rate_limiter: Optional[SlidingWindowRateLimiter] = None


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        # Configure from environment
        window_seconds = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
        max_requests = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "100"))
        _rate_limiter = SlidingWindowRateLimiter(window_seconds, max_requests)
        logger.info(
            f"Initialized rate limiter: {max_requests} requests per {window_seconds}s"
        )

    return _rate_limiter


def check_rate_limit(key: str) -> bool:
    """Check if request is allowed for the given key."""
    return get_rate_limiter().is_allowed(key)
