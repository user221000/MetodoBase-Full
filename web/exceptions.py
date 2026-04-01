"""
web/exceptions.py — Excepciones para la app web.

Re-exporta desde api/exceptions.py para que web/ no dependa directamente de api/.
"""
from api.exceptions import MetodoBaseException  # noqa: F401

__all__ = ["MetodoBaseException"]
