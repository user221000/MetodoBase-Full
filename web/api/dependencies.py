"""Dependencias compartidas: inyección de BD, autenticación básica."""
import sys
from pathlib import Path
from functools import lru_cache

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.gestor_bd import GestorBDClientes


@lru_cache(maxsize=1)
def obtener_gestor_bd() -> GestorBDClientes:
    """Retorna una instancia singleton del gestor de BD (sin modo seguro para la web)."""
    return GestorBDClientes()
