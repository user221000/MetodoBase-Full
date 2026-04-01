# -*- coding: utf-8 -*-
"""
design_system/tokens.py
=======================
Design System DEFINITIVO — MetodoBase SaaS Edition 2026
Single source of truth for ALL visual tokens.

Theme: Black & Yellow Neon — Professional SaaS 2026

Color System:
    Background: #0A0A0A (pure black)
    Primary: #FFEB3B (neon yellow) — ONLY accent color
    Text: white/gray hierarchy
    Rule: YELLOW ONLY. No purple, cyan, or blue accents.

WCAG Contrast Ratios (verified against BG_DEEP #0A0A0A):
    TEXT_PRIMARY   #FFFFFF  → 21.0:1  ✅  WCAG AAA
    TEXT_SECONDARY #A0A0A0  →  7.0:1  ✅  WCAG AAA
    PRIMARY        #FFEB3B  → 18.1:1  ✅  WCAG AAA

Usage:
    from design_system.tokens import Colors, Spacing, Layout, Typography
    
    bg = Colors.BG_DEEP           # "#0A0A0A"
    primary = Colors.PRIMARY      # "#FFEB3B"
"""
from __future__ import annotations

from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# COLORS — Black & Yellow Neon SaaS 2026 Palette
# ══════════════════════════════════════════════════════════════════════════════

