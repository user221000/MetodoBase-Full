"""
api/exceptions.py — Excepciones tipadas para MetodoBase API.

Uso en routes:
    from api.exceptions import ClienteNoEncontradoError
    raise ClienteNoEncontradoError(id_cliente)

El handler global en api/app.py convierte estas excepciones en
respuestas JSON estructuradas con el campo 'error', 'message' y 'timestamp'.
"""
from __future__ import annotations
from datetime import datetime


class MetodoBaseException(Exception):
    """Excepción base; lleva un status_code HTTP y un mensaje legible."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "Error interno"):
        super().__init__(message)
        self.message = message
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "success": False,
            "error": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp,
        }


# ── 4xx — Errores del cliente ─────────────────────────────────────────────────

class ClienteNoEncontradoError(MetodoBaseException):
    """El ID de cliente no existe en la base de datos (HTTP 404)."""
    status_code = 404
    error_code = "CLIENTE_NOT_FOUND"

    def __init__(self, id_cliente: str = ""):
        super().__init__(
            f"Cliente '{id_cliente}' no encontrado" if id_cliente else "Cliente no encontrado"
        )


class DatosInvalidosError(MetodoBaseException):
    """Datos de entrada que no pasan validación de negocio (HTTP 422)."""
    status_code = 422
    error_code = "DATOS_INVALIDOS"

    def __init__(self, detalle: str = "Datos inválidos"):
        super().__init__(detalle)


class ClienteDuplicadoError(MetodoBaseException):
    """Intento de crear un cliente con datos que ya existen (HTTP 409)."""
    status_code = 409
    error_code = "CLIENTE_DUPLICADO"

    def __init__(self, campo: str = ""):
        msg = f"Ya existe un cliente con ese {campo}" if campo else "Cliente duplicado"
        super().__init__(msg)


class AutenticacionError(MetodoBaseException):
    """Credenciales inválidas o sesión expirada (HTTP 401)."""
    status_code = 401
    error_code = "AUTH_ERROR"

    def __init__(self, message: str = "No autorizado"):
        super().__init__(message)


# ── 5xx — Errores del servidor ────────────────────────────────────────────────

class GeneracionPlanError(MetodoBaseException):
    """Fallo durante la generación del plan nutricional (HTTP 500)."""
    status_code = 500
    error_code = "PLAN_GENERATION_ERROR"

    def __init__(self, detalle: str = "No se pudo generar el plan nutricional"):
        super().__init__(detalle)


class PDFGenerationError(MetodoBaseException):
    """Fallo durante la creación del archivo PDF (HTTP 500)."""
    status_code = 500
    error_code = "PDF_GENERATION_ERROR"

    def __init__(self, detalle: str = "No se pudo generar el PDF"):
        super().__init__(detalle)


class BaseDatosError(MetodoBaseException):
    """Error de persistencia en SQLite (HTTP 500)."""
    status_code = 500
    error_code = "DATABASE_ERROR"

    def __init__(self, detalle: str = "Error en base de datos"):
        super().__init__(detalle)
