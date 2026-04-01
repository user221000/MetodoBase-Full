# -*- coding: utf-8 -*-
"""
Panel Generar Plan — Wizard de 3 pasos para generar planes nutricionales.

Paso 1: Seleccionar cliente o registrar nuevo
Paso 2: Parámetros del plan (tipo, plantilla)
Paso 3: Resultado (progreso, PDF, WhatsApp)
"""
from __future__ import annotations

import os
import re
import threading
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
    QPlainTextEdit,
)
from ui_desktop.pyside.widgets.toast import mostrar_toast


from config.constantes import (
    FACTORES_ACTIVIDAD, NIVELES_ACTIVIDAD, OBJETIVOS_VALIDOS,
    CARPETA_SALIDA, CARPETA_PLANES,
)
from config.plantillas_cliente import (
    PLANTILLAS_CLIENTE, PLANTILLAS_LABELS, PLANTILLAS_POR_LABEL,
)
from core.modelos import ClienteEvaluacion
from core.motor_nutricional import MotorNutricional
from core.generador_planes import ConstructorPlanNuevo
from api.pdf_generator import PDFGenerator
from core.exportador_multi import ExportadorMultiformato
from src.gestor_bd import GestorBDClientes
from src.gestor_preferencias import GestorPreferencias
from ui_desktop.pyside.widgets.progress_indicator import ProgressIndicator
from ui_desktop.pyside.dialogo_registro_cliente import DialogoRegistroCliente
from design_system.tokens import Colors
from utils.helpers import abrir_carpeta_pdf
from utils.logger import logger

# Clave para preferencias de gym
_PREF_GYM_ID = "gym_default"


# ── Señales de hilo ───────────────────────────────────────────────────────────

class _Senales(QObject):  # noqa: N801
    log_msg         = Signal(str)
    set_progress    = Signal(float, str)
    complete_prog   = Signal(str)
    show_preview    = Signal(object, dict)
    done            = Signal(str)
    error_msg       = Signal(str)
    btn_spinner     = Signal(bool)


# ── Panel principal ───────────────────────────────────────────────────────────

