# -*- coding: utf-8 -*-
"""
EmptyState Widget — Reusable empty state placeholder for tables and lists.
Follows design system tokens for consistent styling.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
)

from design_system.tokens import Colors, Spacing, Radius


class EmptyState(QFrame):
    """
    A reusable empty state component for when no data is available.
    
    Usage:
        empty = EmptyState(
            icon="👥",
            title="No hay clientes",
            description="Aún no tienes clientes registrados.",
            action_text="+ Agregar cliente",
            on_action=self._add_client
        )
    """

    def __init__(
        self,
        icon: str = "📭",
        title: str = "No hay datos",
        description: str = "Aún no hay información disponible.",
        action_text: str | None = None,
        on_action: callable = None,
        parent=None
    ):
        super().__init__(parent)
        self.setObjectName("emptyState")
        self._setup_ui(icon, title, description, action_text, on_action)

    def _setup_ui(
        self,
        icon: str,
        title: str,
        description: str,
        action_text: str | None,
        on_action: callable
    ) -> None:
        self.setStyleSheet(f"""
            QFrame#emptyState {{
                background-color: {Colors.BG_CARD};
                border: 1px dashed {Colors.BORDER_DEFAULT};
                border-radius: {Radius.LG}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XXL, Spacing.XXL, Spacing.XXL, Spacing.XXL)
        layout.setSpacing(Spacing.MD)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 48px;
            background: transparent;
            padding: {Spacing.MD}px;
        """)
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
            background: transparent;
        """)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: 14px;
            background: transparent;
            max-width: 320px;
        """)
        layout.addWidget(desc_label)

        # Action button (optional)
        if action_text and on_action:
            layout.addSpacing(Spacing.MD)
            
            btn = QPushButton(action_text)
            btn.setObjectName("primaryButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(on_action)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setMinimumHeight(280)


class TableEmptyState(EmptyState):
    """Specialized empty state for tables."""
    
    PRESETS = {
        "clientes": {
            "icon": "👥",
            "title": "Tu base de clientes empieza aquí",
            "description": "Registra tu primer cliente y genera ingresos con planes nutricionales personalizados.",
            "action_text": "+ Registrar primer cliente"
        },
        "suscripciones": {
            "icon": "💳",
            "title": "Empieza a generar ingresos recurrentes",
            "description": "Crea tu primera suscripción y gestiona membresías que generan dinero cada mes.",
            "action_text": "+ Crear suscripción"
        },
        "clases": {
            "icon": "🏋️",
            "title": "Programa tu primera clase",
            "description": "Las clases atraen clientes y generan retención. Crea una ahora.",
            "action_text": "+ Programar clase"
        },
        "instructores": {
            "icon": "👨‍🏫",
            "title": "Agrega tu equipo de instructores",
            "description": "Los instructores potencian tu negocio. Registra al primero para asignar clases.",
            "action_text": "+ Agregar instructor"
        },
        "facturacion": {
            "icon": "🧾",
            "title": "Controla tus ingresos desde día uno",
            "description": "Registra el primer cobro y ten visibilidad total de tu flujo de dinero.",
            "action_text": "+ Registrar cobro"
        },
        "reportes": {
            "icon": "📊",
            "title": "Los reportes se generan con datos",
            "description": "Registra clientes y suscripciones para desbloquear métricas de negocio.",
        }
    }

    def __init__(self, preset: str, on_action: callable = None, parent=None):
        config = self.PRESETS.get(preset, {})
        super().__init__(
            icon=config.get("icon", "📭"),
            title=config.get("title", "No hay datos"),
            description=config.get("description", ""),
            action_text=config.get("action_text"),
            on_action=on_action,
            parent=parent
        )
