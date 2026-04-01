# -*- coding: utf-8 -*-
"""
Design System — Método Base v2.0
Black & Yellow Neon Premium — tokens unificados.

Usage:
    from design_system import Colors, Spacing, Layout, Typography
    from design_system import generate_qss
"""
from design_system.tokens import (
    Colors, Typography, Spacing, Radius, Layout, Animation, Shadows,
    get_color, generate_qss,
)

__all__ = [
    "Colors", "Typography", "Spacing", "Radius", "Layout", "Animation", "Shadows",
    "get_color", "generate_qss",
]
