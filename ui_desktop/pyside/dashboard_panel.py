# -*- coding: utf-8 -*-
"""
Dashboard Panel v2.0 — Premium SaaS 2026 Redesign.

Layout Grid (12 columns):
  ┌──────────────────────────────────────────────────────────────────┐
  │  🔝 HERO SECTION (full width, glass, 120-160px)                 │
  │  Left: Dynamic title + subtitle | Right: CTA "Crear plan ahora" │
  ├──────────────────────────────────┬───────────────────────────────┤
  │  🤖 IA INSIGHTS (8 cols)         │  📊 METRICS (4 cols)          │
  │  "Sugerencias para hoy"          │  Clientes Activos             │
  │  • 3-5 clickable insights        │  Planes Generados             │
  ├──────────────────────────────────┼───────────────────────────────┤
  │  📈 CHART (8 cols)               │  ⚡ ACTIONS (4 cols)          │
  │  Line chart + neon gradient      │  • Crear plan                 │
  │  Best day insight                 │  • Agregar cliente            │
  │                                   │  • Enviar por WhatsApp        │
  ├──────────────────────────────────┴───────────────────────────────┤
  │  👥 RECENT CLIENTS (full width)                                  │
  │  Modern table with avatar, objective, status, quick actions      │
  └──────────────────────────────────────────────────────────────────┘
  ➕ Floating "Crear plan rápido" button (bottom-right)
"""
from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from core.branding import branding
from design_system.tokens import Colors, Spacing, Radius, Typography, Animation
from src.gestor_bd import GestorBDClientes
from ui_desktop.pyside.widgets.charts import LineChartWidget
from ui_desktop.pyside.widgets.avatar_widget import AvatarWidget
from ui_desktop.pyside.widgets.animations import apply_hover_glow, stagger_fade_in
from utils.logger import logger


