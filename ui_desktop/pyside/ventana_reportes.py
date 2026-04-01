# -*- coding: utf-8 -*-
"""
Ventana de reportes — PySide6 + matplotlib QtAgg.
Reemplaza gui/ventana_reportes.py.
"""

from datetime import datetime, timedelta

try:
    import matplotlib
    matplotlib.use("QtAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    _MPL_OK = True
except Exception:
    _MPL_OK = False

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTabWidget, QWidget, QScrollArea, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from src.gestor_bd import GestorBDClientes
from design_system.tokens import Colors
from ui_desktop.pyside.widgets.toast import mostrar_toast
from utils.logger import logger


_PERIODOS = {
    "Últimos 7 días":   7,
    "Últimos 30 días":  30,
    "Últimos 90 días":  90,
    "Último año":       365,
    "Todo el tiempo":   None,
}


class VentanaReportes(QDialog):
    """Panel de reportes y métricas del gimnasio."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reportes — Método Base")
        self.resize(1020, 760)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.gestor_bd = GestorBDClientes()
        self._datos: dict = {}

        self._build_ui()
        self._actualizar()
        logger.info("[REPORTES] Ventana reportes abierta")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(10)

        # Header
        hdr = QFrame()
        hdr.setObjectName("reportHeader")
        hdr.setFixedHeight(68)
        hl = QVBoxLayout(hdr)
        hl.setAlignment(Qt.AlignCenter)
        t = QLabel("📊  Reportes del Gimnasio")
        t.setAlignment(Qt.AlignCenter)
        t.setObjectName("reportTitle")
        hl.addWidget(t)
        root.addWidget(hdr)

        # Toolbar
        bar = QWidget()
        bar.setObjectName("transparentWidget")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(0, 0, 0, 0)
        self.combo_periodo = QComboBox()
        self.combo_periodo.addItems(list(_PERIODOS.keys()))
        self.combo_periodo.setCurrentIndex(1)   # 30 días
        bl.addWidget(QLabel("Período:"))
        bl.addWidget(self.combo_periodo)
        bl.addSpacing(16)
        btn_act = QPushButton("🔄 Actualizar")
        btn_act.setObjectName("ghostButton")
        btn_act.clicked.connect(self._actualizar)
        bl.addWidget(btn_act)
        btn_exp = QPushButton("📤 Exportar")
        btn_exp.setObjectName("btn_success")
        btn_exp.clicked.connect(self._exportar)
        bl.addWidget(btn_exp)
        bl.addStretch()
        root.addWidget(bar)

        # Tabs
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self._crear_tab_dashboard()
        self._crear_tab_graficas()
        self._crear_tab_clientes()

        # Footer
        ftr = QWidget()
        ftr.setObjectName("transparentWidget")
        fl = QHBoxLayout(ftr)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.addStretch()
        btn_cerrar = QPushButton("❌  Cerrar")
        btn_cerrar.setObjectName("reportCloseBtn")
        btn_cerrar.clicked.connect(self.accept)
        fl.addWidget(btn_cerrar)
        root.addWidget(ftr)

    # ------------------------------------------------------------------
    # Pestaña Dashboard (KPIs)
    # ------------------------------------------------------------------

    def _crear_tab_dashboard(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("reportScroll")
        inner = QWidget()
        self.dash_layout = QVBoxLayout(inner)
        self.dash_layout.setContentsMargins(20, 20, 20, 20)
        self.dash_layout.setSpacing(16)
        scroll.setWidget(inner)
        self.tabs.addTab(scroll, "📋 Dashboard")

    def _poblar_dashboard(self) -> None:
        # Limpiar anterior
        while self.dash_layout.count():
            item = self.dash_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        d = self._datos
        kpis = [
            ("👥 Total Clientes",          d.get("total_clientes", 0),           "#FFEB3B"),
            ("📈 Clientes Nuevos",          d.get("clientes_nuevos", 0),          "#FFEB3B"),
            ("🍽️ Planes Generados",         d.get("planes_generados", 0),         "#00FF88"),
            ("⚡ Promedio Kcal / Plan",     f"{d.get('promedio_kcal', 0):.0f}",   "#FFEB3B"),
            ("💪 Objetivo + Común",         d.get("objetivo_comun", "—"),         "#FFEB3B"),
            ("🕐 Planes (período)",          d.get("planes_periodo", 0),           "#FFEB3B"),
        ]

        grid = QGridLayout()
        grid.setSpacing(12)
        for i, (titulo, valor, color) in enumerate(kpis):
            f = QFrame()
            f.setObjectName("reportKpiCard")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(16, 14, 16, 14)
            fl.setSpacing(4)
            tl = QLabel(titulo)
            tl.setAlignment(Qt.AlignCenter)
            tl.setObjectName("reportKpiTitle")
            fl.addWidget(tl)
            vl = QLabel(str(valor))
            vl.setAlignment(Qt.AlignCenter)
            vl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
            fl.addWidget(vl)
            grid.addWidget(f, i // 3, i % 3)
        self.dash_layout.addLayout(grid)

        # Distribución de objetivos
        obj_dist = d.get("distribucion_objetivos", {})
        if obj_dist:
            t = QLabel("📊  Distribución de Objetivos")
            t.setObjectName("reportSectionTitle")
            self.dash_layout.addWidget(t)
            for objetivo, cnt in sorted(obj_dist.items(), key=lambda x: -x[1])[:8]:
                row = QWidget()
                row.setObjectName("transparentWidget")
                rl = QHBoxLayout(row)
                rl.setContentsMargins(0, 0, 0, 0)
                lbl = QLabel(f"• {objetivo}")
                lbl.setObjectName("reportObjLabel")
                rl.addWidget(lbl, 1)
                cnt_lbl = QLabel(str(cnt))
                cnt_lbl.setObjectName("reportObjCount")
                rl.addWidget(cnt_lbl)
                self.dash_layout.addWidget(row)

        self.dash_layout.addStretch()

    # ------------------------------------------------------------------
    # Pestaña Gráficas
    # ------------------------------------------------------------------

    def _crear_tab_graficas(self) -> None:
        w = QWidget()
        self.graficas_layout = QVBoxLayout(w)
        self.graficas_layout.setContentsMargins(4, 4, 4, 4)
        self.tabs.addTab(w, "📈 Gráficas")
        self._canvas_clientes = None
        self._canvas_objetivos = None

    def _poblar_graficas(self) -> None:
        if not _MPL_OK:
            lbl = QLabel("matplotlib no disponible — instala con: pip install matplotlib")
            lbl.setObjectName("error_label")
            self.graficas_layout.addWidget(lbl)
            return

        # Limpiar
        while self.graficas_layout.count():
            item = self.graficas_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        plt.style.use("dark_background")
        d = self._datos

        # Gráfica 1: evolución de clientes nuevos (simplificada como barras)
        clientes_x = list(range(1, 8))
        clientes_y = d.get("clientes_nuevos_semana", [0] * 7)

        fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
        fig.patch.set_facecolor("#0D0D0D")

        axes[0].bar(
            clientes_x, clientes_y[:7] if len(clientes_y) >= 7 else clientes_y + [0] * (7 - len(clientes_y)),
            color="#FFEB3B", edgecolor="#1A1A1A"
        )
        axes[0].set_title("Nuevos clientes (últimos 7 días)", color="#FFFFFF", fontsize=10)
        axes[0].set_facecolor("#1A1A1A")
        axes[0].tick_params(colors="#A1A1AA")

        obj_dist = d.get("distribucion_objetivos", {})
        if obj_dist:
            labels = list(obj_dist.keys())[:6]
            vals   = [obj_dist[k] for k in labels]
            axes[1].pie(vals, labels=labels, autopct="%1.0f%%",
                        colors=[Colors.PRIMARY, Colors.ACCENT, Colors.SUCCESS, Colors.INFO, Colors.PRIMARY, Colors.ERROR],
                        textprops={"color": Colors.TEXT_PRIMARY, "fontsize": 8})
            axes[1].set_title("Distribución de objetivos", color=Colors.TEXT_PRIMARY, fontsize=10)
        else:
            axes[1].text(0.5, 0.5, "Sin datos", ha="center", va="center", color=Colors.TEXT_SECONDARY)

        fig.tight_layout(pad=1.5)
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(280)
        self.graficas_layout.addWidget(canvas)
        self.graficas_layout.addStretch()

    # ------------------------------------------------------------------
    # Pestaña Clientes recientes
    # ------------------------------------------------------------------

    def _crear_tab_clientes(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("reportScroll")
        inner = QWidget()
        self.clientes_tab_layout = QVBoxLayout(inner)
        self.clientes_tab_layout.setContentsMargins(16, 16, 16, 16)
        self.clientes_tab_layout.setSpacing(12)
        scroll.setWidget(inner)
        self.tabs.addTab(scroll, "👥 Clientes")

        # Title and description
        header = QWidget()
        header.setObjectName("transparentWidget")
        hdr_layout = QVBoxLayout(header)
        hdr_layout.setContentsMargins(0, 0, 0, 0)
        hdr_layout.setSpacing(4)
        
        title = QLabel("📋 Clientes Recientes")
        title.setObjectName("reportSectionTitle")
        hdr_layout.addWidget(title)
        
        self.lbl_cli_count = QLabel("Mostrando los últimos 100 clientes registrados")
        self.lbl_cli_count.setObjectName("reportCaption")
        hdr_layout.addWidget(self.lbl_cli_count)
        
        self.clientes_tab_layout.addWidget(header)

        # Table with expanded columns
        self.tabla_cli = QTableWidget()
        self.tabla_cli.setColumnCount(7)
        self.tabla_cli.setHorizontalHeaderLabels([
            "Nombre", "Teléfono", "Edad", "Peso (kg)", 
            "Objetivo", "Estado", "Último plan"
        ])
        
        hdr = self.tabla_cli.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)     # Nombre - stretch
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Teléfono
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Edad
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Peso
        hdr.setSectionResizeMode(4, QHeaderView.Fixed)       # Objetivo - fixed
        hdr.setSectionResizeMode(5, QHeaderView.Fixed)       # Estado - fixed
        hdr.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Último plan
        self.tabla_cli.setColumnWidth(4, 140)
        self.tabla_cli.setColumnWidth(5, 100)
        
        self.tabla_cli.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_cli.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_cli.setAlternatingRowColors(True)
        self.tabla_cli.verticalHeader().setVisible(False)
        self.tabla_cli.setShowGrid(False)
        self.tabla_cli.setObjectName("reportTable")
        self.clientes_tab_layout.addWidget(self.tabla_cli, 1)
        
        # Empty state message (hidden by default)
        self._cli_empty_state = QLabel("No hay clientes registrados en este período")
        self._cli_empty_state.setObjectName("reportEmptyState")
        self._cli_empty_state.setAlignment(Qt.AlignCenter)
        self._cli_empty_state.hide()
        self.clientes_tab_layout.addWidget(self._cli_empty_state)

    def _poblar_tabla_clientes(self) -> None:
        clientes = self._datos.get("clientes_recientes", [])
        self.tabla_cli.setRowCount(0)
        
        # Update count label
        if hasattr(self, 'lbl_cli_count'):
            self.lbl_cli_count.setText(f"Mostrando {len(clientes)} cliente{'s' if len(clientes) != 1 else ''}")
        
        # Show/hide empty state
        if not clientes:
            self.tabla_cli.hide()
            if hasattr(self, '_cli_empty_state'):
                self._cli_empty_state.show()
            return
        else:
            self.tabla_cli.show()
            if hasattr(self, '_cli_empty_state'):
                self._cli_empty_state.hide()
        
        self.tabla_cli.setRowCount(len(clientes))
        for row, cli in enumerate(clientes):
            self.tabla_cli.setRowHeight(row, 48)
            
            # Col 0: Nombre
            nombre = cli.get("nombre", "—")
            item_nombre = QTableWidgetItem(nombre)
            item_nombre.setForeground(QColor(Colors.TEXT_PRIMARY))
            self.tabla_cli.setItem(row, 0, item_nombre)
            
            # Col 1: Teléfono
            telefono = cli.get("telefono", "") or "—"
            item_tel = QTableWidgetItem(telefono)
            item_tel.setForeground(QColor(Colors.TEXT_SECONDARY))
            self.tabla_cli.setItem(row, 1, item_tel)
            
            # Col 2: Edad
            edad = cli.get("edad", "—")
            item_edad = QTableWidgetItem(str(edad) if edad else "—")
            item_edad.setForeground(QColor(Colors.TEXT_SECONDARY))
            self.tabla_cli.setItem(row, 2, item_edad)
            
            # Col 3: Peso
            peso = cli.get("peso_kg", cli.get("peso", ""))
            item_peso = QTableWidgetItem(f"{peso} kg" if peso else "—")
            item_peso.setForeground(QColor(Colors.TEXT_SECONDARY))
            self.tabla_cli.setItem(row, 3, item_peso)
            
            # Col 4: Objetivo (with status tag)
            objetivo = (cli.get("objetivo") or "—").strip()
            widget_obj = QWidget()
            widget_obj.setObjectName("transparentWidget")
            ol = QHBoxLayout(widget_obj)
            ol.setContentsMargins(4, 4, 4, 4)
            
            # Determine tag colors
            obj_lower = objetivo.lower()
            if "déficit" in obj_lower or "deficit" in obj_lower:
                tag_bg, tag_fg = Colors.INFO_BG, Colors.INFO  # Blue
            elif "superávit" in obj_lower or "superavit" in obj_lower:
                tag_bg, tag_fg = Colors.ACCENT_SOFT, Colors.ACCENT_HOVER  # Purple
            else:
                tag_bg, tag_fg = Colors.BG_INPUT, Colors.TEXT_SECONDARY  # Gray
                
            tag = QLabel(objetivo.capitalize())
            tag.setStyleSheet(
                f"background-color: {tag_bg}; color: {tag_fg}; border-radius: 10px;"
                " padding: 4px 10px; font-size: 11px; font-weight: 600;"
            )
            tag.setAlignment(Qt.AlignCenter)
            ol.addWidget(tag)
            ol.addStretch()
            self.tabla_cli.setCellWidget(row, 4, widget_obj)
            
            # Col 5: Estado (active/inactive)
            activo = cli.get("activo", True)
            estado_text = "Activo" if activo else "Inactivo"
            estado_bg = Colors.SUCCESS_BG if activo else Colors.BG_INPUT
            estado_fg = Colors.SUCCESS if activo else Colors.TEXT_HINT
            
            widget_estado = QWidget()
            widget_estado.setObjectName("transparentWidget")
            el = QHBoxLayout(widget_estado)
            el.setContentsMargins(4, 4, 4, 4)
            estado_tag = QLabel(estado_text)
            estado_tag.setStyleSheet(
                f"background-color: {estado_bg}; color: {estado_fg}; border-radius: 10px;"
                " padding: 4px 8px; font-size: 10px; font-weight: 600;"
            )
            estado_tag.setAlignment(Qt.AlignCenter)
            el.addWidget(estado_tag)
            el.addStretch()
            self.tabla_cli.setCellWidget(row, 5, widget_estado)
            
            # Col 6: Último plan (date)
            ultimo_plan = cli.get("ultimo_plan", "")
            if ultimo_plan and len(str(ultimo_plan)) > 10:
                try:
                    dt = datetime.fromisoformat(str(ultimo_plan)[:19])
                    fecha_texto = dt.strftime("%d/%m/%Y")
                except Exception:
                    fecha_texto = str(ultimo_plan)[:10]
            else:
                fecha_texto = str(ultimo_plan) if ultimo_plan else "—"
            
            item_plan = QTableWidgetItem(fecha_texto)
            item_plan.setForeground(QColor(Colors.TEXT_SECONDARY))
            self.tabla_cli.setItem(row, 6, item_plan)

    # ------------------------------------------------------------------
    # Actualizar datos
    # ------------------------------------------------------------------

    def _actualizar(self) -> None:
        periodo_nombre = self.combo_periodo.currentText()
        dias = _PERIODOS.get(periodo_nombre)
        fecha_inicio = None
        if dias:
            fecha_inicio = datetime.now() - timedelta(days=dias)

        try:
            stats = self.gestor_bd.obtener_estadisticas_gym(fecha_inicio=fecha_inicio)
            self._datos = stats or {}
        except Exception as exc:
            logger.error("[REPORTES] Error al cargar estadísticas: %s", exc)
            self._datos = {}

        # Cargar clientes recientes
        try:
            todos = self.gestor_bd.obtener_todos_clientes()
            self._datos["clientes_recientes"] = (todos or [])[:100]
        except Exception:
            self._datos["clientes_recientes"] = []

        self._poblar_dashboard()
        self._poblar_graficas()
        self._poblar_tabla_clientes()

    # ------------------------------------------------------------------
    # Exportar
    # ------------------------------------------------------------------

    def _exportar(self) -> None:
        if not _MPL_OK:
            mostrar_toast(self, "⚠️ matplotlib no disponible para exportar gráficas.", "warning")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar reporte como imagen PNG",
            f"reporte_{datetime.now().strftime('%Y%m%d')}.png",
            "PNG (*.png)",
        )
        if not ruta:
            return
        try:
            plt.savefig(ruta, facecolor="#0D0D0D", bbox_inches="tight")
            mostrar_toast(self, f"✅ Reporte guardado en: {ruta}", "success")
        except Exception as exc:
            mostrar_toast(self, f"❌ No se pudo exportar: {exc}", "error")
