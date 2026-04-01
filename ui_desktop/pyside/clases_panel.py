# -*- coding: utf-8 -*-
"""
ClasesPanel — Módulo de gestión de clases y horarios del gimnasio.
"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QComboBox, QTimeEdit,
    QPushButton, QScrollArea, QSpinBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ui_desktop.pyside.widgets.empty_state import TableEmptyState
from ui_desktop.pyside.widgets.toast import mostrar_toast
from utils.logger import logger
from design_system.tokens import Colors


class DialogoNuevaClase(QDialog):
    """Diálogo para crear nueva clase."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Clase")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Spinning, Yoga, CrossFit")
        form.addRow("Clase:", self.input_nombre)

        self.input_instructor = QLineEdit()
        self.input_instructor.setPlaceholderText("Nombre del instructor")
        form.addRow("Instructor:", self.input_instructor)

        self.combo_dia = QComboBox()
        self.combo_dia.addItems(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        form.addRow("Día:", self.combo_dia)

        self.hora = QTimeEdit()
        self.hora.setTime(datetime.now().time())
        form.addRow("Hora:", self.hora)

        self.spin_cupo = QSpinBox()
        self.spin_cupo.setRange(1, 100)
        self.spin_cupo.setValue(20)
        form.addRow("Cupo máximo:", self.spin_cupo)

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
            "clase": self.input_nombre.text().strip(),
            "instructor": self.input_instructor.text().strip(),
            "dia": self.combo_dia.currentText(),
            "hora": self.hora.time().toString("HH:mm"),
            "cupo": self.spin_cupo.value(),
            "inscritos": 0,
        }


class ClasesPanel(QWidget):
    """Panel de gestión de clases, horarios e instructores."""

    clase_creada = Signal(dict)

    def __init__(self, gestor_bd=None, parent=None):
        super().__init__(parent)
        self.gestor_bd = gestor_bd
        self._clases: list[dict] = []
        self._setup_ui()
        self._cargar_clases()

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
        self._crear_horarios()

    def _crear_header(self) -> None:
        header = QFrame()
        header.setObjectName("headerFrame")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 16)

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("Clases y Horarios")
        title.setObjectName("pageTitle")
        left.addWidget(title)
        subtitle = QLabel("Programación semanal de clases del gimnasio")
        subtitle.setObjectName("pageSubtitle")
        left.addWidget(subtitle)
        layout.addLayout(left)
        layout.addStretch()

        self.btn_nueva = QPushButton("🏋️  Nueva Clase")
        self.btn_nueva.setObjectName("primaryButton")
        self.btn_nueva.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nueva.setFixedHeight(42)
        self.btn_nueva.setToolTip("Programar una nueva clase en el horario")
        self.btn_nueva.clicked.connect(self._nueva_clase)
        layout.addWidget(self.btn_nueva)

        self._layout.addWidget(header)

    def _crear_horarios(self) -> None:
        container = QFrame()
        container.setObjectName("chartContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Horario Semanal")
        title.setObjectName("chartTitle")
        layout.addWidget(title)

        self._tabla = QTableWidget(0, 6)
        self._tabla.setHorizontalHeaderLabels(
            ["Clase", "Instructor", "Día", "Hora", "Cupo", "Inscritos"]
        )
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._tabla)
        
        # Empty state for empty table
        self._empty_state = TableEmptyState(
            preset="clases",
            on_action=self._nueva_clase,
            parent=self
        )
        layout.addWidget(self._empty_state)

        self._layout.addWidget(container)

    def _nueva_clase(self) -> None:
        """Abre diálogo para crear nueva clase."""
        dialogo = DialogoNuevaClase(self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            data = dialogo.get_data()
            if not data["clase"]:
                mostrar_toast(self, "⚠️ Ingresa el nombre de la clase.", "warning")
                return
            self._clases.append(data)
            self._actualizar_tabla()
            mostrar_toast(self, "✅ Clase programada exitosamente", "success")
            self.clase_creada.emit(data)
            logger.info(f"🗓️ Nueva clase creada: {data['clase']} - {data['dia']} {data['hora']}")

    def _cargar_clases(self) -> None:
        """Carga clases desde la base de datos."""
        try:
            if self.gestor_bd and hasattr(self.gestor_bd, "obtener_clases"):
                self._clases = self.gestor_bd.obtener_clases() or []
            else:
                self._clases = []
            self._actualizar_tabla()
            logger.info(f"🗓️ Cargadas {len(self._clases)} clases")
        except Exception as e:
            logger.warning(f"[ClasesPanel] Error cargando clases: {e}")
            self._clases = []
            self._actualizar_tabla()

    def _actualizar_tabla(self) -> None:
        """Actualiza la tabla con las clases actuales."""
        if not self._clases:
            self._tabla.hide()
            self._empty_state.show()
            return

        self._empty_state.hide()
        self._tabla.show()
        self._tabla.setRowCount(len(self._clases))

        for row, clase in enumerate(self._clases):
            self._tabla.setItem(row, 0, QTableWidgetItem(clase.get("clase", "")))
            self._tabla.setItem(row, 1, QTableWidgetItem(clase.get("instructor", "")))
            self._tabla.setItem(row, 2, QTableWidgetItem(clase.get("dia", "")))
            self._tabla.setItem(row, 3, QTableWidgetItem(clase.get("hora", "")))
            self._tabla.setItem(row, 4, QTableWidgetItem(str(clase.get("cupo", 0))))
            inscritos = clase.get("inscritos", 0)
            cupo = clase.get("cupo", 0)
            item_inscritos = QTableWidgetItem(f"{inscritos}/{cupo}")
            if inscritos >= cupo:
                item_inscritos.setForeground(QColor(Colors.ERROR))
            elif inscritos >= cupo * 0.8:
                item_inscritos.setForeground(QColor(Colors.WARNING))
            else:
                item_inscritos.setForeground(QColor(Colors.SUCCESS))
            self._tabla.setItem(row, 5, item_inscritos)

    def refresh(self) -> None:
        """Recarga datos de clases."""
        logger.info("🗓️ Refrescando panel de clases")
        self._cargar_clases()
