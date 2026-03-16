# -*- coding: utf-8 -*-
"""
Componentes GUI reutilizables para Método Base.
Sistema de diseño Aurora Fitness.

Changelog:
- v2.0: Migración a design tokens centralizados
- v1.0: Implementación inicial con paleta legacy
"""
from __future__ import annotations

import customtkinter as ctk
from typing import Callable, Optional, Literal

# Importar tokens del sistema de diseño
from gui.design_tokens import (
    Colors,
    Typography,
    Spacing,
    Radius,
    Component,
)


# ═══════════════════════════════════════════════════════════════
# COMPONENTES DE LAYOUT
# ═══════════════════════════════════════════════════════════════

def crear_seccion(
    parent,
    titulo: str,
    icono: str = "",
    descripcion: str = "",
) -> ctk.CTkFrame:
    """
    Crea una sección card con título, ícono opcional y descripción.

    Args:
        parent: Widget padre
        titulo: Texto del encabezado
        icono: Emoji o símbolo (será reemplazado por Lucide en v3.0)
        descripcion: Subtítulo opcional

    Returns:
        Frame de contenido donde agregar widgets hijos

    Ejemplo:
        >>> section = crear_seccion(root, "Datos del Cliente", "👤")
        >>> ctk.CTkLabel(section, text="Nombre").grid(row=0, column=0)
    """
    # Card contenedor
    card = ctk.CTkFrame(
        parent,
        fg_color=Colors.BG_SECONDARY,
        corner_radius=Radius.MD,
        border_width=Component.CARD_BORDER_WIDTH,
        border_color=Colors.BORDER_SUBTLE,
    )
    card.pack(
        fill="x",
        padx=Spacing.XL2,
        pady=Spacing.MD,
    )

    # Header de la sección
    header = ctk.CTkFrame(card, fg_color="transparent")
    header.pack(fill="x", padx=Component.CARD_PADDING, pady=(Spacing.LG, Spacing.SM))

    # Ícono (si existe)
    if icono:
        lbl_icono = ctk.CTkLabel(
            header,
            text=icono,
            font=(Typography.FONT_STACK, Typography.SIZE_LG),
            text_color=Colors.ACTION_PRIMARY,
            anchor="w",
        )
        lbl_icono.pack(side="left", padx=(0, Spacing.SM))

    # Contenedor vertical para título + descripción
    header_text = ctk.CTkFrame(header, fg_color="transparent")
    header_text.pack(side="left", fill="x", expand=True)

    # Título
    lbl_titulo = ctk.CTkLabel(
        header_text,
        text=titulo,
        font=(Typography.FONT_STACK, Typography.SIZE_LG, Typography.WEIGHT_SEMIBOLD),
        text_color=Colors.TEXT_PRIMARY,
        anchor="w",
    )
    lbl_titulo.pack(fill="x")

    # Descripción (si existe)
    if descripcion:
        lbl_desc = ctk.CTkLabel(
            header_text,
            text=descripcion,
            font=(Typography.FONT_STACK, Typography.SIZE_SM),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        )
        lbl_desc.pack(fill="x", pady=(Spacing.XS, 0))

    # Frame de contenido (donde se agregan los widgets hijos)
    content = ctk.CTkFrame(card, fg_color="transparent")
    content.pack(
        fill="x",
        padx=Spacing.SM,
        pady=(0, Spacing.MD),
    )

    # Configurar grid para 4 columnas (layout responsive)
    for i in range(4):
        content.grid_columnconfigure(i, weight=1)

    return content


# ═══════════════════════════════════════════════════════════════
# BOTONES
# ═══════════════════════════════════════════════════════════════

