import pytest
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState


class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker("test", failure_threshold=3)

        def failing_func():
            raise ValueError("Simulated failure")

        for _ in range(3):
            try:
                cb.call(failing_func)
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

    def test_rejects_calls_when_open(self):
        cb = CircuitBreaker("test", failure_threshold=1)

        def failing_func():
            raise ValueError("fail")

        try:
            cb.call(failing_func)
        except ValueError:
            pass

        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: None)

    def test_successful_calls_reset_failure_count(self):
        cb = CircuitBreaker("test", failure_threshold=5)
        cb.call(lambda: "ok")
        assert cb._failure_count == 0

    def test_get_status(self):
        cb = CircuitBreaker("test-svc")
        status = cb.get_status()
        assert status["name"] == "test-svc"
        assert "state" in status
        assert "failure_count" in status
