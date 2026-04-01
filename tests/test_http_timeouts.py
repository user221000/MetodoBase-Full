"""
tests/test_http_timeouts.py — Tests para configuración de timeouts HTTP.

Verifica que:
- Settings contiene constantes de timeout correctas
- http_client usa los timeouts por defecto de settings
"""
import pytest


def test_settings_has_timeout_constants():
    """Settings tiene las constantes de timeout HTTP."""
    from config.settings import get_settings
    
    settings = get_settings()
    
    assert settings.HTTP_CONNECT_TIMEOUT == 5.0
    assert settings.HTTP_READ_TIMEOUT == 30.0
    assert settings.STRIPE_TIMEOUT == 30.0
    assert settings.MERCADOPAGO_TIMEOUT == 30.0


def test_http_client_uses_default_timeout():
    """http_client retorna los timeouts de settings."""
    from web.services.http_client import get_default_timeout
    
    connect, read = get_default_timeout()
    
    assert connect == 5.0
    assert read == 30.0


def test_http_client_get_applies_timeout(monkeypatch):
    """http_get aplica timeout."""
    from web.services import http_client
    
    captured_kwargs = {}
    
    def mock_get(url, **kwargs):
        captured_kwargs.update(kwargs)
        class MockResponse:
            status_code = 200
        return MockResponse()
    
    monkeypatch.setattr("requests.get", mock_get)
    http_client.http_get("https://example.com")
    
    assert captured_kwargs["timeout"] == (5.0, 30.0)


def test_http_client_post_applies_timeout(monkeypatch):
    """http_post aplica timeout."""
    from web.services import http_client
    
    captured_kwargs = {}
    
    def mock_post(url, **kwargs):
        captured_kwargs.update(kwargs)
        class MockResponse:
            status_code = 200
        return MockResponse()
    
    monkeypatch.setattr("requests.post", mock_post)
    http_client.http_post("https://example.com", json={"test": 1})
    
    assert captured_kwargs["timeout"] == (5.0, 30.0)


def test_http_client_custom_timeout(monkeypatch):
    """http_get/post aceptan timeout personalizado."""
    from web.services import http_client
    
    captured_kwargs = {}
    
    def mock_get(url, **kwargs):
        captured_kwargs.update(kwargs)
        class MockResponse:
            status_code = 200
        return MockResponse()
    
    monkeypatch.setattr("requests.get", mock_get)
    custom_timeout = (2.0, 10.0)
    http_client.http_get("https://example.com", timeout=custom_timeout)
    
    assert captured_kwargs["timeout"] == custom_timeout
