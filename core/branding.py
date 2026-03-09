"""
Gestor de branding configurable por gimnasio.

Lee ``config/branding.json`` y expone los valores con soporte para
*dot-notation*::

    from core.branding import branding
    branding.get('colores.primario')      # '#9B4FB0'
    branding.get('nombre_gym')            # 'Fitness Gym Real del Valle'
"""

import json
from pathlib import Path
from typing import Any, Optional


class GestorBranding:
    """Lee / escribe la configuración de branding del gimnasio."""

    ARCHIVO_BRANDING = "config/branding.json"

    DEFAULTS: dict = {
        "nombre_gym": "",
        "nombre_corto": "Método Base",
        "tagline": "Powered by Consultoría Hernández",
        "colores": {
            "primario": "#9B4FB0",
            "primario_hover": "#B565C6",
            "secundario": "#D4A84B",
            "secundario_hover": "#E4B85B",
        },
        "contacto": {
            "telefono": "",
            "email": "",
            "direccion": "",
            "whatsapp": "",
        },
        "redes_sociales": {
            "facebook": "",
            "instagram": "",
            "tiktok": "",
        },
        "logo": {
            "path": "assets/logo.png",
            "mostrar_watermark": True,
        },
        "pdf": {
            "mostrar_logo": True,
            "mostrar_contacto": True,
            "color_encabezado": "#9B4FB0",
        },
    }

    def __init__(self) -> None:
        self.ruta = Path(self.ARCHIVO_BRANDING)
        self.config: dict = self._cargar_config()

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------

    def _cargar_config(self) -> dict:
        if not self.ruta.exists():
            self._guardar(self.DEFAULTS)
            return self.DEFAULTS.copy()
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                return self._merge(self.DEFAULTS, json.load(f))
        except Exception:
            return self.DEFAULTS.copy()

    @staticmethod
    def _merge(base: dict, updates: dict) -> dict:
        result = base.copy()
        for k, v in updates.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = GestorBranding._merge(result[k], v)
            else:
                result[k] = v
        return result

    def _guardar(self, data: dict) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Acceso
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Acceso con *dot-notation*: ``branding.get('colores.primario')``."""
        cur: Any = self.config
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur

    def set(self, key: str, value: Any) -> bool:
        """Establece un valor y persiste el JSON."""
        parts = key.split(".")
        cur = self.config
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = value
        return self.guardar()

    def guardar(self) -> bool:
        try:
            self._guardar(self.config)
            return True
        except Exception:
            return False

    def recargar(self) -> None:
        self.config = self._cargar_config()

    def obtener_logo_path(self) -> Optional[Path]:
        p = Path(self.get("logo.path", "assets/logo.png"))
        if p.exists():
            return p
        fallback = Path("assets/logo.png")
        return fallback if fallback.exists() else None


# Instancia global lista para importar
branding = GestorBranding()
