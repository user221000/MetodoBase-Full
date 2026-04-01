"""
web/settings.py — Re-export de configuración web.

Web importa desde aquí, no desde config/settings.py.
Esto desacopla la app web del paquete config/ compartido.
"""
from config.settings import Settings, get_settings  # noqa: F401

__all__ = ["Settings", "get_settings"]
