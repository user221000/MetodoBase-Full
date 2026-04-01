# -*- coding: utf-8 -*-
"""
utils/iconos.py — Diccionario de iconografía multiplataforma (Agente 5).

Proporciona íconos Unicode (emoji) y equivalentes Qt (QStyle.StandardPixmap)
para su uso uniforme en botones de la plataforma desktop PySide6.

Uso rápido::

    from utils.iconos import ICONOS_EMOJI, obtener_icono_qt, aplicar_icono_btn

    # Emoji en cualquier plataforma
    label = "🗑️ Eliminar"

    # Ícono Qt
    from PySide6.QtWidgets import QPushButton
    btn = QPushButton()
    aplicar_icono_btn(btn, "borrar")
    btn.setToolTip(TOOLTIP.get("borrar", ""))

Nota de seguridad:
  · Esta función no carga archivos arbitrarios de rutas externas.
  · Solo usa QStyle.StandardPixmap e íconos del sistema o emojis.
"""
from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Diccionario principal: nombre → emojis
# ---------------------------------------------------------------------------

ICONOS_EMOJI: dict[str, str] = {
    # Gestión de datos
    "borrar":          "🗑️",
    "editar":          "✏️",
    "guardar":         "💾",
    "nuevo":           "➕",
    "buscar":          "🔍",
    "filtrar":         "🔽",
    "exportar":        "📤",
    "importar":        "📥",
    "copiar":          "📋",
    "refrescar":       "🔄",
    "deshacer":        "↩️",
    "rehacer":         "↪️",

    # Usuarios y sesión
    "usuario":         "👤",
    "usuarios":        "👥",
    "gym":             "🏢",
    "login":           "🔐",
    "logout":          "🚪",
    "perfil":          "🧑",
    "password":        "🔑",

    # Planes nutricionales
    "generar_plan":    "📋",
    "plan":            "🥗",
    "alimento":        "🍎",
    "calorias":        "🔥",
    "proteina":        "💪",
    "progreso":        "📈",

    # Gimnasio
    "clientes":        "👥",
    "suscripcion":     "💳",
    "clases":          "🗓️",
    "instructores":    "🏋️",
    "facturacion":     "💰",
    "reportes":        "📊",
    "dashboard":       "📊",

    # PDF / exportación
    "pdf":             "📄",
    "imprimir":        "🖨️",
    "abrir_carpeta":   "📂",
    "vista_previa":    "👁️",

    # Estado / feedback
    "exito":           "✅",
    "error":           "❌",
    "advertencia":     "⚠️",
    "info":            "ℹ️",
    "cargando":        "⏳",

    # Navegación
    "volver":          "←",
    "siguiente":       "→",
    "arriba":          "↑",
    "abajo":           "↓",
    "configuracion":   "⚙️",
    "ayuda":           "❓",
    "cerrar":          "✕",
}

# ---------------------------------------------------------------------------
# Tooltips descriptivos para cada ícono
# ---------------------------------------------------------------------------

TOOLTIP: dict[str, str] = {
    "borrar":          "Eliminar permanentemente",
    "editar":          "Editar este elemento",
    "guardar":         "Guardar cambios",
    "nuevo":           "Crear nuevo elemento",
    "buscar":          "Buscar",
    "filtrar":         "Aplicar filtros",
    "exportar":        "Exportar datos",
    "importar":        "Importar datos",
    "copiar":          "Copiar al portapapeles",
    "refrescar":       "Actualizar datos",
    "generar_plan":    "Generar plan nutricional",
    "plan":            "Ver plan nutricional",
    "clientes":        "Gestión de clientes",
    "suscripcion":     "Gestión de suscripciones",
    "pdf":             "Generar PDF",
    "imprimir":        "Imprimir",
    "vista_previa":    "Vista previa",
    "abrir_carpeta":   "Abrir carpeta de archivos",
    "logout":          "Cerrar sesión",
    "configuracion":   "Configuración",
    "exito":           "Operación exitosa",
    "error":           "Error en la operación",
    "advertencia":     "Advertencia",
}

# ---------------------------------------------------------------------------
# Mapa a QStyle.StandardPixmap (para ícono Qt nativo)
# ---------------------------------------------------------------------------

