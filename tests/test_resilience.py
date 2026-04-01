"""
tests/test_resilience.py — Tests para Circuit Breaker y Retry con backoff.

Verifica:
- CircuitBreaker: transiciones de estado, thread safety, reset
- retry_with_backoff: reintentos, backoff exponencial, jitter
- is_retryable: clasificación de errores
"""
import threading
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from web.services.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    is_retryable,
    retry_with_backoff,
    RETRYABLE_STATUS_CODES,
)


# ══════════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestCircuitBreaker:
    """Tests para CircuitBreaker pattern."""

    def test_starts_closed(self):
        """Circuit breaker inicia en estado CLOSED."""
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_transitions_to_open_after_failures(self):
        """Después de N fallos consecutivos, transiciona a OPEN."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)

        def failing_func():
            raise ConnectionError("Network error")

        # Simular 3 fallos
        for _ in range(3):
            with pytest.raises(ConnectionError):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN
        assert cb._failure_count == 3

    def test_transitions_to_half_open_after_timeout(self):
        """Después del recovery_timeout, transiciona a HALF_OPEN."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        cb = CircuitBreaker("test", config)

        def failing_func():
            raise ConnectionError("Network error")

        # Forzar apertura
        for _ in range(2):
            with pytest.raises(ConnectionError):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Esperar recovery timeout
        time.sleep(0.15)

        # Ahora debería estar en HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN

    def test_closes_on_success_in_half_open(self):
        """Si la llamada de prueba en HALF_OPEN tiene éxito, cierra el circuito."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        cb = CircuitBreaker("test", config)

        call_count = 0

        def sometimes_failing_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Network error")
            return "success"

        # Forzar apertura
        for _ in range(2):
            with pytest.raises(ConnectionError):
                cb.call(sometimes_failing_func)

        assert cb.state == CircuitState.OPEN

        # Esperar recovery timeout
        time.sleep(0.15)

        # La siguiente llamada debería tener éxito y cerrar el circuito
        result = cb.call(sometimes_failing_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self):
        """Si la llamada de prueba en HALF_OPEN falla, reabre el circuito."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        cb = CircuitBreaker("test", config)

        def always_failing_func():
            raise ConnectionError("Network error")

        # Forzar apertura
        for _ in range(2):
            with pytest.raises(ConnectionError):
                cb.call(always_failing_func)

        assert cb.state == CircuitState.OPEN

        # Esperar recovery timeout
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        # La llamada de prueba falla, debe reabrir
        with pytest.raises(ConnectionError):
            cb.call(always_failing_func)

        assert cb.state == CircuitState.OPEN

    def test_circuit_open_error_includes_retry_after(self):
        """CircuitOpenError incluye el tiempo de retry_after."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=30.0)
        cb = CircuitBreaker("test_circuit", config)

        def failing_func():
            raise ConnectionError("Network error")

        # Forzar apertura
        for _ in range(2):
            with pytest.raises(ConnectionError):
                cb.call(failing_func)

        # Intentar llamar con circuito abierto
        with pytest.raises(CircuitOpenError) as exc_info:
            cb.call(lambda: None)

        error = exc_info.value
        assert error.name == "test_circuit"
        assert 0 < error.retry_after <= 30.0
        assert "test_circuit" in str(error)
        assert "Retry after" in str(error)

    def test_thread_safety(self):
        """El circuit breaker es thread-safe."""
        config = CircuitBreakerConfig(failure_threshold=50)
        cb = CircuitBreaker("thread_test", config)
        errors = []
        call_count = 0
        lock = threading.Lock()

        def increment_func():
            nonlocal call_count
            with lock:
                call_count += 1
            return call_count

        def worker():
            try:
                for _ in range(100):
                    cb.call(increment_func)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert call_count == 1000  # 10 threads * 100 calls

    def test_reset(self):
        """reset() devuelve el circuit breaker a estado inicial."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("test", config)

        def failing_func():
            raise ConnectionError("Network error")

        # Forzar apertura
        for _ in range(2):
            with pytest.raises(ConnectionError):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Reset
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_get_status(self):
        """get_status() retorna información para monitoreo."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker("status_test", config)

        def failing_func():
            raise ConnectionError("Network error")

        # Generar algunos fallos
        for _ in range(2):
            with pytest.raises(ConnectionError):
                cb.call(failing_func)

        status = cb.get_status()

        assert status["name"] == "status_test"
        assert status["state"] == "closed"  # Aún no llega al threshold
        assert status["failure_count"] == 2
        assert status["failure_threshold"] == 5


# ══════════════════════════════════════════════════════════════════════════════
# RETRY WITH BACKOFF TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestRetryWithBackoff:
    """Tests para retry_with_backoff decorador."""

    def test_retries_on_connection_error(self):
        """Reintenta en errores de conexión."""
        attempt_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01, max_delay=0.05)
        def flaky_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Network error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert attempt_count == 3

    def test_retries_on_timeout_error(self):
        """Reintenta en errores de timeout."""
        attempt_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01, max_delay=0.05)
        def timeout_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise TimeoutError("Request timeout")
            return "done"

        result = timeout_func()
        assert result == "done"
        assert attempt_count == 2

    def test_retries_on_5xx_status(self):
        """Reintenta en errores HTTP 5xx."""
        attempt_count = 0

        class MockError(Exception):
            http_status = 503

        @retry_with_backoff(max_retries=2, initial_delay=0.01, max_delay=0.05)
        def server_error_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise MockError("Service unavailable")
            return "recovered"

        result = server_error_func()
        assert result == "recovered"
        assert attempt_count == 2

    def test_no_retry_on_4xx_status(self):
        """No reintenta en errores HTTP 4xx."""
        attempt_count = 0

        class ClientError(Exception):
            http_status = 400

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def client_error_func():
            nonlocal attempt_count
            attempt_count += 1
            raise ClientError("Bad request")

        with pytest.raises(ClientError):
            client_error_func()

        # Solo un intento, sin reintentos
        assert attempt_count == 1

    def test_no_retry_on_circuit_open(self):
        """No reintenta cuando el circuit breaker está abierto."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=30.0)
        cb = CircuitBreaker("no_retry_test", config)

        # Abrir el circuito
        def force_open():
            raise ConnectionError("Force open")

        with pytest.raises(ConnectionError):
            cb.call(force_open)

        attempt_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01, circuit=cb)
        def protected_func():
            nonlocal attempt_count
            attempt_count += 1
            return "success"

        with pytest.raises(CircuitOpenError):
            protected_func()

        # Sin intentos porque el circuito está abierto
        assert attempt_count == 0

    def test_backoff_exponential(self):
        """El delay aumenta exponencialmente."""
        delays = []
        attempt_count = 0

        original_sleep = time.sleep

        def mock_sleep(delay):
            delays.append(delay)
            # No hacer sleep real para acelerar test

        @retry_with_backoff(
            max_retries=3,
            initial_delay=1.0,
            max_delay=100.0,
            exponential_base=2.0,
            jitter=0,  # Sin jitter para test determinista
        )
        def always_fails():
            nonlocal attempt_count
            attempt_count += 1
            raise ConnectionError("Error")

        with patch("web.services.resilience.time.sleep", mock_sleep):
            with pytest.raises(ConnectionError):
                always_fails()

        # 3 retries = 3 delays
        assert len(delays) == 3
        # Sin jitter: delays deberían ser 1, 2, 4
        assert delays[0] == pytest.approx(1.0, rel=0.01)
        assert delays[1] == pytest.approx(2.0, rel=0.01)
        assert delays[2] == pytest.approx(4.0, rel=0.01)

    def test_jitter_applied(self):
        """Se aplica jitter al delay."""
        delays = []

        def mock_sleep(delay):
            delays.append(delay)

        @retry_with_backoff(
            max_retries=10,
            initial_delay=1.0,
            max_delay=100.0,
            exponential_base=1.0,  # Sin exponencial para aislar jitter
            jitter=0.5,  # 50% jitter
        )
        def always_fails():
            raise ConnectionError("Error")

        with patch("web.services.resilience.time.sleep", mock_sleep):
            with pytest.raises(ConnectionError):
                always_fails()

        # Con jitter, los delays deberían variar
        # Base es 1.0, jitter de 50% significa rango [0.5, 1.5]
        assert all(0.5 <= d <= 1.5 for d in delays)
        # Y no deberían ser todos iguales (probabilísticamente)
        if len(delays) >= 5:
            assert len(set(round(d, 4) for d in delays)) > 1

    def test_max_delay_respected(self):
        """El delay nunca excede max_delay."""
        delays = []

        def mock_sleep(delay):
            delays.append(delay)

        @retry_with_backoff(
            max_retries=5,
            initial_delay=1.0,
            max_delay=3.0,
            exponential_base=10.0,  # Crecimiento muy rápido
            jitter=0,
        )
        def always_fails():
            raise ConnectionError("Error")

        with patch("web.services.resilience.time.sleep", mock_sleep):
            with pytest.raises(ConnectionError):
                always_fails()

        # Todos los delays deberían estar <= max_delay
        assert all(d <= 3.0 for d in delays)


