# -*- coding: utf-8 -*-
"""
ConfiguracionPanel — Módulo de configuración del sistema.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from ui_desktop.pyside.widgets.toast import mostrar_toast
from utils.logger import logger





class ConfiguracionPanel(QWidget):
    """Panel de configuración del gimnasio y preferencias del sistema."""

    def __init__(self, gestor_bd=None, parent=None):
        super().__init__(parent)
        self.gestor_bd = gestor_bd
        self._setup_ui()

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
        self._layout.setSpacing(20)
        scroll.setWidget(content)

        self._crear_header()
        self._crear_seccion_gym()
        self._crear_seccion_cuenta()
        self._crear_seccion_sistema()
        
        self._layout.addStretch()

    def _crear_header(self) -> None:
        header = QFrame()
        header.setObjectName("headerFrame")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 24)

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("Configuración")
        title.setObjectName("pageTitle")
        left.addWidget(title)
        subtitle = QLabel("Panel de control del sistema y preferencias del gimnasio")
        subtitle.setObjectName("pageSubtitle")
        left.addWidget(subtitle)
        layout.addLayout(left)
        layout.addStretch()

        self._layout.addWidget(header)

    def _crear_seccion_gym(self) -> None:
        """Sección 1: Información del Gimnasio"""
        container = QFrame()
        container.setObjectName("configCard")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Card title
        title = QLabel("🏢  Información del Gimnasio")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        # Form fields
        self._crear_campo_config(layout, "Nombre del Gimnasio", "gym_nombre", "Ej: Gimnasio MetodoBase")
        self._crear_campo_config(layout, "Dirección", "gym_direccion", "Ej: Av. Principal 123")
        self._crear_campo_config(layout, "Teléfono", "gym_telefono", "Ej: +52 555 1234567")
        self._crear_campo_config(layout, "Email", "gym_email", "Ej: contacto@gimnasio.com")
        self._crear_campo_config(layout, "Cuota Mensual ($)", "gym_cuota", "Ej: 800")

        # Save button
        btn_guardar = QPushButton("💾  Guardar Cambios")
        btn_guardar.setObjectName("primaryButton")
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.clicked.connect(self._guardar_info_gym)
        layout.addWidget(btn_guardar)

        self._layout.addWidget(container)

    def _crear_seccion_cuenta(self) -> None:
        """Sección 2: Cuenta y Licencia"""
        container = QFrame()
        container.setObjectName("configCard")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Card title
        title = QLabel("🔐  Cuenta y Licencia")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        # License status indicator
        status_container = QFrame()
        status_container.setObjectName("transparentWidget")
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(12)
        
        status_label = QLabel("Estado de Licencia:")
        status_label.setObjectName("configLabel")
        status_layout.addWidget(status_label)
        
        self._badge_licencia = QLabel("Cargando...")
        self._badge_licencia.setObjectName("badgeActive")
        status_layout.addWidget(self._badge_licencia)
        status_layout.addStretch()
        
        layout.addWidget(status_container)

        # License info (read-only) — dynamic
        self._crear_info_readonly(layout, "Plan", "—", "_lbl_plan")
        self._crear_info_readonly(layout, "Vencimiento", "—", "_lbl_vencimiento")

        # Manage license button
        btn_licencia = QPushButton("⚙️  Administrar Licencia")
        btn_licencia.setObjectName("secondaryButton")
        btn_licencia.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_licencia.clicked.connect(self._abrir_ventana_licencia)
        layout.addWidget(btn_licencia)

        self._layout.addWidget(container)
        
        # Load license asynchronously
        self._cargar_licencia()

    def _crear_seccion_sistema(self) -> None:
        """Sección 3: Sistema y Herramientas"""
        container = QFrame()
        container.setObjectName("configCard")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Card title
        title = QLabel("⚙️  Sistema y Herramientas")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("dividerLine")
        layout.addWidget(divider)

        # Action buttons with descriptions
        self._crear_accion_sistema(
            layout,
            "Panel de Administración",
            "Gestionar usuarios, permisos y configuraciones avanzadas",
            "🔧  Abrir Panel",
            self._abrir_admin
        )
        
        self._crear_accion_sistema(
            layout,
            "Copia de Seguridad",
            "Crear backup completo de la base de datos",
            "📦  Crear Backup",
            self._crear_backup
        )
        
        self._crear_accion_sistema(
            layout,
            "Limpiar Caché",
            "Eliminar archivos temporales y optimizar rendimiento",
            "🧹  Limpiar Caché",
            self._limpiar_cache
        )

        self._layout.addWidget(container)

    def _abrir_admin(self) -> None:
        try:
            from ui_desktop.pyside.ventana_admin import VentanaAdmin
            dlg = VentanaAdmin(self)
            dlg.exec()
        except Exception as exc:
            logger.warning("⚠️ No se pudo abrir panel admin: %s", exc)

    def _crear_campo_config(self, layout, label_text, field_id, placeholder):
        """Helper para crear un campo de formulario con label e input"""
        lbl = QLabel(label_text)
        lbl.setObjectName("fieldLabel")
        layout.addWidget(lbl)
        
        inp = QLineEdit()
        inp.setObjectName(field_id)
        inp.setPlaceholderText(placeholder)
        layout.addWidget(inp)
        
        # Store reference for later access
        setattr(self, f"_{field_id}", inp)

    def _crear_info_readonly(self, layout, label_text, value_text, field_id=None):
        """Helper para crear un campo readonly de información"""
        container = QFrame()
        container.setObjectName("transparentWidget")
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        
        lbl = QLabel(label_text + ":")
        lbl.setObjectName("configLabel")
        lbl.setFixedWidth(120)
        row.addWidget(lbl)
        
        val = QLabel(value_text)
        val.setObjectName("configValue")
        row.addWidget(val)
        row.addStretch()
        
        if field_id:
            setattr(self, field_id, val)
        
        layout.addWidget(container)

    def _crear_accion_sistema(self, layout, titulo, descripcion, btn_text, callback):
        """Helper para crear una acción del sistema con título, descripción y botón"""
        container = QFrame()
        container.setObjectName("configActionRow")
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 12)
        row.setSpacing(16)
        
        # Left: text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_lbl = QLabel(titulo)
        title_lbl.setObjectName("configSectionTitle")
        text_layout.addWidget(title_lbl)
        
        desc_lbl = QLabel(descripcion)
        desc_lbl.setObjectName("configLabel")
        desc_lbl.setWordWrap(True)
        text_layout.addWidget(desc_lbl)
        
        row.addLayout(text_layout, 1)
        
        # Right: action button
        btn = QPushButton(btn_text)
        btn.setObjectName("secondaryButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumWidth(160)
        btn.clicked.connect(callback)
        row.addWidget(btn)
        
        layout.addWidget(container)

    def _guardar_info_gym(self):
        """Guardar información del gimnasio en branding.json"""
        try:
            from core.branding import branding
            branding.set("nombre_gym", self._gym_nombre.text().strip())
            branding.set("direccion", self._gym_direccion.text().strip())
            branding.set("telefono", self._gym_telefono.text().strip())
            branding.set("email", self._gym_email.text().strip())
            cuota_text = self._gym_cuota.text().strip()
            if cuota_text:
                branding.set("cuota_mensual", float(cuota_text))
            branding.guardar()
            logger.info("💾 Información del gimnasio guardada")
            mostrar_toast(self, "✅ Información del gimnasio guardada correctamente.", "success")
        except Exception as exc:
            logger.error("❌ Error guardando info gym: %s", exc)
            mostrar_toast(self, f"❌ No se pudo guardar: {exc}", "error")

    def _abrir_ventana_licencia(self):
        """Abrir ventana de gestión de licencia"""
        try:
            from ui_desktop.pyside.ventana_licencia import VentanaActivacionLicencia
            from core.licencia import GestorLicencias
            gestor = GestorLicencias()
            nombre_gym = "MetodoBase"
            try:
                from core.branding import branding
                nombre_gym = branding.get("nombre_gym", "MetodoBase")
            except Exception:
                pass
            dlg = VentanaActivacionLicencia(self, gestor=gestor, nombre_gym=nombre_gym)
            dlg.exec()
        except Exception as exc:
            logger.warning("⚠️ No se pudo abrir ventana de licencia: %s", exc)

    def _crear_backup(self):
        """Crear copia de seguridad de la BD"""
        if self.gestor_bd is None:
            mostrar_toast(self, "⚠️ No hay conexión a la base de datos.", "warning")
            return
        try:
            ruta = self.gestor_bd.crear_backup()
            if ruta:
                logger.info("📦 Backup creado: %s", ruta)
                mostrar_toast(self, f"✅ Backup creado en: {ruta}", "success")
            else:
                mostrar_toast(self, "❌ No se pudo crear el backup.", "error")
        except Exception as exc:
            logger.error("❌ Error creando backup: %s", exc)
            mostrar_toast(self, f"❌ Error al crear backup: {exc}", "error")

    def _limpiar_cache(self):
        """Limpiar caché del sistema (__pycache__ y archivos temporales)"""
        import shutil
        from pathlib import Path
        limpiados = 0
        base = Path(__file__).parent.parent.parent
        for cache_dir in base.rglob("__pycache__"):
            try:
                shutil.rmtree(cache_dir)
                limpiados += 1
            except OSError:
                pass
        logger.info("🧹 Caché limpiada: %d directorios", limpiados)
        mostrar_toast(self, f"✅ Cache limpiada ({limpiados} directorios eliminados).", "success")

    def _cargar_licencia(self) -> None:
        """Carga el estado de la licencia desde el gestor."""
        try:
            from core.licencia import GestorLicencias
            gestor = GestorLicencias()
            estado = gestor.obtener_estado_licencia()
            
            if estado.get("activa"):
                self._badge_licencia.setText("✓ Activa")
                self._badge_licencia.setObjectName("badgeActive")
            else:
                self._badge_licencia.setText("✗ Inactiva")
                self._badge_licencia.setObjectName("badgeInactive")
            self._badge_licencia.style().unpolish(self._badge_licencia)
            self._badge_licencia.style().polish(self._badge_licencia)
            
            self._lbl_plan.setText(estado.get("plan_label", "—"))
            fecha = estado.get("fecha_corte", "")
            dias = estado.get("dias_restantes", 0)
            if fecha:
                self._lbl_vencimiento.setText(f"{fecha}  ({dias} días restantes)")
            else:
                self._lbl_vencimiento.setText("Sin fecha de vencimiento")
        except Exception as exc:
            logger.debug("No se pudo cargar licencia: %s", exc)
            self._badge_licencia.setText("— Sin datos")

    def refresh(self) -> None:
        """Recarga configuración desde branding y licencia."""
        logger.info("⚙️ Refrescando panel de configuración")
        try:
            from core.branding import branding
            self._gym_nombre.setText(branding.get("nombre_gym", ""))
            self._gym_direccion.setText(branding.get("direccion", ""))
            self._gym_telefono.setText(branding.get("telefono", ""))
            self._gym_email.setText(branding.get("email", ""))
            cuota = branding.get("cuota_mensual", 800)
            self._gym_cuota.setText(str(int(cuota)) if cuota == int(cuota) else str(cuota))
        except Exception as exc:
            logger.debug("No se pudieron cargar datos de branding: %s", exc)
        self._cargar_licencia()