# Importación diferida para no requerir PySide6 en entornos de testing puro
_QT_ICONOS: Optional[dict] = None


def _cargar_qt_iconos() -> dict:
    """Carga el mapa nombre→StandardPixmap la primera vez que se necesita."""
    global _QT_ICONOS
    if _QT_ICONOS is not None:
        return _QT_ICONOS

    try:
        from PySide6.QtWidgets import QStyle

        _QT_ICONOS = {
            "borrar":        QStyle.StandardPixmap.SP_TrashIcon,
            "guardar":       QStyle.StandardPixmap.SP_DialogSaveButton,
            "nueva":         QStyle.StandardPixmap.SP_FileIcon,
            "editar":        QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "buscar":        QStyle.StandardPixmap.SP_FileDialogContentsView,
            "exportar":      QStyle.StandardPixmap.SP_ArrowUp,
            "importar":      QStyle.StandardPixmap.SP_ArrowDown,
            "abrir_carpeta": QStyle.StandardPixmap.SP_DirOpenIcon,
            "advertencia":   QStyle.StandardPixmap.SP_MessageBoxWarning,
            "info":          QStyle.StandardPixmap.SP_MessageBoxInformation,
            "error":         QStyle.StandardPixmap.SP_MessageBoxCritical,
            "cerrar":        QStyle.StandardPixmap.SP_DialogCloseButton,
            "ayuda":         QStyle.StandardPixmap.SP_DialogHelpButton,
            "refrescar":     QStyle.StandardPixmap.SP_BrowserReload,
            "volver":        QStyle.StandardPixmap.SP_ArrowLeft,
            "siguiente":     QStyle.StandardPixmap.SP_ArrowRight,
        }
    except ImportError:
        _QT_ICONOS = {}

    return _QT_ICONOS


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def obtener_emoji(nombre: str, fallback: str = "•") -> str:
    """
    Retorna el emoji para el ícono solicitado.

    Args:
        nombre:   Clave del diccionario ICONOS_EMOJI.
        fallback: Texto a retornar si el nombre no existe.

    Returns:
        Emoji unicode como str.
    """
    return ICONOS_EMOJI.get(nombre, fallback)


def obtener_icono_qt(nombre: str):
    """
    Retorna un QIcon para el ícono solicitado usando QStyle.StandardPixmap.

    Requiere PySide6 y una QApplication activa.

    Args:
        nombre: Clave del mapa de íconos Qt.

    Returns:
        QIcon del sistema o QIcon vacío si no se encuentra.
    """
    try:
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            return QIcon()

        qt_map = _cargar_qt_iconos()
        sp = qt_map.get(nombre)
        if sp is None:
            return QIcon()

        return app.style().standardIcon(sp)

    except ImportError:
        return None


def aplicar_icono_btn(btn, nombre: str, plataforma: str = "desktop") -> None:
    """
    Aplica ícono y tooltip a un QPushButton.

    Args:
        btn:        Widget de botón (QPushButton).
        nombre:     Nombre del ícono (clave en ICONOS_EMOJI / Qt).
        plataforma: "desktop" usa QIcon; cualquier otro usa emoji en texto.
    """
    tooltip = TOOLTIP.get(nombre, "")

    if plataforma == "desktop":
        try:
            from PySide6.QtWidgets import QPushButton
            if isinstance(btn, QPushButton):
                icono_qt = obtener_icono_qt(nombre)
                if icono_qt is not None and not icono_qt.isNull():
                    btn.setIcon(icono_qt)
                if tooltip:
                    btn.setToolTip(tooltip)
                return
        except ImportError:
            pass

    # Fallback: emoji en texto del botón
    emoji = obtener_emoji(nombre)
    texto_actual = btn.cget("text") if hasattr(btn, "cget") else (btn.text() or "")
    if emoji and not texto_actual.startswith(emoji):
        nuevo_texto = f"{emoji}  {texto_actual}".strip()
        try:
            btn.configure(text=nuevo_texto)
        except AttributeError:
            btn.setText(nuevo_texto)
    if tooltip:
        try:
            btn.setToolTip(tooltip)
        except AttributeError:
            pass
