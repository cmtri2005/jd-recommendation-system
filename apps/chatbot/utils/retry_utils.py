"""Retry utilities with exponential backoff for LLM calls."""

import time
import functools
from typing import Callable, TypeVar, Any
from logging import Logger

T = TypeVar("T")


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    logger: Logger = None,
):
    """Decorator to retry function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        exponential_base: Base for exponential backoff
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry
        logger: Optional logger for logging retry attempts

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        if logger:
                            logger.error(
                                f"Function {func.__name__} failed after {max_retries} retries: {e}"
                            )
                        raise

                    if logger:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )

                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)

            raise last_exception

        return wrapper

    return decorator


def should_retry_llm_error(exception: Exception) -> bool:
    """Determine if an LLM error should be retried.

    Common retryable errors:
    - Rate limit errors
    - Timeout errors
    - Temporary service unavailability

    Args:
        exception: The exception to check

    Returns:
        True if error should be retried, False otherwise
    """
    error_msg = str(exception).lower()

    retryable_patterns = [
        "rate limit",
        "too many requests",
        "429",
        "timeout",
        "timed out",
        "503",
        "service unavailable",
        "temporarily unavailable",
        "throttling",
        "quota exceeded",
    ]

    return any(pattern in error_msg for pattern in retryable_patterns)
