"""
Configuración centralizada de Sentry para MetodoBase.

Proporciona:
- Inicialización con integraciones FastAPI + SQLAlchemy + Logging
- Filtrado de eventos (validación, health checks)
- Contexto de usuario para traces
- Captura de errores de negocio
"""
import logging
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


logger = logging.getLogger("sentry_setup")


def init_sentry(
    dsn: str,
    environment: str,
    traces_rate: float,
    profiles_rate: float,
) -> None:
    """
    Inicializa Sentry con todas las integraciones.
    
    Args:
        dsn: Sentry DSN. Si está vacío, no se inicializa.
        environment: Ambiente (development, staging, production).
        traces_rate: Porcentaje de transacciones a capturar (0.0 - 1.0).
        profiles_rate: Porcentaje de profiles a capturar (0.0 - 1.0).
    """
    if not dsn:
        logger.info("Sentry DSN no configurado, observabilidad deshabilitada")
        return
    
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=traces_rate,
        profiles_sample_rate=profiles_rate,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.WARNING,
                event_level=logging.ERROR,
            ),
        ],
        before_send=_filter_events,
        before_send_transaction=_filter_transactions,
        send_default_pii=False,
    )
    logger.info("Sentry inicializado [env=%s, traces=%.2f]", environment, traces_rate)


# Errores a filtrar (no enviar a Sentry)
FILTERED_EXCEPTIONS = {
    "ValidationError",
    "RequestValidationError",
    "HTTPException",
    "StarletteHTTPException",
    "HTTPStatusError",
}


def _filter_events(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """
    Filtra eventos antes de enviar a Sentry.
    
    - Descarta errores de validación (RequestValidationError, ValidationError)
    - Descarta errores 4xx comunes que no son bugs
    """
    if "exception" in event:
        values = event.get("exception", {}).get("values", [])
        if values:
            exc_type = values[0].get("type", "")
            # No enviar errores de validación de Pydantic/FastAPI/HTTP
            if exc_type in FILTERED_EXCEPTIONS:
                return None
    return event


def _filter_transactions(
    event: dict[str, Any],
    hint: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Filtra transacciones antes de enviar a Sentry.
    
    - Descarta health checks y métricas para reducir ruido
    """
    transaction = event.get("transaction", "")
    # No enviar health checks ni métricas
    if transaction in (
        "/health",
        "/health/ready",
        "/metrics",
        "/alerts",
    ):
        return None
    return event


def set_user_context(user_id: str, gym_id: str, role: str) -> None:
    """
    Configura contexto de usuario para traces.
    
    Args:
        user_id: ID del usuario autenticado.
        gym_id: ID del gimnasio (tenant).
        role: Rol del usuario.
    """
    sentry_sdk.set_user({
        "id": user_id,
        "gym_id": gym_id,
        "role": role,
    })


def capture_business_error(message: str, extra: dict[str, Any] | None = None) -> None:
    """
    Captura errores de lógica de negocio como eventos de Sentry.
    
    Útil para errores que no son excepciones pero deben monitorearse.
    
    Args:
        message: Descripción del error.
        extra: Contexto adicional (user_id, plan_id, etc.).
    """
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level="error")