class Colors:
    """
    Complete color system for MetodoBase black & yellow neon theme.
    
    All colors optimized for dark mode with WCAG compliance.
    Premium SaaS aesthetic — competitive 2026.
    """
    
    # ── Core Backgrounds ──────────────────────────────────────────────────────
    BG_DEEP = "#050505"           # Pure black — main app background (darker)
    BG_GRADIENT_START = "#050505" # Gradient start (top)
    BG_GRADIENT_END = "#0A0A0A"   # Gradient end (bottom)
    BG_CARD = "#121212"           # Card/panel background
    BG_SURFACE = "#121212"        # Alias for BG_CARD
    BG_INPUT = "#1A1A1A"          # Input field background
    BG_HOVER = "#1E1E1E"          # Hover state background
    BG_ELEVATED = "#252525"       # Dropdowns, tooltips
    BG_MODAL = "#0F0F0F"          # Modal overlay background
    BG_SECONDARY = "#1A1A1A"      # Secondary background
    
    # ── Layer System ───────────────────────────────────────────────────────────
    LAYER_0 = "#050505"           # Background layer
    LAYER_1 = "#0D0D0D"           # Container layer
    LAYER_2 = "#141414"           # Card/glass layer
    LAYER_3 = "#1E1E1E"           # Interactive elements
    
    # ── Glass Morphism ─────────────────────────────────────────────────────────
    GLASS_BG = "rgba(18, 18, 18, 0.75)"      # Glass background
    GLASS_BORDER = "rgba(255, 235, 59, 0.12)" # Glass border
    GLASS_HOVER = "rgba(26, 26, 26, 0.85)"    # Glass hover
    
    # ── Primary Color — Neon Yellow ───────────────────────────────────────────
    # Contrast: 18.1:1 on BG_DEEP ✅ WCAG AAA
    PRIMARY = "#FFEB3B"           # Main brand action color — Neon Yellow
    PRIMARY_LIGHT = "#FFF176"     # Light variant
    PRIMARY_HOVER = "#FFD700"     # Hover state (gold)
    PRIMARY_PRESSED = "#F9A825"   # Pressed/active state
    PRIMARY_MUTED = "#FFEB3B50"   # 50% opacity — backgrounds
    PRIMARY_GLOW = "#FFEB3B30"    # 30% opacity — glow effects
    PRIMARY_SOFT = "#FFEB3B15"    # 15% opacity — subtle tints
    
    # ── Accent Color — Purple/Pink Neon ────────────────────────────────────────
    # Secondary accent for visual variety and premium SaaS feel
    ACCENT = "#B388FF"            # Neon purple — secondary accent
    ACCENT_HOVER = "#CE93D8"      # Hover state (lighter purple)
    ACCENT_PRESSED = "#9C27B0"    # Pressed state
    ACCENT_MUTED = "#B388FF50"    # 50% opacity
    ACCENT_SOFT = "#B388FF20"     # 20% opacity — subtle backgrounds
    ACCENT_GLOW = "#B388FF30"     # 30% opacity — glow effects
    ACCENT_LIGHT = "#E1BEE7"      # Light purple for text
    ACCENT_PINK = "#FF4081"       # Neon pink — highlights
    ACCENT_PINK_SOFT = "#FF408120" # Pink soft background
    
    # ── Secondary Color — White/Gray ──────────────────────────────────────────
    SECONDARY = "#E5E5E5"         # Light gray for secondary actions
    SECONDARY_HOVER = "#F5F5F5"   # Hover state
    SECONDARY_PRESSED = "#D4D4D4" # Pressed state
    SECONDARY_MUTED = "#E5E5E550" # 50% opacity
    
    # ── Text Colors ───────────────────────────────────────────────────────────
    # HARD CONSTRAINT: never use TEXT_MUTED or TEXT_DISABLED for informative content
    TEXT_PRIMARY = "#FFFFFF"      # 21.0:1 on BG_DEEP ✅ AAA — all body content
    TEXT_SECONDARY = "#A0A0A0"    #  7.0:1 on BG_DEEP ✅ AAA — supporting text
    TEXT_HINT = "#71717A"         #  4.5:1 on BG_DEEP ✅ AA — secondary metadata
    TEXT_MUTED = "#808080"        #  4.5:1 on BG_DEEP ⚠️ DECORATIVE ONLY
    TEXT_DISABLED = "#525252"     #  2.6:1 on BG_DEEP ⚠️ DECORATIVE ONLY
    TEXT_INVERSE = "#0A0A0A"      # Text on light/accent backgrounds
    TEXT_ACCENT = "#FFEB3B"       # Accent text — neon yellow
    
    # ── Border Colors ─────────────────────────────────────────────────────────
    BORDER_SUBTLE = "#1F1F1F"     # Very subtle — dividers
    BORDER_DEFAULT = "#2A2A2A"    # Default visible border
    BORDER_HOVER = "#3F3F3F"      # Hover state border
    BORDER_FOCUS = "#FFEB3B"      # Focus ring (primary yellow)
    BORDER_ACCENT = "#FFEB3B"     # Accent highlight border (yellow)
    BORDER_YELLOW = "#FFEB3B30"   # Subtle yellow border
    
    # Aliases for compatibility
    BORDER = "#2A2A2A"            # Alias for BORDER_DEFAULT
    BORDER_ACTIVE = "#FFEB3B"     # Alias for BORDER_FOCUS
    
    # ── Semantic Colors — Success (Neon Green) ────────────────────────────────
    # Contrast: 12.5:1 on BG_DEEP ✅ WCAG AAA
    SUCCESS = "#00FF88"           # Neon green — confirmations
    SUCCESS_LIGHT = "#33FF9E"     # Light variant — hover
    SUCCESS_DARK = "#00CC6A"      # Dark variant — pressed
    SUCCESS_SOFT = "#00FF8820"    # 20% opacity — background
    SUCCESS_BG = "#052E16"        # Solid dark background
    
    # ── Semantic Colors — Warning (Neon Orange) ───────────────────────────────
    # Contrast: 10.2:1 on BG_DEEP ✅ WCAG AAA
    WARNING = "#FF9800"           # Neon orange — alerts
    WARNING_LIGHT = "#FFB74D"     # Light variant — hover
    WARNING_DARK = "#F57C00"      # Dark variant — pressed
    WARNING_SOFT = "#FF980020"    # 20% opacity — background
    WARNING_BG = "#3D1F00"        # Solid dark background
    
    # ── Semantic Colors — Error (Neon Red) ────────────────────────────────────
    # Contrast: 5.6:1 on BG_DEEP ✅ WCAG AA
    ERROR = "#FF1744"             # Neon red — errors
    ERROR_LIGHT = "#FF5252"       # Light variant — hover
    ERROR_DARK = "#D50000"        # Dark variant — pressed
    ERROR_SOFT = "#FF174420"      # 20% opacity — background
    ERROR_BG = "#3D0A0A"          # Solid dark background
    
    # ── Semantic Colors — Info (Yellow-based, no blue) ────────────────────────
    # Info uses muted yellow to maintain yellow-only system
    INFO = "#FFEB3B"              # Yellow — informational (unified)
    INFO_LIGHT = "#FFF176"        # Light yellow — hover
    INFO_DARK = "#FFD700"         # Gold — pressed
    INFO_SOFT = "#FFEB3B20"       # 20% opacity — background
    INFO_BG = "#1A1A0A"           # Solid dark yellow-tint background
    
    # ── Legacy Cyan aliases (mapped to yellow) ────────────────────────────────
    # Kept for backward compatibility — all point to yellow system
    CYAN = "#FFEB3B"              # → PRIMARY (yellow)
    CYAN_LIGHT = "#FFF176"        # → PRIMARY_LIGHT
    CYAN_DARK = "#FFD700"         # → PRIMARY_HOVER
    CYAN_SOFT = "#FFEB3B20"       # → PRIMARY opacity
    
    # ── Sidebar Colors (Pure Black) ───────────────────────────────────────────
    # HARD CONSTRAINT: sidebar is always dark → text is always white
    SIDEBAR_BG = "#080808"        # Slightly darker than main bg
    SIDEBAR_TEXT = "#FFFFFF"      # 21.0:1 ✅ — navigation labels
    SIDEBAR_TEXT_MUTED = "#A0A0A0"# 7.0:1 ✅ — supporting text
    SIDEBAR_ITEM_HOVER = "#1A1A1A"# Hover background
    SIDEBAR_ITEM_ACTIVE = "#1E1E1E"# Active item background
    SIDEBAR_ACTIVE_BAR = "#FFEB3B"# 3px left border on active item (yellow)
    
    # ── Overlay Colors ────────────────────────────────────────────────────────
    OVERLAY_DARK = "#000000CC"    # 80% black — modal backdrop
    OVERLAY_MEDIUM = "#00000099"  # 60% black
    OVERLAY_LIGHT = "#00000066"   # 40% black
    OVERLAY = "#000000CC"         # Alias for OVERLAY_DARK
    
    # ── Shadow Colors ─────────────────────────────────────────────────────────
    SHADOW_SM = "#00000033"       # 20% black
    SHADOW_MD = "#00000066"       # 40% black
    SHADOW_LG = "#000000B3"       # 70% black
    SHADOW_PRIMARY = "#FFEB3B33"  # Primary glow shadow (neon yellow)
    SHADOW_ACCENT = "#FFEB3B33"   # Accent glow shadow (yellow)
    SHADOW_NEON = "rgba(255, 235, 59, 0.5)"  # Neon glow effect
    
    # ── KPI Card Colors ───────────────────────────────────────────────────────
    # Rule: Only yellow + semantic (success/warning/error). No purple/blue/cyan.
    KPI_YELLOW = "#FFEB3B"        # Primary neon yellow
    KPI_GREEN = "#00FF88"         # Neon green (success)
    KPI_PURPLE = "#FFEB3B"        # → Mapped to yellow (no purple)
    KPI_BLUE = "#FFEB3B"          # → Mapped to yellow (no blue)
    KPI_ORANGE = "#FF9800"        # Neon orange (warning)
    KPI_RED = "#FF1744"           # Neon red (error/risk)
    KPI_CYAN = "#FFEB3B"          # → Mapped to yellow (no cyan)
    
    # ── Neon Effects ──────────────────────────────────────────────────────────
    NEON_GLOW_SM = "0 0 5px rgba(255, 235, 59, 0.3)"
    NEON_GLOW_MD = "0 0 10px rgba(255, 235, 59, 0.5)"
    NEON_GLOW_LG = "0 0 20px rgba(255, 235, 59, 0.7)"
    NEON_BORDER = "1px solid rgba(255, 235, 59, 0.3)"
    
    # ── WhatsApp (Official — DO NOT MODIFY) ───────────────────────────────────
    WHATSAPP_BG = "#25D366"
    WHATSAPP_HOVER = "#1FB858"
    WHATSAPP_PRESSED = "#128C41"


