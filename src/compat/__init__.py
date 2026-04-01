"""
src/compat — Capas de compatibilidad para migración gradual.

Permite usar nuevas implementaciones (Repository pattern) sin
romper código legacy que depende de interfaces antiguas.
"""

from src.compat.gestor_bd_compat import GestorBDCompat, get_gestor_compat

__all__ = [
    "GestorBDCompat",
    "get_gestor_compat",
]
