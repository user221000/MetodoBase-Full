"""
web/rate_limiter_redis.py — Redis-backed rate limiting middleware.

Drop-in replacement for the in-memory RateLimitMiddleware when REDIS_URL is set.
Uses redis.asyncio for non-blocking calls with atomic MULTI/EXEC pipelines.

Key format: rl:{client_ip}:{path_prefix}
TTL: window_seconds (auto-expires keys)
"""
import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from web.rate_limiter import RATE_RULES, _DEFAULT_RULE, _get_client_ip, _match_rule

logger = logging.getLogger(__name__)

_redis_pool = None


async def _get_redis():
    """Lazy-init Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        import redis.asyncio as aioredis
        from web.settings import get_settings
        url = getattr(get_settings(), "REDIS_URL", "")
        if not url:
            raise RuntimeError("REDIS_URL not configured")
        _redis_pool = aioredis.from_url(url, decode_responses=True)
    return _redis_pool


async def _is_allowed_redis(key: str, limit: int, window: int) -> tuple[bool, dict]:
    """Atomic check-and-increment using Redis pipeline."""
    r = await _get_redis()
    async with r.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, window)
        results = await pipe.execute()

    current = results[0]  # INCR returns the new value

    if current > limit:
        ttl = await r.ttl(key)
        retry_after = max(ttl, 1)
        return False, {"remaining": 0, "retry_after": retry_after}

    remaining = limit - current
    return True, {"remaining": remaining, "retry_after": 0}


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware backed by Redis for multi-pod deployments."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        rule = _match_rule(path)

        limit = rule.get("limit", 0)
        if limit == 0:
            return await call_next(request)

        window = rule.get("window", 60)
        client_ip = _get_client_ip(request)
        bucket_key = f"rl:{client_ip}:{rule['path_prefix']}"

        try:
            allowed, info = await _is_allowed_redis(bucket_key, limit, window)
        except Exception:
            logger.warning("Redis rate limiter unavailable, allowing request")
            return await call_next(request)

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
