# -*- coding: utf-8 -*-
"""
Sistema de tokens de diseño Aurora Fitness.
Centraliza todos los valores visuales para consistencia y escalabilidad.
"""
from typing import Literal

# ═══════════════════════════════════════════════════════════════
# PALETA DE COLORES - Aurora Fitness Design System
# ═══════════════════════════════════════════════════════════════


class ColorTokens:
    """
    Paleta de colores Aurora Fitness.
    Todos los colores cumplen WCAG 2.1 AA (contraste mínimo 4.5:1).
    """

    # ─── Neutrales (Escala de grises) ───
    NEUTRAL_950 = "#0A0A0B"    # Fondo principal app
    NEUTRAL_900 = "#121214"    # Cards principales
    NEUTRAL_800 = "#1A1A1C"    # Cards secundarios / hover
    NEUTRAL_700 = "#2A2A2E"    # Inputs / borders sutiles
    NEUTRAL_600 = "#3E3E44"    # Borders activos
    NEUTRAL_500 = "#5E5E66"    # Disabled states
    NEUTRAL_400 = "#94949C"    # Texto secundario
    NEUTRAL_300 = "#C4C4CC"    # Texto hints
    NEUTRAL_100 = "#E8E8EC"    # Texto principal
    NEUTRAL_50  = "#F7F7FA"    # Texto alto contraste

    # ─── Aurora Mint (Color Primario) ───
    MINT_900 = "#004D44"       # Mint más oscuro
    MINT_800 = "#005A50"       # Mint muy oscuro
    MINT_700 = "#006B5F"       # Mint oscuro (hover pressed)
    MINT_600 = "#00897B"       # 🎯 Mint principal (CTA primario)
    MINT_500 = "#00A693"       # Mint hover
    MINT_400 = "#26C6BB"       # Mint accent
    MINT_300 = "#5FDED4"       # Mint claro
    MINT_100 = "#A8F0E9"       # Mint muy claro
    MINT_50  = "#E0F7F5"       # Mint background

    # ─── Verde Bosque (Color Secundario) ───
    FOREST_900 = "#1E3A29"     # Verde más oscuro
    FOREST_800 = "#2E5A3F"     # Verde oscuro profundo
    FOREST_700 = "#3D7D52"     # Verde oscuro medio
    FOREST_600 = "#4CAF5E"     # 🎯 Verde secundario principal
    FOREST_500 = "#7CB342"     # Verde claro (confirmaciones)
    FOREST_400 = "#8BC34A"     # Verde hover
    FOREST_300 = "#A8D87F"     # Verde accent
    FOREST_100 = "#D4EFC0"     # Verde muy claro

    # ─── Estados Semánticos ───
    SUCCESS = "#4CAF50"        # Verde éxito
    SUCCESS_HOVER = "#43A047"
    WARNING = "#F59E0B"        # Naranja advertencia
    WARNING_HOVER = "#D97706"
    ERROR = "#EF4444"          # Rojo error
    ERROR_HOVER = "#DC2626"
    INFO = "#3B82F6"           # Azul información
    INFO_HOVER = "#2563EB"

    # ─── Aliases Semánticos (para facilitar uso) ───
    BG_PRIMARY = NEUTRAL_950
    BG_SECONDARY = NEUTRAL_900
    BG_TERTIARY = NEUTRAL_800

    BORDER_SUBTLE = NEUTRAL_700
    BORDER_DEFAULT = NEUTRAL_600
    BORDER_STRONG = NEUTRAL_500

    TEXT_PRIMARY = NEUTRAL_100
    TEXT_SECONDARY = NEUTRAL_400
    TEXT_TERTIARY = NEUTRAL_300
    TEXT_INVERTED = NEUTRAL_950

    ACTION_PRIMARY = MINT_600
    ACTION_PRIMARY_HOVER = MINT_700
    ACTION_SECONDARY = FOREST_600
    ACTION_SECONDARY_HOVER = FOREST_700


class TypographyTokens:
    """
    Sistema tipográfico basado en Inter.
    Escala modular con ratio 1.25 (Cuarta Mayor).
    """

    # ─── Familias de Fuentes ───
    FAMILY_PRIMARY = "Inter"          # Sans principal
    FAMILY_MONO = "JetBrains Mono"    # Monospace para código/datos
    FAMILY_FALLBACK = "Segoe UI"      # Fallback para Windows

    FONT_STACK = f"{FAMILY_PRIMARY}, {FAMILY_FALLBACK}, system-ui, sans-serif"

    # ─── Escala de Tamaños (px) ───
    SIZE_XS = 11      # Captions, footnotes
    SIZE_SM = 13      # Body secundario, labels pequeños
    SIZE_BASE = 15    # Body principal, inputs
    SIZE_LG = 18      # Subtítulos, botones grandes
    SIZE_XL = 22      # Títulos H3
    SIZE_2XL = 28     # Títulos H2
    SIZE_3XL = 36     # Títulos H1
    SIZE_4XL = 48     # Display (hero, marketing)

    # ─── Pesos ───
    WEIGHT_NORMAL = "normal"      # 400
    WEIGHT_MEDIUM = "500"         # 500 - Botones
    WEIGHT_SEMIBOLD = "600"       # 600 - Énfasis
    WEIGHT_BOLD = "bold"          # 700 - Títulos

    # ─── Line Heights ───
    LEADING_TIGHT = 1.2       # Títulos
    LEADING_NORMAL = 1.5      # Body
    LEADING_RELAXED = 1.75    # Párrafos largos


