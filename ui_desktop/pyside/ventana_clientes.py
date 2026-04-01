# -*- coding: utf-8 -*-
"""
Ventana de gestión de clientes — PySide6.
Reemplaza gui/ventana_clientes.py.
"""

import csv

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from src.gestor_bd import GestorBDClientes
from ui_desktop.pyside.widgets.confirm_dialog import confirmar
from ui_desktop.pyside.widgets.toast import mostrar_toast
from utils.logger import logger
from design_system.tokens import Colors, Typography, Spacing, Radius


_COLS = [
    ("Nombre",             "nombre"),
    ("Teléfono",           "telefono"),
    ("Edad",               "edad"),
    ("Peso (kg)",          "peso"),
    ("Objetivo",           "objetivo"),
    ("Planes",             "total_planes"),
    ("Último plan",        "ultimo_plan"),
]


class VentanaClientes(QDialog):
    """Listado y búsqueda de clientes del gimnasio."""

    def __init__(self, parent=None, gestor_bd=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Clientes — Método Base")
        self.resize(920, 680)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.gestor_bd = gestor_bd if gestor_bd is not None else GestorBDClientes()

        self._build_ui()
        self._cargar_clientes()
        logger.info("[CLIENTES] Ventana clientes abierta")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(10)

        # Header
        hdr = QFrame()
        hdr.setObjectName("chartContainer")
        hdr.setFixedHeight(68)
        hl = QVBoxLayout(hdr)
        hl.setAlignment(Qt.AlignCenter)
        t = QLabel("👥  Clientes del Gimnasio")
        t.setAlignment(Qt.AlignCenter)
        t.setObjectName("pageTitle")
        hl.addWidget(t)
        root.addWidget(hdr)

        # Barra de acciones
        bar = QWidget()
        bar.setObjectName("transparentWidget")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(0, 0, 0, 0)
        self.entry_busqueda = QLineEdit()
        self.entry_busqueda.setPlaceholderText("Buscar por nombre, teléfono o ID…")
        self.entry_busqueda.textChanged.connect(self._on_busqueda_cambia)
        bl.addWidget(self.entry_busqueda, 1)
        self.lbl_total = QLabel("")
        self.lbl_total.setObjectName("kpiContext")
        bl.addWidget(self.lbl_total)
        bl.addSpacing(12)
        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setObjectName("ghostButton")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self._cargar_clientes)
        bl.addWidget(btn_refresh)
        btn_csv = QPushButton("📊 Exportar CSV")
        btn_csv.setObjectName("successButton")
        btn_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_csv.clicked.connect(self._exportar_csv)
        bl.addWidget(btn_csv)
        root.addWidget(bar)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(_COLS))
        self.tabla.setHorizontalHeaderLabels([c[0] for c in _COLS])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        # Set fixed width for "Último plan" column to ensure proper display
        self.tabla.setColumnWidth(6, 120)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setShowGrid(False)
        self.tabla.setObjectName("dataTable")
        root.addWidget(self.tabla, 1)

        # Footer
        ftr = QWidget()
        ftr.setObjectName("transparentWidget")
        fl = QHBoxLayout(ftr)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("ghostButton")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.clicked.connect(self.accept)
        fl.addWidget(btn_cerrar)
        root.addWidget(ftr)

    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------

    def _cargar_clientes(self, query: str = "") -> None:
        try:
            if query.strip():
                clientes = self.gestor_bd.buscar_clientes(query.strip())
            else:
                clientes = self.gestor_bd.obtener_todos_clientes()
        except Exception as exc:
            logger.error("[CLIENTES] Error al cargar clientes: %s", exc)
            mostrar_toast(self, f"❌ Error al cargar clientes: {exc}", "error")
            return

        self._poblar_tabla(clientes or [])

    def _on_busqueda_cambia(self, text: str) -> None:
        self._cargar_clientes(query=text)

    def _poblar_tabla(self, clientes: list) -> None:
        self.tabla.setRowCount(0)
        self.tabla.setRowCount(len(clientes))
        for row, cli in enumerate(clientes):
            for col, (col_label, key) in enumerate(_COLS):
                val = cli.get(key, "")
                
                # Special vertical layout for "Último plan" column with boxed styling
                if col == 6 and key == "ultimo_plan":
                    # Container with padding
                    container = QWidget()
                    container.setStyleSheet("background: transparent;")
                    container_layout = QHBoxLayout(container)
                    container_layout.setContentsMargins(4, 4, 4, 4)
                    container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Inner widget with border and background
                    plan_widget = QWidget()
                    plan_layout = QVBoxLayout(plan_widget)
                    plan_layout.setContentsMargins(8, 6, 8, 6)
                    plan_layout.setSpacing(2)
                    plan_widget.setStyleSheet(
                        "QWidget { "
                        "  background-color: rgba(42, 42, 46, 0.6); "
                        "  border: 1px solid rgba(142, 142, 147, 0.3); "
                        "  border-radius: 6px; "
                        "}"
                    )
                    
                    # Label "Último plan"
                    lbl_titulo = QLabel("Último plan")
                    lbl_titulo.setStyleSheet(
                        "color: #A1A1AA; font-size: 9px; font-weight: 600; "
                        "background: transparent; border: none; text-transform: uppercase; "
                        "letter-spacing: 0.5px;"
                    )
                    lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    plan_layout.addWidget(lbl_titulo)
                    
                    # Fecha value
                    fecha_texto = str(val) if val else "—"
                    # Format date if it's a datetime string
                    if val and len(str(val)) > 10:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(str(val)[:19])
                            fecha_texto = dt.strftime("%d/%m/%y")
                        except Exception:
                            pass
                    
                    lbl_fecha = QLabel(fecha_texto)
                    lbl_fecha.setStyleSheet(
                        "color: #FFFFFF; font-size: 12px; font-weight: 600; "
                        "background: transparent; border: none;"
                    )
                    lbl_fecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    plan_layout.addWidget(lbl_fecha)
                    
                    container_layout.addWidget(plan_widget)
                    self.tabla.setCellWidget(row, col, container)
                else:
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    item.setForeground(QColor("#FFFFFF"))
                    self.tabla.setItem(row, col, item)

        total = len(clientes)
        self.lbl_total.setText(f"{total} cliente{'s' if total != 1 else ''}")

    def _exportar_csv(self) -> None:
        if not self._confirmar_exportacion():
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar CSV", "clientes.csv", "CSV (*.csv)"
        )
        if not ruta:
            return
        try:
            with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                # Solo encabezados de campos públicos permitidos
                writer.writerow([c[0] for c in _COLS])
                for row in range(self.tabla.rowCount()):
                    writer.writerow([
                        (self.tabla.item(row, col).text() if self.tabla.item(row, col) else "")
                        for col in range(len(_COLS))
                    ])
            mostrar_toast(self, f"✅ CSV guardado en: {ruta}", "success")
            logger.info("[CLIENTES] CSV exportado (campos públicos): %s", ruta)
        except Exception as exc:
            mostrar_toast(self, f"❌ No se pudo exportar: {exc}", "error")

    def _confirmar_exportacion(self) -> bool:
        """Muestra aviso de privacidad obligatorio antes de cualquier exportación."""
        return confirmar(
            self,
            "⚠️  Aviso de Privacidad — Exportación",
            "Estás a punto de exportar datos de clientes.\n\n"
            "• Solo se incluyen campos públicos (nombre, edad, peso, objetivo).\n"
            "• No se exportan contraseñas, hashes, tokens cifrados ni emails.\n"
            "• El archivo exportado no estará cifrado; guárdalo en un lugar seguro.\n"
            "• Comparte este archivo solo con personas autorizadas.",
            texto_si="Sí, exportar",
            texto_no="Cancelar",
        )
