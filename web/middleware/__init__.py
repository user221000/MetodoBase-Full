"""
web/middleware — Middlewares de seguridad y utilidades para FastAPI.

Todos los middlewares aquí son reutilizables entre api/ y web/.
"""
from .security_headers import SecurityHeadersMiddleware
from .request_id import RequestIDMiddleware
from .csrf import CSRFMiddleware, get_csrf_token, csrf_input_html
from .rate_limiter import (
    RateLimiterMiddleware,
    RateLimitExceeded,
    rate_limit_dependency,
    get_rate_limiter_metrics,
)
from .metrics import (
    MetricsMiddleware,
    get_metrics_summary,
    get_recent_errors,
    check_alerts as check_metrics_alerts,
)
from .alerting import (
    ErrorAlerter,
    AlertSeverity,
    AlertChannel,
    send_alert,
    track_error,
    get_error_alerter,
)
from .tenant import TenantMiddleware, get_current_tenant, current_tenant
# SentryContextMiddleware removido — usar web.auth_deps.with_sentry_context como dependency

__all__ = [
    # Security
    "SecurityHeadersMiddleware",
    "RequestIDMiddleware",
    "CSRFMiddleware",
    "get_csrf_token",
    "csrf_input_html",
    # Rate Limiting
    "RateLimiterMiddleware",
    "RateLimitExceeded",
    "rate_limit_dependency",
    "get_rate_limiter_metrics",
    # Metrics
    "MetricsMiddleware",
    "get_metrics_summary",
    "get_recent_errors",
    "check_metrics_alerts",
    # Alerting
    "ErrorAlerter",
    "AlertSeverity",
    "AlertChannel",
    "send_alert",
    "track_error",
    "get_error_alerter",
    # Tenant
    "TenantMiddleware",
    "get_current_tenant",
    "current_tenant",
]
