"""
Rate limiting utilities for the VirtualBox MCP server.

This module provides a token bucket rate limiter implementation to control
the rate of requests to the API endpoints.
"""

import threading
import time
from collections import defaultdict


class RateLimiter:
    """
    A token bucket rate limiter implementation.

    This class implements a token bucket algorithm for rate limiting.
    Each request consumes a token, and tokens are replenished at a fixed rate.
    """

    def __init__(self, max_calls: int, period: float, burst: int | None = None):
        """
        Initialize the rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in the time period.
            period: Time period in seconds for the rate limit.
            burst: Maximum burst size (optional). If not provided, defaults to max_calls.
        """
        self.max_calls = max_calls
        self.period = period
        self.burst = burst or max_calls

        # Thread safety
        self._lock = threading.RLock()

        # Track usage per client (IP, user ID, etc.)
        self._tokens = defaultdict(int)
        self._timestamps = defaultdict(float)

        # Track sliding window for each client
        self._windows = defaultdict(list)

    def allow_request(self, client_id: str = "default") -> bool:
        """
        Check if a request is allowed for the given client.

        Args:
            client_id: Identifier for the client (e.g., IP address or user ID).

        Returns:
            bool: True if the request is allowed, False if rate limited.
        """
        with self._lock:
            now = time.time()
            last_time = self._timestamps.get(client_id, 0)

            # Calculate tokens to add based on time passed
            time_passed = now - last_time
            tokens_to_add = (time_passed / self.period) * self.max_calls

            # Update token count, but don't exceed max_calls
            self._tokens[client_id] = min(
                self._tokens.get(client_id, self.max_calls) + tokens_to_add, self.max_calls
            )

            # Update the last request time
            self._timestamps[client_id] = now

            # Check if we have enough tokens
            if self._tokens[client_id] >= 1.0:
                self._tokens[client_id] -= 1.0
                self._update_sliding_window(client_id, now)
                return True

            return False

    def _update_sliding_window(self, client_id: str, timestamp: float) -> None:
        """
        Update the sliding window for a client.

        Args:
            client_id: Identifier for the client.
            timestamp: Current timestamp.
        """
        # Remove timestamps older than the window
        window = self._windows[client_id]
        window = [t for t in window if (timestamp - t) <= self.period]

        # Add the new timestamp
        window.append(timestamp)
        self._windows[client_id] = window

    def get_usage(self, client_id: str = "default") -> dict:
        """
        Get usage statistics for a client.

        Args:
            client_id: Identifier for the client.

        Returns:
            dict: Dictionary containing usage statistics.
        """
        with self._lock:
            now = time.time()
            window = self._windows.get(client_id, [])

            # Remove old timestamps
            window = [t for t in window if (now - t) <= self.period]
            self._windows[client_id] = window

            return {
                "calls": len(window),
                "max_calls": self.max_calls,
                "period": self.period,
                "remaining": max(0, self.max_calls - len(window)),
                "reset_time": self.time_until_next_window(),
            }

    def time_until_next_window(self) -> float:
        """
        Get the time in seconds until the next rate limit window resets.

        Returns:
            float: Time in seconds until the next window.
        """
        return max(0, self.period - (time.time() % self.period))

    def reset(self, client_id: str = "default") -> None:
        """
        Reset the rate limiter for a client.

        Args:
            client_id: Identifier for the client.
        """
        with self._lock:
            if client_id in self._tokens:
                del self._tokens[client_id]
            if client_id in self._timestamps:
                del self._timestamps[client_id]
            if client_id in self._windows:
                del self._windows[client_id]


# Global rate limiter instance
global_rate_limiter = RateLimiter(
    max_calls=100,  # 100 requests
    period=60,  # per minute
    burst=20,  # allow burst of 20 requests
)
