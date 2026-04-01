"""
web/schemas.py — Esquemas Pydantic para la app web.

Re-exporta desde api/schemas.py para que web/ no dependa directamente de api/.
"""
from api.schemas import ClienteCreate, ClienteUpdate, PlanRequest  # noqa: F401

__all__ = ["ClienteCreate", "ClienteUpdate", "PlanRequest"]