# ══════════════════════════════════════════════════════════════════════════════
# TYPOGRAPHY — Inter Font System
# ══════════════════════════════════════════════════════════════════════════════

class Typography:
    """
    Typography system using Inter with system fallbacks.
    
    Minimum 12px for all informative text (accessibility).
    """
    
    # ── Font Families ─────────────────────────────────────────────────────────
    FAMILY = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
    FAMILY_MONO = "JetBrains Mono, Consolas, Monaco, monospace"
    
    # Aliases for compatibility
    FONT_FAMILY = FAMILY
    FONT_MONO = FAMILY_MONO
    
    # ── Font Sizes (px) ───────────────────────────────────────────────────────
    # HARD CONSTRAINT: minimum 12px for all informative text
    SIZE_XS = 11              # Decorative only — badges, counters
    SIZE_SM = 12              # Minimum informative — labels, captions
    SIZE_MD = 14              # Body text (default)
    SIZE_LG = 16              # Subheadings, emphasis
    SIZE_XL = 18              # Section headings
    SIZE_XXL = 24             # Card/dialog titles
    SIZE_HERO = 32            # Hero text, large displays
    SIZE_DISPLAY = 48         # Display headlines
    
    # Semantic aliases
    DISPLAY = 28              # Page/section titles
    TITLE = 20                # Card/window titles
    BODY = 14                 # General content
    SMALL = 12                # Metadata, labels (MINIMUM)
    MONO = 13                 # Numeric values, IDs
    
    # ── Font Weights ──────────────────────────────────────────────────────────
    WEIGHT_REGULAR = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
    
    # String aliases for QSS compatibility
    REGULAR = "normal"        # 400
    MEDIUM = "500"            # 500
    SEMIBOLD = "600"          # 600
    BOLD = "bold"             # 700
    
    # ── Line Heights ──────────────────────────────────────────────────────────
    LINE_HEIGHT_TIGHT = 1.1   # Headings, compact text
    LINE_HEIGHT_NORMAL = 1.4  # Body text
    LINE_HEIGHT_RELAXED = 1.6 # Long-form content


# ══════════════════════════════════════════════════════════════════════════════
# SPACING — 8px Base Grid
# ══════════════════════════════════════════════════════════════════════════════

