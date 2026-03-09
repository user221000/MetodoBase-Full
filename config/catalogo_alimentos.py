"""
Catálogo centralizado de alimentos — Fuente Única de Verdad (Single Source of Truth).

Todos los módulos que necesiten listas de alimentos por categoría DEBEN importar
desde aquí. Las listas se derivan dinámicamente de src.alimentos_base.CATEGORIAS
para garantizar coherencia.
"""

from src.alimentos_base import CATEGORIAS, ALIMENTOS_BASE


# ---------------------------------------------------------------------------
# Listas canónicas por categoría (derivadas de CATEGORIAS)
# ---------------------------------------------------------------------------

PROTEINAS: list[str] = list(CATEGORIAS.get('proteina', []))
CARBS: list[str] = list(CATEGORIAS.get('carbs', []))
GRASAS: list[str] = list(CATEGORIAS.get('grasa', []))
VERDURAS: list[str] = list(CATEGORIAS.get('verdura', []))
FRUTAS: list[str] = list(CATEGORIAS.get('fruta', []))

# Sets equivalentes (para búsquedas O(1))
PROTEINAS_SET: set[str] = set(PROTEINAS)
CARBS_SET: set[str] = set(CARBS)
GRASAS_SET: set[str] = set(GRASAS)
VERDURAS_SET: set[str] = set(VERDURAS)
FRUTAS_SET: set[str] = set(FRUTAS)

# Mapa tipo -> lista (útil para iteración genérica)
CATALOGO_POR_TIPO: dict[str, list[str]] = {
    'proteina': PROTEINAS,
    'carbs': CARBS,
    'grasa': GRASAS,
    'verdura': VERDURAS,
    'fruta': FRUTAS,
}

# Mapa tipo -> set
CATALOGO_SETS: dict[str, set[str]] = {
    'proteina': PROTEINAS_SET,
    'carbs': CARBS_SET,
    'grasa': GRASAS_SET,
    'verdura': VERDURAS_SET,
    'fruta': FRUTAS_SET,
}


def categoria_de(alimento: str) -> str | None:
    """Devuelve la categoría ('proteina', 'carbs', 'grasa', …) de un alimento, o None."""
    for tipo, items in CATALOGO_SETS.items():
        if alimento in items:
            return tipo
    return None
