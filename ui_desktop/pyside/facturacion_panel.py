# -*- coding: utf-8 -*-
"""
FacturacionPanel — Módulo de facturación e inventario del gimnasio.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QComboBox, QDateEdit,
    QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)
from PySide6.QtCore import QDate

from ui_desktop.pyside.widgets.kpi_card import KPICard
from ui_desktop.pyside.widgets.empty_state import TableEmptyState
from ui_desktop.pyside.widgets.toast import mostrar_toast
from utils.logger import logger


class FacturacionPanel(QWidget):
    """Panel de facturación, pagos y finanzas."""

    def __init__(self, gestor_bd=None, parent=None):
        super().__init__(parent)
        self.gestor_bd = gestor_bd
        self._movimientos: list[dict] = []
        self._setup_ui()
        self._actualizar_kpis()

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
        self._crear_kpis()
        self._crear_tabla()

    def _crear_header(self) -> None:
        header = QFrame()
        header.setObjectName("headerFrame")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 16)

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("Facturación")
        title.setObjectName("pageTitle")
        left.addWidget(title)
        subtitle = QLabel("Control de pagos, ingresos y egresos")
        subtitle.setObjectName("pageSubtitle")
        left.addWidget(subtitle)
        layout.addLayout(left)
        layout.addStretch()

        btn_nuevo = QPushButton("💰  Nuevo Cobro")
        btn_nuevo.setObjectName("primaryButton")
        btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo.setFixedHeight(42)
        btn_nuevo.setToolTip("Registrar un nuevo cobro o pago")
        btn_nuevo.clicked.connect(self._nuevo_cobro)
        layout.addWidget(btn_nuevo)

        self._layout.addWidget(header)

    def _crear_kpis(self) -> None:
        row = QHBoxLayout()
        row.setSpacing(16)

        self.kpi_ingresos = KPICard("cyan", "💰", 0, "INGRESOS MES", "Total cobrado", "neutral")
        self.kpi_pendientes = KPICard("yellow", "⏳", 0, "PAGOS PENDIENTES", "Por cobrar", "neutral")
        self.kpi_clientes_al_dia = KPICard("purple", "✅", 0, "AL DÍA", "Clientes activos", "up")

        row.addWidget(self.kpi_ingresos)
        row.addWidget(self.kpi_pendientes)
        row.addWidget(self.kpi_clientes_al_dia)

        self._layout.addLayout(row)

    def _crear_tabla(self) -> None:
        container = QFrame()
        container.setObjectName("chartContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Últimos Movimientos")
        title.setObjectName("chartTitle")
        layout.addWidget(title)

        self._tabla = QTableWidget(0, 5)
        self._tabla.setHorizontalHeaderLabels(
            ["Fecha", "Cliente", "Concepto", "Monto", "Estado"]
        )
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._tabla)
        
        # Empty state for empty table
        self._empty_state = TableEmptyState(
            preset="facturacion",
            on_action=self._nuevo_cobro,
            parent=self
        )
        layout.addWidget(self._empty_state)
        
        # Hide table, show empty state by default
        self._tabla.hide()

        self._layout.addWidget(container)

    def _nuevo_cobro(self) -> None:
        """Abrir diálogo para registrar un nuevo cobro/pago."""
        dlg = _DialogoNuevoCobro(self.gestor_bd, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._agregar_movimiento(data)
            logger.info("💰 Nuevo cobro registrado: %s", data)

    def _agregar_movimiento(self, data: dict) -> None:
        """Agrega un movimiento a la tabla y actualiza KPIs."""
        self._movimientos.append(data)
        self._empty_state.hide()
        self._tabla.show()

        row = self._tabla.rowCount()
        self._tabla.insertRow(row)
        self._tabla.setItem(row, 0, QTableWidgetItem(data.get("fecha", "")))
        self._tabla.setItem(row, 1, QTableWidgetItem(data.get("cliente", "")))
        self._tabla.setItem(row, 2, QTableWidgetItem(data.get("concepto", "")))
        self._tabla.setItem(row, 3, QTableWidgetItem(f"${data.get('monto', 0):,.2f}"))
        self._tabla.setItem(row, 4, QTableWidgetItem(data.get("estado", "Pagado")))
        self._actualizar_kpis()

    def _actualizar_kpis(self) -> None:
        """Actualiza KPIs con datos reales."""
        # Ingresos: suma de movimientos pagados
        ingresos = sum(
            m.get("monto", 0) for m in self._movimientos
            if m.get("estado") == "Pagado"
        )
        pendientes = sum(
            1 for m in self._movimientos
            if m.get("estado") in ("Pendiente", "Parcial")
        )
        # Clientes al día from BD
        al_dia = 0
        try:
            if self.gestor_bd:
                activos = self.gestor_bd.buscar_clientes("", solo_activos=True, limite=10000)
                al_dia = len(activos)
        except Exception:
            pass

        self.kpi_ingresos.set_value(int(ingresos))
        self.kpi_pendientes.set_value(pendientes)
        self.kpi_clientes_al_dia.set_value(al_dia)

    def refresh(self) -> None:
        """Recarga datos de facturación."""
        logger.info("💰 Refrescando panel de facturación")
        self._actualizar_kpis()


class _DialogoNuevoCobro(QDialog):
    """Diálogo para registrar un nuevo cobro o pago."""

    def __init__(self, gestor_bd=None, parent=None):
        super().__init__(parent)
        self.gestor_bd = gestor_bd
        self.setWindowTitle("Nuevo Cobro")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Cliente
        self._combo_cliente = QComboBox()
        self._combo_cliente.setEditable(True)
        self._combo_cliente.setPlaceholderText("Seleccionar cliente...")
        self._cargar_clientes()
        layout.addRow("Cliente:", self._combo_cliente)

        # Concepto
        self._concepto = QComboBox()
        self._concepto.addItems([
            "Mensualidad", "Inscripción", "Plan Nutricional",
            "Clase Personal", "Productos", "Otro"
        ])
        layout.addRow("Concepto:", self._concepto)

        # Monto
        self._monto = QDoubleSpinBox()
        self._monto.setRange(0, 999999)
        self._monto.setPrefix("$ ")
        self._monto.setDecimals(2)
        self._monto.setValue(0)
        layout.addRow("Monto:", self._monto)

        # Fecha
        self._fecha = QDateEdit()
        self._fecha.setDate(QDate.currentDate())
        self._fecha.setCalendarPopup(True)
        layout.addRow("Fecha:", self._fecha)

        # Estado
        self._estado = QComboBox()
        self._estado.addItems(["Pagado", "Pendiente", "Parcial"])
        layout.addRow("Estado:", self._estado)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validar_y_aceptar)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _cargar_clientes(self) -> None:
        if self.gestor_bd is None:
            return
        try:
            clientes = self.gestor_bd.obtener_todos_clientes(solo_activos=True)
            for c in clientes:
                self._combo_cliente.addItem(c.get("nombre", ""), c.get("id_cliente"))
        except Exception as exc:
            logger.debug("No se pudieron cargar clientes: %s", exc)

    def _validar_y_aceptar(self) -> None:
        if self._monto.value() <= 0:
            mostrar_toast(self, "⚠️ El monto debe ser mayor a 0.", "warning")
            return
        if not self._combo_cliente.currentText().strip():
            mostrar_toast(self, "⚠️ Seleccione un cliente.", "warning")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "cliente": self._combo_cliente.currentText(),
            "concepto": self._concepto.currentText(),
            "monto": self._monto.value(),
            "fecha": self._fecha.date().toString("yyyy-MM-dd"),
            "estado": self._estado.currentText(),
        }