class DashboardPanel(QWidget):
    """Premium SaaS dashboard — action-first, data-driven."""

    navigate_to = Signal(str)

    def __init__(self, gestor_bd: GestorBDClientes | None = None, parent=None):
        super().__init__(parent)
        self.gestor_bd = gestor_bd or GestorBDClientes()
        self._setup_ui()
        QTimer.singleShot(300, self.cargar_datos)

    # ══════════════════════════════════════════════════════════════════════════
    # UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root.addWidget(scroll)

        content = QWidget()
        content.setObjectName("dashboardBody")
        self._main_layout = QVBoxLayout(content)
        self._main_layout.setContentsMargins(28, 24, 28, 28)
        self._main_layout.setSpacing(24)
        scroll.setWidget(content)

        self._build_hero()
        self._build_insights_metrics_row()
        self._build_chart_actions_row()
        self._build_recent_clients()
        self._main_layout.addStretch()

        # Apply micro-interactions
        self._apply_microinteractions()

        # Floating action button
        self._build_fab()

    # ── HERO SECTION ──────────────────────────────────────────────────────────

    def _build_hero(self) -> None:
        hero = QFrame()
        hero.setObjectName("heroSection")
        hero.setFixedHeight(150)

        layout = QHBoxLayout(hero)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # Left: Dynamic title
        left = QVBoxLayout()
        left.setSpacing(8)

        self._hero_title = QLabel("Hoy puedes generar planes en menos de 5 minutos")
        self._hero_title.setObjectName("heroTitle")
        self._hero_title.setWordWrap(True)
        left.addWidget(self._hero_title)

        self._hero_subtitle = QLabel("Tu sistema está listo. 0 clientes esperan un plan.")
        self._hero_subtitle.setObjectName("heroSubtitle")
        self._hero_subtitle.setWordWrap(True)
        left.addWidget(self._hero_subtitle)

        layout.addLayout(left, 1)

        # Right: CTA button
        btn_crear = QPushButton("⚡  Crear plan ahora")
        btn_crear.setObjectName("heroCTA")
        btn_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_crear.setFixedHeight(52)
        btn_crear.setMinimumWidth(220)
        btn_crear.clicked.connect(lambda: self.navigate_to.emit("generar_plan"))
        layout.addWidget(btn_crear, 0, Qt.AlignmentFlag.AlignVCenter)

        self._main_layout.addWidget(hero)

    # ── INSIGHTS + METRICS ROW ────────────────────────────────────────────────

    def _build_insights_metrics_row(self) -> None:
        row = QHBoxLayout()
        row.setSpacing(24)

        # IA Insights (8 cols equivalent)
        self._insights_card = self._create_glass_card()
        insights_layout = QVBoxLayout(self._insights_card)
        insights_layout.setContentsMargins(24, 20, 24, 20)
        insights_layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("🤖  Sugerencias para hoy")
        title.setObjectName("sectionHeader")
        header.addWidget(title)
        header.addStretch()
        insights_layout.addLayout(header)

        self._insights_container = QVBoxLayout()
        self._insights_container.setSpacing(8)
        insights_layout.addLayout(self._insights_container)
        insights_layout.addStretch()

        row.addWidget(self._insights_card, 2)

        # Metrics (4 cols equivalent)
        metrics_col = QVBoxLayout()
        metrics_col.setSpacing(16)

        # KPI 1: Clientes activos
        self._metric_clients = self._create_metric_card(
            "👥", "Clientes activos", "0", "+0% vs semana pasada", "neutral"
        )
        metrics_col.addWidget(self._metric_clients["card"])

        # KPI 2: Planes generados
        self._metric_plans = self._create_metric_card(
            "📋", "Planes generados", "0", "+0 esta semana", "neutral"
        )
        metrics_col.addWidget(self._metric_plans["card"])

        row.addLayout(metrics_col, 1)
        self._main_layout.addLayout(row)

    # ── CHART + ACTIONS ROW ───────────────────────────────────────────────────

    def _build_chart_actions_row(self) -> None:
        row = QHBoxLayout()
        row.setSpacing(24)

        # Chart (8 cols)
        chart_card = self._create_glass_card()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(24, 20, 24, 16)
        chart_layout.setSpacing(12)

        chart_header = QHBoxLayout()
        chart_title = QLabel("📈  Actividad de planes")
        chart_title.setObjectName("sectionHeader")
        chart_header.addWidget(chart_title)
        chart_header.addStretch()

        self._chart_insight = QLabel("")
        self._chart_insight.setObjectName("chartInsight")
        chart_header.addWidget(self._chart_insight)

        chart_layout.addLayout(chart_header)

        self._chart = LineChartWidget()
        self._chart.setMinimumHeight(200)
        chart_layout.addWidget(self._chart)

        row.addWidget(chart_card, 2)

        # Actions (4 cols)
        actions_card = self._create_glass_card()
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(24, 20, 24, 20)
        actions_layout.setSpacing(12)

        actions_title = QLabel("⚡  Acciones rápidas")
        actions_title.setObjectName("sectionHeader")
        actions_layout.addWidget(actions_title)
        actions_layout.addSpacing(4)

        # Action 1: Crear plan
        btn1 = self._create_action_button("📋  Crear plan para cliente", "generar_plan")
        actions_layout.addWidget(btn1)

        # Action 2: Agregar cliente
        btn2 = self._create_action_button("👤  Agregar nuevo cliente", "clientes")
        actions_layout.addWidget(btn2)

        # Action 3: WhatsApp
        btn3 = QPushButton("📱  Enviar plan por WhatsApp")
        btn3.setObjectName("actionButtonWhatsApp")
        btn3.setCursor(Qt.CursorShape.PointingHandCursor)
        btn3.setFixedHeight(48)
        btn3.clicked.connect(lambda: self.navigate_to.emit("generar_plan"))
        actions_layout.addWidget(btn3)

        actions_layout.addStretch()

        row.addLayout(actions_card_wrapper := QVBoxLayout(), 1)
        actions_card_wrapper.addWidget(actions_card)

        self._main_layout.addLayout(row)

    # ── RECENT CLIENTS ────────────────────────────────────────────────────────

    def _build_recent_clients(self) -> None:
        card = self._create_glass_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("👥  Clientes recientes")
        title.setObjectName("sectionHeader")
        header.addWidget(title)
        header.addStretch()

        btn_ver_todos = QPushButton("Ver todos →")
        btn_ver_todos.setObjectName("btn_text")
        btn_ver_todos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ver_todos.clicked.connect(lambda: self.navigate_to.emit("clientes"))
        header.addWidget(btn_ver_todos)
        layout.addLayout(header)

        # Table header
        th = QFrame()
        th.setObjectName("tableHeader")
        th_layout = QHBoxLayout(th)
        th_layout.setContentsMargins(16, 8, 16, 8)
        th_layout.setSpacing(0)
        for text, stretch in [("CLIENTE", 3), ("OBJETIVO", 2), ("ESTADO", 2), ("ACCIÓN", 1)]:
            lbl = QLabel(text)
            lbl.setObjectName("tableHeaderLabel")
            th_layout.addWidget(lbl, stretch)
        layout.addWidget(th)

        # Rows container
        self._clients_container = QVBoxLayout()
        self._clients_container.setSpacing(4)
        layout.addLayout(self._clients_container)

        # Empty state
        self._empty_state = QLabel("No hay clientes registrados. ¡Comienza agregando uno!")
        self._empty_state.setObjectName("emptyStateMessage")
        self._empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state.setFixedHeight(80)
        layout.addWidget(self._empty_state)
        self._empty_state.hide()

        self._main_layout.addWidget(card)

    # ── MICROINTERACTIONS ────────────────────────────────────────────────────

    def _apply_microinteractions(self) -> None:
        """Apply hover glow and stagger fade-in to dashboard cards."""
        # Hover glow on metric cards
        for metric in (self._metric_clients, self._metric_plans):
            apply_hover_glow(
                metric["card"],
                color=Colors.PRIMARY,
                blur_rest=0,
                blur_hover=20,
                duration=200,
            )

        # Hover glow on insights card
        apply_hover_glow(
            self._insights_card,
            color=Colors.ACCENT,
            blur_rest=0,
            blur_hover=16,
            duration=200,
        )

    # ── FLOATING ACTION BUTTON ────────────────────────────────────────────────

    def _build_fab(self) -> None:
        self._fab = QPushButton("＋  Crear plan rápido")
        self._fab.setObjectName("fab")
        self._fab.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fab.setFixedHeight(48)
        self._fab.setParent(self)
        self._fab.clicked.connect(lambda: self.navigate_to.emit("generar_plan"))
        self._fab.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_fab"):
            self._fab.move(
                self.width() - self._fab.sizeHint().width() - 28,
                self.height() - 72,
            )

    # ══════════════════════════════════════════════════════════════════════════
    # HELPER BUILDERS
    # ══════════════════════════════════════════════════════════════════════════

    def _create_glass_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("glassCard")
        return card

    def _create_metric_card(
        self, icon: str, label: str, value: str, delta: str, trend: str
    ) -> dict:
        card = QFrame()
        card.setObjectName("metricCard")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setFixedHeight(130)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(6)

        # Icon + label row
        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("metricIcon")
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(icon_lbl)
        top.addStretch()
        layout.addLayout(top)

        # Value
        val_lbl = QLabel(value)
        val_lbl.setObjectName("metricValue")
        layout.addWidget(val_lbl)

        # Label  
        label_lbl = QLabel(label)
        label_lbl.setObjectName("metricLabel")
        layout.addWidget(label_lbl)

        # Delta
        delta_lbl = QLabel(delta)
        delta_lbl.setObjectName("metricDelta")
        delta_lbl.setProperty("trend", trend)
        layout.addWidget(delta_lbl)

        layout.addStretch()

        return {
            "card": card,
            "value": val_lbl,
            "label": label_lbl,
            "delta": delta_lbl,
        }

    def _create_action_button(self, text: str, target: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("actionButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(48)
        btn.clicked.connect(lambda: self.navigate_to.emit(target))
        return btn

    def _create_insight_row(self, icon: str, text: str, action: str = "") -> QFrame:
        row = QFrame()
        row.setObjectName("insightRow")
        row.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("insightIcon")
        icon_lbl.setFixedSize(28, 28)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        text_lbl = QLabel(text)
        text_lbl.setObjectName("insightText")
        text_lbl.setWordWrap(True)
        layout.addWidget(text_lbl, 1)

        if action:
            arrow = QLabel("→")
            arrow.setObjectName("insightArrow")
            layout.addWidget(arrow)

        if action:
            row.mousePressEvent = lambda e: self.navigate_to.emit(action)

        return row

    def _create_client_row(
        self, nombre: str, objetivo: str, status: str, badge_id: str
    ) -> QFrame:
        row = QFrame()
        row.setObjectName("clientRow")

        layout = QHBoxLayout(row)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(0)

        # Avatar + name (stretch 3)
        name_col = QHBoxLayout()
        name_col.setSpacing(12)

        avatar = AvatarWidget(nombre, size=36)
        name_col.addWidget(avatar)

        name_lbl = QLabel(nombre)
        name_lbl.setObjectName("clientRowName")
        name_col.addWidget(name_lbl)
        name_col.addStretch()

        name_w = QWidget()
        name_w.setLayout(name_col)
        layout.addWidget(name_w, 3)

        # Objective (stretch 2)
        obj_lbl = QLabel(objetivo.replace("_", " ").capitalize() if objetivo else "General")
        obj_lbl.setObjectName("clientRowObjective")
        layout.addWidget(obj_lbl, 2)

        # Status badge (stretch 2)
        badge = QLabel(status)
        badge.setObjectName(badge_id)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedWidth(100)
        layout.addWidget(badge, 2, Qt.AlignmentFlag.AlignCenter)

        # Action button (stretch 1)
        btn = QPushButton("📋 Plan")
        btn.setObjectName("btnTablePrimary")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(90, 32)
        btn.clicked.connect(lambda: self.navigate_to.emit("generar_plan"))
        layout.addWidget(btn, 1, Qt.AlignmentFlag.AlignRight)

        return row

    # ══════════════════════════════════════════════════════════════════════════
    # DATA LOADING
    # ══════════════════════════════════════════════════════════════════════════

    def cargar_datos(self) -> None:
        try:
            ahora = datetime.now()
            stats = self.gestor_bd.obtener_estadisticas_gym(
                fecha_inicio=ahora - timedelta(days=30),
                fecha_fin=ahora,
            )
            clientes_recientes = self.gestor_bd.buscar_clientes("", limite=8)
            self._cargar_hero(stats)
            self._cargar_metrics(stats)
            self._cargar_insights(stats)
            self._cargar_chart(stats)
            self._cargar_clientes_recientes(clientes_recientes)
        except Exception as exc:
            logger.error("[DASHBOARD] Error cargando datos: %s", exc, exc_info=True)

    def _cargar_hero(self, stats: dict) -> None:
        try:
            total = stats.get("total_clientes", 0)
            sin_plan = stats.get("sin_plan", 0)

            if total == 0:
                self._hero_title.setText(
                    "Comienza registrando tu primer cliente y genera su plan nutricional"
                )
                self._hero_subtitle.setText(
                    "El sistema te guía paso a paso. Solo toma 5 minutos."
                )
            elif sin_plan > 0:
                self._hero_title.setText(
                    f"Tienes {sin_plan} clientes esperando un plan nutricional"
                )
                self._hero_subtitle.setText(
                    "Genera sus planes personalizados ahora — cada uno toma menos de 5 minutos."
                )
            else:
                self._hero_title.setText(
                    f"Todos tus {total} clientes tienen plan activo 🎉"
                )
                self._hero_subtitle.setText(
                    "Revisa los resultados o genera nuevos planes cuando lo necesites."
                )
        except Exception:
            pass

    def _cargar_metrics(self, stats: dict) -> None:
        try:
            total_activos = stats.get("clientes_activos", 0)
            clientes_nuevos = stats.get("clientes_nuevos", 0)
            planes_periodo = stats.get("planes_periodo", 0)

            # Active clients metric
            self._metric_clients["value"].setText(str(total_activos))
            self._metric_clients["delta"].setText(f"+{clientes_nuevos} este mes")
            self._metric_clients["delta"].setProperty("trend", "up" if clientes_nuevos > 0 else "neutral")
            self._metric_clients["delta"].style().unpolish(self._metric_clients["delta"])
            self._metric_clients["delta"].style().polish(self._metric_clients["delta"])

            # Plans generated metric
            self._metric_plans["value"].setText(str(planes_periodo))
            self._metric_plans["delta"].setText(f"{planes_periodo} este mes")
            self._metric_plans["delta"].setProperty("trend", "up" if planes_periodo > 0 else "neutral")
            self._metric_plans["delta"].style().unpolish(self._metric_plans["delta"])
            self._metric_plans["delta"].style().polish(self._metric_plans["delta"])

        except Exception as exc:
            logger.warning("[DASHBOARD] Error en métricas: %s", exc)

    def _cargar_insights(self, stats: dict) -> None:
        # Clear existing
        while self._insights_container.count():
            item = self._insights_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            total = stats.get("total_clientes", 0)
            activos = stats.get("clientes_activos", 0)
            sin_plan = stats.get("sin_plan", 0)
            nuevos = stats.get("clientes_nuevos", 0)

            insights = []

            # Insight 1: Clients without plan
            if sin_plan > 0:
                insights.append(("⚠️", f"{sin_plan} clientes no tienen plan activo", "clientes"))

            # Insight 2: New this month
            if nuevos > 0:
                insights.append(("🎉", f"{nuevos} nuevos clientes este mes", "clientes"))

            # Insight 3: Active ratio
            if total > 0:
                ratio = (activos / total) * 100
                if ratio < 60:
                    insights.append(("📉", f"Solo {ratio:.0f}% de tus clientes están activos", "clientes"))
                elif ratio >= 80:
                    insights.append(("🔥", f"{ratio:.0f}% de clientes activos — excelente retención", ""))

            # Insight 4: Revenue opportunity
            cuota = float(branding.get("cuota_mensual", 800))
            if sin_plan > 0:
                oportunidad = sin_plan * cuota
                insights.append(("💰", f"Oportunidad: ${oportunidad:,.0f}/mes si activas los {sin_plan} restantes", "generar_plan"))

            # Insight 5: Empty state
            if total == 0:
                insights.append(("👤", "Registra tu primer cliente para empezar", "generar_plan"))

            for icon, text, action in insights[:5]:
                widget = self._create_insight_row(icon, text, action)
                self._insights_container.addWidget(widget)

        except Exception as exc:
            logger.warning("[DASHBOARD] Error en insights: %s", exc)

    def _cargar_chart(self, stats: dict) -> None:
        try:
            labels = stats.get("planes_labels", [])
            values = stats.get("planes_por_dia", [])

            if not labels or not values:
                DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                ahora = datetime.now()
                labels = [DIAS[(ahora - timedelta(days=6 - i)).weekday()] for i in range(7)]
                values = [0] * 7

            self._chart.set_data(labels, values)

            # Best day insight
            if values and max(values) > 0:
                best_idx = values.index(max(values))
                self._chart_insight.setText(
                    f"✨ Mejor día: {labels[best_idx]} ({max(values)} planes)"
                )
                self._chart_insight.setObjectName("chartInsight")
            else:
                self._chart_insight.setText("Sin actividad esta semana")

        except Exception as exc:
            logger.warning("[DASHBOARD] Error en gráfica: %s", exc)

    def _cargar_clientes_recientes(self, clientes: list) -> None:
        # Clear existing rows
        while self._clients_container.count():
            item = self._clients_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not clientes:
            self._empty_state.show()
            return

        self._empty_state.hide()

        for cliente in clientes[:8]:
            nombre = cliente.get("nombre", "—")
            objetivo = cliente.get("objetivo", "General") or "General"
            status_text, badge_id = self._get_client_status(cliente)

            row = self._create_client_row(nombre, objetivo, status_text, badge_id)
            self._clients_container.addWidget(row)

    def _get_client_status(self, cliente: dict) -> tuple[str, str]:
        total_planes = cliente.get("total_planes_generados", 0)
        ultimo_plan = cliente.get("ultimo_plan")
        fecha_registro = cliente.get("fecha_registro", "")

        try:
            if fecha_registro:
                dt = datetime.fromisoformat(str(fecha_registro)[:19])
                if (datetime.now() - dt).days <= 7:
                    return ("Nuevo", "badgeNuevo")
        except Exception:
            pass

        if not ultimo_plan or total_planes == 0:
            return ("Sin plan", "badgeSinPlan")

        return ("Activo", "badgeActive")

    # ── Public API ────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self.cargar_datos()
