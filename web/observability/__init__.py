"""
web/observability — Observabilidad centralizada para MetodoBase.
"""
from .sentry_setup import (
    init_sentry,
    set_user_context,
    capture_business_error,
)

__all__ = [
    "init_sentry",
    "set_user_context",
    "capture_business_error",
]
