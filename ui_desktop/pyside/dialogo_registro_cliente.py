# -*- coding: utf-8 -*-
"""
Diálogo unificado para registrar/editar clientes — MetodoBase 2026.

Este componente centraliza toda la lógica de registro y edición de clientes,
garantizando una UI/UX consistente en toda la aplicación.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout,
    QWidget,
)

from config.constantes import (
    FACTORES_ACTIVIDAD, NIVELES_ACTIVIDAD, OBJETIVOS_VALIDOS,
)
from core.modelos import ClienteEvaluacion
from design_system.tokens import Colors
from src.gestor_bd import GestorBDClientes
from ui_desktop.pyside.widgets.toast import mostrar_toast
from ui_desktop.pyside.widgets.animations import fade_in_dialog
from utils.logger import logger


class DialogoRegistroCliente(QDialog):
    """
    Diálogo unificado para registrar un nuevo cliente.
    
    Este diálogo centraliza el formulario usado desde:
    - Panel de clientes (botón "Registrar cliente")
    - Panel de generar plan (botón "Nuevo cliente")
    - Dashboard (cualquier botón que lleve a registro)
    
    Parámetros:
    -----------
    gestor_bd : GestorBDClientes
        Gestor de base de datos para operaciones CRUD.
    modo : str
        'registrar' (solo registrar) o 'registrar_y_continuar' (registrar y generar plan).
    cliente_data : dict | None
        Si se proporciona, el diálogo actúa como editor en lugar de registro.
    parent : QWidget | None
        Widget padre del diálogo.
    
    Atributos públicos después de accept():
    ----------------------------------------
    cliente_registrado : dict | None
        Diccionario con los datos del cliente registrado.
    generar_plan : bool
        True si el usuario eligió "Registrar y generar plan".
    """

    def __init__(
        self,
        gestor_bd: GestorBDClientes,
        modo: str = "registrar",
        cliente_data: dict | None = None,
        parent=None
    ):
        super().__init__(parent)
        self.gestor_bd = gestor_bd
        self.modo = modo
        self.cliente_data = cliente_data
        self.es_edicion = bool(cliente_data)
        
        # Resultados
        self.cliente_registrado: dict | None = None
        self.generar_plan = False

        # Timer para búsqueda de duplicados
        self._dup_timer = QTimer(self)
        self._dup_timer.setSingleShot(True)
        self._dup_timer.setInterval(400)
        self._dup_timer.timeout.connect(self._buscar_duplicados)

        self._setup_window()
        self._build_ui()
        
        if self.es_edicion:
            self._rellenar_campos()
        
        # Micro-animation: dialog fade-in
        fade_in_dialog(self, duration=300)

    # ══════════════════════════════════════════════════════════════════════════
    # WINDOW SETUP
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_window(self) -> None:
        if self.es_edicion:
            self.setWindowTitle("Editar Cliente")
        else:
            self.setWindowTitle("Registrar Nuevo Cliente")
        
        self.setMinimumWidth(680)
        self.setMinimumHeight(600)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

    # ══════════════════════════════════════════════════════════════════════════
    # UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────────────
        header_container = QWidget()
        header_container.setObjectName("transparentWidget")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 16)
        header_layout.setSpacing(12)
        
        # Icon badge
        icon_badge = QLabel("👤")
        icon_badge.setFixedSize(44, 44)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setObjectName("kpiIcon")
        icon_badge.setProperty("color", "yellow")
        header_layout.addWidget(icon_badge)
        
        # Title and subtitle
        title_container = QWidget()
        title_container.setObjectName("transparentWidget")
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        
        title_text = "Editar Cliente" if self.es_edicion else "Registrar Nuevo Cliente"
        title = QLabel(title_text)
        title.setObjectName("formSectionHeader")
        title_layout.addWidget(title)
        
        subtitle_text = "Actualice los datos del cliente" if self.es_edicion else "Complete los datos para registrar un nuevo cliente"
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("clienteInfo")
        title_layout.addWidget(subtitle)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        layout.addWidget(header_container)
        
        # ── Divider ───────────────────────────────────────────────────────────
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {Colors.BORDER_SUBTLE};")
        layout.addWidget(divider)
        layout.addSpacing(4)

        # ═══════════════════════════════════════════════════════════════════════
        # SECTION 1: Información Personal
        # ═══════════════════════════════════════════════════════════════════════
        
        layout.addWidget(self._create_section_header("Información Personal", "📋"))
        
        # Grid layout for personal info
        grid1 = QGridLayout()
        grid1.setSpacing(12)
        grid1.setColumnStretch(0, 2)  # Nombre takes 2/3
        grid1.setColumnStretch(1, 1)  # Teléfono takes 1/3
        
        # Nombre
        grid1.addWidget(self._create_field_label("Nombre completo", required=True), 0, 0)
        self.entry_nombre = QLineEdit()
        self.entry_nombre.setPlaceholderText("Ej: Juan Pérez")
        self.entry_nombre.textChanged.connect(self._validar_form)
        if not self.es_edicion:
            self.entry_nombre.textChanged.connect(lambda _: self._dup_timer.start())
        grid1.addWidget(self.entry_nombre, 1, 0)
        
        self.lbl_error_nombre = QLabel("")
        self.lbl_error_nombre.setObjectName("errorLabel")
        self.lbl_error_nombre.hide()
        grid1.addWidget(self.lbl_error_nombre, 2, 0)

        # Duplicate warning (only for new registrations)
        if not self.es_edicion:
            self.lbl_duplicados = QLabel("")
            self.lbl_duplicados.setObjectName("clienteInfo")
            self.lbl_duplicados.setWordWrap(True)
            self.lbl_duplicados.hide()
            grid1.addWidget(self.lbl_duplicados, 2, 1)
        
        # Teléfono
        grid1.addWidget(self._create_field_label("Teléfono"), 0, 1)
        self.entry_telefono = QLineEdit()
        self.entry_telefono.setPlaceholderText("10 dígitos")
        grid1.addWidget(self.entry_telefono, 1, 1)
        
        layout.addLayout(grid1)
        layout.addSpacing(8)
        
        # ═══════════════════════════════════════════════════════════════════════
        # SECTION 2: Datos Físicos
        # ═══════════════════════════════════════════════════════════════════════
        layout.addWidget(self._create_section_header("Datos Físicos", "📊"))
        
        # Row 1: Edad | Sexo | Objetivo
        grid2 = QGridLayout()
        grid2.setSpacing(12)
        
        # Edad
        grid2.addWidget(self._create_field_label("Edad", required=True), 0, 0)
        self.spin_edad = QSpinBox()
        self.spin_edad.setRange(14, 100)
        self.spin_edad.setValue(25)
        grid2.addWidget(self.spin_edad, 1, 0)
        
        # Sexo
        grid2.addWidget(self._create_field_label("Sexo"), 0, 1)
        self.combo_sexo = QComboBox()
        self.combo_sexo.addItems(["M", "F", "Otro"])
        grid2.addWidget(self.combo_sexo, 1, 1)
        
        # Objetivo
        grid2.addWidget(self._create_field_label("Objetivo", required=True), 0, 2)
        self.combo_objetivo = QComboBox()
        objetivos = OBJETIVOS_VALIDOS if OBJETIVOS_VALIDOS else [
            "Déficit calórico", "Mantenimiento", "Superávit calórico"
        ]
        self.combo_objetivo.addItems(objetivos)
        grid2.addWidget(self.combo_objetivo, 1, 2)
        
        layout.addLayout(grid2)
        layout.addSpacing(8)
        
        # Row 2: Peso | Estatura | % Grasa | Nivel actividad
        grid3 = QGridLayout()
        grid3.setSpacing(12)
        
        # Peso
        grid3.addWidget(self._create_field_label("Peso (kg)", required=True), 0, 0)
        self.spin_peso = QDoubleSpinBox()
        self.spin_peso.setRange(30, 250)
        self.spin_peso.setValue(70.0)
        self.spin_peso.setSingleStep(0.5)
        grid3.addWidget(self.spin_peso, 1, 0)
        
        # Estatura
        grid3.addWidget(self._create_field_label("Estatura (cm)", required=True), 0, 1)
        self.spin_estatura = QDoubleSpinBox()
        self.spin_estatura.setRange(100, 250)
        self.spin_estatura.setValue(170.0)
        grid3.addWidget(self.spin_estatura, 1, 1)
        
        # % Grasa
        grid3.addWidget(self._create_field_label("% Grasa corporal"), 0, 2)
        self.spin_grasa = QDoubleSpinBox()
        self.spin_grasa.setRange(3, 60)
        self.spin_grasa.setValue(15.0)
        self.spin_grasa.setSingleStep(0.5)
        grid3.addWidget(self.spin_grasa, 1, 2)
        
        # Nivel actividad
        grid3.addWidget(self._create_field_label("Actividad", required=True), 0, 3)
        self.combo_actividad = QComboBox()
        niveles = NIVELES_ACTIVIDAD if NIVELES_ACTIVIDAD else [
            "nula", "leve", "moderada", "intensa"
        ]
        self.combo_actividad.addItems(niveles)
        self.combo_actividad.setCurrentText("moderada")
        grid3.addWidget(self.combo_actividad, 1, 3)
        
        layout.addLayout(grid3)
        layout.addSpacing(8)
        
        # ═══════════════════════════════════════════════════════════════════════
        # SECTION 3: Notas Adicionales
        # ═══════════════════════════════════════════════════════════════════════
        layout.addWidget(self._create_section_header("Notas Adicionales", "📝"))
        
        notas_layout = QVBoxLayout()
        notas_layout.setSpacing(4)
        notas_layout.addWidget(self._create_field_label("Observaciones del cliente"))
        
        self.txt_notas = QPlainTextEdit()
        self.txt_notas.setPlaceholderText("Alergias, preferencias, lesiones...")
        self.txt_notas.setFixedHeight(72)
        self.txt_notas.textChanged.connect(self._actualizar_contador_notas)
        notas_layout.addWidget(self.txt_notas)
        
        # Character counter
        self.lbl_contador_notas = QLabel("0 / 500 caracteres")
        self.lbl_contador_notas.setObjectName("clienteInfo")
        self.lbl_contador_notas.setAlignment(Qt.AlignmentFlag.AlignRight)
        notas_layout.addWidget(self.lbl_contador_notas)
        
        layout.addLayout(notas_layout)
        layout.addSpacing(8)

        # ═══════════════════════════════════════════════════════════════════════
        # FOOTER: Divider + Action Buttons
        # ═══════════════════════════════════════════════════════════════════════
        
        divider2 = QFrame()
        divider2.setFixedHeight(1)
        divider2.setStyleSheet(f"background-color: {Colors.BORDER_SUBTLE};")
        layout.addWidget(divider2)
        layout.addSpacing(12)
        
        self._build_buttons(layout)

    def _build_buttons(self, layout: QVBoxLayout) -> None:
        """Construye los botones según el modo."""
        btns = QHBoxLayout()
        btns.setSpacing(12)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnGhost")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        btns.addWidget(btn_cancelar)
        btns.addStretch()
        
        if self.es_edicion:
            # Modo edición: solo un botón "Guardar cambios"
            btn_guardar = QPushButton("✅  Guardar cambios")
            btn_guardar.setObjectName("primaryButton")
            btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_guardar.clicked.connect(self._on_guardar_edicion)
            btns.addWidget(btn_guardar)
        
        elif self.modo == "registrar_y_continuar":
            # Modo generar plan: solo "Registrar y continuar"
            self.btn_registrar = QPushButton("✅  Registrar y continuar →")
            self.btn_registrar.setObjectName("primaryButton")
            self.btn_registrar.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_registrar.setEnabled(False)
            self.btn_registrar.clicked.connect(self._on_registrar)
            btns.addWidget(self.btn_registrar)
        
        else:
            # Modo clientes panel: dos botones
            btn_reg_plan = QPushButton("📋  Registrar y generar plan")
            btn_reg_plan.setObjectName("secondaryButton")
            btn_reg_plan.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_reg_plan.clicked.connect(self._on_registrar_y_generar)
            btns.addWidget(btn_reg_plan)

            self.btn_registrar = QPushButton("Registrar cliente")
            self.btn_registrar.setObjectName("primaryButton")
            self.btn_registrar.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_registrar.setEnabled(False)
            self.btn_registrar.clicked.connect(self._on_registrar)
            btns.addWidget(self.btn_registrar)
        
        layout.addLayout(btns)

    # ══════════════════════════════════════════════════════════════════════════
    # UI HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _create_section_header(self, title: str, icon: str = "") -> QWidget:
        """Creates a premium section header."""
        container = QWidget()
        container.setObjectName("transparentWidget")
        hl = QHBoxLayout(container)
        hl.setContentsMargins(0, 4, 0, 8)
        hl.setSpacing(8)
        
        if icon:
            icon_lbl = QLabel(icon)
            hl.addWidget(icon_lbl)
        
        label = QLabel(title)
        label.setObjectName("formSectionHeader")
        hl.addWidget(label)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {Colors.BORDER_DEFAULT};")
        hl.addWidget(line, 1)
        
        return container

    def _create_field_label(self, text: str, required: bool = False) -> QWidget:
        """Creates a field label with optional required indicator."""
        container = QWidget()
        container.setObjectName("transparentWidget")
        hl = QHBoxLayout(container)
        hl.setContentsMargins(0, 0, 0, 4)
        hl.setSpacing(4)
        
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        hl.addWidget(label)
        
        if required:
            asterisk = QLabel("*")
            asterisk.setObjectName("errorLabel")
            hl.addWidget(asterisk)
        
        hl.addStretch()
        return container

    # ══════════════════════════════════════════════════════════════════════════
    # VALIDATION & LOGIC
    # ══════════════════════════════════════════════════════════════════════════

    def _validar_form(self) -> None:
        """Valida el formulario y habilita/deshabilita el botón de registro."""
        nombre = self.entry_nombre.text().strip()
        ok = bool(nombre)
        
        # Show/hide error message
        if not nombre:
            self.lbl_error_nombre.setText("El nombre es obligatorio")
            self.lbl_error_nombre.show()
            self.entry_nombre.setProperty("validationError", True)
        else:
            self.lbl_error_nombre.hide()
            self.entry_nombre.setProperty("validationError", False)
        
        # Reapply styles
        self.entry_nombre.style().unpolish(self.entry_nombre)
        self.entry_nombre.style().polish(self.entry_nombre)
        
        # Enable/disable submit button
        if hasattr(self, 'btn_registrar'):
            self.btn_registrar.setEnabled(ok)

    def _buscar_duplicados(self) -> None:
        """Busca nombres similares y muestra aviso."""
        if self.es_edicion:
            return
        
        nombre = self.entry_nombre.text().strip()
        if len(nombre) < 3:
            if hasattr(self, 'lbl_duplicados'):
                self.lbl_duplicados.hide()
            return
        
        try:
            dups = self.gestor_bd.buscar_duplicados_nombre(nombre)
            if dups and hasattr(self, 'lbl_duplicados'):
                nombres = ", ".join(d.get("nombre", "") for d in dups[:3])
                self.lbl_duplicados.setText(f"⚠️ Similares: {nombres}")
                self.lbl_duplicados.show()
            elif hasattr(self, 'lbl_duplicados'):
                self.lbl_duplicados.hide()
        except Exception:
            if hasattr(self, 'lbl_duplicados'):
                self.lbl_duplicados.hide()

    def _actualizar_contador_notas(self) -> None:
        """Updates the character counter for the notes textarea."""
        MAX_CHARS = 500
        current = len(self.txt_notas.toPlainText())
        self.lbl_contador_notas.setText(f"{current} / {MAX_CHARS} caracteres")
        
        # Change color based on character count
        if current > MAX_CHARS:
            self.lbl_contador_notas.setStyleSheet(f"color: {Colors.ERROR};")
            # Truncate text if over limit
            cursor = self.txt_notas.textCursor()
            self.txt_notas.setPlainText(self.txt_notas.toPlainText()[:MAX_CHARS])
            cursor.movePosition(cursor.MoveOperation.End)
            self.txt_notas.setTextCursor(cursor)
        elif current > MAX_CHARS * 0.9:
            self.lbl_contador_notas.setStyleSheet(f"color: {Colors.WARNING};")
        else:
            self.lbl_contador_notas.setStyleSheet(f"color: {Colors.TEXT_HINT};")

    def _build_cliente(self) -> ClienteEvaluacion:
        """Construye un ClienteEvaluacion desde los campos del formulario."""
        nivel = self.combo_actividad.currentText()
        cliente = ClienteEvaluacion(
            nombre=self.entry_nombre.text().strip(),
            telefono=self.entry_telefono.text().strip() or None,
            edad=self.spin_edad.value(),
            peso_kg=self.spin_peso.value(),
            estatura_cm=self.spin_estatura.value(),
            grasa_corporal_pct=self.spin_grasa.value(),
            nivel_actividad=nivel,
            objetivo=self.combo_objetivo.currentText(),
        )
        cliente.factor_actividad = FACTORES_ACTIVIDAD.get(nivel, 1.375)
        
        # Si hay ID del cliente (edición), preservarlo
        if self.es_edicion and self.cliente_data:
            cliente.id_cliente = self.cliente_data.get("id_cliente")
        
        return cliente

    # ══════════════════════════════════════════════════════════════════════════
    # ACTION HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_registrar(self) -> None:
        """Registra el cliente y cierra el diálogo."""
        nombre = self.entry_nombre.text().strip()
        if not nombre:
            self._validar_form()
            return

        cliente = self._build_cliente()
        try:
            ok = self.gestor_bd.registrar_cliente(cliente)
            if ok:
                self.cliente_registrado = {
                    "id_cliente": cliente.id_cliente,
                    "nombre": cliente.nombre,
                    "telefono": cliente.telefono,
                    "edad": cliente.edad,
                    "peso_kg": cliente.peso_kg,
                    "estatura_cm": cliente.estatura_cm,
                    "grasa_corporal_pct": cliente.grasa_corporal_pct,
                    "nivel_actividad": cliente.nivel_actividad,
                    "objetivo": cliente.objetivo,
                    "factor_actividad": cliente.factor_actividad,
                }
                self.generar_plan = False
                self.accept()
            else:
                mostrar_toast(self, "❌ No se pudo registrar el cliente.", "error")
        except Exception as exc:
            logger.error("[REGISTRO] Error al registrar cliente: %s", exc)
            mostrar_toast(self, f"❌ Error al registrar: {exc}", "error")

    def _on_registrar_y_generar(self) -> None:
        """Registra el cliente y marca flag para generar plan automáticamente."""
        nombre = self.entry_nombre.text().strip()
        if not nombre:
            self._validar_form()
            return

        cliente = self._build_cliente()
        try:
            ok = self.gestor_bd.registrar_cliente(cliente)
            if ok:
                self.generar_plan = True
                self.cliente_registrado = {
                    "id_cliente": cliente.id_cliente,
                    "nombre": cliente.nombre,
                    "telefono": cliente.telefono,
                    "edad": cliente.edad,
                    "peso_kg": cliente.peso_kg,
                    "estatura_cm": cliente.estatura_cm,
                    "grasa_corporal_pct": cliente.grasa_corporal_pct,
                    "nivel_actividad": cliente.nivel_actividad,
                    "objetivo": cliente.objetivo,
                    "factor_actividad": cliente.factor_actividad,
                }
                self.accept()
            else:
                mostrar_toast(self, "❌ No se pudo registrar el cliente.", "error")
        except Exception as exc:
            logger.error("[REGISTRO] Error al registrar y generar: %s", exc)
            mostrar_toast(self, f"❌ Error al registrar: {exc}", "error")

    def _on_guardar_edicion(self) -> None:
        """Guarda los cambios de un cliente existente."""
        nombre = self.entry_nombre.text().strip()
        if not nombre:
            self._validar_form()
            return

        cliente = self._build_cliente()
        try:
            ok = self.gestor_bd.actualizar_cliente(cliente)
            if ok:
                self.cliente_registrado = {
                    "id_cliente": cliente.id_cliente,
                    "nombre": cliente.nombre,
                    "telefono": cliente.telefono,
                    "edad": cliente.edad,
                    "peso_kg": cliente.peso_kg,
                    "estatura_cm": cliente.estatura_cm,
                    "grasa_corporal_pct": cliente.grasa_corporal_pct,
                    "nivel_actividad": cliente.nivel_actividad,
                    "objetivo": cliente.objetivo,
                    "factor_actividad": cliente.factor_actividad,
                }
                mostrar_toast(self, "✅ Cliente actualizado correctamente.", "success")
                self.accept()
            else:
                mostrar_toast(self, "❌ No se pudo actualizar el cliente.", "error")
        except Exception as exc:
            logger.error("[EDICIÓN] Error al actualizar cliente: %s", exc)
            mostrar_toast(self, f"❌ Error al actualizar: {exc}", "error")

    def _rellenar_campos(self) -> None:
        """Rellena los campos del formulario con los datos del cliente (modo edición)."""
        if not self.cliente_data:
            return
        
        c = self.cliente_data
        self.entry_nombre.setText(c.get("nombre", ""))
        self.entry_telefono.setText(c.get("telefono", "") or "")
        
        if c.get("edad"):
            self.spin_edad.setValue(int(c["edad"]))
        if c.get("peso_kg"):
            self.spin_peso.setValue(float(c["peso_kg"]))
        if c.get("estatura_cm"):
            self.spin_estatura.setValue(float(c["estatura_cm"]))
        if c.get("grasa_corporal_pct"):
            self.spin_grasa.setValue(float(c["grasa_corporal_pct"]))
        
        # Sexo
        sexo = c.get("sexo", "M")
        idx_sexo = self.combo_sexo.findText(sexo, Qt.MatchFlag.MatchContains)
        if idx_sexo >= 0:
            self.combo_sexo.setCurrentIndex(idx_sexo)
        
        # Objetivo
        obj = c.get("objetivo", "")
        idx_obj = self.combo_objetivo.findText(obj, Qt.MatchFlag.MatchContains)
        if idx_obj >= 0:
            self.combo_objetivo.setCurrentIndex(idx_obj)
        
        # Nivel actividad
        nivel = c.get("nivel_actividad", "")
        idx_nivel = self.combo_actividad.findText(nivel, Qt.MatchFlag.MatchContains)
        if idx_nivel >= 0:
            self.combo_actividad.setCurrentIndex(idx_nivel)