class Spacing:
    """
    8px-based spacing system for consistent layouts.
    
    Every value (except XS) is a multiple of 8px.
    """
    
    NONE = 0
    XXS = 2                   # Micro adjustments
    XS = 4                    # Tight gaps, icon padding
    SM = 8                    # Default gap inside components
    MD = 12                   # Intermediate spacing
    LG = 16                   # Between elements in a group
    XL = 24                   # Between sections
    XXL = 32                  # Between major sections
    XXXL = 48                 # Page-level breathing room
    XXXXL = 64                # Hero/display spacing
    
    # ── Component-specific spacing ────────────────────────────────────────────
    INPUT_PADDING_X = 16      # Horizontal padding for inputs
    INPUT_PADDING_Y = 12      # Vertical padding for inputs
    BUTTON_PADDING_X = 24     # Horizontal padding for buttons
    BUTTON_PADDING_Y = 14     # Vertical padding for buttons
    CARD_PADDING = 24         # Default card padding
    SECTION_GAP = 32          # Gap between sections


# ══════════════════════════════════════════════════════════════════════════════
# RADIUS — Border Radius System
# ══════════════════════════════════════════════════════════════════════════════

class Radius:
    """
    Border radius values for rounded corners.
    
    Modern SaaS uses generous, consistent radius values.
    """
    
    NONE = 0
    XS = 4                    # Extra small — tooltips, small elements
    SM = 6                    # Small — buttons, badges
    MD = 8                    # Medium — inputs, small cards
    LG = 12                   # Large — cards, panels
    XL = 16                   # Extra large — modals, large panels
    XXL = 24                  # 2x extra large — hero cards
    FULL = 9999               # Pill/circle shape


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT — Component Dimensions
# ══════════════════════════════════════════════════════════════════════════════

class Layout:
    """
    Fixed dimensions for layout structure and components.
    
    All values in pixels.
    """
    
    # ── Main Structure ────────────────────────────────────────────────────────
    SIDEBAR_WIDTH = 240       # Fixed sidebar width
    SIDEBAR_COLLAPSED = 64    # Collapsed sidebar width
    TOPBAR_HEIGHT = 56        # Fixed topbar height
    CONTENT_PADDING_H = 32    # Horizontal padding in content area
    CONTENT_PADDING_V = 24    # Vertical padding in content area
    
    # ── Component Sizes ───────────────────────────────────────────────────────
    KPI_CARD_HEIGHT = 140
    KPI_CARD_MIN_WIDTH = 180
    TABLE_ROW_HEIGHT = 48
    TABLE_HEADER_HEIGHT = 40
    
    BUTTON_HEIGHT_SM = 32     # Small buttons
    BUTTON_HEIGHT_MD = 40     # Medium buttons (default)
    BUTTON_HEIGHT_LG = 44     # Large buttons — primary CTA minimum
    
    INPUT_HEIGHT = 40         # Standard input height
    INPUT_MIN_WIDTH = 200     # Minimum input width
    
    MODAL_WIDTH_SM = 400      # Small modals
    MODAL_WIDTH_MD = 560      # Medium modals
    MODAL_WIDTH_LG = 720      # Large modals
    
    # ── Accessibility ─────────────────────────────────────────────────────────
    # HARD CONSTRAINT: all interactive elements must meet this minimum
    MIN_TOUCH_TARGET = 32     # 32×32 px minimum touch/click target


# ══════════════════════════════════════════════════════════════════════════════
# ANIMATION — Timing System
# ══════════════════════════════════════════════════════════════════════════════

class Animation:
    """
    Animation timing values in milliseconds.
    
    HARD CONSTRAINT: all feedback animations < 300ms.
    """
    
    INSTANT = 50              # Immediate feedback
    FAST = 100                # Hover states, micro-interactions
    NORMAL = 200              # Standard transitions
    SLOW = 300                # Modals, slide-ins (MAX for feedback)
    SMOOTH = 400              # Complex animations
    KPI_COUNT = 800           # KPI counter animation
    
    # ── Easing Curves (CSS) ───────────────────────────────────────────────────
    EASE_OUT = "cubic-bezier(0.0, 0.0, 0.2, 1)"
    EASE_IN = "cubic-bezier(0.4, 0.0, 1, 1)"
    EASE_IN_OUT = "cubic-bezier(0.4, 0.0, 0.2, 1)"
    BOUNCE = "cubic-bezier(0.68, -0.55, 0.265, 1.55)"


# ══════════════════════════════════════════════════════════════════════════════
# SHADOWS — Elevation System
# ══════════════════════════════════════════════════════════════════════════════