class SpacingTokens:
    """
    Sistema de espaciado basado en múltiplos de 4px.
    Proporciona consistencia en padding, margin y gaps.
    """

    XS = 4      # 0.25rem - Gaps mínimos
    SM = 8      # 0.5rem  - Padding interno pequeño
    MD = 12     # 0.75rem - Separación entre elementos
    LG = 16     # 1rem    - Padding de cards estándar
    XL = 24     # 1.5rem  - Margen entre secciones
    XL2 = 32    # 2rem    - Separación de bloques grandes
    XL3 = 48    # 3rem    - Márgenes externos, heros
    XL4 = 64    # 4rem    - Espaciado máximo
    XL5 = 96    # 6rem    - Separaciones especiales


class RadiusTokens:
    """Border radius para diferentes componentes."""

    NONE = 0
    SM = 6      # Inputs pequeños, tags
    MD = 10     # Cards, botones estándar
    LG = 16     # Modales, paneles grandes
    XL = 24     # Hero sections, imágenes destacadas
    FULL = 9999 # Pills, avatares circulares


class ElevationTokens:
    """
    Sistema de elevación (box-shadows) para profundidad visual.
    Nota: CustomTkinter no soporta shadows nativamente.
    Usar para referencia en diseño o implementación futura en PySide6.
    """

    NONE = "none"
    SM = "0 1px 3px rgba(0, 0, 0, 0.3)"
    MD = "0 4px 12px rgba(0, 0, 0, 0.4)"
    LG = "0 12px 24px rgba(0, 0, 0, 0.5)"
    XL = "0 24px 48px rgba(0, 0, 0, 0.6)"

    # Elevaciones específicas
    CARD = MD
    MODAL = XL
    DROPDOWN = LG
    BUTTON_HOVER = SM


class TransitionTokens:
    """Duraciones y funciones de timing para animaciones."""

    DURATION_FAST = 150      # ms - Hover states
    DURATION_BASE = 200      # ms - Transiciones estándar
    DURATION_SLOW = 300      # ms - Modales, overlays

    EASING_DEFAULT = "ease"
    EASING_IN = "ease-in"
    EASING_OUT = "ease-out"
    EASING_IN_OUT = "ease-in-out"


# ═══════════════════════════════════════════════════════════════
# SISTEMA DE COMPONENTES - Configuraciones predefinidas
# ═══════════════════════════════════════════════════════════════


class ComponentConfig:
    """Configuraciones reutilizables para componentes UI."""

    # ─── Botones ───
    BUTTON_HEIGHT_SM = 32
    BUTTON_HEIGHT_MD = 44
    BUTTON_HEIGHT_LG = 52

    BUTTON_PADDING_X = SpacingTokens.LG
    BUTTON_PADDING_Y = SpacingTokens.SM

    # ─── Inputs ───
    INPUT_HEIGHT = 44
    INPUT_PADDING = SpacingTokens.MD
    INPUT_BORDER_WIDTH = 1

    # ─── Cards ───
    CARD_PADDING = SpacingTokens.LG
    CARD_BORDER_WIDTH = 1

    # ─── Modales ───
    MODAL_WIDTH_SM = 400
    MODAL_WIDTH_MD = 600
    MODAL_WIDTH_LG = 800


# ═══════════════════════════════════════════════════════════════
# EXPORTACIONES CONVENIENTES
# ═══════════════════════════════════════════════════════════════

# Instancias para import directo
Colors = ColorTokens()
Typography = TypographyTokens()
Spacing = SpacingTokens()
Radius = RadiusTokens()
Elevation = ElevationTokens()
Transition = TransitionTokens()
Component = ComponentConfig()

# Para imports estilo: from gui.design_tokens import Colors, Spacing
__all__ = [
    "Colors",
    "Typography",
    "Spacing",
    "Radius",
    "Elevation",
    "Transition",
    "Component",
    "ColorTokens",
    "TypographyTokens",
    "SpacingTokens",
    "RadiusTokens",
    "ElevationTokens",
    "TransitionTokens",
    "ComponentConfig",
]