# ══════════════════════════════════════════════════════════════════════════════
# IS_RETRYABLE TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestIsRetryable:
    """Tests para is_retryable helper."""

    def test_connection_error_retryable(self):
        """ConnectionError es retryable."""
        error = ConnectionError("Connection refused")
        assert is_retryable(error) is True

    def test_timeout_error_retryable(self):
        """TimeoutError es retryable."""
        error = TimeoutError("Request timeout")
        assert is_retryable(error) is True

    def test_500_status_retryable(self):
        """Error con http_status 500 es retryable."""

        class APIError(Exception):
            http_status = 500

        assert is_retryable(APIError("Server error")) is True

    def test_400_status_not_retryable(self):
        """Error con http_status 400 no es retryable."""

        class ClientError(Exception):
            http_status = 400

        assert is_retryable(ClientError("Bad request")) is False

    def test_stripe_error_with_500_retryable(self):
        """Error de Stripe con http_status 500+ es retryable."""

        class StripeError(Exception):
            """Mock de stripe.error.APIError."""
            def __init__(self, message, http_status):
                super().__init__(message)
                self.http_status = http_status

        assert is_retryable(StripeError("Server error", 500)) is True
        assert is_retryable(StripeError("Gateway timeout", 502)) is True
        assert is_retryable(StripeError("Service unavailable", 503)) is True
        assert is_retryable(StripeError("Rate limited", 429)) is True

    def test_os_error_retryable(self):
        """OSError (incluyendo network errors) es retryable."""
        error = OSError("Network unreachable")
        assert is_retryable(error) is True

    def test_value_error_not_retryable(self):
        """ValueError no es retryable."""
        error = ValueError("Invalid input")
        assert is_retryable(error) is False

    def test_generic_exception_not_retryable(self):
        """Exception genérica no es retryable."""
        error = Exception("Something went wrong")
        assert is_retryable(error) is False

    def test_response_with_5xx_status_retryable(self):
        """Error con response.status_code 5xx es retryable."""

        class MockResponse:
            status_code = 503

        class HTTPError(Exception):
            def __init__(self):
                self.response = MockResponse()

        assert is_retryable(HTTPError()) is True

    def test_response_with_4xx_status_not_retryable(self):
        """Error con response.status_code 4xx no es retryable."""

        class MockResponse:
            status_code = 404

        class HTTPError(Exception):
            def __init__(self):
                self.response = MockResponse()

        assert is_retryable(HTTPError()) is False
