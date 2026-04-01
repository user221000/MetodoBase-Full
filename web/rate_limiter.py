"""
web/rate_limiter.py — Rate limiting middleware (in-memory token bucket)

Protección contra abuso sin dependencias externas.
Migración a Redis: reemplazar _buckets dict por Redis INCR + EXPIRE.

Límites por defecto:
 - Login endpoints:     5 req/min  por IP  (anti brute-force)
 - Generación de plan: 10 req/min  por IP  (CPU-bound ~10s c/u)
 - API general:        60 req/min  por IP
 - Health / static:    sin límite
"""
import time
import threading
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


# ── Configuración de límites ─────────────────────────────────────────────────

RATE_RULES: list[dict] = [
    # Orden importa: la primera coincidencia gana
    {"path_prefix": "/health",            "limit": 0},      # 0 = sin límite
    {"path_prefix": "/static/",           "limit": 0},
    {"path_prefix": "/api/auth/refresh",  "limit": 10, "window": 60},
    {"path_prefix": "/api/auth/logout",   "limit": 5,  "window": 60},
    {"path_prefix": "/api/auth/login",    "limit": 5,  "window": 60},
    {"path_prefix": "/api/auth/registro", "limit": 5,  "window": 60},
    {"path_prefix": "/api/generar-plan",  "limit": 10, "window": 60},
    {"path_prefix": "/api/",              "limit": 60, "window": 60},
]

# Regla por defecto para rutas no listadas (HTML pages, etc.)
_DEFAULT_RULE = {"limit": 0}  # sin límite para páginas HTML


# ── Almacenamiento en memoria ────────────────────────────────────────────────

_buckets: dict[str, list[float]] = {}
_lock = threading.Lock()
_CLEANUP_INTERVAL = 300  # limpiar entradas viejas cada 5 min
_last_cleanup = time.monotonic()


def _get_client_ip(request: Request) -> str:
    """Extrae IP real considerando proxies (Railway, nginx).
    
    Uses TRUSTED_PROXY_COUNT to pick the correct hop from X-Forwarded-For,
    preventing spoofing by untrusted clients.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",")]
        try:
            from web.settings import get_settings
            proxy_count = get_settings().TRUSTED_PROXY_COUNT
        except Exception:
            proxy_count = 1
        idx = max(0, len(parts) - proxy_count)
        return parts[idx]
    if request.client:
        return request.client.host
    return "unknown"


def _match_rule(path: str) -> dict:
    """Devuelve la primera regla que coincida con el path."""
    for rule in RATE_RULES:
        if path.startswith(rule["path_prefix"]):
            return rule
    return _DEFAULT_RULE


def _cleanup_expired() -> None:
    """Elimina entradas con todos los timestamps expirados.
    
    MUST be called with _lock held.
    """
    global _last_cleanup
    now = time.monotonic()
    if now - _last_cleanup < _CLEANUP_INTERVAL:
        return
    _last_cleanup = now

    max_window = max((r.get("window", 60) for r in RATE_RULES), default=60)
    cutoff = now - max_window

    # Build list of expired keys first to avoid modifying dict during iteration
    expired_keys = [k for k, timestamps in _buckets.items()
                    if not timestamps or timestamps[-1] < cutoff]
    for k in expired_keys:
        _buckets.pop(k, None)
    
    # Also trim old timestamps from remaining buckets to prevent memory growth
    for k in list(_buckets.keys()):
        timestamps = _buckets.get(k)
        if timestamps:
            trimmed = [t for t in timestamps if t > cutoff]
            if trimmed:
                _buckets[k] = trimmed
            else:
                _buckets.pop(k, None)


def _is_allowed(key: str, limit: int, window: int) -> tuple[bool, dict]:
    """
    Verifica si la solicitud está permitida bajo el límite.
    Retorna (allowed, info) donde info tiene remaining y retry_after.
    """
    now = time.monotonic()
    cutoff = now - window

    with _lock:
        _cleanup_expired()

        timestamps = _buckets.get(key, [])
        # Descartar requests fuera de la ventana
        timestamps = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= limit:
            oldest = timestamps[0] if timestamps else now
            retry_after = int(oldest + window - now) + 1
            _buckets[key] = timestamps
            return False, {"remaining": 0, "retry_after": max(retry_after, 1)}

        timestamps.append(now)
        _buckets[key] = timestamps
        remaining = limit - len(timestamps)
        return True, {"remaining": remaining, "retry_after": 0}


# ── Middleware ────────────────────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware que aplica rate limiting por IP basado en path.
    Responde 429 con Retry-After cuando se excede el límite.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        rule = _match_rule(path)

        limit = rule.get("limit", 0)
        if limit == 0:
            return await call_next(request)

        window = rule.get("window", 60)
        client_ip = _get_client_ip(request)
        # Clave: IP + prefijo de ruta (no ruta exacta, para evitar bypass)
        bucket_key = f"{client_ip}:{rule['path_prefix']}"

        allowed, info = _is_allowed(bucket_key, limit, window)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Demasiadas solicitudes. Intenta de nuevo más tarde.",
                    "retry_after": info["retry_after"],
                },
                headers={
                    "Retry-After": str(info["retry_after"]),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        return response