class GenerarPlanPanel(QWidget):
    """Wizard de 3 pasos para generar un plan nutricional."""

    # Emitida cuando se quiere navegar a otro panel
    navigate_to = Signal(str)   # "dashboard" | "clientes"

    def __init__(self, gestor_bd: GestorBDClientes | None = None, parent=None):
        super().__init__(parent)
        self.gestor_bd = gestor_bd or GestorBDClientes()

        # Estado del wizard
        self._cliente_actual: ClienteEvaluacion | None = None
        self._ultimo_pdf: str | None = None
        self._preview_confirmed = False
        self._preview_event: threading.Event | None = None
        self._prefs = GestorPreferencias(_PREF_GYM_ID)

        # Señales thread-safe
        self._sig = _Senales()
        self._sig.log_msg.connect(self._log)
        self._sig.set_progress.connect(lambda v, s: self.progress.set_progress(v, s))
        self._sig.complete_prog.connect(lambda s: self.progress.complete(s))
        self._sig.show_preview.connect(self._abrir_preview)
        self._sig.done.connect(self._on_done)
        self._sig.error_msg.connect(self._on_error)
        self._sig.btn_spinner.connect(self._set_btn_spinner)

        self._setup_ui()

    # ── Construcción ──────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        self._vbox = QVBoxLayout(content)
        self._vbox.setContentsMargins(28, 20, 28, 28)
        self._vbox.setSpacing(20)
        scroll.setWidget(content)

        self._crear_header()
        self._crear_wizard_steps()
        self._stack = QStackedWidget()
        self._vbox.addWidget(self._stack)

        # Páginas del wizard
        self._page1 = self._crear_pagina1()
        self._page2 = self._crear_pagina2()
        self._page3 = self._crear_pagina3()

        self._stack.addWidget(self._page1)
        self._stack.addWidget(self._page2)
        self._stack.addWidget(self._page3)

        self._ir_a_paso(0)

    def _crear_header(self) -> None:
        header = QFrame()
        header.setObjectName("headerFrame")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 16)

        left = QVBoxLayout()
        left.setSpacing(4)

        title = QLabel("Generar Plan Nutricional")
        title.setObjectName("pageTitle")
        left.addWidget(title)

        subtitle = QLabel("Crea un plan personalizado en 3 pasos")
        subtitle.setObjectName("pageSubtitle")
        left.addWidget(subtitle)

        layout.addLayout(left)
        layout.addStretch()
        self._vbox.addWidget(header)

    def _crear_wizard_steps(self) -> None:
        """Barra de progreso visual de los 3 pasos."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        pasos = [
            ("1", "Seleccionar cliente"),
            ("2", "Datos del plan"),
            ("3", "Resultado"),
        ]

        self._step_circles: list[QLabel] = []
        self._step_labels: list[QLabel] = []

        for i, (num, texto) in enumerate(pasos):
            # Círculo numerado
            circle = QLabel(num)
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            circle.setFixedSize(36, 36)
            circle.setObjectName("stepInactive")
            self._step_circles.append(circle)
            layout.addWidget(circle)

            # Texto
            lbl = QLabel(texto)
            lbl.setObjectName("stepLabelInactive")
            self._step_labels.append(lbl)
            layout.addWidget(lbl)

            # Línea separadora (excepto en el último)
            if i < len(pasos) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setFixedHeight(2)
                sep.setStyleSheet(f"background-color: {Colors.BORDER_DEFAULT};")
                sep.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                layout.addWidget(sep, 1)

        self._vbox.addWidget(container)

    def _actualizar_steps(self, paso_actual: int) -> None:
        """Actualiza los estilos visuales de los círculos de pasos."""
        for i, (circle, lbl) in enumerate(
            zip(self._step_circles, self._step_labels)
        ):
            if i < paso_actual:
                circle.setObjectName("stepCompleted")
                lbl.setObjectName("stepLabelInactive")
            elif i == paso_actual:
                circle.setObjectName("stepActive")
                lbl.setObjectName("stepLabelActive")
            else:
                circle.setObjectName("stepInactive")
                lbl.setObjectName("stepLabelInactive")
            circle.style().unpolish(circle)
            circle.style().polish(circle)
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

    # ── Página 1: Selección de cliente ────────────────────────────────────────

    def _crear_pagina1(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Barra de búsqueda — Premium styling
        search_row = QHBoxLayout()
        search_row.setSpacing(12)
        
        self.entry_busqueda = QLineEdit()
        self.entry_busqueda.setPlaceholderText("🔍  Buscar cliente o crear nuevo...")
        self.entry_busqueda.textChanged.connect(self._on_buscar_cliente)
        search_row.addWidget(self.entry_busqueda, 1)

        btn_nuevo = QPushButton("➕  Nuevo cliente")
        btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo.setObjectName("btnNuevoCliente")
        btn_nuevo.setFixedHeight(42)
        btn_nuevo.setMinimumWidth(160)
        btn_nuevo.clicked.connect(self._abrir_dialogo_nuevo_cliente)
        search_row.addWidget(btn_nuevo)
        layout.addLayout(search_row)

        # Área de resultados de búsqueda
        self.resultado_container = QFrame()
        self.resultado_container.setObjectName("formCard")
        results_layout = QVBoxLayout(self.resultado_container)
        results_layout.setContentsMargins(16, 16, 16, 16)
        results_layout.setSpacing(8)
        self._results_layout = results_layout
        layout.addWidget(self.resultado_container)

        # Cargar clientes recientes al iniciar
        self._mostrar_clientes_recientes()

        layout.addStretch()
        return page

    # ── Página 2: Parámetros del plan ─────────────────────────────────────────

    def _crear_pagina2(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # ── Cliente badge ─────────────────────────────────────────────
        cliente_badge = QFrame()
        cliente_badge.setObjectName("formCard")
        badge_lay = QHBoxLayout(cliente_badge)
        badge_lay.setContentsMargins(16, 12, 16, 12)
        badge_lay.setSpacing(10)

        avatar_lbl = QLabel("👤")
        avatar_lbl.setFixedSize(36, 36)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet(
            f"background:{Colors.PRIMARY};color:#000;border-radius:18px;"
            "font-size:18px;"
        )
        badge_lay.addWidget(avatar_lbl)

        self.lbl_cliente_info = QLabel("Sin cliente seleccionado")
        self.lbl_cliente_info.setObjectName("clienteNombre")
        badge_lay.addWidget(self.lbl_cliente_info, 1)
        layout.addWidget(cliente_badge)

        # ── Configuración del plan (single card) ─────────────────────
        config_card = QFrame()
        config_card.setObjectName("formCard")
        config_lay = QVBoxLayout(config_card)
        config_lay.setContentsMargins(20, 16, 20, 16)
        config_lay.setSpacing(14)

        # Formato de entrega
        lbl_tipo = QLabel("Formato de entrega")
        lbl_tipo.setObjectName("sectionTitle")
        config_lay.addWidget(lbl_tipo)

        tipo_row = QHBoxLayout()
        self.btn_menu_fijo = QPushButton("📋  Menú Fijo")
        self.btn_menu_fijo.setCheckable(True)
        self.btn_menu_fijo.setChecked(True)
        self.btn_menu_fijo.clicked.connect(lambda: self._cambiar_tipo("menu_fijo"))
        self.btn_menu_fijo.setObjectName("toggleButtonActive")
        tipo_row.addWidget(self.btn_menu_fijo)

        self.btn_con_opciones = QPushButton("🔀  Con Opciones")
        self.btn_con_opciones.setCheckable(True)
        self.btn_con_opciones.clicked.connect(lambda: self._cambiar_tipo("con_opciones"))
        self.btn_con_opciones.setObjectName("toggleButtonInactive")
        tipo_row.addWidget(self.btn_con_opciones)
        tipo_row.addStretch()
        config_lay.addLayout(tipo_row)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{Colors.BORDER_SUBTLE};")
        config_lay.addWidget(div)

        # Plantilla del cliente
        lbl_plant = QLabel("Plantilla del cliente")
        lbl_plant.setObjectName("sectionTitle")
        config_lay.addWidget(lbl_plant)

        self.combo_plantilla = QComboBox()
        self.combo_plantilla.addItems(PLANTILLAS_LABELS)
        config_lay.addWidget(self.combo_plantilla)

        self.lbl_plantilla_desc = QLabel("")
        self.lbl_plantilla_desc.setObjectName("clienteInfo")
        self.lbl_plantilla_desc.setWordWrap(True)
        config_lay.addWidget(self.lbl_plantilla_desc)

        self.combo_plantilla.currentTextChanged.connect(self._on_plantilla_change)
        self._on_plantilla_change(self.combo_plantilla.currentText())

        # Restaurar última plantilla y tipo usados
        self._restaurar_preferencias_plan()

        layout.addWidget(config_card)

        # Botones
        btns_row = QHBoxLayout()
        btn_atras = QPushButton("←  Atrás")
        btn_atras.setObjectName("secondaryButton")
        btn_atras.clicked.connect(lambda: self._ir_a_paso(0))
        btns_row.addWidget(btn_atras)
        btns_row.addStretch()

        self.btn_generar = QPushButton("⚡  Generar Plan")
        self.btn_generar.setObjectName("btnGenerarPlan")
        self.btn_generar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generar.clicked.connect(self._on_generar_click)
        btns_row.addWidget(self.btn_generar)

        layout.addLayout(btns_row)
        layout.addStretch()
        return page

    # ── Página 3: Resultado ───────────────────────────────────────────────────

    def _crear_pagina3(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Indicador de progreso
        self.progress = ProgressIndicator()
        layout.addWidget(self.progress)

        # Resultado
        resultado_card = QFrame()
        resultado_card.setObjectName("formCard")
        res_layout = QVBoxLayout(resultado_card)
        res_layout.setContentsMargins(20, 16, 20, 16)
        res_layout.setSpacing(12)

        self.lbl_resultado = QLabel("Generando plan nutricional...")
        self.lbl_resultado.setObjectName("loadingLabel")
        self.lbl_resultado.setWordWrap(True)
        res_layout.addWidget(self.lbl_resultado)

        self.lbl_pdf_ruta = QLabel("")
        self.lbl_pdf_ruta.setObjectName("clienteInfo")
        self.lbl_pdf_ruta.setWordWrap(True)
        res_layout.addWidget(self.lbl_pdf_ruta)

        layout.addWidget(resultado_card)

        # ── Resumen de macronutrientes (oculto hasta que se genera) ──────────
        self._macro_card = QFrame()
        self._macro_card.setObjectName("formCard")
        self._macro_card.setVisible(False)
        macro_layout = QVBoxLayout(self._macro_card)
        macro_layout.setContentsMargins(20, 16, 20, 16)
        macro_layout.setSpacing(12)

        macro_header = QLabel("📊  Resumen Nutricional")
        macro_header.setObjectName("sectionTitle")
        macro_layout.addWidget(macro_header)

        macro_grid = QHBoxLayout()
        macro_grid.setSpacing(16)

        def _macro_kpi(label: str, color: str) -> tuple[QFrame, QLabel]:
            card = QFrame()
            card.setObjectName("kpiCard")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            cl.setSpacing(4)
            lbl_t = QLabel(label)
            lbl_t.setObjectName("kpiLabel")
            cl.addWidget(lbl_t)
            lbl_v = QLabel("—")
            lbl_v.setObjectName("statCardValue")
            lbl_v.setProperty("color", color)
            cl.addWidget(lbl_v)
            return card, lbl_v

        card_kcal, self._lbl_macro_kcal = _macro_kpi("🔥 Kcal objetivo", "yellow")
        card_prot, self._lbl_macro_prot = _macro_kpi("🥩 Proteína", "green")
        card_carbs, self._lbl_macro_carbs = _macro_kpi("🌾 Carbohidratos", "cyan")
        card_grasa, self._lbl_macro_grasa = _macro_kpi("🥑 Grasa", "orange")

        macro_grid.addWidget(card_kcal)
        macro_grid.addWidget(card_prot)
        macro_grid.addWidget(card_carbs)
        macro_grid.addWidget(card_grasa)

        macro_layout.addLayout(macro_grid)
        layout.addWidget(self._macro_card)

        # Bitácora
        log_card = QFrame()
        log_card.setObjectName("formCard")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(16, 12, 16, 12)

        lbl_log = QLabel("Bitácora")
        lbl_log.setObjectName("formSectionHeader")
        log_layout.addWidget(lbl_log)

        self.textbox_log = QPlainTextEdit()
        self.textbox_log.setReadOnly(True)
        self.textbox_log.setFixedHeight(100)
        log_layout.addWidget(self.textbox_log)
        layout.addWidget(log_card)

        # Botones de resultado
        btns_row = QHBoxLayout()
        btns_row.setSpacing(10)

        self.btn_nuevo_plan = QPushButton("🔄  Nuevo Plan")
        self.btn_nuevo_plan.setObjectName("secondaryButton")
        self.btn_nuevo_plan.clicked.connect(self._reset_wizard)
        btns_row.addWidget(self.btn_nuevo_plan)

        self.btn_abrir_carpeta = QPushButton("📁  Abrir carpeta")
        self.btn_abrir_carpeta.setObjectName("ghostButton")
        self.btn_abrir_carpeta.setEnabled(False)
        self.btn_abrir_carpeta.clicked.connect(self._abrir_carpeta)
        btns_row.addWidget(self.btn_abrir_carpeta)

        self.btn_whatsapp = QPushButton("💬  WhatsApp")
        self.btn_whatsapp.setObjectName("btnWhatsApp")
        self.btn_whatsapp.setEnabled(False)
        self.btn_whatsapp.clicked.connect(self._enviar_whatsapp)
        btns_row.addWidget(self.btn_whatsapp)

        btns_row.addStretch()
        layout.addLayout(btns_row)
        layout.addStretch()
        return page

    # ── Navegación del wizard ─────────────────────────────────────────────────

    def _ir_a_paso(self, paso: int) -> None:
        self._step_actual = paso
        self._stack.setCurrentIndex(paso)
        self._actualizar_steps(paso)

    def iniciar_con_cliente(self, cliente: dict) -> None:
        """Inicia el wizard con un cliente ya seleccionado (desde ClientesPanel)."""
        self._cargar_cliente_de_dict(cliente)
        self._ir_a_paso(1)

    def iniciar_plan_rapido(self, cliente: dict) -> None:
        """Plan rápido: carga cliente + última configuración y genera directo."""
        self._cargar_cliente_de_dict(cliente)
        self._restaurar_preferencias_plan()
        self._ir_a_paso(1)
        # Auto-trigger generation after brief UI update
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._on_generar_click)

    # ── Clientes recientes ─────────────────────────────────────────────────────

    def _mostrar_clientes_recientes(self) -> None:
        """Muestra los últimos 10 clientes activos en el paso 1."""
        self._limpiar_resultados()
        try:
            recientes = self.gestor_bd.obtener_clientes_recientes(limite=10)
        except Exception:
            recientes = []

        if not recientes:
            lbl = QLabel("No hay clientes registrados aún. Crea uno nuevo con el botón de arriba.")
            lbl.setObjectName("clienteInfo")
            self._results_layout.addWidget(lbl)
            return

        header = QLabel("⏱  Clientes recientes")
        header.setObjectName("sectionTitle")
        self._results_layout.addWidget(header)
        for c in recientes:
            row = self._crear_cliente_row(c)
            self._results_layout.addWidget(row)

    def _limpiar_resultados(self) -> None:
        """Limpia todos los widgets del contenedor de resultados."""
        while self._results_layout.count() > 0:
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Lógica paso 1 ─────────────────────────────────────────────────────────

    def _on_buscar_cliente(self, texto: str) -> None:
        self._limpiar_resultados()

        if not texto.strip():
            self._mostrar_clientes_recientes()
            return

        try:
            clientes = self.gestor_bd.buscar_clientes(texto, solo_activos=True, limite=5)
        except Exception:
            clientes = []

        if not clientes:
            lbl = QLabel("No se encontraron clientes.")
            lbl.setObjectName("clienteInfo")
            self._results_layout.addWidget(lbl)
            return

        for c in clientes:
            row = self._crear_cliente_row(c)
            self._results_layout.addWidget(row)

    def _crear_cliente_row(self, cliente: dict) -> QFrame:
        """Crea una fila clickeable para un cliente en los resultados."""
        row = QFrame()
        row.setObjectName("clienteRow")
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Avatar
        from ui_desktop.pyside.widgets.avatar_widget import AvatarWidget
        idx = hash(cliente.get("id_cliente", "")) % 7
        avatar = AvatarWidget(cliente.get("nombre", "?"), size=36, color_idx=idx)
        layout.addWidget(avatar)

        # Info
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        nombre_lbl = QLabel(cliente.get("nombre", "—"))
        nombre_lbl.setObjectName("clienteNombre")
        info_col.addWidget(nombre_lbl)
        detalle = QLabel(
            f"{cliente.get('objetivo', '—')} · {cliente.get('edad', '—')} años · "
            f"{cliente.get('peso_kg', '—')} kg"
        )
        detalle.setObjectName("clienteInfo")
        info_col.addWidget(detalle)
        layout.addLayout(info_col)
        layout.addStretch()

        # Botón seleccionar
        btn = QPushButton("✅  Seleccionar")
        btn.setObjectName("primaryButton")
        _c = dict(cliente)
        btn.clicked.connect(lambda _, cl=_c: self._on_seleccionar_cliente(cl))
        layout.addWidget(btn)

        return row

    def _on_seleccionar_cliente(self, cliente: dict) -> None:
        self._cargar_cliente_de_dict(cliente)
        self._ir_a_paso(1)

    def _cargar_cliente_de_dict(self, cliente: dict) -> None:
        """Construye un ClienteEvaluacion desde un dict de BD."""
        nivel = cliente.get("nivel_actividad") or "moderada"
        self._cliente_actual = ClienteEvaluacion(
            nombre=cliente.get("nombre", ""),
            telefono=cliente.get("telefono") or None,
            edad=int(cliente.get("edad") or 25),
            peso_kg=float(cliente.get("peso_kg") or 70),
            estatura_cm=float(cliente.get("estatura_cm") or 170),
            grasa_corporal_pct=float(cliente.get("grasa_corporal_pct") or 15),
            nivel_actividad=nivel,
            objetivo=cliente.get("objetivo") or "Mantenimiento",
        )
        if cliente.get("id_cliente"):
            self._cliente_actual.id_cliente = cliente["id_cliente"]
        self._cliente_actual.factor_actividad = FACTORES_ACTIVIDAD.get(nivel, 1.375)

        # Actualizar info en página 2
        self.lbl_cliente_info.setText(
            f"👤  {self._cliente_actual.nombre}  ·  {self._cliente_actual.objetivo}  "
            f"·  {self._cliente_actual.edad} años  ·  {self._cliente_actual.peso_kg} kg"
        )

    # ── Dialog para nuevo cliente ─────────────────────────────────────────────

    def _abrir_dialogo_nuevo_cliente(self) -> None:
        """Abre el diálogo unificado para registrar un nuevo cliente."""
        from PySide6.QtWidgets import QDialog
        
        dlg = DialogoRegistroCliente(
            gestor_bd=self.gestor_bd,
            modo="registrar_y_continuar",
            parent=self
        )
        result = dlg.exec()
        if result == QDialog.DialogCode.Accepted and dlg.cliente_registrado:
            # Construir ClienteEvaluacion desde los datos registrados
            datos = dlg.cliente_registrado
            self._cliente_actual = ClienteEvaluacion(
                nombre=datos["nombre"],
                telefono=datos.get("telefono"),
                edad=datos["edad"],
                peso_kg=datos["peso_kg"],
                estatura_cm=datos["estatura_cm"],
                grasa_corporal_pct=datos.get("grasa_corporal_pct", 15.0),
                nivel_actividad=datos["nivel_actividad"],
                objetivo=datos["objetivo"],
            )
            self._cliente_actual.factor_actividad = datos.get("factor_actividad", 1.375)
            self._cliente_actual.id_cliente = datos.get("id_cliente")
            
            # Actualizar badge de cliente en paso 2
            self.lbl_cliente_info.setText(
                f"👤  {self._cliente_actual.nombre}  ·  {self._cliente_actual.objetivo}  "
                f"·  {self._cliente_actual.edad} años  ·  {self._cliente_actual.peso_kg} kg"
            )
            
            # Ir directamente al paso 2 (parámetros del plan)
            self._ir_a_paso(1)

    # ── Lógica paso 2 ─────────────────────────────────────────────────────────

    def _cambiar_tipo(self, tipo: str) -> None:
        es_fijo = (tipo == "menu_fijo")
        self.btn_menu_fijo.setChecked(es_fijo)
        self.btn_con_opciones.setChecked(not es_fijo)
        self.btn_menu_fijo.setObjectName(
            "toggleButtonActive" if es_fijo else "toggleButtonInactive"
        )
        self.btn_con_opciones.setObjectName(
            "toggleButtonActive" if not es_fijo else "toggleButtonInactive"
        )
        for btn in (self.btn_menu_fijo, self.btn_con_opciones):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_plantilla_change(self, label: str) -> None:
        key = PLANTILLAS_POR_LABEL.get(label, "perdida_grasa")
        data = PLANTILLAS_CLIENTE.get(key, {})
        desc = data.get("descripcion", "")
        self.lbl_plantilla_desc.setText(desc)

    def _restaurar_preferencias_plan(self) -> None:
        """Restaura la última plantilla y tipo de plan usados."""
        last_plantilla = self._prefs.obtener("ultima_plantilla")
        last_tipo = self._prefs.obtener("ultimo_tipo_plan", "menu_fijo")
        if last_plantilla:
            idx = self.combo_plantilla.findText(last_plantilla)
            if idx >= 0:
                self.combo_plantilla.setCurrentIndex(idx)
        if last_tipo == "con_opciones":
            self._cambiar_tipo("con_opciones")

    def _guardar_preferencias_plan(self) -> None:
        """Persiste la plantilla y tipo de plan seleccionados."""
        datos = self._prefs.cargar()
        datos["ultima_plantilla"] = self.combo_plantilla.currentText()
        datos["ultimo_tipo_plan"] = self._tipo_plan_activo()
        self._prefs.guardar(datos)

    def _tipo_plan_activo(self) -> str:
        return "menu_fijo" if self.btn_menu_fijo.isChecked() else "con_opciones"

    def _on_generar_click(self) -> None:
        if self._cliente_actual is None:
            mostrar_toast(self, "Selecciona o registra un cliente primero.", "warning")
            return

        if getattr(self, '_generating', False):
            return

        # Guardar preferencias de plantilla/tipo para próxima vez
        self._guardar_preferencias_plan()

        # Aplicar plantilla al objetivo
        plantilla_lbl = self.combo_plantilla.currentText()
        plantilla_key = PLANTILLAS_POR_LABEL.get(plantilla_lbl, "perdida_grasa")
        objetivo_motor = PLANTILLAS_CLIENTE.get(
            plantilla_key, PLANTILLAS_CLIENTE.get("perdida_grasa", {})
        ).get("objetivo_motor", self._cliente_actual.objetivo)
        self._cliente_actual.objetivo = objetivo_motor
        self._cliente_actual.plantilla_tipo = plantilla_key

        self._ir_a_paso(2)
        self.btn_whatsapp.setEnabled(False)
        self.btn_abrir_carpeta.setEnabled(False)
        self.lbl_resultado.setText("Generando plan nutricional...")
        self.lbl_resultado.setObjectName("loadingLabel")
        self.lbl_resultado.style().unpolish(self.lbl_resultado)
        self.lbl_resultado.style().polish(self.lbl_resultado)
        self.lbl_pdf_ruta.setText("")
        self.textbox_log.clear()
        self.progress.reset()
        self.progress.setVisible(True)

        self.btn_generar.setEnabled(False)
        self._generating = True
        thread = threading.Thread(target=self._procesar_en_hilo, daemon=True)
        thread.start()

    # ── Hilo de procesamiento ─────────────────────────────────────────────────

    def _procesar_en_hilo(self) -> None:
        try:
            self._sig.log_msg.emit("Iniciando cálculo nutricional...")
            self._sig.set_progress.emit(0.1, "Calculando objetivo calórico...")

            cliente = self._cliente_actual
            cliente = MotorNutricional.calcular_motor(cliente)
            self._sig.log_msg.emit(
                f"Objetivo: {cliente.kcal_objetivo:.0f} kcal "
                f"(GET: {cliente.get_total:.0f} kcal)"
            )

            self._sig.set_progress.emit(0.3, "Armando plan de comidas...")

            tipo = self._tipo_plan_activo()
            os.makedirs(CARPETA_PLANES, exist_ok=True)

            if tipo == "con_opciones":
                from core.generador_opciones import ConstructorPlanConOpciones
                from core.exportador_opciones import GeneradorPDFConOpciones

                plan = ConstructorPlanConOpciones.construir(
                    cliente, plan_numero=1,
                    directorio_planes=CARPETA_PLANES,
                    num_opciones_por_macro=3,
                )
                self._sig.set_progress.emit(0.7, "Exportando PDF...")

                fecha = datetime.now().strftime("%Y-%m-%d")
                hora = datetime.now().strftime("%H-%M-%S")
                nombre_san = re.sub(r"[^a-zA-Z0-9_]", "", cliente.nombre.replace(" ", "_"))
                carpeta_cli = Path(CARPETA_SALIDA) / nombre_san
                carpeta_cli.mkdir(parents=True, exist_ok=True)

                ruta_pdf = str(carpeta_cli / f"{nombre_san}_OPCIONES_{fecha}_{hora}.pdf")
                gen = GeneradorPDFConOpciones(ruta_pdf)
                ruta_pdf = gen.generar(cliente, plan)
                if not (ruta_pdf and os.path.exists(ruta_pdf)):
                    ruta_pdf = None

                try:
                    ruta_xl = str(carpeta_cli / f"{nombre_san}_OPCIONES_{fecha}_{hora}.xlsx")
                    ExportadorMultiformato.a_excel(cliente, plan, ruta_xl)
                    self._sig.log_msg.emit(f"Excel: {Path(ruta_xl).name}")
                except Exception as exc:
                    self._sig.log_msg.emit(f"Excel no disponible: {exc}")

            else:
                plan = ConstructorPlanNuevo.construir(
                    cliente, plan_numero=1, directorio_planes=CARPETA_PLANES
                )
                self._sig.set_progress.emit(0.6, "Mostrando preview...")

                self._preview_confirmed = False
                self._preview_event = threading.Event()
                self._sig.show_preview.emit(cliente, plan)
                self._preview_event.wait()

                if not self._preview_confirmed:
                    self._sig.log_msg.emit("Generación cancelada.")
                    self._sig.set_progress.emit(0.0, "Cancelado")
                    self._sig.btn_spinner.emit(False)
                    return

                self._sig.set_progress.emit(0.8, "Exportando PDF...")

                fecha = datetime.now().strftime("%Y-%m-%d")
                hora = datetime.now().strftime("%H-%M-%S")
                nombre_san = re.sub(r"[^a-zA-Z0-9_]", "", cliente.nombre.replace(" ", "_"))
                carpeta_cli = Path(CARPETA_SALIDA) / nombre_san
                carpeta_cli.mkdir(parents=True, exist_ok=True)

                ruta_pdf = str(carpeta_cli / f"{nombre_san}_{fecha}_{hora}.pdf")
                pdf_gen = PDFGenerator()
                datos_pdf = PDFGenerator.datos_from_cliente(cliente, plan)
                ruta_pdf = str(pdf_gen.generar_plan(datos_pdf, Path(ruta_pdf)))
                if not (ruta_pdf and os.path.exists(ruta_pdf)):
                    ruta_pdf = None

                try:
                    ruta_xl = str(carpeta_cli / f"{nombre_san}_{fecha}_{hora}.xlsx")
                    ExportadorMultiformato.a_excel(cliente, plan, ruta_xl)
                    self._sig.log_msg.emit(f"Excel: {Path(ruta_xl).name}")
                except Exception as exc:
                    self._sig.log_msg.emit(f"Excel no disponible: {exc}")

            # Guardar en BD
            if self.gestor_bd:
                try:
                    self.gestor_bd.registrar_cliente(cliente)
                    if ruta_pdf:
                        self.gestor_bd.registrar_plan_generado(
                            cliente, plan, ruta_pdf, tipo_plan=tipo
                        )
                    self._sig.log_msg.emit("Guardado en BD correctamente.")
                except Exception as exc:
                    logger.warning("[PLAN] Error BD: %s", exc)

            self._sig.done.emit(ruta_pdf or "")

        except ValueError as ve:
            self._sig.error_msg.emit(f"Error de validación: {ve}")
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self._sig.error_msg.emit(f"Error inesperado: {exc}")
        finally:
            self._generating = False
            self._sig.btn_spinner.emit(False)

    # ── Callbacks de señales ──────────────────────────────────────────────────

    def _abrir_preview(self, cliente, plan: dict) -> None:
        from ui_desktop.pyside.ventana_preview import PlanPreviewWindow
        dlg = PlanPreviewWindow(self, cliente, plan)
        result = dlg.exec()
        self._preview_confirmed = (result == dlg.Accepted)
        if self._preview_event:
            self._preview_event.set()

    def _on_done(self, ruta_pdf: str) -> None:
        self._ultimo_pdf = ruta_pdf or None
        self.progress.complete("✓ Plan generado exitosamente")
        self.lbl_resultado.setText("✅  Plan nutricional generado con éxito")
        self.lbl_resultado.setObjectName("successLabel")
        self.lbl_resultado.style().unpolish(self.lbl_resultado)
        self.lbl_resultado.style().polish(self.lbl_resultado)
        if self._ultimo_pdf:
            self.lbl_pdf_ruta.setText(f"📄  {self._ultimo_pdf}")
            self.btn_abrir_carpeta.setEnabled(True)
            self.btn_whatsapp.setEnabled(
                bool(self._cliente_actual and self._cliente_actual.telefono)
            )
        self.btn_generar.setEnabled(True)

        # Mostrar resumen de macronutrientes
        cli = self._cliente_actual
        if cli and cli.kcal_objetivo:
            self._lbl_macro_kcal.setText(f"{cli.kcal_objetivo:.0f} kcal")
            self._lbl_macro_prot.setText(f"{cli.proteina_g:.0f} g" if cli.proteina_g else "—")
            self._lbl_macro_carbs.setText(f"{cli.carbs_g:.0f} g" if cli.carbs_g else "—")
            self._lbl_macro_grasa.setText(f"{cli.grasa_g:.0f} g" if cli.grasa_g else "—")
            self._macro_card.setVisible(True)

    def _on_error(self, msg: str) -> None:
        self.progress.setVisible(False)
        self.lbl_resultado.setText(f"❌  {msg}")
        self.lbl_resultado.setObjectName("errorLabel")
        self.lbl_resultado.style().unpolish(self.lbl_resultado)
        self.lbl_resultado.style().polish(self.lbl_resultado)
        self.btn_generar.setEnabled(True)
        mostrar_toast(self, msg, "error")

    def _set_btn_spinner(self, spin: bool) -> None:
        self.btn_generar.setEnabled(not spin)
        self.btn_generar.setText("Procesando..." if spin else "⚡  Generar Plan")

    def _log(self, mensaje: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.textbox_log.appendPlainText(f"[{ts}] {mensaje}")
        self.textbox_log.verticalScrollBar().setValue(
            self.textbox_log.verticalScrollBar().maximum()
        )

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _abrir_carpeta(self) -> None:
        if self._ultimo_pdf and os.path.exists(self._ultimo_pdf):
            abrir_carpeta_pdf(os.path.dirname(self._ultimo_pdf))
        else:
            abrir_carpeta_pdf()

    def _enviar_whatsapp(self) -> None:
        if not self._ultimo_pdf or not os.path.exists(self._ultimo_pdf):
            mostrar_toast(self, "Primero genera el plan.", "error")
            return
        if not self._cliente_actual or not self._cliente_actual.telefono:
            mostrar_toast(self, "El cliente no tiene teléfono registrado.", "warning")
            return
        tel = self._cliente_actual.telefono
        nombre = self._cliente_actual.nombre
        msg = (
            f"Hola {nombre} 💪 Tu plan nutricional personalizado está listo. "
            "Aquí está tu PDF para que lo revises cuando quieras. ¡Éxito!"
        )
        url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
        webbrowser.open(url)

    def _reset_wizard(self) -> None:
        """Reinicia el wizard para generar un nuevo plan."""
        self._cliente_actual = None
        self._ultimo_pdf = None
        self.entry_busqueda.clear()
        self._mostrar_clientes_recientes()
        self.lbl_cliente_info.setText("Sin cliente seleccionado")
        self.resultado_container.setVisible(True)
        self.textbox_log.clear()
        self.progress.reset()
        self.btn_generar.setEnabled(True)
        self._macro_card.setVisible(False)
        self._ir_a_paso(0)
