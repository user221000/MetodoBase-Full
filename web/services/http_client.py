"""
web/services/http_client.py — Cliente HTTP con timeouts configurados.

Uso:
    from web.services.http_client import http_get, http_post
    
    response = http_get("https://api.example.com/data")
    response = http_post("https://api.example.com/data", json=payload)
"""
import requests
from web.settings import get_settings


def get_default_timeout() -> tuple[float, float]:
    """Retorna (connect_timeout, read_timeout)."""
    settings = get_settings()
    return (settings.HTTP_CONNECT_TIMEOUT, settings.HTTP_READ_TIMEOUT)


def http_get(url: str, timeout: tuple[float, float] | None = None, **kwargs):
    """GET con timeout por defecto."""
    timeout = timeout or get_default_timeout()
    return requests.get(url, timeout=timeout, **kwargs)


def http_post(url: str, timeout: tuple[float, float] | None = None, **kwargs):
    """POST con timeout por defecto."""
    timeout = timeout or get_default_timeout()
    return requests.post(url, timeout=timeout, **kwargs)
