# -*- coding: utf-8 -*-
"""
GymAppWindow — Ventana principal del modo GYM con diseño dark mode premium.

Layout:
    ┌──────────────────────────────────────────────────────────┐
    │  CustomSidebar (240px) │  QStackedWidget (resto)         │
    │  ── PRINCIPAL ──        │  0: DashboardPanel              │
    │   📊 Dashboard          │  1: ClientesPanel               │
    │   👥 Clientes           │  2: GenerarPlanPanel             │
    │   📋 Generar Plan       │                                  │
    │  ── SISTEMA ──          │                                  │
    │   📖 API Docs           │                                  │
    │   ─────────────         │                                  │
    │   [usuario footer]      │                                  │
    └─────────────────────────────────────────────────────────-┘
"""
from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QMainWindow,
    QStackedWidget, QWidget,
)

from core.branding import branding
from src.gestor_bd import GestorBDClientes
from design_system.tokens import Colors
from ui_desktop.pyside.dashboard_panel import DashboardPanel
from ui_desktop.pyside.clientes_panel import ClientesPanel
from ui_desktop.pyside.generar_plan_panel import GenerarPlanPanel
from ui_desktop.pyside.suscripciones_panel import SuscripcionesPanel
from ui_desktop.pyside.clases_panel import ClasesPanel
from ui_desktop.pyside.instructores_panel import InstructoresPanel
# FacturacionPanel importada condicionalmente según ENABLE_BILLING
from ui_desktop.pyside.reportes_panel_gym import ReportesPanelGym
from ui_desktop.pyside.configuracion_panel import ConfiguracionPanel
from ui_desktop.pyside.widgets.sidebar import CustomSidebar
from utils.logger import logger

try:
    from config.constantes import ENABLE_BILLING
except ImportError:
    ENABLE_BILLING = True   # fallback seguro: no deshabilitar si no se puede leer

# Mapa page_id → índice en QStackedWidget
_PAGE_INDEX = {
    "dashboard":      0,
    "clientes":       1,
    "generar_plan":   2,
    "suscripciones":  3,
    "clases":         4,
    "instructores":   5,
    "facturacion":    6,
    "reportes":       7,
    "configuracion":  8,
}


