# -*- coding: utf-8 -*-
"""
Sidebar personalizado — diseño moderno oscuro con navegación simple.
Inspirado en dashboard de gestión de gimnasio con sidebar dark.
"""
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpacerItem, QSizePolicy, QWidget,
)
from PySide6.QtCore import Qt, Signal

from core.branding import branding
from design_system.tokens import Colors, Spacing

try:
    from config.constantes import ENABLE_BILLING
except ImportError:
    ENABLE_BILLING = True


class CustomSidebar(QFrame):
    """Sidebar de navegación con diseño oscuro moderno."""

    navigation_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self._nav_buttons: dict[str, QPushButton] = {}
        self._setup_ui()

    # ── Construcción ──────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo ──────────────────────────────────────────────────────────────
        logo_container = QWidget()
        logo_container.setStyleSheet("background: transparent;")
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(20, 24, 20, 8)
        logo_layout.setSpacing(10)

        logo_icon = QLabel("⚡")
        logo_icon.setObjectName("sidebarLogoIcon")
        logo_layout.addWidget(logo_icon)

        logo_label = QLabel(branding.get("nombre_corto", "MetodoBase"))
        logo_label.setObjectName("sidebarLogo")
        logo_layout.addWidget(logo_label)
        logo_layout.addStretch()

        layout.addWidget(logo_container)
        layout.addSpacing(12)

        # ── Sección Principal ─────────────────────────────────────────────────
        self._add_section_label("Principal", layout)
        self._add_nav("dashboard",    "📊  Dashboard",       layout)
        self._add_nav("clientes",     "👥  Miembros",        layout)
        self._add_nav("generar_plan", "📋  Generar planes",  layout)
        
        layout.addSpacing(16)
        
        # ── Sección Gestión ───────────────────────────────────────────────────
        self._add_section_label("Gestión", layout)
        self._add_nav("suscripciones","💳  Suscripciones",   layout)
        self._add_nav("clases",       "🏋  Clases",          layout)
        self._add_nav("instructores", "👨‍🏫  Instructores",    layout)
        if ENABLE_BILLING:
            self._add_nav("facturacion",  "🧾  Facturación",     layout)
        self._add_nav("reportes",     "📈  Reportes",        layout)
        
        layout.addSpacing(16)
        
        # ── Sección Sistema ───────────────────────────────────────────────────
        self._add_section_label("Sistema", layout)
        self._add_nav("configuracion","⚙️  Opciones",        layout)

        # ── Spacer ────────────────────────────────────────────────────────────
        layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # ── Footer: Cerrar sesión ─────────────────────────────────────────────
        self._add_nav_bottom("switch_gym", "🚪  Cerrar sesión", layout)

        layout.addSpacing(8)

        # ── Usuario Footer ────────────────────────────────────────────────────
        layout.addWidget(self._create_user_footer())

    def _add_nav(self, page_id: str, text: str, layout: QVBoxLayout) -> None:
        btn = self._create_nav_button(text, page_id)
        self._nav_buttons[page_id] = btn
        layout.addWidget(btn)

    def _add_section_label(self, text: str, layout: QVBoxLayout) -> None:
        """Agrega una etiqueta de sección al sidebar."""
        label = QLabel(text.upper())
        label.setObjectName("sidebarSectionLabel")
        layout.addWidget(label)

    def _add_nav_bottom(self, page_id: str, text: str, layout: QVBoxLayout) -> None:
        """Agrega botón de navegación en la sección inferior (sin estado activo)."""
        btn = self._create_nav_button(text, page_id)
        # Para Settings/Switch no marcamos activo
        self._nav_buttons[page_id] = btn
        layout.addWidget(btn)

    def _create_nav_button(self, text: str, page_id: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("navItem")  # Uses sidebar nav styles from amarillo_neon.qss
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._on_nav_clicked(page_id))
        return btn

    def _create_user_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("sidebarFooter")

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        # Avatar circular
        nombre_gym = branding.get("nombre_gym", "Mi Gimnasio")
        initials = "".join(w[0].upper() for w in nombre_gym.split()[:2]) or "GY"
        avatar = QLabel(initials)
        avatar.setObjectName("sidebarAvatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(36, 36)
        layout.addWidget(avatar)

        # Información
        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name_label = QLabel(nombre_gym)
        name_label.setObjectName("sidebarUserName")
        info_layout.addWidget(name_label)

        plan_label = QLabel("Premium")
        plan_label.setObjectName("sidebarUserRole")
        info_layout.addWidget(plan_label)

        layout.addWidget(info_widget)
        layout.addStretch()

        return footer

    # ── Lógica de navegación ──────────────────────────────────────────────────

    # IDs que no corresponden a panels reales del stack
    _NON_PANEL_IDS = {"switch_gym", "configuracion_sys"}

    def _on_nav_clicked(self, page_id: str) -> None:
        if page_id == "switch_gym":
            # Emitir señal especial
            self.navigation_changed.emit("switch_gym")
            return
        if page_id == "configuracion_sys":
            # Redirige a configuración estándar
            self._set_active("configuracion")
            self.navigation_changed.emit("configuracion")
            return
        self._set_active(page_id)
        self.navigation_changed.emit(page_id)

    def _set_active(self, page_id: str) -> None:
        for pid, btn in self._nav_buttons.items():
            is_active = (pid == page_id)
            btn.setChecked(is_active)
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

    def set_active_page(self, page_id: str) -> None:
        """Activa programáticamente una página en el sidebar."""
        self._set_active(page_id)

    def activate_dashboard(self) -> None:
        self._set_active("dashboard")

    def activate_clientes(self) -> None:
        self._set_active("clientes")

    def activate_generar_plan(self) -> None:
        self._set_active("generar_plan")