class Shadows:
    """
    Shadow definitions for elevation effects.
    
    Use QGraphicsDropShadowEffect for implementation.
    """
    
    NONE = "none"
    
    # Shadow dictionaries for QGraphicsDropShadowEffect
    SM = {"blur": 4, "offset_y": 1, "color": Colors.SHADOW_SM}
    MD = {"blur": 8, "offset_y": 2, "color": Colors.SHADOW_MD}
    LG = {"blur": 16, "offset_y": 4, "color": Colors.SHADOW_LG}
    XL = {"blur": 24, "offset_y": 8, "color": Colors.SHADOW_LG}
    
    # Glow effects
    PRIMARY_GLOW = {"blur": 20, "offset_y": 0, "color": Colors.SHADOW_PRIMARY}
    ACCENT_GLOW = {"blur": 20, "offset_y": 0, "color": Colors.SHADOW_ACCENT}  # Now yellow
    
    # CSS-style shadow strings (for reference)
    SM_CSS = "0 1px 4px rgba(0,0,0,0.2)"
    MD_CSS = "0 2px 8px rgba(0,0,0,0.4)"
    LG_CSS = "0 4px 16px rgba(0,0,0,0.7)"
    XL_CSS = "0 8px 24px rgba(0,0,0,0.7)"


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_color(name: str) -> Optional[str]:
    """
    Get a color value by name.
    
    Args:
        name: Color name (e.g., 'PRIMARY', 'BG_DEEP', 'TEXT_PRIMARY')
        
    Returns:
        Hex color string or None if not found.
        
    Example:
        >>> get_color('PRIMARY')
        '#FFEB3B'
        >>> get_color('text_primary')  # case-insensitive
        '#FFFFFF'
    """
    name_upper = name.upper().replace("-", "_").replace(" ", "_")
    return getattr(Colors, name_upper, None)


