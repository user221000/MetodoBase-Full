"""
web/catalogo.py — Re-export del catálogo de alimentos para la app web.

Web importa desde aquí, no desde config/catalogo_alimentos.py.
"""
from config.catalogo_alimentos import (  # noqa: F401
    CATALOGO_POR_TIPO,
    CATEGORIAS,
    _refrescar_lista,
)

__all__ = ["CATALOGO_POR_TIPO", "CATEGORIAS", "_refrescar_lista"]