def crear_boton(
    parent,
    texto: str,
    command: Callable,
    variant: Literal["primary", "secondary", "success", "danger", "ghost"] = "primary",
    size: Literal["sm", "md", "lg"] = "md",
    icono: str = "",
    **kwargs,
) -> ctk.CTkButton:
    """
    Crea un botón con estilos predefinidos del design system.

    Args:
        parent: Widget padre
        texto: Texto del botón
        command: Función a ejecutar al hacer click
        variant: Estilo visual del botón
        size: Tamaño del botón
        icono: Emoji/ícono a mostrar antes del texto
        **kwargs: Props adicionales para CTkButton

    Variantes:
        - primary: Acción principal (mint)
        - secondary: Acción secundaria (verde bosque)
        - success: Confirmación (verde)
        - danger: Acción destructiva (rojo)
        - ghost: Acción terciaria (transparente con borde)
    """
    # Mapeo de variantes a colores
    variant_styles = {
        "primary": {
            "fg_color": Colors.ACTION_PRIMARY,
            "hover_color": Colors.ACTION_PRIMARY_HOVER,
            "text_color": Colors.TEXT_INVERTED,
            "border_width": 0,
        },
        "secondary": {
            "fg_color": Colors.ACTION_SECONDARY,
            "hover_color": Colors.ACTION_SECONDARY_HOVER,
            "text_color": Colors.TEXT_INVERTED,
            "border_width": 0,
        },
        "success": {
            "fg_color": Colors.SUCCESS,
            "hover_color": Colors.SUCCESS_HOVER,
            "text_color": Colors.TEXT_INVERTED,
            "border_width": 0,
        },
        "danger": {
            "fg_color": Colors.ERROR,
            "hover_color": Colors.ERROR_HOVER,
            "text_color": Colors.TEXT_INVERTED,
            "border_width": 0,
        },
        "ghost": {
            "fg_color": "transparent",
            "hover_color": Colors.BG_TERTIARY,
            "text_color": Colors.TEXT_SECONDARY,
            "border_width": 1,
            "border_color": Colors.BORDER_DEFAULT,
        },
    }

    # Mapeo de tamaños
    size_config = {
        "sm": {
            "height": Component.BUTTON_HEIGHT_SM,
            "font_size": Typography.SIZE_SM,
        },
        "md": {
            "height": Component.BUTTON_HEIGHT_MD,
            "font_size": Typography.SIZE_BASE,
        },
        "lg": {
            "height": Component.BUTTON_HEIGHT_LG,
            "font_size": Typography.SIZE_LG,
        },
    }

    style = variant_styles.get(variant, variant_styles["primary"])
    size_props = size_config.get(size, size_config["md"])
    texto_final = f"{icono}  {texto}" if icono else texto

    btn = ctk.CTkButton(
        parent,
        text=texto_final,
        command=command,
        height=size_props["height"],
        corner_radius=Radius.MD,
        font=(
            Typography.FONT_STACK,
            size_props["font_size"],
            Typography.WEIGHT_MEDIUM,
        ),
        **style,
        **kwargs,
    )

    return btn


# ═══════════════════════════════════════════════════════════════
# INPUTS
# ═══════════════════════════════════════════════════════════════

def crear_input_con_label(
    parent,
    label_text: str,
    placeholder: str = "",
    row: int = 0,
    colspan: int = 4,
    col: int = 0,
    helper_text: str = "",
    **kwargs,
) -> tuple[ctk.CTkEntry, ctk.CTkLabel]:
    """
    Crea un campo de entrada con label y label de error/helper.

    Args:
        parent: Widget padre (debe tener grid layout)
        label_text: Texto del label
        placeholder: Placeholder del input
        row: Fila en el grid
        colspan: Columnas que ocupa
        col: Columna inicial
        helper_text: Texto de ayuda (opcional)
        **kwargs: Props adicionales para CTkEntry

    Returns:
        Tupla (entry, label_error) para validación posterior
    """
    base_row = row * 3  # Cada input ocupa 3 filas (label, entry, error)

    # Label
    lbl = ctk.CTkLabel(
        parent,
        text=label_text,
        font=(Typography.FONT_STACK, Typography.SIZE_SM, Typography.WEIGHT_MEDIUM),
        text_color=Colors.TEXT_PRIMARY,
        anchor="w",
    )
    lbl.grid(
        row=base_row,
        column=col,
        columnspan=colspan,
        padx=(Component.CARD_PADDING, Spacing.XS),
        pady=(Spacing.SM, Spacing.XS),
        sticky="w",
    )

    # Input
    entry = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        height=Component.INPUT_HEIGHT,
        corner_radius=Radius.SM,
        border_width=Component.INPUT_BORDER_WIDTH,
        border_color=Colors.BORDER_SUBTLE,
        fg_color=Colors.BG_TERTIARY,
        font=(Typography.FONT_STACK, Typography.SIZE_BASE),
        placeholder_text_color=Colors.TEXT_TERTIARY,
        text_color=Colors.TEXT_PRIMARY,
        **kwargs,
    )
    entry.grid(
        row=base_row + 1,
        column=col,
        columnspan=colspan,
        padx=Component.CARD_PADDING,
        pady=(0, Spacing.XS),
        sticky="ew",
    )

    # Label de error/helper
    lbl_error = ctk.CTkLabel(
        parent,
        text=helper_text,
        anchor="w",
        font=(Typography.FONT_STACK, Typography.SIZE_XS),
        text_color=Colors.TEXT_TERTIARY if helper_text else Colors.ERROR,
        wraplength=580,
        justify="left",
    )
    lbl_error.grid(
        row=base_row + 2,
        column=col,
        columnspan=colspan,
        padx=(Component.CARD_PADDING + Spacing.XS, Component.CARD_PADDING),
        pady=(0, Spacing.SM),
        sticky="w",
    )

    return entry, lbl_error


