"""
web/dependencies.py — Funciones compartidas para la app web.

Re-exporta build_cliente_from_dict para que web/ no dependa directamente de api/.
"""
from api.dependencies import build_cliente_from_dict  # noqa: F401

__all__ = ["build_cliente_from_dict"]