class GymAppWindow(QMainWindow):
    """Ventana principal GYM con sidebar + stacked panels."""

    def __init__(self):
        super().__init__()

        # NOTE: No aplicar tema aquí — ThemeManager.reload() en main.py
        # ya cargó el QSS a nivel de QApplication.

        # Gestor de BD compartido
        try:
            self._db = GestorBDClientes()
        except Exception as exc:
            logger.error("[DB] Error al inicializar BD: %s", exc)
            self._db = None

        # Configuración de la ventana
        nombre = branding.get("nombre_gym", "Método Base")
        self.setWindowTitle(f"{nombre} — Sistema Nutricional v2.0")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        self._build_ui()
        self._conectar_senales()
        self._setup_shortcuts()
        self._mostrar_banner_trial()

        # Mostrar dashboard al iniciar
        self._navegar("dashboard")

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = CustomSidebar(self)
        main_layout.addWidget(self._sidebar)

        # ── Separador visual ──────────────────────────────────────────────────
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"background-color: {Colors.BORDER_SUBTLE}; border: none; max-width: 1px;")
        main_layout.addWidget(sep)

        # ── Área de contenido (stacked) ───────────────────────────────────────
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack)

        # ── Panels ────────────────────────────────────────────────────────────
        self._panel_dashboard = DashboardPanel(gestor_bd=self._db, parent=self)
        self._panel_clientes = ClientesPanel(gestor_bd=self._db, parent=self)
        self._panel_generar = GenerarPlanPanel(gestor_bd=self._db, parent=self)
        self._panel_suscripciones = SuscripcionesPanel(gestor_bd=self._db, parent=self)
        self._panel_clases = ClasesPanel(gestor_bd=self._db, parent=self)
        self._panel_instructores = InstructoresPanel(gestor_bd=self._db, parent=self)

        # Facturación — condicional según ENABLE_BILLING
        if ENABLE_BILLING:
            from ui_desktop.pyside.facturacion_panel import FacturacionPanel
            self._panel_facturacion = FacturacionPanel(gestor_bd=self._db, parent=self)
        else:
            self._panel_facturacion = QWidget()   # placeholder vacío
            self._panel_facturacion.setVisible(False)
            logger.info("[GYM] Módulo de facturación desactivado (ENABLE_BILLING=False)")

        self._panel_reportes = ReportesPanelGym(gestor_bd=self._db, parent=self)
        self._panel_configuracion = ConfiguracionPanel(gestor_bd=self._db, parent=self)

        self._stack.addWidget(self._panel_dashboard)       # 0
        self._stack.addWidget(self._panel_clientes)        # 1
        self._stack.addWidget(self._panel_generar)         # 2
        self._stack.addWidget(self._panel_suscripciones)   # 3
        self._stack.addWidget(self._panel_clases)          # 4
        self._stack.addWidget(self._panel_instructores)    # 5
        self._stack.addWidget(self._panel_facturacion)     # 6
        self._stack.addWidget(self._panel_reportes)        # 7
        self._stack.addWidget(self._panel_configuracion)   # 8

    def _conectar_senales(self) -> None:
        # Sidebar → stacked
        self._sidebar.navigation_changed.connect(self._navegar)

        # Dashboard → navegación directa
        self._panel_dashboard.navigate_to.connect(self._navegar)

        # Clientes → Generar plan
        self._panel_clientes.generar_plan_para.connect(self._generar_plan_para_cliente)

        # Clientes → Plan rápido (skip step 2)
        self._panel_clientes.plan_rapido_para.connect(self._plan_rapido_para_cliente)

        # Generar plan → navegación
        self._panel_generar.navigate_to.connect(self._navegar)

    def _setup_shortcuts(self) -> None:
        # Ctrl+Shift+A → panel admin (heredado del MainWindow original)
        sc = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        sc.activated.connect(self._abrir_admin)

        # Ctrl+1..9 → fast navigation to all panels
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(
            lambda: self._navegar("dashboard")
        )
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(
            lambda: self._navegar("clientes")
        )
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(
            lambda: self._navegar("generar_plan")
        )
        QShortcut(QKeySequence("Ctrl+4"), self).activated.connect(
            lambda: self._navegar("suscripciones")
        )
        QShortcut(QKeySequence("Ctrl+5"), self).activated.connect(
            lambda: self._navegar("clases")
        )
        QShortcut(QKeySequence("Ctrl+6"), self).activated.connect(
            lambda: self._navegar("instructores")
        )
        QShortcut(QKeySequence("Ctrl+7"), self).activated.connect(
            lambda: self._navegar("reportes")
        )
        QShortcut(QKeySequence("Ctrl+8"), self).activated.connect(
            lambda: self._navegar("configuracion")
        )
        # Ctrl+N → quick register new client
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(
            self._registro_rapido
        )
        # Ctrl+G → go to generate plan panel
        QShortcut(QKeySequence("Ctrl+G"), self).activated.connect(
            lambda: self._navegar("generar_plan")
        )

    # ── Banner Trial ────────────────────────────────────────────────────────

    def _mostrar_banner_trial(self) -> None:
        """Si la licencia es trial, muestra un banner con los días restantes."""
        try:
            from core.licencia import GestorLicencias
            gestor = GestorLicencias()
            if not gestor.es_trial():
                return
            vigente, dias = gestor.validar_trial()
            if not vigente:
                return
            from PySide6.QtWidgets import QLabel
            banner = QLabel(
                f"⏱ Trial — {dias} días restantes  |  Máx. 3 clientes  |  "
                "Activa tu licencia para desbloquear todas las funciones"
            )
            banner.setStyleSheet(
                f"background: {Colors.WARNING}; color: {Colors.TEXT_INVERSE}; padding: 6px 12px; "
                "font-size: 12px; font-weight: 600;"
            )
            banner.setAlignment(Qt.AlignCenter)
            self.statusBar().addPermanentWidget(banner, 1)
        except Exception as exc:
            logger.debug("[TRIAL] No se pudo mostrar banner: %s", exc)

    # ── Navegación ────────────────────────────────────────────────────────────

    def _navegar(self, page_id: str) -> None:
        # Cerrar sesión → confirmar y salir
        if page_id == "switch_gym":
            self._cerrar_sesion()
            return

        # Bloquear navegación a facturación si el módulo está desactivado
        if page_id == "facturacion" and not ENABLE_BILLING:
            logger.debug("[NAV] Facturación desactivada — redirigiendo a dashboard")
            page_id = "dashboard"

        idx = _PAGE_INDEX.get(page_id)
        if idx is None:
            # API Docs → abrir navegador
            if page_id == "api_docs":
                self._abrir_api_docs()
            return

        self._stack.setCurrentIndex(idx)
        self._sidebar.set_active_page(page_id)

        # Refrescar datos al cambiar de panel
        panel_map = {
            "dashboard": self._panel_dashboard,
            "clientes": self._panel_clientes,
            "suscripciones": self._panel_suscripciones,
            "clases": self._panel_clases,
            "instructores": self._panel_instructores,
            "facturacion": self._panel_facturacion,
            "reportes": self._panel_reportes,
            "configuracion": self._panel_configuracion,
        }
        panel = panel_map.get(page_id)
        if panel and hasattr(panel, "refresh"):
            panel.refresh()

        logger.info("[NAV] Panel activo: %s", page_id)

    def _generar_plan_para_cliente(self, cliente: dict) -> None:
        """Navega al panel de generar plan con el cliente pre-cargado."""
        self._navegar("generar_plan")
        QTimer.singleShot(50, lambda: self._panel_generar.iniciar_con_cliente(cliente))

    def _plan_rapido_para_cliente(self, cliente: dict) -> None:
        """Plan rápido: navega y genera con última configuración."""
        self._navegar("generar_plan")
        QTimer.singleShot(50, lambda: self._panel_generar.iniciar_plan_rapido(cliente))

    # ── Acciones adicionales ──────────────────────────────────────────────────

    def _abrir_api_docs(self) -> None:
        """Abrir API docs en navegador web (URL configurable)."""
        import os
        api_docs_url = os.getenv("API_DOCS_URL", "http://localhost:8000/docs")
        webbrowser.open(api_docs_url)

    def _cerrar_sesion(self) -> None:
        """Confirma y cierra la sesión actual."""
        from ui_desktop.pyside.widgets.confirm_dialog import confirmar
        if confirmar(
            self, "Cerrar sesión",
            "¿Deseas cerrar la sesión actual?",
            texto_si="Sí, cerrar",
            texto_no="Cancelar",
        ):
            logger.info("[SESSION] Sesión cerrada por el usuario.")
            self.close()

    def _abrir_admin(self) -> None:
        try:
            from ui_desktop.pyside.ventana_admin import VentanaAdmin
            dlg = VentanaAdmin(self)
            dlg.exec()
        except Exception as exc:
            logger.warning("[ADMIN] No se pudo abrir panel admin: %s", exc)

    def _registro_rapido(self) -> None:
        """Ctrl+N shortcut: navigate to clients and open registration dialog."""
        self._navegar("clientes")
        QTimer.singleShot(100, self._panel_clientes._abrir_dialogo_registro)
