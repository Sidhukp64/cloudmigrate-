"""
Circuit Breaker implementation for external service calls (S3, SFTP, webhooks).
States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing recovery)
"""
import time
import threading
from enum import Enum
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # Failing — reject calls immediately
    HALF_OPEN = "HALF_OPEN" # Testing if service recovered


class CircuitBreaker:
    """
    Thread-safe circuit breaker.

    Args:
        name: Human-readable service name
        failure_threshold: Failures before OPEN
        recovery_timeout: Seconds before trying HALF_OPEN
        success_threshold: Successes in HALF_OPEN before CLOSED
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info(f"[CircuitBreaker:{self.name}] Transitioning OPEN → HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
            return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        state = self.state
        if state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(f"Circuit breaker [{self.name}] is OPEN — rejecting call")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise exc

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    logger.info(f"[CircuitBreaker:{self.name}] Transitioning HALF_OPEN → CLOSED")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            else:
                self._failure_count = 0

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                logger.warning(f"[CircuitBreaker:{self.name}] Transitioning CLOSED → OPEN after {self._failure_count} failures")
                self._state = CircuitState.OPEN

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
        }


class CircuitBreakerOpenError(Exception):
    pass


# Global circuit breakers for external services
s3_circuit_breaker = CircuitBreaker("AWS-S3", failure_threshold=5, recovery_timeout=30)
sftp_circuit_breaker = CircuitBreaker("SFTP", failure_threshold=3, recovery_timeout=60)
webhook_circuit_breaker = CircuitBreaker("Webhooks", failure_threshold=10, recovery_timeout=120)
