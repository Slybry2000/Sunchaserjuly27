import logging
import time
from enum import Enum
from typing import Optional, Type

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Simple circuit breaker for external service calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit."""
        if self.state != CircuitState.OPEN:
            return False

        if self.last_failure_time is None:
            return True

        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    def _record_success(self):
        """Record a successful call."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        logger.info("Circuit breaker reset to CLOSED state")

    def _record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker moving to HALF_OPEN state")
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e

    async def async_call(self, func, *args, **kwargs):
        """Execute async function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker moving to HALF_OPEN state")
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e

    @property
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self.state == CircuitState.OPEN


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""

    pass


# Global circuit breaker for Unsplash API
_unsplash_circuit_breaker: Optional[CircuitBreaker] = None


def get_unsplash_circuit_breaker() -> CircuitBreaker:
    """Get the global Unsplash circuit breaker."""
    global _unsplash_circuit_breaker
    if _unsplash_circuit_breaker is None:
        import os

        failure_threshold = int(
            os.environ.get("UNSPLASH_CIRCUIT_FAILURE_THRESHOLD", "5")
        )
        recovery_timeout = int(
            os.environ.get("UNSPLASH_CIRCUIT_RECOVERY_TIMEOUT", "60")
        )
        _unsplash_circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold, recovery_timeout=recovery_timeout
        )
        logger.info(
            "Initialized Unsplash circuit breaker: %d failures, %ds recovery",
            failure_threshold,
            recovery_timeout,
        )

    return _unsplash_circuit_breaker
