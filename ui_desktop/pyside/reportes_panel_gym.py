# -*- coding: utf-8 -*-
"""
ReportesPanelGym — Módulo de reportes y estadísticas del gimnasio.
"""
from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from ui_desktop.pyside.widgets.kpi_card import KPICard
from ui_desktop.pyside.widgets.toast import mostrar_toast
from utils.logger import logger


class ReportesPanelGym(QWidget):
    """Panel de reportes y estadísticas financieras y operativas."""

    def __init__(self, gestor_bd=None, parent=None):
        super().__init__(parent)
        self.gestor_bd = gestor_bd
        self._estadisticas: dict = {}
        self._setup_ui()
        self._cargar_estadisticas()

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
        self._crear_graficos_placeholder()

    def _crear_header(self) -> None:
        header = QFrame()
        header.setObjectName("headerFrame")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 16)

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("Reportes")
        title.setObjectName("pageTitle")
        left.addWidget(title)
        subtitle = QLabel("Estadísticas y análisis del gimnasio")
        subtitle.setObjectName("pageSubtitle")
        left.addWidget(subtitle)
        layout.addLayout(left)
        layout.addStretch()

        self.btn_exportar = QPushButton("📥  Exportar")
        self.btn_exportar.setObjectName("secondaryButton")
        self.btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exportar.setToolTip("Exportar reportes a CSV")
        self.btn_exportar.clicked.connect(self._exportar_reportes)
        layout.addWidget(self.btn_exportar)

        self._layout.addWidget(header)

    def _crear_kpis(self) -> None:
        row = QHBoxLayout()
        row.setSpacing(16)

        self.kpi_clientes_total = KPICard("yellow", "👥", 0, "CLIENTES TOTALES", "Registrados", "neutral")
        self.kpi_planes_mes = KPICard("green", "📋", 0, "PLANES / MES", "Generados", "neutral")
        self.kpi_tasa_retencion = KPICard("orange", "📈", 0, "RETENCIÓN %", "Tasa mensual", "up")
        self.kpi_ingresos = KPICard("yellow", "💰", 0, "INGRESOS", "Este mes", "neutral")

        row.addWidget(self.kpi_clientes_total)
        row.addWidget(self.kpi_planes_mes)
        row.addWidget(self.kpi_tasa_retencion)
        row.addWidget(self.kpi_ingresos)

        self._layout.addLayout(row)

    def _crear_graficos_placeholder(self) -> None:
        """Sección de resumen estadístico."""
        container = QFrame()
        container.setObjectName("chartContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Análisis")
        title.setObjectName("chartTitle")
        layout.addWidget(title)

        self._analysis_label = QLabel("Cargando estadísticas...")
        self._analysis_label.setObjectName("chartSubtitle")
        self._analysis_label.setAlignment(Qt.AlignCenter)
        self._analysis_label.setWordWrap(True)
        self._analysis_label.setMinimumHeight(200)
        layout.addWidget(self._analysis_label)

        self._layout.addWidget(container)

    def _cargar_estadisticas(self) -> None:
        """Carga estadísticas desde la base de datos."""
        try:
            if self.gestor_bd:
                from datetime import timedelta
                ahora = datetime.now()
                inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                # Use real gestor_bd methods
                stats = self.gestor_bd.obtener_estadisticas_gym(inicio_mes, ahora)
                self._estadisticas["clientes_total"] = stats.get("total_clientes", 0)
                self._estadisticas["planes_mes"] = stats.get("planes_periodo", 0)
                self._estadisticas["retencion"] = stats.get("tasa_retencion", 0)
                self._estadisticas["clientes_nuevos"] = stats.get("clientes_nuevos", 0)
                self._estadisticas["clientes_activos"] = stats.get("clientes_activos", 0)

                # Ingresos estimados (clientes activos * cuota mensual)
                from core.branding import branding as _branding
                cuota = float(_branding.get("cuota_mensual", 800))
                activos = stats.get("clientes_activos", 0)
                self._estadisticas["ingresos"] = int(activos * cuota)
                self._estadisticas["cuota"] = cuota
                self._estadisticas["clientes_activos"] = activos
            else:
                self._estadisticas = {
                    "clientes_total": 0,
                    "planes_mes": 0,
                    "retencion": 0,
                    "ingresos": 0,
                    "clientes_nuevos": 0,
                    "clientes_activos": 0,
                }

            self._actualizar_kpis()
            self._actualizar_analisis()
            logger.info("📈 Estadísticas cargadas")
        except Exception as e:
            logger.warning(f"[ReportesPanelGym] Error cargando estadísticas: {e}")
            self._estadisticas = {"clientes_total": 0, "planes_mes": 0, "retencion": 0, "ingresos": 0}

    def _actualizar_kpis(self) -> None:
        """Actualiza los valores de las cards KPI."""
        self.kpi_clientes_total.set_value(self._estadisticas.get("clientes_total", 0))
        self.kpi_planes_mes.set_value(self._estadisticas.get("planes_mes", 0))
        self.kpi_tasa_retencion.set_value(self._estadisticas.get("retencion", 0))
        ingresos = self._estadisticas.get("ingresos", 0)
        activos = self._estadisticas.get("clientes_activos", 0)
        cuota = self._estadisticas.get("cuota", 800)
        self.kpi_ingresos.set_value(
            ingresos,
            change_value=f"{activos} × ${int(cuota)}",
            trend="neutral",
        )

    def _actualizar_analisis(self) -> None:
        """Actualiza el resumen de análisis con datos reales."""
        if not hasattr(self, "_analysis_label"):
            return
        total = self._estadisticas.get("clientes_total", 0)
        activos = self._estadisticas.get("clientes_activos", 0)
        nuevos = self._estadisticas.get("clientes_nuevos", 0)
        planes = self._estadisticas.get("planes_mes", 0)
        retencion = self._estadisticas.get("retencion", 0)

        if total == 0:
            self._analysis_label.setText(
                "📊 Sin datos aún.\n\n"
                "Registra tu primer cliente para ver las estadísticas aquí."
            )
            return

        text = (
            f"📊  Resumen del Mes\n\n"
            f"👥  {total} clientes registrados  ·  {activos} activos este mes\n"
            f"✨  {nuevos} nuevos registros este mes\n"
            f"📋  {planes} planes nutricionales generados\n"
            f"📈  Tasa de retención: {retencion}%"
        )
        self._analysis_label.setText(text)

    def _exportar_reportes(self) -> None:
        """Exporta un resumen de reportes a CSV."""
        try:
            # Crear directorio de exportación si no existe
            export_dir = Path.home() / "MetodoBase_Exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            default_name = f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Reporte",
                str(export_dir / default_name),
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not filepath:
                return
            
            # Preparar datos
            data = [
                ["Métrica", "Valor", "Fecha"],
                ["Clientes Totales", self._estadisticas.get("clientes_total", 0), datetime.now().isoformat()],
                ["Planes este Mes", self._estadisticas.get("planes_mes", 0), datetime.now().isoformat()],
                ["Tasa Retención %", self._estadisticas.get("retencion", 0), datetime.now().isoformat()],
                ["Ingresos", self._estadisticas.get("ingresos", 0), datetime.now().isoformat()],
            ]
            
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(data)
            
            mostrar_toast(self, f"✅ Reporte exportado: {Path(filepath).name}", "success")
            logger.info(f"📥 Reporte exportado a: {filepath}")
            
        except Exception as e:
            mostrar_toast(self, f"❌ No se pudo exportar el reporte: {e}", "error")
            logger.error(f"[ReportesPanelGym] Error exportando: {e}")

    def refresh(self) -> None:
        """Recarga datos de reportes."""
        logger.info("📈 Refrescando panel de reportes")
        self._cargar_estadisticas()
