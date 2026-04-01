# -*- coding: utf-8 -*-
"""
Panel de administración — PySide6.
Reemplaza gui/ventana_admin.py.
"""

import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTabWidget, QWidget, QScrollArea,
    QFileDialog, QApplication, QGridLayout,
)
from PySide6.QtCore import Qt

from core.branding import branding
from core.licencia import GestorLicencias
from config.constantes import CARPETA_CONFIG
from src.gestor_bd import GestorBDClientes
from design_system.tokens import Colors
from ui_desktop.pyside.widgets.confirm_dialog import confirmar
from ui_desktop.pyside.widgets.toast import mostrar_toast
from utils.logger import logger


class VentanaAdmin(QDialog):
    """Panel de administración del sistema."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Panel de Administración — Método Base")
        self.resize(820, 720)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.branding    = branding
        self.gestor_bd   = GestorBDClientes()
        self.gestor_lic  = GestorLicencias()

        self._build_ui()
        logger.info("[ADMIN] Panel de administración abierto")

    # ------------------------------------------------------------------
    # UI principal
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(8)

        # Header
        hdr = QFrame()
        hdr.setObjectName("adminHeader")
        hdr.setFixedHeight(72)
        hl = QVBoxLayout(hdr)
        hl.setAlignment(Qt.AlignCenter)
        t = QLabel("⚙️  Panel de Administración")
        t.setAlignment(Qt.AlignCenter)
        t.setObjectName("adminTitle")
        hl.addWidget(t)
        sub = QLabel("Configuración avanzada del sistema")
        sub.setAlignment(Qt.AlignCenter)
        sub.setObjectName("adminSubtitle")
        hl.addWidget(sub)
        root.addWidget(hdr)

        # Tabs
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self._crear_tab_branding()
        self._crear_tab_bd()
        self._crear_tab_busqueda()

        # Cerrar
        btn_cerrar = QPushButton("❌  Cerrar")
        btn_cerrar.setFixedWidth(140)
        btn_cerrar.setObjectName("ghostButton")
        btn_cerrar.clicked.connect(self.accept)
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.addStretch()
        rl.addWidget(btn_cerrar)
        root.addWidget(row)

    # ------------------------------------------------------------------
    # Pestaña Branding
    # ------------------------------------------------------------------

    def _crear_tab_branding(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        scroll.setWidget(inner)
        self.tabs.addTab(scroll, "🎨 Branding")

        # Datos del gym
        self._seccion(layout, "Información del Gimnasio")
        self.entry_nombre_gym   = self._campo(layout, "Nombre del Gym:",  self.branding.get("nombre_gym", ""))
        self.entry_nombre_corto = self._campo(layout, "Nombre Corto:",    self.branding.get("nombre_corto", ""))
        self.entry_tagline      = self._campo(layout, "Tagline:",         self.branding.get("tagline", ""))

        self._seccion(layout, "Información de Contacto")
        self.entry_tel     = self._campo(layout, "Teléfono:",   self.branding.get("contacto.telefono", ""))
        self.entry_email   = self._campo(layout, "Email:",      self.branding.get("contacto.email", ""))
        self.entry_dir     = self._campo(layout, "Dirección:",  self.branding.get("contacto.direccion", ""))
        self.entry_wa      = self._campo(layout, "WhatsApp:",   self.branding.get("contacto.whatsapp", ""))

        self._seccion(layout, "Color Encabezado PDF")
        self.entry_col_pdf  = self._campo(layout, "Color Encabezado PDF (hex):", self.branding.get("pdf.color_encabezado", "#FFEB3B"))

        self._seccion(layout, "Logo del PDF")
        self.entry_logo = self._campo(layout, "Ruta logo PDF:", self.branding.get("pdf.logo_path", "assets/logo.png"))
        self.entry_logo.setReadOnly(True)

        logo_btns = QWidget()
        logo_btns.setObjectName("transparentWidget")
        lb = QHBoxLayout(logo_btns)
        lb.setContentsMargins(0, 0, 0, 0)
        b1 = QPushButton("🖼️  Seleccionar Logo...")
        b1.setObjectName("ghostButton")
        b1.clicked.connect(self._seleccionar_logo)
        lb.addWidget(b1)
        b2 = QPushButton("↩️  Restaurar Predeterminado")
        b2.setObjectName("btn_secondary")
        b2.clicked.connect(self._restaurar_logo)
        lb.addWidget(b2)
        lb.addStretch()
        layout.addWidget(logo_btns)

        # Guardar
        btn_guardar = QPushButton("💾  Guardar Configuración")
        btn_guardar.setMinimumHeight(44)
        btn_guardar.setObjectName("successButton")
        btn_guardar.clicked.connect(self._guardar_branding)
        layout.addWidget(btn_guardar)
        layout.addStretch()

    # ------------------------------------------------------------------
    # Pestaña Base de Datos
    # ------------------------------------------------------------------

    def _crear_tab_bd(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        scroll.setWidget(inner)
        self.tabs.addTab(scroll, "💾 Base de Datos")

        # Estado de licencia
        lic_card = self._card()
        lc = QVBoxLayout(lic_card)
        lc.setContentsMargins(16, 14, 16, 14)
        t = QLabel("🔐  Estado de Licencia")
        t.setObjectName("adminSectionTitle")
        lc.addWidget(t)

        self.lbl_lic_estado = QLabel("Estado: consultando...")
        self.lbl_lic_plan   = QLabel("Plan: --")
        self.lbl_lic_dias   = QLabel("Días restantes: --")
        self.lbl_lic_corte  = QLabel("Fecha de corte: --")
        for lbl in (self.lbl_lic_estado, self.lbl_lic_plan, self.lbl_lic_dias, self.lbl_lic_corte):
            lbl.setObjectName("adminValueLabel")
            lc.addWidget(lbl)

        lic_btns = QWidget()
        lic_btns.setObjectName("transparentWidget")
        lb = QHBoxLayout(lic_btns)
        lb.setContentsMargins(0, 8, 0, 0)
        b_renov = QPushButton("🔄 Renovar ahora")
        b_renov.setObjectName("primaryButton")
        b_renov.clicked.connect(self._renovar_licencia)
        lb.addWidget(b_renov)
        b_cid = QPushButton("📋 Copiar ID instalación")
        b_cid.setObjectName("ghostButton")
        b_cid.clicked.connect(self._copiar_id_lic)
        lb.addWidget(b_cid)
        lb.addStretch()
        lc.addWidget(lic_btns)
        layout.addWidget(lic_card)

        self._refrescar_licencia()

        # Estadísticas
        stats = self.gestor_bd.obtener_estadisticas_gym()
        stats_card = self._card()
        sl = QVBoxLayout(stats_card)
        sl.setContentsMargins(16, 14, 16, 14)
        t2 = QLabel("📊  Estadísticas del Gimnasio")
        t2.setObjectName("adminSectionTitle")
        sl.addWidget(t2)
        sg = QGridLayout()
        sg.setSpacing(8)
        self._stat_box(sg, 0, 0, "👥 Total Clientes",          str(stats.get("total_clientes", 0)))
        self._stat_box(sg, 0, 1, "📈 Clientes Nuevos (30d)",   str(stats.get("clientes_nuevos", 0)))
        self._stat_box(sg, 1, 0, "🍽️ Planes Generados (30d)",  str(stats.get("planes_periodo", 0)))
        self._stat_box(sg, 1, 1, "⚡ Promedio Kcal",            f"{stats.get('promedio_kcal', 0):.0f}")
        sl.addLayout(sg)
        layout.addWidget(stats_card)

        # Backups
        back_card = self._card()
        bl = QVBoxLayout(back_card)
        bl.setContentsMargins(16, 14, 16, 14)
        t3 = QLabel("💾  Gestión de Backups")
        t3.setObjectName("adminSectionTitle")
        bl.addWidget(t3)
        info = QLabel("Los backups se crean automáticamente cada 7 días.")
        info.setObjectName("adminLabel")
        info.setWordWrap(True)
        bl.addWidget(info)
        back_btns = QWidget()
        back_btns.setObjectName("transparentWidget")
        bb = QHBoxLayout(back_btns)
        bb.setContentsMargins(0, 8, 0, 0)
        b_cr = QPushButton("📦 Crear Backup")
        b_cr.setObjectName("successButton")
        b_cr.clicked.connect(self._crear_backup)
        bb.addWidget(b_cr)
        b_lm = QPushButton("🗑️ Limpiar Antiguos")
        b_lm.setObjectName("dangerButton")
        b_lm.clicked.connect(self._limpiar_backups)
        bb.addWidget(b_lm)
        bb.addStretch()
        bl.addWidget(back_btns)
        layout.addWidget(back_card)

        # Reportes
        btn_rep = QPushButton("📊  Ver Reportes Completos")
        btn_rep.setMinimumHeight(50)
        btn_rep.setObjectName("premiumButton")
        btn_rep.clicked.connect(self._abrir_reportes)
        layout.addWidget(btn_rep)
        layout.addStretch()

    # ------------------------------------------------------------------
    # Pestaña Búsqueda
    # ------------------------------------------------------------------

    def _crear_tab_busqueda(self) -> None:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        self.tabs.addTab(w, "🔍 Búsqueda")

        s_card = self._card()
        sl = QVBoxLayout(s_card)
        sl.setContentsMargins(16, 12, 16, 12)
        t = QLabel("🔍  Buscar Cliente")
        t.setObjectName("adminSectionTitle")
        sl.addWidget(t)
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        self.entry_busqueda = QLineEdit()
        self.entry_busqueda.setPlaceholderText("Nombre, teléfono o ID del cliente...")
        rl.addWidget(self.entry_busqueda, 1)
        btn_b = QPushButton("🔍  Buscar")
        btn_b.setObjectName("primaryButton")
        btn_b.clicked.connect(self._buscar_clientes)
        rl.addWidget(btn_b)
        sl.addWidget(row)
        layout.addWidget(s_card)

        # Resultados
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: 1px solid #2A2A2A; border-radius: 8px;")
        self.resultados_inner = QWidget()
        self.resultados_inner.setStyleSheet("background-color: #0D0D0D;")
        self.resultados_layout = QVBoxLayout(self.resultados_inner)
        self.resultados_layout.setSpacing(6)
        self.resultados_layout.setContentsMargins(8, 8, 8, 8)
        scroll.setWidget(self.resultados_inner)
        layout.addWidget(scroll, 1)

    # ------------------------------------------------------------------
    # Helpers de UI
    # ------------------------------------------------------------------

    def _seccion(self, layout: QVBoxLayout, titulo: str) -> None:
        lbl = QLabel(titulo)
        lbl.setObjectName("adminSectionTitle")
        layout.addWidget(lbl)

    def _campo(self, layout: QVBoxLayout, label: str, valor: str) -> QLineEdit:
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setFixedWidth(200)
        lbl.setObjectName("adminLabel")
        rl.addWidget(lbl)
        entry = QLineEdit(valor)
        rl.addWidget(entry, 1)
        layout.addWidget(row)
        return entry

    def _card(self) -> QFrame:
        f = QFrame()
        f.setObjectName("adminCard")
        return f

    def _stat_box(self, grid: QGridLayout, row: int, col: int, titulo: str, valor: str) -> None:
        f = QFrame()
        f.setObjectName("adminCard")
        fl = QVBoxLayout(f)
        fl.setContentsMargins(12, 10, 12, 10)
        fl.setSpacing(4)
        t = QLabel(titulo)
        t.setObjectName("adminLabel")
        t.setAlignment(Qt.AlignCenter)
        fl.addWidget(t)
        v = QLabel(valor)
        v.setAlignment(Qt.AlignCenter)
        v.setObjectName("kpiValue")
        v.setStyleSheet("font-size: 22px;")
        fl.addWidget(v)
        grid.addWidget(f, row, col)

    # ------------------------------------------------------------------
    # Acciones de Branding
    # ------------------------------------------------------------------

    def _guardar_branding(self) -> None:
        cambios = {
            "nombre_gym":            self.entry_nombre_gym.text().strip(),
            "nombre_corto":          self.entry_nombre_corto.text().strip(),
            "tagline":               self.entry_tagline.text().strip(),
            "contacto.telefono":     self.entry_tel.text().strip(),
            "contacto.email":        self.entry_email.text().strip(),
            "contacto.direccion":    self.entry_dir.text().strip(),
            "contacto.whatsapp":     self.entry_wa.text().strip(),
            "pdf.color_encabezado":  self.entry_col_pdf.text().strip(),
            "pdf.logo_path":         self.entry_logo.text().strip(),
        }
        for key, val in cambios.items():
            if val:
                self.branding.set(key, val)
        self.branding.guardar()
        logger.info("[ADMIN] Branding guardado")
        mostrar_toast(self, "✅ Configuración de branding guardada correctamente.", "success")

    def _seleccionar_logo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Logo",
            str(Path(CARPETA_CONFIG)),
            "Imágenes (*.png *.jpg *.jpeg *.svg)",
        )
        if not ruta:
            return
        destino = Path(CARPETA_CONFIG) / "logo_custom.png"
        try:
            shutil.copy2(ruta, destino)
            self.entry_logo.setText(str(destino))
            mostrar_toast(self, f"✅ Logo copiado a: {destino}", "success")
        except Exception as exc:
            mostrar_toast(self, f"❌ No se pudo copiar el logo: {exc}", "error")

    def _restaurar_logo(self) -> None:
        self.entry_logo.setText("assets/logo.png")

    # ------------------------------------------------------------------
    # Acciones de BD
    # ------------------------------------------------------------------

    def _refrescar_licencia(self) -> None:
        try:
            valida, msg, info = self.gestor_lic.validar_licencia()
            color = Colors.SUCCESS if valida else Colors.ERROR
            self.lbl_lic_estado.setText(f"Estado: {msg}")
            self.lbl_lic_estado.setStyleSheet(f"color: {color}; font-size: 12px;")
            if info:
                self.lbl_lic_plan.setText(f"Plan: {info.get('plan_comercial', '--')}")
                self.lbl_lic_dias.setText(f"Días restantes: {info.get('dias_restantes', '--')}")
                self.lbl_lic_corte.setText(f"Fecha de corte: {info.get('fecha_corte', '--')}")
        except Exception as exc:
            self.lbl_lic_estado.setText(f"Error al consultar licencia: {exc}")

    def _renovar_licencia(self) -> None:
        from ui_desktop.pyside.ventana_licencia import VentanaActivacionLicencia
        nombre = self.branding.get("nombre_gym", "MetodoBase")
        dlg = VentanaActivacionLicencia(self, gestor=self.gestor_lic, nombre_gym=nombre)
        if dlg.exec() and dlg.activada:
            self._refrescar_licencia()

    def _copiar_id_lic(self) -> None:
        id_inst = self.gestor_lic.obtener_id_instalacion()
        QApplication.clipboard().setText(id_inst)
        mostrar_toast(self, "✅ ID de instalación copiado al portapapeles.", "success")

    def _crear_backup(self) -> None:
        try:
            resultado = self.gestor_bd.crear_backup()
            if resultado:
                mostrar_toast(self, f"✅ Backup guardado en: {resultado}", "success")
            else:
                mostrar_toast(self, "❌ No se pudo crear el backup.", "error")
        except Exception as exc:
            mostrar_toast(self, f"❌ Error al crear backup: {exc}", "error")

    def _limpiar_backups(self) -> None:
        if confirmar(
            self,
            "Limpiar backups",
            "¿Deseas eliminar los backups con más de 30 días?",
            texto_si="Sí, limpiar",
            texto_no="Cancelar",
        ):
            eliminados = self.gestor_bd.limpiar_backups_antiguos(dias=30)
            mostrar_toast(self, f"✅ Se eliminaron {eliminados} backups antiguos.", "success")

    def _abrir_reportes(self) -> None:
        from ui_desktop.pyside.ventana_reportes import VentanaReportes
        dlg = VentanaReportes(self)
        dlg.exec()

    # ------------------------------------------------------------------
    # Búsqueda de clientes
    # ------------------------------------------------------------------

    def _buscar_clientes(self) -> None:
        # Limpiar resultados anteriores
        while self.resultados_layout.count():
            item = self.resultados_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        query = self.entry_busqueda.text().strip()
        if not query:
            lbl = QLabel("Escribe un término de búsqueda.")
            lbl.setStyleSheet("color: #A1A1AA;")
            self.resultados_layout.addWidget(lbl)
            return

        try:
            clientes = self.gestor_bd.buscar_clientes(query)
            if not clientes:
                lbl = QLabel("No se encontraron clientes.")
                lbl.setStyleSheet("color: #A1A1AA;")
                self.resultados_layout.addWidget(lbl)
                return
            for cli in clientes[:50]:
                card = QFrame()
                card.setStyleSheet(
                    "QFrame { background-color: #1A1A1A; border-radius: 8px; border: none; }"
                )
                cl = QHBoxLayout(card)
                cl.setContentsMargins(12, 8, 12, 8)
                nombre = cli.get("nombre", "—")
                tel    = cli.get("telefono", "—")
                lbl = QLabel(f"<b>{nombre}</b>  •  {tel}")
                lbl.setStyleSheet("color: #FFFFFF; font-size: 12px;")
                cl.addWidget(lbl, 1)
                self.resultados_layout.addWidget(card)
            self.resultados_layout.addStretch()
        except Exception as exc:
            lbl = QLabel(f"Error: {exc}")
            lbl.setStyleSheet("color: #FF1744;")
            self.resultados_layout.addWidget(lbl)
