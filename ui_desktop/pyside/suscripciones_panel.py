# -*- coding: utf-8 -*-
"""
SuscripcionesPanel v2.0 — Premium SaaS Subscription Management.

Layout:
  ┌──────────────────────────────────────────────────────────────────┐
  │  Header: Title + "Nueva Suscripción" CTA                        │
  ├──────────────────────────────────────────────────────────────────┤
  │  KPI Summary: Activas | Vencidas | Pendientes                   │
  ├──────────┬──────────────────┬───────────────────────────────────┤
  │  MENSUAL │  ★ TRIMESTRAL ★  │  ANUAL                            │
  │          │  "Más elegido"   │                                    │
  │  pricing │  pricing card    │  pricing card                      │
  │  card    │  FEATURED        │                                    │
  ├──────────┴──────────────────┴───────────────────────────────────┤
  │  Suscripciones Recientes (table)                                │
  └──────────────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QComboBox, QDateEdit,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QGraphicsDropShadowEffect, QSizePolicy,
)

from ui_desktop.pyside.widgets.empty_state import TableEmptyState
from ui_desktop.pyside.widgets.toast import mostrar_toast
from utils.logger import logger
from design_system.tokens import Colors, Spacing, Radius


# ── Plan definitions ──────────────────────────────────────────────────────────
PLANES = [
    {
        "id": "mensual",
        "nombre": "Mensual",
        "precio": "$29",
        "periodo": "/mes",
        "dias": 30,
        "featured": False,
        "features": [
            "Planes nutricionales ilimitados",
            "Hasta 30 clientes activos",
            "Exportación PDF básica",
        ],
        "value_prop": "Ideal para empezar",
    },
    {
        "id": "trimestral",
        "nombre": "Trimestral",
        "precio": "$69",
        "periodo": "/trimestre",
        "dias": 90,
        "featured": True,
        "badge": "⭐ Más elegido por gimnasios",
        "features": [
            "Todo lo del plan Mensual",
            "Clientes ilimitados",
            "WhatsApp directo",
            "Soporte prioritario",
        ],
        "value_prop": "Recupera tu inversión con 1 cliente",
    },
    {
        "id": "anual",
        "nombre": "Anual",
        "precio": "$199",
        "periodo": "/año",
        "dias": 365,
        "featured": False,
        "features": [
            "Todo lo del plan Trimestral",
            "Reportes avanzados",
            "API personalizada",
            "Onboarding dedicado",
        ],
        "value_prop": "Ahorra 10h/semana en planificación",
    },
]


class DialogoNuevaSuscripcion(QDialog):
    """Diálogo para crear nueva suscripción."""

    def __init__(self, plan_preseleccionado: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Suscripción")
        self.setMinimumWidth(400)
        self._plan_preseleccionado = plan_preseleccionado
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        self.input_cliente = QLineEdit()
        self.input_cliente.setPlaceholderText("Nombre del cliente")
        form.addRow("Cliente:", self.input_cliente)

        self.combo_plan = QComboBox()
        self.combo_plan.addItems(["Mensual", "Trimestral", "Semestral", "Anual"])
        if self._plan_preseleccionado:
            idx = self.combo_plan.findText(self._plan_preseleccionado)
            if idx >= 0:
                self.combo_plan.setCurrentIndex(idx)
        form.addRow("Plan:", self.combo_plan)

        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(datetime.now().date())
        self.fecha_inicio.setCalendarPopup(True)
        form.addRow("Fecha inicio:", self.fecha_inicio)

        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["Activa", "Pendiente", "Vencida"])
        self.combo_estado.setCurrentIndex(0)
        form.addRow("Estado:", self.combo_estado)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> dict:
        """Devuelve los datos del formulario."""
        duracion_map = {"Mensual": 30, "Trimestral": 90, "Semestral": 180, "Anual": 365}
        plan = self.combo_plan.currentText()
        inicio = self.fecha_inicio.date().toPython()
        vencimiento = inicio + timedelta(days=duracion_map.get(plan, 30))
        return {
            "cliente": self.input_cliente.text().strip(),
            "plan": plan,
            "inicio": inicio,
            "vencimiento": vencimiento,
            "estado": self.combo_estado.currentText(),
        }


class SuscripcionesPanel(QWidget):
    """Premium SaaS subscription management panel."""

    suscripcion_creada = Signal(dict)

    def __init__(self, gestor_bd=None, parent=None):
        super().__init__(parent)
        self.gestor_bd = gestor_bd
        self._suscripciones: list[dict] = []
        self._setup_ui()
        self._cargar_suscripciones()

    # ── UI Setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root_layout.addWidget(scroll)

        content = QWidget()
        content.setObjectName("transparentWidget")
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(32, 24, 32, 32)
        self._layout.setSpacing(24)
        scroll.setWidget(content)

        self._crear_header()
        self._crear_resumen()
        self._crear_pricing_cards()
        self._crear_tabla()

    def _crear_header(self) -> None:
        header = QFrame()
        header.setObjectName("headerFrame")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 16)

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("Suscripciones")
        title.setObjectName("pageTitle")
        left.addWidget(title)
        subtitle = QLabel("Gestión de membresías y planes de pago")
        subtitle.setObjectName("pageSubtitle")
        left.addWidget(subtitle)
        layout.addLayout(left)
        layout.addStretch()

        self.btn_nueva = QPushButton("💳  Nueva Suscripción")
        self.btn_nueva.setObjectName("primaryButton")
        self.btn_nueva.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nueva.setFixedHeight(42)
        self.btn_nueva.setToolTip("Crear una nueva suscripción o membresía")
        self.btn_nueva.clicked.connect(self._nueva_suscripcion)
        layout.addWidget(self.btn_nueva)

        self._layout.addWidget(header)

    def _crear_resumen(self) -> None:
        """KPI summary cards: activas, vencidas, pendientes."""
        row = QHBoxLayout()
        row.setSpacing(16)

        self._kpi_labels: dict[str, QLabel] = {}

        for key, label, valor, tag_name in [
            ("activas", "ACTIVAS", "0", "tagSubActiva"),
            ("vencidas", "VENCIDAS", "0", "tagSubVencida"),
            ("pendientes", "PENDIENTES", "0", "tagSubPendiente"),
        ]:
            card = QFrame()
            card.setObjectName("kpiCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(24, 24, 24, 20)

            v = QLabel(valor)
            v.setObjectName("kpiValue")
            card_layout.addWidget(v)
            self._kpi_labels[key] = v

            l = QLabel(label)
            l.setObjectName("kpiLabel")
            card_layout.addWidget(l)

            tag = QLabel("●")
            tag.setObjectName(tag_name)
            card_layout.addWidget(tag)

            card_layout.addStretch()
            row.addWidget(card)

        self._layout.addLayout(row)

    def _crear_pricing_cards(self) -> None:
        """Premium pricing cards with featured plan highlight."""
        section_title = QLabel("Planes Disponibles")
        section_title.setObjectName("chartTitle")
        self._layout.addWidget(section_title)

        row = QHBoxLayout()
        row.setSpacing(20)

        for plan in PLANES:
            card = self._build_pricing_card(plan)
            row.addWidget(card)

        self._layout.addLayout(row)

    def _build_pricing_card(self, plan: dict) -> QFrame:
        """Build a single pricing card. Featured plans get special treatment."""
        is_featured = plan.get("featured", False)

        card = QFrame()
        card.setObjectName("pricingCardFeatured" if is_featured else "pricingCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Badge for featured plan
        if is_featured and plan.get("badge"):
            badge = QLabel(plan["badge"])
            badge.setObjectName("pricingBadge")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addSpacing(4)

        # Plan name
        name = QLabel(plan["nombre"])
        name.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 14px; "
            f"font-weight: 600; letter-spacing: 1px; background: transparent;"
        )
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name)

        # Price
        price_row = QHBoxLayout()
        price_row.setSpacing(2)
        price_row.addStretch()
        price_lbl = QLabel(plan["precio"])
        price_lbl.setObjectName("pricingPrice")
        price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_row.addWidget(price_lbl)
        period_lbl = QLabel(plan["periodo"])
        period_lbl.setObjectName("pricingPeriod")
        period_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)
        price_row.addWidget(period_lbl)
        price_row.addStretch()
        layout.addLayout(price_row)

        # Features list
        layout.addSpacing(8)
        for feat in plan.get("features", []):
            feat_lbl = QLabel(f"✓  {feat}")
            feat_lbl.setObjectName("pricingFeature")
            feat_lbl.setWordWrap(True)
            layout.addWidget(feat_lbl)

        layout.addSpacing(8)

        # Value proposition
        if plan.get("value_prop"):
            vp = QLabel(f"💡 {plan['value_prop']}")
            vp.setObjectName("pricingValueProp")
            vp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vp.setWordWrap(True)
            layout.addWidget(vp)

        layout.addStretch()

        # CTA button
        plan_name = plan["nombre"]
        cta = QPushButton(f"Elegir {plan_name}")
        cta.setObjectName("primaryButton" if is_featured else "secondaryButton")
        cta.setCursor(Qt.CursorShape.PointingHandCursor)
        cta.setFixedHeight(44 if is_featured else 38)
        cta.clicked.connect(lambda checked=False, p=plan_name: self._nueva_suscripcion(p))
        layout.addWidget(cta)

        # Glow effect for featured card
        if is_featured:
            glow = QGraphicsDropShadowEffect(card)
            glow.setBlurRadius(40)
            glow.setColor(QColor(Colors.PRIMARY_GLOW))
            glow.setOffset(0, 0)
            card.setGraphicsEffect(glow)

        return card

    def _crear_tabla(self) -> None:
        container = QFrame()
        container.setObjectName("chartContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Suscripciones Recientes")
        title.setObjectName("chartTitle")
        layout.addWidget(title)

        self._tabla = QTableWidget(0, 5)
        self._tabla.setHorizontalHeaderLabels(
            ["Cliente", "Plan", "Inicio", "Vencimiento", "Estado"]
        )
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._tabla)

        # Empty state for empty table
        self._empty_state = TableEmptyState(
            preset="suscripciones",
            on_action=self._nueva_suscripcion,
            parent=self
        )
        layout.addWidget(self._empty_state)

        self._layout.addWidget(container)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _nueva_suscripcion(self, plan_preseleccionado: str = "") -> None:
        """Abre diálogo para crear nueva suscripción."""
        dialogo = DialogoNuevaSuscripcion(
            plan_preseleccionado=plan_preseleccionado if isinstance(plan_preseleccionado, str) else "",
            parent=self,
        )
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            data = dialogo.get_data()
            if not data["cliente"]:
                mostrar_toast(self, "⚠️ Ingresa el nombre del cliente.", "warning")
                return
            self._suscripciones.append(data)
            self._actualizar_tabla()
            mostrar_toast(self, "✅ Suscripción creada exitosamente", "success")
            self.suscripcion_creada.emit(data)
            logger.info(f"Nueva suscripcion creada: {data['cliente']} - {data['plan']}")

    def _cargar_suscripciones(self) -> None:
        """Carga suscripciones desde la base de datos."""
        try:
            if self.gestor_bd and hasattr(self.gestor_bd, "obtener_suscripciones"):
                self._suscripciones = self.gestor_bd.obtener_suscripciones() or []
            else:
                self._suscripciones = []
            self._actualizar_tabla()
            logger.info(f"Cargadas {len(self._suscripciones)} suscripciones")
        except Exception as e:
            logger.warning(f"[SuscripcionesPanel] Error cargando suscripciones: {e}")
            self._suscripciones = []
            self._actualizar_tabla()

    def _actualizar_tabla(self) -> None:
        """Actualiza la tabla con las suscripciones actuales."""
        if not self._suscripciones:
            self._tabla.hide()
            self._empty_state.show()
            return

        self._empty_state.hide()
        self._tabla.show()
        self._tabla.setRowCount(len(self._suscripciones))

        for row, sub in enumerate(self._suscripciones):
            self._tabla.setItem(row, 0, QTableWidgetItem(sub.get("cliente", "")))
            self._tabla.setItem(row, 1, QTableWidgetItem(sub.get("plan", "")))
            inicio = sub.get("inicio", "")
            if hasattr(inicio, "strftime"):
                inicio = inicio.strftime("%d/%m/%Y")
            self._tabla.setItem(row, 2, QTableWidgetItem(str(inicio)))
            vencimiento = sub.get("vencimiento", "")
            if hasattr(vencimiento, "strftime"):
                vencimiento = vencimiento.strftime("%d/%m/%Y")
            self._tabla.setItem(row, 3, QTableWidgetItem(str(vencimiento)))
            estado = sub.get("estado", "Activa")
            item_estado = QTableWidgetItem(estado)
            if estado == "Activa":
                item_estado.setForeground(QColor(Colors.SUCCESS))
            elif estado == "Vencida":
                item_estado.setForeground(QColor(Colors.ERROR))
            else:
                item_estado.setForeground(QColor(Colors.WARNING))
            self._tabla.setItem(row, 4, item_estado)

        self._actualizar_resumen()

    def _actualizar_resumen(self) -> None:
        """Actualiza las cards de resumen."""
        activas = sum(1 for s in self._suscripciones if s.get("estado") == "Activa")
        vencidas = sum(1 for s in self._suscripciones if s.get("estado") == "Vencida")
        pendientes = sum(1 for s in self._suscripciones if s.get("estado") == "Pendiente")
        self._kpi_labels["activas"].setText(str(activas))
        self._kpi_labels["vencidas"].setText(str(vencidas))
        self._kpi_labels["pendientes"].setText(str(pendientes))

    def refresh(self) -> None:
        """Recarga datos de suscripciones."""
        logger.info("Refrescando panel de suscripciones")
        self._cargar_suscripciones()
