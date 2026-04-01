# -*- coding: utf-8 -*-
"""
Panel Clientes — Gestión embebida de clientes del gimnasio.
SaaS Premium Edition 2026 — Competitive Design
"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QDialog, QDoubleSpinBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QComboBox,
)

from ui_desktop.pyside.widgets.animations import fade_in_dialog

from src.gestor_bd import GestorBDClientes
from ui_desktop.pyside.widgets.avatar_widget import AvatarWidget
from ui_desktop.pyside.widgets.empty_state import TableEmptyState
from ui_desktop.pyside.widgets.confirm_dialog import confirmar
from ui_desktop.pyside.widgets.toast import mostrar_toast
from ui_desktop.pyside.dialogo_registro_cliente import DialogoRegistroCliente
from config.constantes import OBJETIVOS_VALIDOS, NIVELES_ACTIVIDAD
from utils.logger import logger
from design_system.tokens import Colors


# ══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS — Premium SaaS 2026
# ══════════════════════════════════════════════════════════════════════════════

_COLS = [
    ("CLIENTE",        "nombre"),
    ("TELÉFONO",       "telefono"),
    ("EDAD / PESO",    "edad_peso"),
    ("OBJETIVO",       "objetivo"),
    ("KCAL OBJ.",      "kcal_obj"),
    ("ÚLTIMO PLAN",    "ultimo_plan"),
    ("ACCIONES",       "acciones"),
]

class ClientesPanel(QWidget):
    """Panel de gestión de clientes — SaaS Premium Edition."""

    generar_plan_para = Signal(dict)
    plan_rapido_para = Signal(dict)

    def __init__(self, gestor_bd: GestorBDClientes | None = None, parent=None):
        super().__init__(parent)
        self.gestor_bd = gestor_bd or GestorBDClientes()
        self._todos_clientes: list[dict] = []
        self._filtro_suscripcion: str = "todos"  # "todos" | "activas" | "inactivas"
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._cargar_clientes)
        self._setup_ui()
        self._cargar_clientes()

    # ══════════════════════════════════════════════════════════════════════════
    # UI CONSTRUCTION — Premium Layout
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        content.setObjectName("dashboardBody")
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(32, 28, 32, 32)
        self._layout.setSpacing(24)
        scroll.setWidget(content)

        self._crear_header_premium()
        self._crear_stats_cards()
        self._crear_suscripciones_panel()
        self._crear_barra_acciones_premium()
        self._crear_tabla_premium()

    def _crear_header_premium(self) -> None:
        """Premium header with modern SaaS styling."""
        header = QFrame()
        header.setObjectName("clientesPanelHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Icon + Title
        left = QHBoxLayout()
        left.setSpacing(16)

        # Icon badge
        icon_badge = QLabel("👥")
        icon_badge.setFixedSize(48, 48)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setObjectName("kpiIcon")
        icon_badge.setProperty("color", "yellow")
        left.addWidget(icon_badge)

        # Title container
        title_container = QVBoxLayout()
        title_container.setSpacing(2)

        title = QLabel("Clientes")
        title.setObjectName("panelTitle")
        title_container.addWidget(title)

        self.lbl_subtitle = QLabel("Cargando clientes...")
        self.lbl_subtitle.setObjectName("panelSubtitle")
        title_container.addWidget(self.lbl_subtitle)

        left.addLayout(title_container)
        layout.addLayout(left)
        layout.addStretch()

        # Right side: Primary CTA
        btn_nuevo = QPushButton("➕  Registrar cliente")
        btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo.setObjectName("btnNuevoCliente")
        btn_nuevo.setFixedHeight(42)
        btn_nuevo.clicked.connect(self._abrir_dialogo_registro)
        layout.addWidget(btn_nuevo)

        self._layout.addWidget(header)

    def _crear_stats_cards(self) -> None:
        """Stats cards row showing key metrics."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        def create_stat_card(icon: str, title: str, value: str, subtitle: str, color_key: str) -> tuple[QFrame, QLabel]:
            card = QFrame()
            card.setObjectName("kpiCard")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(18, 16, 18, 16)
            card_layout.setSpacing(14)

            icon_lbl = QLabel(icon)
            icon_lbl.setFixedSize(44, 44)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setObjectName("kpiIcon")
            icon_lbl.setProperty("color", color_key)
            card_layout.addWidget(icon_lbl)

            content = QVBoxLayout()
            content.setSpacing(2)

            title_lbl = QLabel(title)
            title_lbl.setObjectName("kpiLabel")
            content.addWidget(title_lbl)

            value_row = QHBoxLayout()
            value_row.setSpacing(8)
            value_lbl = QLabel(value)
            value_lbl.setObjectName("statCardValue")
            value_lbl.setProperty("color", color_key)
            value_row.addWidget(value_lbl)

            sub_lbl = QLabel(subtitle)
            sub_lbl.setObjectName("kpiContext")
            value_row.addWidget(sub_lbl)
            value_row.addStretch()

            content.addLayout(value_row)
            card_layout.addLayout(content)
            card_layout.addStretch()
            return card, value_lbl

        self.card_total, self._val_total = create_stat_card("👥", "Total Clientes", "0", "activos", "yellow")
        self.card_nuevos, self._val_nuevos = create_stat_card("✨", "Nuevos Este Mes", "0", "registros", "green")
        self.card_activos, self._val_activos = create_stat_card("📋", "Con Planes", "0", "clientes", "cyan")
        self.card_objetivo, self._val_objetivo = create_stat_card("🎯", "En Déficit", "0", "clientes", "orange")

        layout.addWidget(self.card_total)
        layout.addWidget(self.card_nuevos)
        layout.addWidget(self.card_activos)
        layout.addWidget(self.card_objetivo)

        self._layout.addWidget(container)

    def _crear_suscripciones_panel(self) -> None:
        """Mini-panel de suscripciones con pestañas activas/inactivas."""
        container = QFrame()
        container.setObjectName("chartContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header row
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        icon_lbl = QLabel("💳")
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 18px; background: {Colors.PRIMARY_SOFT}; border-radius: 8px;")
        header_row.addWidget(icon_lbl)

        title_lbl = QLabel("Suscripciones")
        title_lbl.setObjectName("kpiLabel")
        title_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        header_row.addWidget(title_lbl)

        header_row.addStretch()

        # Counters (updated dynamically)
        self._lbl_count_activas = QLabel("0")
        self._lbl_count_activas.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 13px; font-weight: 600;")
        header_row.addWidget(self._lbl_count_activas)

        lbl_sep = QLabel("/")
        lbl_sep.setStyleSheet(f"color: {Colors.TEXT_HINT}; font-size: 13px;")
        header_row.addWidget(lbl_sep)

        self._lbl_count_inactivas = QLabel("0")
        self._lbl_count_inactivas.setStyleSheet(f"color: {Colors.ERROR}; font-size: 13px; font-weight: 600;")
        header_row.addWidget(self._lbl_count_inactivas)

        layout.addLayout(header_row)

        # Tab buttons row
        tabs_row = QHBoxLayout()
        tabs_row.setSpacing(8)

        self._btn_todos = QPushButton("👥  Todos")
        self._btn_activas = QPushButton("✅  Suscripciones Activas")
        self._btn_inactivas = QPushButton("⛔  Suscripciones Inactivas")

        for btn in (self._btn_todos, self._btn_activas, self._btn_inactivas):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(38)
            btn.setCheckable(True)

        self._btn_todos.setChecked(True)

        self._btn_todos.clicked.connect(lambda: self._set_filtro_suscripcion("todos"))
        self._btn_activas.clicked.connect(lambda: self._set_filtro_suscripcion("activas"))
        self._btn_inactivas.clicked.connect(lambda: self._set_filtro_suscripcion("inactivas"))

        tabs_row.addWidget(self._btn_todos)
        tabs_row.addWidget(self._btn_activas)
        tabs_row.addWidget(self._btn_inactivas)
        tabs_row.addStretch()

        layout.addLayout(tabs_row)

        self._aplicar_estilos_tabs()
        self._layout.addWidget(container)

    def _aplicar_estilos_tabs(self) -> None:
        """Aplica estilos a los botones tab de suscripciones según estado."""
        style_active = f"""
            QPushButton {{
                background: {Colors.PRIMARY};
                color: {Colors.TEXT_INVERSE};
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 600;
            }}
        """
        style_inactive = f"""
            QPushButton {{
                background: {Colors.BG_INPUT};
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {Colors.BG_HOVER};
                border-color: {Colors.BORDER_HOVER};
                color: {Colors.TEXT_PRIMARY};
            }}
        """
        for btn in (self._btn_todos, self._btn_activas, self._btn_inactivas):
            if btn.isChecked():
                btn.setStyleSheet(style_active)
            else:
                btn.setStyleSheet(style_inactive)

    def _set_filtro_suscripcion(self, filtro: str) -> None:
        """Cambia el filtro de suscripción y recarga la tabla."""
        self._filtro_suscripcion = filtro
        self._btn_todos.setChecked(filtro == "todos")
        self._btn_activas.setChecked(filtro == "activas")
        self._btn_inactivas.setChecked(filtro == "inactivas")
        self._aplicar_estilos_tabs()
        self._cargar_clientes()

    def _crear_barra_acciones_premium(self) -> None:
        """Premium search bar with modern styling."""
        bar = QFrame()
        bar.setObjectName("searchContainer")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(20, 16, 20, 16)
        bl.setSpacing(12)

        # Search input
        self.entry_busqueda = QLineEdit()
        self.entry_busqueda.setPlaceholderText("Buscar por nombre, teléfono...")
        self.entry_busqueda.textChanged.connect(self._on_busqueda)
        bl.addWidget(self.entry_busqueda, 1)

        # Filter buttons
        btn_actualizar = QPushButton("🔄  Actualizar")
        btn_actualizar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_actualizar.setObjectName("ghostButton")
        btn_actualizar.clicked.connect(self._cargar_clientes)
        bl.addWidget(btn_actualizar)

        btn_export = QPushButton("📊 Exportar CSV")
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.setObjectName("ghostButton")
        btn_export.clicked.connect(self._exportar_csv)
        bl.addWidget(btn_export)

        btn_import = QPushButton("📥 Importar CSV")
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_import.setObjectName("ghostButton")
        btn_import.clicked.connect(self._importar_csv)
        bl.addWidget(btn_import)

        self._layout.addWidget(bar)

    def _crear_tabla_premium(self) -> None:
        """Premium data table with modern SaaS styling."""
        container = QFrame()
        container.setObjectName("chartContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Table header bar
        header_bar = QWidget()
        hb_layout = QHBoxLayout(header_bar)
        hb_layout.setContentsMargins(20, 16, 20, 16)

        self.lbl_total = QLabel("0 clientes")
        self.lbl_total.setObjectName("kpiContext")
        hb_layout.addWidget(self.lbl_total)
        hb_layout.addStretch()

        layout.addWidget(header_bar)

        # Loading indicator
        self._loading_indicator = QLabel("⏳ Cargando clientes...")
        self._loading_indicator.setObjectName("loadingLabel")
        self._loading_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_indicator.hide()
        layout.addWidget(self._loading_indicator)

        # Table
        self.tabla = QTableWidget()
        self.tabla.setObjectName("dataTable")
        self.tabla.setColumnCount(len(_COLS))
        self.tabla.setHorizontalHeaderLabels([c[0] for c in _COLS])
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setShowGrid(False)
        self.tabla.setMouseTracking(True)

        hdr = self.tabla.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(3, 160)
        self.tabla.setColumnWidth(6, 300)

        layout.addWidget(self.tabla)
        
        # Empty state
        self._empty_state = TableEmptyState(
            preset="clientes",
            on_action=self._abrir_dialogo_registro,
            parent=self
        )
        self._empty_state.hide()
        layout.addWidget(self._empty_state)
        
        self._layout.addWidget(container)

    # ══════════════════════════════════════════════════════════════════════════
    # DATA LOADING
    # ══════════════════════════════════════════════════════════════════════════

    def _mostrar_cargando(self, show: bool = True) -> None:
        """Muestra u oculta el indicador de carga."""
        if hasattr(self, '_loading_indicator'):
            if show:
                self._loading_indicator.show()
                self.tabla.hide()
                self._empty_state.hide()
            else:
                self._loading_indicator.hide()

    def _cargar_clientes(self) -> None:
        # Show loading state
        self._mostrar_cargando(True)
        
        termino = self.entry_busqueda.text().strip() if hasattr(self, "entry_busqueda") else ""
        filtro = self._filtro_suscripcion
        try:
            if filtro == "inactivas":
                # Mostrar clientes inactivos (suscripción inactiva)
                todos = self.gestor_bd.obtener_todos_clientes(solo_activos=False)
                clientes = [c for c in todos if not c.get("activo", 1)]
                if termino:
                    t = termino.lower()
                    clientes = [c for c in clientes
                                if t in (c.get("nombre") or "").lower()
                                or t in (c.get("telefono") or "").lower()][:200]
            elif filtro == "activas":
                # Mostrar solo clientes activos (suscripción activa)
                if termino:
                    clientes = self.gestor_bd.buscar_clientes(termino, solo_activos=True, limite=200)
                else:
                    clientes = self.gestor_bd.obtener_todos_clientes(solo_activos=True)
            else:
                # "todos" — comportamiento original (solo activos)
                if termino:
                    clientes = self.gestor_bd.buscar_clientes(termino, solo_activos=True, limite=200)
                else:
                    self._todos_clientes = self.gestor_bd.obtener_todos_clientes(solo_activos=True)
                    clientes = self._todos_clientes

            # Actualizar contadores de suscripciones
            self._actualizar_contadores_suscripciones()
        except Exception as exc:
            logger.error("[CLIENTES] Error al cargar: %s", exc)
            clientes = []
            self._mostrar_error("No se pudieron cargar los clientes. Verifica la conexión a la base de datos.")

        self._poblar_tabla(clientes)

    def _mostrar_error(self, mensaje: str) -> None:
        """Muestra una notificación de error al usuario."""
        try:
            from ui_desktop.pyside.widgets.toast import ToastWidget
            # Find topmost parent window
            parent = self.window() if self.window() else self
            ToastWidget(parent, mensaje, tipo="error", duracion=5000)
        except Exception as e:
            logger.warning("No se pudo mostrar toast: %s", e)

    def _poblar_tabla(self, clientes: list[dict]) -> None:
        """Populates the premium table with client data."""
        # Hide loading indicator
        if hasattr(self, '_loading_indicator'):
            self._loading_indicator.hide()

        # Preserve scroll position and selection
        scroll_val = self.tabla.verticalScrollBar().value()
        selected_row = self.tabla.currentRow()
        selected_name = ""
        if selected_row >= 0:
            w = self.tabla.cellWidget(selected_row, 0)
            if w:
                lbl = w.findChild(QLabel, "clienteNombre")
                if lbl:
                    selected_name = lbl.text()

        self.tabla.setRowCount(0)
        total = len(clientes)
        self.lbl_total.setText(f"{total} cliente{'s' if total != 1 else ''}")
        self.lbl_subtitle.setText(f"{total} clientes registrados")
        
        # Update stats cards
        self._actualizar_stats_cards(clientes)

        # Toggle empty state vs table
        if not clientes:
            self.tabla.hide()
            self._empty_state.show()
            return
        else:
            self._empty_state.hide()
            self.tabla.show()

        for i, c in enumerate(clientes):
            self.tabla.insertRow(i)
            self.tabla.setRowHeight(i, 72)

            nombre = c.get("nombre", "—")
            telefono = c.get("telefono", "") or "—"
            edad = c.get("edad", "—")
            peso = c.get("peso_kg", "—")
            objetivo = (c.get("objetivo") or "—").strip()
            total_planes = c.get("total_planes_generados", 0) or 0

            # ── Col 0: Cliente (Avatar + Name + Sub-info) ─────────────────────
            widget_nombre = QWidget()
            wl = QHBoxLayout(widget_nombre)
            wl.setContentsMargins(16, 8, 8, 8)
            wl.setSpacing(14)
            avatar = AvatarWidget(nombre, size=44, color_idx=i % 7)
            wl.addWidget(avatar)

            name_col = QVBoxLayout()
            name_col.setSpacing(3)
            lbl_nombre = QLabel(nombre)
            lbl_nombre.setObjectName("clienteNombre")
            name_col.addWidget(lbl_nombre)

            # Sub-info: plan count or email
            if total_planes > 0:
                lbl_sub = QLabel(f"📋 {total_planes} plan{'es' if total_planes != 1 else ''} generado{'s' if total_planes != 1 else ''}")
            else:
                lbl_sub = QLabel("Sin planes generados")
            lbl_sub.setObjectName("clienteInfo")
            name_col.addWidget(lbl_sub)

            wl.addLayout(name_col)
            wl.addStretch()
            self.tabla.setCellWidget(i, 0, widget_nombre)

            # ── Col 1: Teléfono ───────────────────────────────────────────────
            widget_tel = QWidget()
            tel_layout = QHBoxLayout(widget_tel)
            tel_layout.setContentsMargins(8, 8, 8, 8)

            lbl_tel = QLabel(telefono)
            lbl_tel.setObjectName("clienteMeta")
            tel_layout.addWidget(lbl_tel)
            tel_layout.addStretch()
            self.tabla.setCellWidget(i, 1, widget_tel)

            # ── Col 2: Edad / Peso ────────────────────────────────────────────
            widget_ep = QWidget()
            ep_layout = QVBoxLayout(widget_ep)
            ep_layout.setContentsMargins(8, 8, 8, 8)
            ep_layout.setSpacing(2)

            lbl_edad = QLabel(f"{edad} años")
            lbl_edad.setObjectName("clienteNombre")
            ep_layout.addWidget(lbl_edad)

            lbl_peso = QLabel(f"{peso} kg")
            lbl_peso.setObjectName("clienteInfo")
            ep_layout.addWidget(lbl_peso)

            self.tabla.setCellWidget(i, 2, widget_ep)

            # ── Col 3: Objetivo (Premium Tag) ─────────────────────────────────
            obj_lower = objetivo.lower()
            
            # Determine tag type for QSS property selector
            if "deficit" in obj_lower or "déficit" in obj_lower:
                tag_tipo = "deficit"
            elif "superavit" in obj_lower or "superávit" in obj_lower:
                tag_tipo = "superavit"
            else:
                tag_tipo = "mantenimiento"
            
            widget_obj = QWidget()
            widget_obj.setObjectName("tableCellTransparent")
            ol = QHBoxLayout(widget_obj)
            ol.setContentsMargins(4, 8, 4, 8)
            
            tag = QLabel(objetivo.capitalize())
            tag.setObjectName("objetivoTag")
            tag.setProperty("tipo", tag_tipo)
            tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ol.addWidget(tag)
            ol.addStretch()
            self.tabla.setCellWidget(i, 3, widget_obj)

            # ── Col 4: Kcal Objetivo ──────────────────────────────────────────
            kcal_str = self._calcular_kcal_display(c)
            widget_kcal = QWidget()
            kcal_layout = QHBoxLayout(widget_kcal)
            kcal_layout.setContentsMargins(8, 8, 8, 8)

            lbl_kcal = QLabel(kcal_str)
            lbl_kcal.setObjectName("kcalLabel")
            kcal_layout.addWidget(lbl_kcal)
            kcal_layout.addStretch()
            self.tabla.setCellWidget(i, 4, widget_kcal)

            # ── Col 5: Último Plan ────────────────────────────────────────────
            ultimo_plan = c.get("ultimo_plan", "") or ""
            if ultimo_plan:
                try:
                    dt = datetime.fromisoformat(str(ultimo_plan)[:19])
                    fecha_str = dt.strftime("%d/%m/%Y")
                except Exception:
                    fecha_str = str(ultimo_plan)[:10]
            else:
                fecha_str = "—"
            
            widget_plan = QWidget()
            plan_layout = QVBoxLayout(widget_plan)
            plan_layout.setContentsMargins(8, 8, 8, 8)
            plan_layout.setSpacing(2)

            lbl_fecha = QLabel(fecha_str)
            lbl_fecha.setObjectName("clienteNombre")
            plan_layout.addWidget(lbl_fecha)
            plan_layout.addStretch()

            self.tabla.setCellWidget(i, 5, widget_plan)

            # ── Col 6: Acciones (Premium Buttons) ─────────────────────────────
            widget_acc = QWidget()
            widget_acc.setObjectName("tableCellTransparent")
            al = QHBoxLayout(widget_acc)
            al.setContentsMargins(8, 8, 8, 8)
            al.setSpacing(6)

            # Primary CTA - Generate Plan (icon separated from text)
            btn_plan = QPushButton("Crear Plan")
            btn_plan.setToolTip("Generar plan nutricional")
            btn_plan.setFixedHeight(36)
            btn_plan.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_plan.setObjectName("btnTablePrimary")
            _c = dict(c)
            btn_plan.clicked.connect(lambda _, cl=_c: self._on_generar_plan(cl))
            al.addWidget(btn_plan)

            # Quick Plan — icon-only button with fixed size
            btn_quick = QPushButton("🚀")
            btn_quick.setToolTip("Plan rápido (última config)")
            btn_quick.setFixedSize(36, 36)
            btn_quick.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_quick.setObjectName("btnTableAction")
            _cq = dict(c)
            btn_quick.clicked.connect(lambda _, cl=_cq: self._on_plan_rapido(cl))
            al.addWidget(btn_quick)

            # Secondary - Edit — icon-only
            btn_edit = QPushButton("✏️")
            btn_edit.setToolTip("Editar cliente")
            btn_edit.setFixedSize(36, 36)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setObjectName("btnTableAction")
            _c2 = dict(c)
            btn_edit.clicked.connect(lambda _, cl=_c2: self._on_editar(cl))
            al.addWidget(btn_edit)

            # WhatsApp — 1-click client contact
            tel = c.get("telefono", "") or ""
            if tel:
                nombre_cli = c.get("nombre", "")
                btn_wa = QPushButton("📱")
                btn_wa.setToolTip(f"WhatsApp: {tel}")
                btn_wa.setFixedSize(36, 36)
                btn_wa.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_wa.setObjectName("btnWhatsAppMini")
                _tel = str(tel)
                _nom = str(nombre_cli)
                btn_wa.clicked.connect(lambda _, t=_tel, n=_nom: self._enviar_whatsapp(t, n))
                al.addWidget(btn_wa)

            # Danger - Delete — icon-only
            btn_delete = QPushButton("🗑️")
            btn_delete.setToolTip("Eliminar cliente")
            btn_delete.setFixedSize(36, 36)
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.setObjectName("btnTableDanger")
            _c3 = dict(c)
            btn_delete.clicked.connect(lambda _, cl=_c3: self._on_eliminar(cl))
            al.addWidget(btn_delete)

            al.addStretch()
            self.tabla.setCellWidget(i, 6, widget_acc)

        # Restore selection and scroll position
        if selected_name:
            for row in range(self.tabla.rowCount()):
                w = self.tabla.cellWidget(row, 0)
                if w:
                    lbl = w.findChild(QLabel, "clienteNombre")
                    if lbl and lbl.text() == selected_name:
                        self.tabla.setCurrentCell(row, 0)
                        break
        if scroll_val > 0:
            self.tabla.verticalScrollBar().setValue(scroll_val)

    def _actualizar_contadores_suscripciones(self) -> None:
        """Actualiza los contadores de suscripciones activas/inactivas."""
        try:
            todos = self.gestor_bd.obtener_todos_clientes(solo_activos=False)
            activas = sum(1 for c in todos if c.get("activo", 1))
            inactivas = len(todos) - activas
            if hasattr(self, '_lbl_count_activas'):
                self._lbl_count_activas.setText(f"{activas} activas")
            if hasattr(self, '_lbl_count_inactivas'):
                self._lbl_count_inactivas.setText(f"{inactivas} inactivas")
        except Exception:
            pass

    def _actualizar_stats_cards(self, clientes: list[dict]) -> None:
        """Update the stats cards with real data using direct label references."""
        total = len(clientes)
        
        # Count new clients this month
        from datetime import datetime
        now = datetime.now()
        nuevos_mes = 0
        con_planes = 0
        en_deficit = 0
        
        for c in clientes:
            # Count new this month
            fecha_reg = c.get("fecha_registro", "")
            if fecha_reg:
                try:
                    dt = datetime.fromisoformat(str(fecha_reg)[:19])
                    if dt.year == now.year and dt.month == now.month:
                        nuevos_mes += 1
                except Exception:
                    pass
            
            # Count with plans
            if c.get("total_planes_generados", 0) > 0:
                con_planes += 1
            
            # Count in deficit
            obj = (c.get("objetivo") or "").lower()
            if "deficit" in obj or "déficit" in obj:
                en_deficit += 1
        
        # Update cards using direct references (robust, no findChildren)
        if hasattr(self, '_val_total'):
            self._val_total.setText(str(total))
        if hasattr(self, '_val_nuevos'):
            self._val_nuevos.setText(str(nuevos_mes))
        if hasattr(self, '_val_activos'):
            self._val_activos.setText(str(con_planes))
        if hasattr(self, '_val_objetivo'):
            self._val_objetivo.setText(str(en_deficit))

    def _exportar_csv(self) -> None:
        """Export clients to CSV file."""
        try:
            import csv
            from pathlib import Path
            from datetime import datetime
            
            # Create output directory if not exists
            output_dir = Path("Output")
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = output_dir / f"clientes_export_{timestamp}.csv"
            
            # Get all clients
            clientes = self._todos_clientes or self.gestor_bd.obtener_todos_clientes(solo_activos=True)
            
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(['Nombre', 'Teléfono', 'Edad', 'Peso (kg)', 'Objetivo', 'Nivel Actividad', 'Fecha Registro'])
                # Data
                for c in clientes:
                    writer.writerow([
                        c.get('nombre', ''),
                        c.get('telefono', ''),
                        c.get('edad', ''),
                        c.get('peso_kg', ''),
                        c.get('objetivo', ''),
                        c.get('nivel_actividad', ''),
                        str(c.get('fecha_registro', ''))[:10],
                    ])
            
            # Show success message
            mostrar_toast(self, f"✅ Se exportaron {len(clientes)} clientes a: {filepath}", "success")
            
            # Open folder
            import subprocess
            import platform
            if platform.system() == "Windows":
                subprocess.run(['explorer', '/select,', str(filepath)])
            elif platform.system() == "Darwin":
                subprocess.run(['open', '-R', str(filepath)])
            else:
                subprocess.run(['xdg-open', str(output_dir)])
                
        except Exception as e:
            logger.error(f"Error al exportar CSV: {e}")
            mostrar_toast(self, f"❌ No se pudo exportar: {e}", "error")

    def _importar_csv(self) -> None:
        """Importa clientes desde un archivo CSV."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo CSV", "",
            "Archivos CSV (*.csv);;Todos los archivos (*)"
        )
        if not filepath:
            return

        try:
            import csv
            filas: list[dict] = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # Mapeo flexible de columnas
                for row in reader:
                    fila = {}
                    for k, v in row.items():
                        key = k.strip().lower().replace(" ", "_").replace("(", "").replace(")", "")
                        if "nombre" in key:
                            fila["nombre"] = v
                        elif "telefono" in key or "teléfono" in key:
                            fila["telefono"] = v
                        elif "edad" in key:
                            fila["edad"] = v
                        elif "peso" in key:
                            fila["peso_kg"] = v
                        elif "estatura" in key or "altura" in key:
                            fila["estatura_cm"] = v
                        elif "grasa" in key:
                            fila["grasa_corporal_pct"] = v
                        elif "actividad" in key or "nivel" in key:
                            fila["nivel_actividad"] = v
                        elif "objetivo" in key:
                            fila["objetivo"] = v
                    if fila.get("nombre"):
                        filas.append(fila)

            if not filas:
                mostrar_toast(self, "⚠️ El archivo CSV no contiene filas válidas.", "warning")
                return

            ok, fail = self.gestor_bd.importar_clientes_csv(filas)
            self._cargar_clientes()
            msg = f"✅ Importados: {ok} clientes"
            if fail:
                msg += f"  |  ⚠️ Fallidos: {fail}"
            mostrar_toast(self, msg, "success" if fail == 0 else "warning")

        except Exception as e:
            logger.error(f"Error al importar CSV: {e}")
            mostrar_toast(self, f"❌ No se pudo importar: {e}", "error")

    @staticmethod
    def _calcular_kcal_display(c: dict) -> str:
        """Calcula la kcal objetivo aproximada usando el motor nutricional."""
        try:
            from core.modelos import ClienteEvaluacion
            from core.motor_nutricional import MotorNutricional
            from config.constantes import FACTORES_ACTIVIDAD

            cliente = ClienteEvaluacion(
                nombre=c.get("nombre", ""),
                edad=int(c.get("edad") or 25),
                peso_kg=float(c.get("peso_kg") or 70),
                estatura_cm=float(c.get("estatura_cm") or 170),
                grasa_corporal_pct=float(c.get("grasa_corporal_pct") or 15),
                nivel_actividad=c.get("nivel_actividad") or "moderada",
                objetivo=c.get("objetivo") or "mantenimiento",
            )
            nivel = c.get("nivel_actividad") or "moderada"
            cliente.factor_actividad = FACTORES_ACTIVIDAD.get(nivel, 1.375)
            cliente = MotorNutricional.calcular_motor(cliente)
            return f"{int(cliente.kcal_objetivo):,} kcal"
        except Exception:
            return "—"

    # ── Eventos ───────────────────────────────────────────────────────────────

    def _on_busqueda(self, texto: str) -> None:
        """Debounced search — waits 300ms after last keystroke to avoid flicker."""
        self._search_timer.start()

    def _on_buscar_click(self) -> None:
        self._cargar_clientes()

    def _enviar_whatsapp(self, telefono: str, nombre: str) -> None:
        """Open WhatsApp Web with pre-filled message for this client."""
        import urllib.parse
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        telefono_limpio = "".join(filter(str.isdigit, telefono))
        if not telefono_limpio:
            self._mostrar_error("Este cliente no tiene teléfono registrado.")
            return
        mensaje = f"Hola {nombre}, te contactamos desde el gimnasio."
        url = f"https://wa.me/{telefono_limpio}?text={urllib.parse.quote(mensaje)}"
        QDesktopServices.openUrl(QUrl(url))

    def _on_generar_plan(self, cliente: dict) -> None:
        self.generar_plan_para.emit(cliente)

    def _on_plan_rapido(self, cliente: dict) -> None:
        """Emite señal para plan rápido (genera con última configuración)."""
        self.plan_rapido_para.emit(cliente)

    def _on_editar(self, cliente: dict) -> None:
        dlg = DialogoRegistroCliente(
            gestor_bd=self.gestor_bd,
            modo="registrar",
            cliente_data=cliente,
            parent=self
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._cargar_clientes()

    def _on_eliminar(self, cliente: dict) -> None:
        nombre = cliente.get("nombre", "Este cliente")
        if not confirmar(
            self,
            "Confirmar eliminación",
            f"¿Deseas eliminar a {nombre}?\nEl registro quedará inactivo y no aparecerá en la lista.",
            texto_si="Sí, eliminar",
            texto_no="Cancelar",
        ):
            return
        id_cliente = cliente.get("id_cliente", "")
        if not id_cliente:
            return
        try:
            ok = self.gestor_bd.desactivar_cliente(id_cliente)
            if ok:
                self._cargar_clientes()
            else:
                mostrar_toast(self, "❌ No se pudo eliminar el cliente.", "error")
        except Exception as exc:
            mostrar_toast(self, f"❌ Error al eliminar: {exc}", "error")

    def _abrir_dialogo_registro(self) -> None:
        dlg = DialogoRegistroCliente(
            gestor_bd=self.gestor_bd,
            modo="registrar",
            parent=self
        )
        result = dlg.exec()
        if result == QDialog.DialogCode.Accepted:
            self._cargar_clientes()
            # Si el usuario eligió "Registrar y generar plan"
            if dlg.generar_plan and dlg.cliente_registrado:
                self.generar_plan_para.emit(dlg.cliente_registrado)

    def refresh(self) -> None:
        self._cargar_clientes()