# ═══════════════════════════════════════════════════════════════
# CARDS Y WIDGETS COMPLEJOS
# ═══════════════════════════════════════════════════════════════

def crear_kpi_card(
    parent,
    row: int,
    col: int,
    icono: str,
    label: str,
    valor: str,
    color: str = None,
) -> ctk.CTkFrame:
    """
    Crea una tarjeta KPI (métrica destacada) para dashboards.

    Args:
        parent: Widget padre
        row: Fila en el grid
        col: Columna en el grid
        icono: Emoji/ícono de la métrica
        label: Descripción de la métrica
        valor: Valor a mostrar
        color: Color del valor (opcional, default: mint)
    """
    card = ctk.CTkFrame(
        parent,
        fg_color=Colors.BG_SECONDARY,
        corner_radius=Radius.MD,
        border_width=1,
        border_color=Colors.BORDER_SUBTLE,
    )
    card.grid(
        row=row,
        column=col,
        padx=Spacing.MD,
        pady=Spacing.MD,
        sticky="nsew",
    )

    ctk.CTkLabel(
        card,
        text=icono,
        font=(Typography.FONT_STACK, 32),
    ).pack(pady=(Spacing.XL, Spacing.XS))

    ctk.CTkLabel(
        card,
        text=valor,
        font=(Typography.FONT_STACK, Typography.SIZE_3XL, Typography.WEIGHT_BOLD),
        text_color=color or Colors.ACTION_PRIMARY,
    ).pack(pady=(0, Spacing.XS))

    ctk.CTkLabel(
        card,
        text=label,
        font=(Typography.FONT_STACK, Typography.SIZE_SM),
        text_color=Colors.TEXT_SECONDARY,
    ).pack(pady=(0, Spacing.XL))

    return card


def crear_lista_items(
    parent_scroll: ctk.CTkScrollableFrame,
    items: list[str],
    on_select: Callable[[str], None],
    empty_msg: str = "Sin resultados",
) -> None:
    """
    Llena un scrollable-frame con botones seleccionables.

    Args:
        parent_scroll: Frame scrollable padre
        items: Lista de items a mostrar
        on_select: Callback al seleccionar un item
        empty_msg: Mensaje cuando no hay items
    """
    for widget in parent_scroll.winfo_children():
        widget.destroy()

    if not items:
        ctk.CTkLabel(
            parent_scroll,
            text=empty_msg,
            font=(Typography.FONT_STACK, Typography.SIZE_SM),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(pady=Spacing.XL)
        return

    for item in items:
        btn = ctk.CTkButton(
            parent_scroll,
            text=item.replace("_", " ").title(),
            command=lambda n=item: on_select(n),
            fg_color=Colors.BG_PRIMARY,
            hover_color=Colors.ACTION_PRIMARY,
            text_color=Colors.TEXT_PRIMARY,
            height=34,
            anchor="w",
            font=(Typography.FONT_STACK, Typography.SIZE_BASE),
        )
        btn.pack(fill="x", padx=Spacing.MD, pady=Spacing.XS)


# ═══════════════════════════════════════════════════════════════
# HELPERS DE ESTILO
# ═══════════════════════════════════════════════════════════════

def aplicar_estilo_error(label: ctk.CTkLabel, mensaje: str) -> None:
    """Aplica estilo de error a un label."""
    label.configure(
        text=mensaje,
        text_color=Colors.ERROR,
        font=(Typography.FONT_STACK, Typography.SIZE_XS),
    )


def aplicar_estilo_exito(label: ctk.CTkLabel, mensaje: str) -> None:
    """Aplica estilo de éxito a un label."""
    label.configure(
        text=mensaje,
        text_color=Colors.SUCCESS,
        font=(Typography.FONT_STACK, Typography.SIZE_XS),
    )


def limpiar_estilo_helper(label: ctk.CTkLabel) -> None:
    """Limpia el estilo de un label helper."""
    label.configure(text="", text_color=Colors.TEXT_TERTIARY)