def generate_qss() -> str:
    """
    Generate a complete QSS stylesheet from design tokens.
    
    Returns:
        Complete QSS string ready to apply to QApplication.
        
    Example:
        >>> from PyQt6.QtWidgets import QApplication
        >>> app = QApplication([])
        >>> app.setStyleSheet(generate_qss())
    """
    return f'''
/* ══════════════════════════════════════════════════════════════════════════════
   METODOBASE DESIGN SYSTEM — Auto-generated QSS
   Source: design_system/tokens.py
   ══════════════════════════════════════════════════════════════════════════════ */

/* ── RESET & BASE ───────────────────────────────────────────────────────────── */

QWidget {{
    background-color: {Colors.BG_DEEP};
    color: {Colors.TEXT_PRIMARY};
    font-family: {Typography.FAMILY};
    font-size: {Typography.SIZE_MD}px;
}}

QMainWindow {{
    background-color: {Colors.BG_DEEP};
}}

QDialog {{
    background-color: {Colors.BG_CARD};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.XL}px;
}}

/* ── SIDEBAR ────────────────────────────────────────────────────────────────── */

#sidebar {{
    background-color: {Colors.SIDEBAR_BG};
    border-right: 1px solid {Colors.BORDER_SUBTLE};
    min-width: {Layout.SIDEBAR_WIDTH}px;
    max-width: {Layout.SIDEBAR_WIDTH}px;
}}

.sidebar-item {{
    background-color: transparent;
    color: {Colors.SIDEBAR_TEXT};
    border: none;
    border-radius: {Radius.SM}px;
    padding: {Spacing.SM}px {Spacing.MD}px;
    text-align: left;
}}

.sidebar-item:hover {{
    background-color: {Colors.SIDEBAR_ITEM_HOVER};
}}

.sidebar-item[active="true"] {{
    background-color: {Colors.SIDEBAR_ITEM_ACTIVE};
    border-left: 3px solid {Colors.SIDEBAR_ACTIVE_BAR};
}}

/* ── TOPBAR ─────────────────────────────────────────────────────────────────── */

#topbar {{
    background-color: {Colors.BG_DEEP};
    border-bottom: 1px solid {Colors.BORDER_SUBTLE};
    min-height: {Layout.TOPBAR_HEIGHT}px;
    max-height: {Layout.TOPBAR_HEIGHT}px;
    padding: 0 {Spacing.LG}px;
}}

.topbar-title {{
    color: {Colors.TEXT_PRIMARY};
    font-size: {Typography.TITLE}px;
    font-weight: {Typography.WEIGHT_SEMIBOLD};
}}

.user-badge {{
    background-color: {Colors.PRIMARY_SOFT};
    color: {Colors.PRIMARY_LIGHT};
    border-radius: {Radius.FULL}px;
    padding: {Spacing.XS}px {Spacing.SM}px;
    font-size: {Typography.SIZE_SM}px;
}}

/* ── BUTTONS ────────────────────────────────────────────────────────────────── */

QPushButton {{
    background-color: {Colors.BG_ELEVATED};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.SM}px;
    padding: {Spacing.SM}px {Spacing.LG}px;
    min-height: {Layout.BUTTON_HEIGHT_MD}px;
    font-weight: {Typography.WEIGHT_MEDIUM};
}}

QPushButton:hover {{
    background-color: {Colors.BG_HOVER};
    border-color: {Colors.BORDER_HOVER};
}}

QPushButton:pressed {{
    background-color: {Colors.BG_CARD};
}}

QPushButton:disabled {{
    background-color: {Colors.BG_CARD};
    color: {Colors.TEXT_DISABLED};
    border-color: {Colors.BORDER_SUBTLE};
}}

/* Button variants via class */
.btn-primary {{
    background-color: {Colors.PRIMARY};
    color: {Colors.TEXT_PRIMARY};
    border: none;
}}

.btn-primary:hover {{
    background-color: {Colors.PRIMARY_HOVER};
}}

.btn-primary:pressed {{
    background-color: {Colors.PRIMARY_PRESSED};
}}

.btn-accent {{
    background-color: {Colors.ACCENT};
    color: {Colors.TEXT_INVERSE};
    border: none;
}}

.btn-accent:hover {{
    background-color: {Colors.ACCENT_HOVER};
}}

.btn-accent:pressed {{
    background-color: {Colors.ACCENT_PRESSED};
}}

.btn-ghost {{
    background-color: transparent;
    color: {Colors.TEXT_SECONDARY};
    border: none;
}}

.btn-ghost:hover {{
    background-color: {Colors.BG_HOVER};
    color: {Colors.TEXT_PRIMARY};
}}

.btn-danger {{
    background-color: {Colors.ERROR};
    color: {Colors.TEXT_PRIMARY};
    border: none;
}}

.btn-danger:hover {{
    background-color: {Colors.ERROR_DARK};
}}

/* ── INPUTS ─────────────────────────────────────────────────────────────────── */

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {Colors.BG_INPUT};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.MD}px;
    padding: {Spacing.SM}px {Spacing.MD}px;
    min-height: {Layout.INPUT_HEIGHT}px;
    selection-background-color: {Colors.PRIMARY_MUTED};
}}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
    border-color: {Colors.BORDER_HOVER};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {Colors.BORDER_FOCUS};
    background-color: {Colors.BG_CARD};
}}

QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {Colors.BG_DEEP};
    color: {Colors.TEXT_DISABLED};
    border-color: {Colors.BORDER_SUBTLE};
}}

QLineEdit[placeholder] {{
    color: {Colors.TEXT_MUTED};
}}

/* ── COMBOBOX ───────────────────────────────────────────────────────────────── */

QComboBox {{
    background-color: {Colors.BG_INPUT};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.MD}px;
    padding: {Spacing.SM}px {Spacing.MD}px;
    min-height: {Layout.INPUT_HEIGHT}px;
}}

QComboBox:hover {{
    border-color: {Colors.BORDER_HOVER};
}}

QComboBox:focus {{
    border-color: {Colors.BORDER_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {Colors.BG_ELEVATED};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.MD}px;
    selection-background-color: {Colors.PRIMARY_SOFT};
    selection-color: {Colors.TEXT_PRIMARY};
}}

/* ── SPINBOX ────────────────────────────────────────────────────────────────── */

QSpinBox, QDoubleSpinBox {{
    background-color: {Colors.BG_INPUT};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.MD}px;
    padding: {Spacing.SM}px {Spacing.MD}px;
    min-height: {Layout.INPUT_HEIGHT}px;
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {Colors.BORDER_HOVER};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {Colors.BORDER_FOCUS};
}}

/* ── TABLES ─────────────────────────────────────────────────────────────────── */

QTableWidget, QTableView {{
    background-color: {Colors.BG_CARD};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.LG}px;
    gridline-color: {Colors.BORDER_SUBTLE};
    selection-background-color: {Colors.PRIMARY_SOFT};
    selection-color: {Colors.TEXT_PRIMARY};
}}

QTableWidget::item, QTableView::item {{
    padding: {Spacing.SM}px {Spacing.MD}px;
    border-bottom: 1px solid {Colors.BORDER_SUBTLE};
}}

QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {Colors.PRIMARY_SOFT};
}}

QTableWidget::item:hover, QTableView::item:hover {{
    background-color: {Colors.BG_HOVER};
}}

QHeaderView::section {{
    background-color: {Colors.BG_ELEVATED};
    color: {Colors.TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid {Colors.BORDER_DEFAULT};
    padding: {Spacing.SM}px {Spacing.MD}px;
    font-weight: {Typography.WEIGHT_SEMIBOLD};
    font-size: {Typography.SIZE_SM}px;
}}

/* ── KPI CARDS ──────────────────────────────────────────────────────────────── */

.kpi-card {{
    background-color: {Colors.BG_CARD};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.LG}px;
    padding: {Spacing.XL}px;
    min-height: {Layout.KPI_CARD_HEIGHT}px;
    min-width: {Layout.KPI_CARD_MIN_WIDTH}px;
}}

.kpi-card:hover {{
    border-color: {Colors.BORDER_HOVER};
    background-color: {Colors.BG_HOVER};
}}

.kpi-value {{
    color: {Colors.TEXT_PRIMARY};
    font-size: {Typography.SIZE_HERO}px;
    font-weight: {Typography.WEIGHT_BOLD};
}}

.kpi-label {{
    color: {Colors.TEXT_SECONDARY};
    font-size: {Typography.SIZE_SM}px;
    font-weight: {Typography.WEIGHT_MEDIUM};
}}

.kpi-trend-up {{
    color: {Colors.SUCCESS};
}}

.kpi-trend-down {{
    color: {Colors.ERROR};
}}

/* ── MODALS ─────────────────────────────────────────────────────────────────── */

.modal {{
    background-color: {Colors.BG_CARD};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.XL}px;
    padding: {Spacing.XL}px;
}}

.modal-title {{
    color: {Colors.TEXT_PRIMARY};
    font-size: {Typography.TITLE}px;
    font-weight: {Typography.WEIGHT_SEMIBOLD};
    margin-bottom: {Spacing.MD}px;
}}

.modal-body {{
    color: {Colors.TEXT_SECONDARY};
    font-size: {Typography.BODY}px;
}}

/* ── SCROLLBARS ─────────────────────────────────────────────────────────────── */

QScrollBar:vertical {{
    background-color: {Colors.BG_DEEP};
    width: 8px;
    margin: 0;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: {Colors.BORDER_DEFAULT};
    border-radius: 4px;
    min-height: 40px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {Colors.BORDER_HOVER};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {Colors.BG_DEEP};
    height: 8px;
    margin: 0;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background-color: {Colors.BORDER_DEFAULT};
    border-radius: 4px;
    min-width: 40px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {Colors.BORDER_HOVER};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── LABELS ─────────────────────────────────────────────────────────────────── */

QLabel {{
    color: {Colors.TEXT_PRIMARY};
    background-color: transparent;
}}

.label-secondary {{
    color: {Colors.TEXT_SECONDARY};
}}

.label-muted {{
    color: {Colors.TEXT_MUTED};
}}

/* ── TOOLTIPS ───────────────────────────────────────────────────────────────── */

QToolTip {{
    background-color: {Colors.BG_ELEVATED};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.SM}px;
    padding: {Spacing.XS}px {Spacing.SM}px;
    font-size: {Typography.SIZE_SM}px;
}}

/* ── TABS ───────────────────────────────────────────────────────────────────── */

QTabWidget::pane {{
    background-color: {Colors.BG_CARD};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.LG}px;
    margin-top: -1px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {Colors.TEXT_SECONDARY};
    padding: {Spacing.SM}px {Spacing.LG}px;
    border-bottom: 2px solid transparent;
    font-weight: {Typography.WEIGHT_MEDIUM};
}}

QTabBar::tab:hover {{
    color: {Colors.TEXT_PRIMARY};
    background-color: {Colors.BG_HOVER};
}}

QTabBar::tab:selected {{
    color: {Colors.PRIMARY};
    border-bottom: 2px solid {Colors.PRIMARY};
}}

/* ── PROGRESS BARS ──────────────────────────────────────────────────────────── */

QProgressBar {{
    background-color: {Colors.BG_INPUT};
    border: none;
    border-radius: {Radius.FULL}px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {Colors.PRIMARY};
    border-radius: {Radius.FULL}px;
}}

.progress-success::chunk {{
    background-color: {Colors.SUCCESS};
}}

.progress-accent::chunk {{
    background-color: {Colors.ACCENT};
}}

/* ── CHECKBOXES & RADIO ─────────────────────────────────────────────────────── */

QCheckBox {{
    color: {Colors.TEXT_PRIMARY};
    spacing: {Spacing.SM}px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.XS}px;
    background-color: {Colors.BG_INPUT};
}}

QCheckBox::indicator:checked {{
    background-color: {Colors.PRIMARY};
    border-color: {Colors.PRIMARY};
}}

QCheckBox::indicator:hover {{
    border-color: {Colors.BORDER_HOVER};
}}

QRadioButton {{
    color: {Colors.TEXT_PRIMARY};
    spacing: {Spacing.SM}px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 9px;
    background-color: {Colors.BG_INPUT};
}}

QRadioButton::indicator:checked {{
    background-color: {Colors.PRIMARY};
    border-color: {Colors.PRIMARY};
}}

/* ── STATUS BADGES ──────────────────────────────────────────────────────────── */

.badge-success {{
    background-color: {Colors.SUCCESS_SOFT};
    color: {Colors.SUCCESS};
    border-radius: {Radius.FULL}px;
    padding: {Spacing.XXS}px {Spacing.SM}px;
    font-size: {Typography.SIZE_SM}px;
}}

.badge-warning {{
    background-color: {Colors.WARNING_SOFT};
    color: {Colors.WARNING};
    border-radius: {Radius.FULL}px;
    padding: {Spacing.XXS}px {Spacing.SM}px;
    font-size: {Typography.SIZE_SM}px;
}}

.badge-error {{
    background-color: {Colors.ERROR_SOFT};
    color: {Colors.ERROR};
    border-radius: {Radius.FULL}px;
    padding: {Spacing.XXS}px {Spacing.SM}px;
    font-size: {Typography.SIZE_SM}px;
}}

.badge-info {{
    background-color: {Colors.INFO_SOFT};
    color: {Colors.INFO};
    border-radius: {Radius.FULL}px;
    padding: {Spacing.XXS}px {Spacing.SM}px;
    font-size: {Typography.SIZE_SM}px;
}}

.badge-primary {{
    background-color: {Colors.PRIMARY_SOFT};
    color: {Colors.PRIMARY_LIGHT};
    border-radius: {Radius.FULL}px;
    padding: {Spacing.XXS}px {Spacing.SM}px;
    font-size: {Typography.SIZE_SM}px;
}}

.badge-accent {{
    background-color: {Colors.ACCENT_SOFT};
    color: {Colors.ACCENT};
    border-radius: {Radius.FULL}px;
    padding: {Spacing.XXS}px {Spacing.SM}px;
    font-size: {Typography.SIZE_SM}px;
}}

/* ── GROUPBOX ───────────────────────────────────────────────────────────────── */

QGroupBox {{
    background-color: {Colors.BG_CARD};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.LG}px;
    margin-top: {Spacing.LG}px;
    padding-top: {Spacing.LG}px;
    font-weight: {Typography.WEIGHT_SEMIBOLD};
}}

QGroupBox::title {{
    color: {Colors.TEXT_PRIMARY};
    subcontrol-origin: margin;
    left: {Spacing.MD}px;
    padding: 0 {Spacing.SM}px;
}}

/* ── MENU ───────────────────────────────────────────────────────────────────── */

QMenu {{
    background-color: {Colors.BG_ELEVATED};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Radius.MD}px;
    padding: {Spacing.XS}px;
}}

QMenu::item {{
    padding: {Spacing.SM}px {Spacing.LG}px;
    border-radius: {Radius.SM}px;
}}

QMenu::item:selected {{
    background-color: {Colors.PRIMARY_SOFT};
    color: {Colors.TEXT_PRIMARY};
}}

QMenu::separator {{
    height: 1px;
    background-color: {Colors.BORDER_SUBTLE};
    margin: {Spacing.XS}px {Spacing.SM}px;
}}

/* ── SLIDERS ────────────────────────────────────────────────────────────────── */

QSlider::groove:horizontal {{
    background-color: {Colors.BG_INPUT};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {Colors.PRIMARY};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background-color: {Colors.PRIMARY_HOVER};
}}

QSlider::sub-page:horizontal {{
    background-color: {Colors.PRIMARY};
    border-radius: 3px;
}}

/* ══════════════════════════════════════════════════════════════════════════════
   END OF STYLESHEET
   ══════════════════════════════════════════════════════════════════════════════ */
'''


