# -*- coding: utf-8 -*-
"""
InstructoresPanel — Módulo de gestión de instructores del gimnasio.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QComboBox,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ui_desktop.pyside.widgets.empty_state import TableEmptyState
from ui_desktop.pyside.widgets.toast import mostrar_toast
from utils.logger import logger
from design_system.tokens import Colors


class DialogoNuevoInstructor(QDialog):
    """Diálogo para crear nuevo instructor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Instructor")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre completo")
        form.addRow("Nombre:", self.input_nombre)

        self.combo_especialidad = QComboBox()
        self.combo_especialidad.addItems([
            "Entrenamiento Personal", "CrossFit", "Spinning", "Yoga",
            "Pilates", "Funcional", "Musculación", "Cardio", "Nutrición"
        ])
        form.addRow("Especialidad:", self.combo_especialidad)

        self.input_horario = QLineEdit()
        self.input_horario.setPlaceholderText("Ej: Lunes a Viernes 8:00 - 14:00")
        form.addRow("Horario:", self.input_horario)

        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["Activo", "Inactivo", "Vacaciones"])
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
        return {
            "nombre": self.input_nombre.text().strip(),
            "especialidad": self.combo_especialidad.currentText(),
            "clases": 0,
            "horario": self.input_horario.text().strip(),
            "estado": self.combo_estado.currentText(),
        }


class InstructoresPanel(QWidget):
    """Panel de gestión de instructores."""

    instructor_creado = Signal(dict)

    def __init__(self, gestor_bd=None, parent=None):
        super().__init__(parent)
        self.gestor_bd = gestor_bd
        self._instructores: list[dict] = []
        self._setup_ui()
        self._cargar_instructores()

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
        self._crear_tabla()

    def _crear_header(self) -> None:
        header = QFrame()
        header.setObjectName("headerFrame")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 16)

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("Instructores")
        title.setObjectName("pageTitle")
        left.addWidget(title)
        subtitle = QLabel("Equipo de entrenadores y especialistas")
        subtitle.setObjectName("pageSubtitle")
        left.addWidget(subtitle)
        layout.addLayout(left)
        layout.addStretch()

        self.btn_nuevo = QPushButton("👨‍🏫  Nuevo Instructor")
        self.btn_nuevo.setObjectName("primaryButton")
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.setFixedHeight(42)
        self.btn_nuevo.setToolTip("Agregar un nuevo instructor al equipo")
        self.btn_nuevo.clicked.connect(self._nuevo_instructor)
        layout.addWidget(self.btn_nuevo)

        self._layout.addWidget(header)

    def _crear_tabla(self) -> None:
        container = QFrame()
        container.setObjectName("chartContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Equipo")
        title.setObjectName("chartTitle")
        layout.addWidget(title)

        self._tabla = QTableWidget(0, 5)
        self._tabla.setHorizontalHeaderLabels(
            ["Nombre", "Especialidad", "Clases", "Horario", "Estado"]
        )
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._tabla)
        
        # Empty state for empty table
        self._empty_state = TableEmptyState(
            preset="instructores",
            on_action=self._nuevo_instructor,
            parent=self
        )
        layout.addWidget(self._empty_state)

        self._layout.addWidget(container)

    def _nuevo_instructor(self) -> None:
        """Abre diálogo para crear nuevo instructor."""
        dialogo = DialogoNuevoInstructor(self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            data = dialogo.get_data()
            if not data["nombre"]:
                mostrar_toast(self, "⚠️ Ingresa el nombre del instructor.", "warning")
                return
            self._instructores.append(data)
            self._actualizar_tabla()
            mostrar_toast(self, "✅ Instructor agregado exitosamente", "success")
            self.instructor_creado.emit(data)
            logger.info(f"🏋️ Nuevo instructor: {data['nombre']} - {data['especialidad']}")

    def _cargar_instructores(self) -> None:
        """Carga instructores desde la base de datos."""
        try:
            if self.gestor_bd and hasattr(self.gestor_bd, "obtener_instructores"):
                self._instructores = self.gestor_bd.obtener_instructores() or []
            else:
                self._instructores = []
            self._actualizar_tabla()
            logger.info(f"🏋️ Cargados {len(self._instructores)} instructores")
        except Exception as e:
            logger.warning(f"[InstructoresPanel] Error cargando instructores: {e}")
            self._instructores = []
            self._actualizar_tabla()

    def _actualizar_tabla(self) -> None:
        """Actualiza la tabla con los instructores actuales."""
        if not self._instructores:
            self._tabla.hide()
            self._empty_state.show()
            return

        self._empty_state.hide()
        self._tabla.show()
        self._tabla.setRowCount(len(self._instructores))

        for row, instructor in enumerate(self._instructores):
            self._tabla.setItem(row, 0, QTableWidgetItem(instructor.get("nombre", "")))
            self._tabla.setItem(row, 1, QTableWidgetItem(instructor.get("especialidad", "")))
            self._tabla.setItem(row, 2, QTableWidgetItem(str(instructor.get("clases", 0))))
            self._tabla.setItem(row, 3, QTableWidgetItem(instructor.get("horario", "")))
            estado = instructor.get("estado", "Activo")
            item_estado = QTableWidgetItem(estado)
            if estado == "Activo":
                item_estado.setForeground(QColor(Colors.SUCCESS))
            elif estado == "Inactivo":
                item_estado.setForeground(QColor(Colors.ERROR))
            else:
                item_estado.setForeground(QColor(Colors.WARNING))
            self._tabla.setItem(row, 4, item_estado)

    def refresh(self) -> None:
        """Recarga datos de instructores."""
        logger.info("🏋️ Refrescando panel de instructores")
        self._cargar_instructores()
