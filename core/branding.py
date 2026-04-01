"""
Gestor de branding configurable por gimnasio.

Lee ``config/branding.json`` y expone los valores con soporte para
*dot-notation*::

    from core.branding import branding
    branding.get('colores.primario')      # '#FFEB3B'
    branding.get('nombre_gym')            # 'Mi Gimnasio'
"""

import json
from pathlib import Path
from typing import Any, Optional

from config.constantes import CARPETA_CONFIG, resource_path


class GestorBranding:
    """Lee / escribe la configuración de branding del gimnasio."""

    ARCHIVO_BRANDING = str(Path(CARPETA_CONFIG) / "branding.json")
    # Tema visual fijo: Yellow Neon Premium (Black & Yellow)
    # Los colores de la interfaz los gobierna design_system/tokens.py
    # y el QSS amarillo_neon.qss. Estos valores solo afectan PDFs/branding.
    TEMA_VISUAL = "Yellow Neon Premium"
    COLORES_FIJOS: dict[str, str] = {
        "primario": "#FFEB3B",
        "primario_hover": "#FDD835",
        "secundario": "#FFD700",
        "secundario_hover": "#F9A825",
        "pdf_color": "#FFEB3B",
    }

    DEFAULTS: dict = {
        "nombre_gym": "",
        "nombre_corto": "Método Base",
        "tagline": "Powered by Consultoría Hernández",
        "tema_visual": "Yellow Neon Premium",
        "colores": {
            "primario": "#FFEB3B",
            "primario_hover": "#FDD835",
            "secundario": "#FFD700",
            "secundario_hover": "#F9A825",
        },
        "contacto": {
            "telefono": "",
            "email": "",
            "direccion": "",
            "direccion_linea1": "",
            "direccion_linea2": "",
            "direccion_linea3": "",
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
            "logo_path": "assets/logo.png",
            "mostrar_contacto": True,
            "color_encabezado": "#FFEB3B",
        },
        "alimentos": {
            "excluidos": [],
        },
        "cuota_mensual": 800,
        "whatsapp": {
            "mensaje_plan": (
                "Hola {nombre} 👋\n\n"
                "Tu plan personalizado de {nombre_gym} ya está listo.\n"
                "Adjunto encontrarás tu plan alimenticio.\n"
                "Cualquier duda consúltala con tu entrenador.\n"
                "{nombre_gym} agradece tu preferencia y te espera el próximo mes con tu plan actualizado.\n"
                "📞 {telefono_gym}"
            ),
        },
    }

    def __init__(self) -> None:
        self.ruta = Path(self.ARCHIVO_BRANDING)
        self.config: dict = self._cargar_config()
        self._migrar_a_neon_premium()

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------

    def _migrar_a_neon_premium(self) -> None:
        """Fuerza los colores del interfaz al tema Yellow Neon Premium.

        Limpia claves sueltas que temas legacy dejaron a nivel raíz
        (primario, secundario, pdf_color, neutral_*) y sobreescribe
        colores.primario / colores.secundario con los valores fijos.
        """
        changed = False

        # Limpiar claves legacy a nivel raíz
        _LEGACY_KEYS = (
            "primario", "primario_hover", "secundario", "secundario_hover",
            "pdf_color", "neutral_bg", "neutral_card", "neutral_text",
        )
        for k in _LEGACY_KEYS:
            if k in self.config:
                del self.config[k]
                changed = True

        # Forzar tema visual
        if self.config.get("tema_visual") != self.TEMA_VISUAL:
            self.config["tema_visual"] = self.TEMA_VISUAL
            changed = True

        # Forzar colores a neon premium
        colores = self.config.setdefault("colores", {})
        for key, val in self.COLORES_FIJOS.items():
            if key == "pdf_color":
                continue  # pdf_color va en pdf.color_encabezado
            if colores.get(key) != val:
                colores[key] = val
                changed = True

        # Forzar color PDF si es legacy
        pdf = self.config.setdefault("pdf", {})
        if pdf.get("color_encabezado") not in ("#FFEB3B", ""):
            pdf["color_encabezado"] = "#FFEB3B"
            changed = True

        if changed:
            self._guardar(self.config)

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

    def _resolver_ruta(self, ruta: str | None) -> Optional[Path]:
        if not ruta:
            return None
        p = Path(ruta).expanduser()
        if p.exists():
            return p
        p_resource = Path(resource_path(ruta))
        if p_resource.exists():
            return p_resource
        return None

    def obtener_logo_path(self) -> Optional[Path]:
        """Logo general de branding (UI/watermark)."""
        candidatos = [
            self.get("logo.path", "assets/logo.png"),
            "assets/logo.png",
        ]
        for candidato in candidatos:
            resuelto = self._resolver_ruta(candidato)
            if resuelto:
                return resuelto
        return None

    def obtener_logo_pdf_path(self) -> Optional[Path]:
        """Logo para esquina superior derecha de PDF."""
        candidatos = [
            self.get("pdf.logo_path", ""),
            self.get("logo.path", "assets/logo.png"),
            "assets/logo.png",
        ]
        for candidato in candidatos:
            resuelto = self._resolver_ruta(candidato)
            if resuelto:
                return resuelto
        return None

    def obtener_fondo_login_path(self) -> Optional[Path]:
        """
        Ruta de la imagen de fondo para la pantalla de login.

        Busca en orden:
          1. ``login.fondo_path``  (configurable en branding.json)
          2. ``assets/FONDO.PNG``  (imagen incluida por defecto en el repo)
          3. ``assets/login_background.png`` (alias alternativo)
        """
        candidatos = [
            self.get("login.fondo_path", ""),
            "assets/FONDO.PNG",
            "assets/login_background.png",
        ]
        for candidato in candidatos:
            resuelto = self._resolver_ruta(candidato)
            if resuelto:
                return resuelto
        return None

    def obtener_colores_fijos(self) -> dict[str, str]:
        """Retorna los colores fijos del tema Yellow Neon Premium."""
        return self.COLORES_FIJOS.copy()


# Instancia global lista para importar
branding = GestorBranding()