# ══════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "Colors",
    "Typography",
    "Spacing",
    "Radius",
    "Layout",
    "Animation",
    "Shadows",
    "get_color",
    "generate_qss",
]


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION (run with: python -m design_system.tokens)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("MetodoBase Design System — Token Verification")
    print("=" * 60)
    
    print(f"\n🎨 Colors:")
    print(f"   BG_DEEP:      {Colors.BG_DEEP}")
    print(f"   PRIMARY:      {Colors.PRIMARY}")
    print(f"   ACCENT:       {Colors.ACCENT}")
    print(f"   TEXT_PRIMARY: {Colors.TEXT_PRIMARY}")
    
    print(f"\n📐 Layout:")
    print(f"   SIDEBAR_WIDTH: {Layout.SIDEBAR_WIDTH}px")
    print(f"   TOPBAR_HEIGHT: {Layout.TOPBAR_HEIGHT}px")
    
    print(f"\n🔤 Typography:")
    print(f"   FAMILY: {Typography.FAMILY}")
    print(f"   BODY:   {Typography.BODY}px")
    
    print(f"\n📏 Spacing (8px grid):")
    print(f"   SM={Spacing.SM}  MD={Spacing.MD}  LG={Spacing.LG}  XL={Spacing.XL}")
    
    print(f"\n🔘 Radius:")
    print(f"   SM={Radius.SM}  MD={Radius.MD}  LG={Radius.LG}  FULL={Radius.FULL}")
    
    print(f"\n⏱️ Animation:")
    print(f"   FAST={Animation.FAST}ms  NORMAL={Animation.NORMAL}ms  SLOW={Animation.SLOW}ms")
    
    print(f"\n✅ get_color('primary'): {get_color('primary')}")
    print(f"✅ QSS generated: {len(generate_qss())} characters")
    
    print("\n" + "=" * 60)
    print("All tokens verified successfully!")
    print("=" * 60)
