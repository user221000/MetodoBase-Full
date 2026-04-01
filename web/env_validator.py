"""
web/env_validator.py — Re-export de validación de entorno.

Web importa desde aquí, no desde config/env_validator.py.
"""
from config.env_validator import validate_env_vars  # noqa: F401

__all__ = ["validate_env_vars"]
