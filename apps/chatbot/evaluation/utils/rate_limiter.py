"""
Rate Limiter Utility for LLM API Calls

This module provides rate limiting capabilities with exponential backoff,
retry logic, and token bucket algorithm to prevent hitting API rate limits.
"""

import time
import logging
from typing import Callable, TypeVar, Any
from functools import wraps
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 10
    requests_per_second: float = 2.0
    max_retries: int = 5
    initial_retry_delay: float = 5.0
    max_retry_delay: float = 300.0
    backoff_multiplier: float = 2.0
    batch_size: int = 3
    batch_delay: float = 60.0
    item_delay: float = 10.0


class RateLimiter:
    """
    Rate limiter with exponential backoff and token bucket algorithm.

    Features:
    - Token bucket for smooth rate limiting
    - Exponential backoff on failures
    - Configurable retry logic
    - Request tracking and statistics
    """

    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()

        # Token bucket state
        self.tokens = self.config.requests_per_second
        self.last_update = time.time()

        # Statistics
        self.total_requests = 0
        self.failed_requests = 0
        self.total_wait_time = 0.0
        self.rate_limit_hits = 0

    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on time elapsed
        tokens_to_add = elapsed * self.config.requests_per_second
        self.tokens = min(self.config.requests_per_second, self.tokens + tokens_to_add)
        self.last_update = now

    def acquire(self, tokens: float = 1.0) -> float:
        """
        Acquire tokens for making a request.

        Args:
            tokens: Number of tokens to acquire (default 1.0)

        Returns:
            Time waited in seconds
        """
        self._refill_tokens()

        # If not enough tokens, wait
        if self.tokens < tokens:
            wait_time = (tokens - self.tokens) / self.config.requests_per_second
            logger.debug(f"Rate limit: waiting {wait_time:.2f}s for tokens")
            time.sleep(wait_time)
            self.total_wait_time += wait_time
            self._refill_tokens()

        # Consume tokens
        self.tokens -= tokens
        self.total_requests += 1

        return self.total_wait_time

    def with_retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function with exponential backoff retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function

        Raises:
            Exception: If all retries are exhausted
        """
        retry_delay = self.config.initial_retry_delay
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                # Acquire token before making request
                self.acquire()

                # Execute function
                result = func(*args, **kwargs)

                # Success - reset retry delay for next call
                return result

            except Exception as e:
                error_msg = str(e).lower()
                last_exception = e

                # Check if it's a rate limit error
                is_rate_limit = any(
                    keyword in error_msg
                    for keyword in ["rate limit", "throttl", "too many requests", "429"]
                )

                if is_rate_limit:
                    self.rate_limit_hits += 1
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{self.config.max_retries}). "
                        f"Waiting {retry_delay:.1f}s before retry..."
                    )
                else:
                    logger.error(
                        f"Error in request (attempt {attempt + 1}/{self.config.max_retries}): "
                        f"{e}"
                    )

                self.failed_requests += 1

                # If this was the last attempt, raise the exception
                if attempt == self.config.max_retries - 1:
                    logger.error(
                        f"All {self.config.max_retries} retry attempts exhausted"
                    )
                    raise last_exception

                # Wait with exponential backoff
                time.sleep(retry_delay)
                self.total_wait_time += retry_delay

                # Increase delay for next retry
                retry_delay = min(
                    retry_delay * self.config.backoff_multiplier,
                    self.config.max_retry_delay,
                )

        # Should not reach here, but just in case
        raise last_exception

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "rate_limit_hits": self.rate_limit_hits,
            "total_wait_time": round(self.total_wait_time, 2),
            "success_rate": round(
                (self.total_requests - self.failed_requests)
                / max(self.total_requests, 1)
                * 100,
                2,
            ),
        }

    def reset_stats(self):
        """Reset statistics counters."""
        self.total_requests = 0
        self.failed_requests = 0
        self.total_wait_time = 0.0
        self.rate_limit_hits = 0


def with_rate_limit(rate_limiter: RateLimiter):
    """
    Decorator to add rate limiting to a function.

    Usage:
        rate_limiter = RateLimiter()

        @with_rate_limit(rate_limiter)
        def make_api_call(param):
            return api.call(param)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return rate_limiter.with_retry(func, *args, **kwargs)

        return wrapper

    return decorator


def load_config(config_path: str) -> RateLimitConfig:
    """Load rate limit configuration from JSON file."""
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
        return RateLimitConfig(**data)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        return RateLimitConfig()
    except Exception as e:
        logger.error(f"Error loading config: {e}. Using defaults.")
        return RateLimitConfig()
