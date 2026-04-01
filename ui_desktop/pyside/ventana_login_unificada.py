# -*- coding: utf-8 -*-
"""
VentanaLoginUnificada — Pantalla de inicio de sesión unificada.

Layout (WIN_W × WIN_H):
  ┌─────────────────────────────────────────┬───────────────────┐
  │  FONDO.PNG  (escalado a la ventana)     │    Panel Login    │
  │  + overlay oscuro baked-in             │  ┌─────────────┐  │
  │                                         │  │ [🏢 GYM] [👤]│  │
  │  Método Base                            │  │  email      │  │
  │  Tu plan nutricional                    │  │  password   │  │
  │  personalizado…                         │  │  [Acceder]  │  │
  │                                         │  └─────────────┘  │
  └─────────────────────────────────────────┴───────────────────┘

Modos de acceso:
  · GYM     → email + contraseña → rol 'gym' / 'admin'
  · Usuario → email + contraseña (o registro simplificado)

Señales:
  login_exitoso(dict)  emitida con {'tipo': 'gym'|'usuario', 'sesion': SesionActiva}

Códigos de retorno de exec():
  ResultadoLogin.GYM      (1)  — sesion_gym  disponible
  ResultadoLogin.USUARIO  (2)  — sesion_usuario disponible
  ResultadoLogin.CANCELADO(0)  — ventana cerrada sin autenticar
"""
from __future__ import annotations

import re
from enum import IntEnum
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.services.auth_service import SesionActiva, crear_auth_service
from design_system.tokens import Colors
from utils.helpers import resource_path
from utils.logger import logger

# ── Regex email ──────────────────────────────────────────────────────────────
_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ── QSS reutilizable ──────────────────────────────────────────────────────────
_ENTRY_QSS = f"""
    QLineEdit {{
        background: {Colors.BG_CARD};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_DEFAULT};
        border-radius: 8px;
        padding: 0 14px;
        font-family: "Segoe UI", "DejaVu Sans", sans-serif;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border: 1px solid {Colors.PRIMARY};
    }}
    QLineEdit:disabled {{
        background: {Colors.BG_INPUT};
        color: {Colors.TEXT_HINT};
    }}
"""


# ── Enum de resultado ─────────────────────────────────────────────────────────

class ResultadoLogin(IntEnum):
    CANCELADO = 0
    GYM       = 1
    USUARIO   = 2


# ── Helpers de UI ─────────────────────────────────────────────────────────────

def _lbl_plain(text: str, size: int = 13, bold: bool = False,
               color: str = Colors.TEXT_PRIMARY) -> QLabel:
    """Crea un QLabel simple con fuente Segoe UI."""
    lbl = QLabel(text)
    f = QFont("Segoe UI, DejaVu Sans", size)
    f.setBold(bold)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color: {color}; background: transparent;")
    return lbl


def _entry(placeholder: str = "", password: bool = False) -> QLineEdit:
    e = QLineEdit()
    e.setPlaceholderText(placeholder)
    e.setFixedHeight(42)
    e.setStyleSheet(_ENTRY_QSS)
    if password:
        e.setEchoMode(QLineEdit.Password)
    return e


def _primary_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setFixedHeight(46)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setObjectName("loginPrimaryBtn")
    return btn


def _error_lbl() -> QLabel:
    lbl = QLabel("")
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"color: {Colors.ERROR}; background: transparent; "
        f"font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 12px;"
    )
    lbl.hide()
    return lbl


def _link_lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setOpenExternalLinks(False)
    lbl.setStyleSheet(
        f"color: {Colors.TEXT_SECONDARY}; background: transparent; "
        f"font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 12px;"
    )
    return lbl


# ── Panel interno: Login GYM ──────────────────────────────────────────────────

class _PanelGymLogin(QWidget):
    """Formulario de login para cuenta tipo 'gym' / 'admin'."""

    autenticado          = Signal(SesionActiva)
    solicitar_registro   = Signal()   # emitida si usuario pide registro nuevo

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("transparentWidget")
        self._auth = crear_auth_service()
        self._sesion: Optional[SesionActiva] = None
        self._build()

    @property
    def sesion(self) -> Optional[SesionActiva]:
        return self._sesion

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Ícono
        ic = _lbl_plain("🏢", size=32)
        ic.setAlignment(Qt.AlignHCenter)
        lay.addWidget(ic)

        # Título y subtítulo
        title = _lbl_plain("Socio Comercial GYM", size=17, bold=True)
        title.setAlignment(Qt.AlignHCenter)
        lay.addWidget(title)

        sub = _lbl_plain("Accede con tus credenciales de gym", size=11, color=Colors.TEXT_SECONDARY)
        sub.setAlignment(Qt.AlignHCenter)
        lay.addWidget(sub)

        lay.addSpacing(6)

        # Campos
        self._email = _entry("Correo del gym")
        lay.addWidget(self._email)

        self._pw = _entry("Contraseña", password=True)
        lay.addWidget(self._pw)

        # Error
        self._error = _error_lbl()
        lay.addWidget(self._error)

        # Botón
        self._btn_acceder = _primary_btn("🏢  Acceder como GYM")
        lay.addWidget(self._btn_acceder)
        self._btn_acceder.clicked.connect(self._intentar_login)

        # Atajos de teclado
        self._email.returnPressed.connect(self._intentar_login)
        self._pw.returnPressed.connect(self._intentar_login)

        lay.addSpacing(4)
        # Tooltip informativo
        self._btn_acceder.setToolTip(
            "Inicia sesión con el correo y contraseña de tu cuenta GYM"
        )

        # Link para primera vez / registro
        lnk_reg = _link_lbl(
            "¿Primera vez? "
            "<a href='reg' style='color:#FFEB3B;'>Registrar mi gym →</a>"
        )
        lnk_reg.setOpenExternalLinks(False)
        lnk_reg.setAlignment(Qt.AlignHCenter)
        lnk_reg.linkActivated.connect(lambda _: self.solicitar_registro.emit())
        lay.addWidget(lnk_reg)

    def limpiar(self) -> None:
        """Limpia campos sensibles al cambiar de tab."""
        self._pw.clear()
        self._error.hide()

    def _intentar_login(self) -> None:
        email = self._email.text().strip().lower()
        pw = self._pw.text()
        self._error.hide()

        if not email or not _RE_EMAIL.match(email):
            self._mostrar_error("Ingresa un correo electrónico válido.")
            return
        if not pw:
            self._mostrar_error("Ingresa tu contraseña.")
            return

        self._btn_acceder.setEnabled(False)
        self._btn_acceder.setText("Verificando…")

        resultado = self._auth.login(email, pw)

        self._btn_acceder.setEnabled(True)
        self._btn_acceder.setText("🏢  Acceder como GYM")

        if not resultado.ok:
            msg = resultado.errores[0] if resultado.errores else "Credenciales incorrectas."
            self._mostrar_error(msg)
            self._pw.clear()
            logger.warning("[LOGIN_UNIF] Intento GYM fallido")
            return

        sesion = resultado.sesion
        if sesion is None or sesion.rol not in ("gym", "admin"):
            self._mostrar_error("Esta cuenta no tiene acceso de GYM.")
            self._pw.clear()
            return

        self._sesion = sesion
        self._pw.clear()
        logger.info("[LOGIN_UNIF] GYM autenticado rol=%s", sesion.rol)
        self.autenticado.emit(sesion)

    def _mostrar_error(self, msg: str) -> None:
        self._error.setText(f"❌  {msg}")
        self._error.show()


# ── Panel interno: Login Usuario Regular ──────────────────────────────────────

class _PanelUsuarioLogin(QWidget):
    """Formulario de login/registro para usuario regular."""

    autenticado = Signal(SesionActiva)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("transparentWidget")
        self._auth = crear_auth_service()
        self._sesion: Optional[SesionActiva] = None
        self._build()

    @property
    def sesion(self) -> Optional[SesionActiva]:
        return self._sesion

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Ícono
        ic = _lbl_plain("👤", size=32)
        ic.setAlignment(Qt.AlignHCenter)
        lay.addWidget(ic)

        title = _lbl_plain("Usuario Regular", size=17, bold=True)
        title.setAlignment(Qt.AlignHCenter)
        lay.addWidget(title)

        sub = _lbl_plain("Genera tu plan nutricional personal", size=11, color=Colors.TEXT_SECONDARY)
        sub.setAlignment(Qt.AlignHCenter)
        lay.addWidget(sub)

        lay.addSpacing(6)

        # Sub-stack: login (0) | registro (1)
        self._sub_stack = QStackedWidget()
        self._sub_stack.setObjectName("transparentWidget")
        lay.addWidget(self._sub_stack)

        self._sub_stack.addWidget(self._build_login_sub())
        self._sub_stack.addWidget(self._build_registro_sub())

    def limpiar(self) -> None:
        """Limpia campos sensibles."""
        self._pw_login.clear()
        self._error_login.hide()
        self._reg_pw.clear()
        self._reg_pw2.clear()
        self._error_reg.hide()
        self._sub_stack.setCurrentIndex(0)

    # ── Sub-panel login ───────────────────────────────────────────────────────

    def _build_login_sub(self) -> QWidget:
        page = QWidget()
        page.setObjectName("transparentWidget")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self._email_login = _entry("Correo electrónico")
        lay.addWidget(self._email_login)

        self._pw_login = _entry("Contraseña", password=True)
        lay.addWidget(self._pw_login)

        self._error_login = _error_lbl()
        lay.addWidget(self._error_login)

        btn = _primary_btn("👤  Iniciar Sesión")
        btn.setToolTip("Inicia sesión con tu correo y contraseña")
        btn.clicked.connect(self._intentar_login)
        lay.addWidget(btn)
        self._btn_login = btn

        self._email_login.returnPressed.connect(self._intentar_login)
        self._pw_login.returnPressed.connect(self._intentar_login)

        # Link registro
        row = QHBoxLayout()
        row.addStretch()
        lnk = _link_lbl(
            "¿Sin cuenta? <a href='reg' style='color:#FFEB3B;'>Regístrate</a>"
        )
        lnk.setOpenExternalLinks(False)
        lnk.linkActivated.connect(lambda _: self._sub_stack.setCurrentIndex(1))
        row.addWidget(lnk)
        row.addStretch()
        lay.addLayout(row)

        return page

    # ── Sub-panel registro ────────────────────────────────────────────────────

    def _build_registro_sub(self) -> QWidget:
        page = QWidget()
        page.setObjectName("transparentWidget")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        title_reg = _lbl_plain("Crear cuenta", size=15, bold=True)
        title_reg.setAlignment(Qt.AlignHCenter)
        lay.addWidget(title_reg)

        self._reg_nombre   = _entry("Nombre")
        self._reg_apellido = _entry("Apellido")
        self._reg_email    = _entry("Correo electrónico")
        self._reg_pw       = _entry("Contraseña", password=True)
        self._reg_pw2      = _entry("Repetir contraseña", password=True)

        for w in (self._reg_nombre, self._reg_apellido,
                  self._reg_email, self._reg_pw, self._reg_pw2):
            lay.addWidget(w)

        self._error_reg = _error_lbl()
        lay.addWidget(self._error_reg)

        btn_reg = _primary_btn("✅  Crear Cuenta")
        btn_reg.setToolTip("Crea tu cuenta de usuario regular")
        btn_reg.clicked.connect(self._intentar_registro)
        lay.addWidget(btn_reg)
        self._btn_registrar = btn_reg

        lnk_back = _link_lbl(
            "<a href='back' style='color:#FFEB3B;'>← Volver a inicio de sesión</a>"
        )
        lnk_back.setOpenExternalLinks(False)
        lnk_back.setAlignment(Qt.AlignHCenter)
        lnk_back.linkActivated.connect(lambda _: self._sub_stack.setCurrentIndex(0))
        lay.addWidget(lnk_back)

        return page

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _intentar_login(self) -> None:
        email = self._email_login.text().strip().lower()
        pw = self._pw_login.text()
        self._error_login.hide()

        if not email or not _RE_EMAIL.match(email):
            self._error_login.setText("❌  Ingresa un correo válido.")
            self._error_login.show()
            return
        if not pw:
            self._error_login.setText("❌  Ingresa tu contraseña.")
            self._error_login.show()
            return

        self._btn_login.setEnabled(False)
        self._btn_login.setText("Verificando…")

        resultado = self._auth.login(email, pw)

        self._btn_login.setEnabled(True)
        self._btn_login.setText("👤  Iniciar Sesión")

        if not resultado.ok:
            msg = resultado.errores[0] if resultado.errores else "Credenciales incorrectas."
            self._error_login.setText(f"❌  {msg}")
            self._error_login.show()
            self._pw_login.clear()
            return

        self._sesion = resultado.sesion
        self._pw_login.clear()
        logger.info("[LOGIN_UNIF] Usuario autenticado rol=%s", self._sesion.rol)
        self.autenticado.emit(self._sesion)

    def _intentar_registro(self) -> None:
        nombre   = self._reg_nombre.text().strip()
        apellido = self._reg_apellido.text().strip()
        email    = self._reg_email.text().strip().lower()
        pw       = self._reg_pw.text()
        pw2      = self._reg_pw2.text()
        self._error_reg.hide()

        if not nombre:
            self._error_reg.setText("❌  El nombre es obligatorio.")
            self._error_reg.show()
            return
        if not apellido:
            self._error_reg.setText("❌  El apellido es obligatorio.")
            self._error_reg.show()
            return
        if not email or not _RE_EMAIL.match(email):
            self._error_reg.setText("❌  Correo electrónico inválido.")
            self._error_reg.show()
            return
        if pw != pw2:
            self._error_reg.setText("❌  Las contraseñas no coinciden.")
            self._error_reg.show()
            return
        if not pw:
            self._error_reg.setText("❌  La contraseña es obligatoria.")
            self._error_reg.show()
            return

        self._btn_registrar.setEnabled(False)
        self._btn_registrar.setText("Registrando…")

        resultado = self._auth.registrar(
            nombre=nombre, apellido=apellido, email=email, password=pw
        )

        self._btn_registrar.setEnabled(True)
        self._btn_registrar.setText("✅  Crear Cuenta")

        if not resultado.ok:
            msg = "\n".join(resultado.errores) if resultado.errores else "Error al registrar."
            self._error_reg.setText(f"❌  {msg}")
            self._error_reg.show()
            self._reg_pw.clear()
            self._reg_pw2.clear()
            return

        self._sesion = resultado.sesion
        self._reg_pw.clear()
        self._reg_pw2.clear()
        logger.info("[LOGIN_UNIF] Usuario registrado id=***")
        self.autenticado.emit(self._sesion)


# ── Ventana Login Unificada ───────────────────────────────────────────────────

class VentanaLoginUnificada(QDialog):
    """
    Diálogo principal de inicio de sesión con fondo FONDO.PNG.

    Uso::

        dlg = VentanaLoginUnificada()
        resultado = dlg.exec()

        if resultado == ResultadoLogin.GYM:
            sesion = dlg.sesion_gym     # SesionActiva
        elif resultado == ResultadoLogin.USUARIO:
            sesion = dlg.sesion_usuario # SesionActiva
    """

    login_exitoso = Signal(dict)   # {'tipo': 'gym'|'usuario', 'sesion': SesionActiva}

    WIN_W   = 1200
    WIN_H   = 700
    PANEL_W = 430
    PANEL_H = 610

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Método Base — Iniciar Sesión")
        self.setFixedSize(self.WIN_W, self.WIN_H)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet(f"QDialog {{ background: {Colors.BG_DEEP}; }}")

        self._sesion_gym:     Optional[SesionActiva] = None
        self._sesion_usuario: Optional[SesionActiva] = None

        self._build_ui()

    # ── API pública ───────────────────────────────────────────────────────────

    @property
    def sesion_gym(self) -> Optional[SesionActiva]:
        """Sesión GYM activa tras autenticación exitosa de tipo GYM."""
        return self._sesion_gym

    @property
    def sesion_usuario(self) -> Optional[SesionActiva]:
        """Sesión de usuario regular tras autenticación exitosa."""
        return self._sesion_usuario

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Fondo con imagen (baked overlay) ─────────────────────────────────
        self._bg = QLabel(self)
        self._bg.setGeometry(0, 0, self.WIN_W, self.WIN_H)
        self._bg.setScaledContents(True)
        self._cargar_fondo()

        # ── Texto de bienvenida sobre el fondo (izquierda) ───────────────────
        brand_x, brand_y = 60, self.WIN_H // 2 - 80
        self._brand = QLabel(self)
        self._brand.setGeometry(brand_x, brand_y, self.WIN_W - self.PANEL_W - 120, 180)
        self._brand.setWordWrap(True)
        self._brand.setObjectName("transparentWidget")
        self._brand.setText(
            "<span style='color:#FFFFFF;font-size:32px;font-weight:700;line-height:1.2;'>"
            "Bienvenido a<br>"
            "<span style='color:#FFEB3B;'>MetodoBase</span></span><br><br>"
            "<span style='color:#A1A1AA;font-size:15px;font-weight:600;'>"
            "Una opción Innovadora<br>para tu gym</span><br><br>"
            "<span style='color:#A1A1AA;font-size:12px;'>"
            "Gestiona miembros, clases, planes nutricionales<br>"
            "y suscripciones en un solo lugar.</span>"
        )

        # ── Panel lateral derecho ─────────────────────────────────────────────
        panel_x = self.WIN_W - self.PANEL_W - 30
        panel_y = (self.WIN_H - self.PANEL_H) // 2
        self._panel = QFrame(self)
        self._panel.setGeometry(panel_x, panel_y, self.PANEL_W, self.PANEL_H)
        self._panel.setObjectName("LoginPanel")
        self._panel.setStyleSheet(f"""
            QFrame#LoginPanel {{
                background: {Colors.BG_INPUT};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 16px;
            }}
            QFrame#LoginPanel QLabel {{
                color: {Colors.TEXT_PRIMARY};
                background: transparent;
            }}
        """)

        # Sombra del panel
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(48)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 12)
        self._panel.setGraphicsEffect(shadow)

        # ── Layout del panel ──────────────────────────────────────────────────
        panel_lay = QVBoxLayout(self._panel)
        panel_lay.setContentsMargins(28, 22, 28, 22)
        panel_lay.setSpacing(0)

        # Logo icon + nombre
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignHCenter)
        logo_row.setSpacing(8)

        logo_icon = QLabel("⚡")
        logo_icon.setFixedSize(36, 36)
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_icon.setObjectName("loginLogoIcon")
        logo_row.addWidget(logo_icon)

        logo_name = _lbl_plain("Método Base", size=18, bold=True)
        logo_name.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        logo_row.addWidget(logo_name)
        panel_lay.addLayout(logo_row)

        tagline = _lbl_plain("Inicia sesión en tu cuenta", size=10, color=Colors.TEXT_SECONDARY)
        tagline.setAlignment(Qt.AlignHCenter)
        panel_lay.addWidget(tagline)

        panel_lay.addSpacing(16)

        # Divisor
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {Colors.BORDER_DEFAULT}; border: none;")
        panel_lay.addWidget(sep)

        panel_lay.addSpacing(14)

        # ── Tabs GYM / USUARIO ────────────────────────────────────────────────
        tabs_frame = QFrame()
        tabs_frame.setObjectName("loginTabsFrame")
        tabs_frame.setFixedHeight(46)
        tabs_lay = QHBoxLayout(tabs_frame)
        tabs_lay.setContentsMargins(4, 4, 4, 4)
        tabs_lay.setSpacing(4)

        self._btn_tab_gym = QPushButton("🏢  GYM")
        self._btn_tab_gym.setCheckable(True)
        self._btn_tab_gym.setChecked(True)
        self._btn_tab_gym.setCursor(Qt.PointingHandCursor)
        self._btn_tab_gym.setFixedHeight(38)
        self._btn_tab_gym.setObjectName("loginTabActive")
        self._btn_tab_gym.setToolTip("Acceso para socios comerciales gym")

        self._btn_tab_user = QPushButton("👤  Usuario")
        self._btn_tab_user.setCheckable(True)
        self._btn_tab_user.setCursor(Qt.PointingHandCursor)
        self._btn_tab_user.setFixedHeight(38)
        self._btn_tab_user.setObjectName("loginTabInactive")
        self._btn_tab_user.setToolTip("Acceso para usuarios regulares")

        tabs_lay.addWidget(self._btn_tab_gym)
        tabs_lay.addWidget(self._btn_tab_user)
        panel_lay.addWidget(tabs_frame)

        panel_lay.addSpacing(16)

        # ── Stack con formularios ─────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setObjectName("transparentWidget")
        panel_lay.addWidget(self._stack)

        self._panel_gym_form  = _PanelGymLogin()
        self._panel_user_form = _PanelUsuarioLogin()
        self._stack.addWidget(self._panel_gym_form)   # 0 → GYM
        self._stack.addWidget(self._panel_user_form)  # 1 → Usuario

        panel_lay.addStretch()

        # ── Señales ───────────────────────────────────────────────────────────
        self._btn_tab_gym.clicked.connect(self._cambiar_a_gym)
        self._btn_tab_user.clicked.connect(self._cambiar_a_usuario)
        self._panel_gym_form.autenticado.connect(self._on_gym_autenticado)
        self._panel_gym_form.solicitar_registro.connect(self._on_gym_registro_solicitado)
        self._panel_user_form.autenticado.connect(self._on_usuario_autenticado)

    # ── Carga de fondo ────────────────────────────────────────────────────────

    def _cargar_fondo(self) -> None:
        """Carga FONDO.PNG (o alternativa del branding) con overlay oscuro baked-in."""
        # Primero consultar branding para ruta dinámica; fallback a resource_path
        bg_path: str | None = None
        try:
            from core.branding import branding as _branding
            fondo = _branding.obtener_fondo_login_path()
            if fondo:
                bg_path = str(fondo)
        except Exception:
            pass

        if not bg_path:
            bg_path = resource_path("assets/FONDO.PNG")
        if not Path(bg_path).exists():
            # Fallback: fondo sólido con gradiente
            self._bg.setStyleSheet(
                f"background: qlineargradient("
                f"x1:0,y1:0,x2:1,y2:1,"
                f"stop:0 #0D0D0D,stop:1 #0A0A0A);"
            )
            return

        # Escalar imagen para llenar la ventana
        original = QPixmap(bg_path).scaled(
            self.WIN_W, self.WIN_H,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        ).copy(0, 0, self.WIN_W, self.WIN_H)  # crop al tamaño exacto

        # Aplicar overlay oscuro para mejorar legibilidad del texto
        with_overlay = QPixmap(self.WIN_W, self.WIN_H)
        with_overlay.fill(Qt.transparent)
        painter = QPainter(with_overlay)
        painter.drawPixmap(0, 0, original)
        painter.fillRect(
            0, 0, self.WIN_W, self.WIN_H,
            QColor(0, 0, 0, 140),   # negro semitransparente ~55%
        )
        painter.end()

        self._bg.setPixmap(with_overlay)

    # ── Cambios de tab ────────────────────────────────────────────────────────

    def _cambiar_a_gym(self) -> None:
        self._btn_tab_gym.setChecked(True)
        self._btn_tab_gym.setObjectName("loginTabActive")
        self._btn_tab_gym.style().unpolish(self._btn_tab_gym)
        self._btn_tab_gym.style().polish(self._btn_tab_gym)
        self._btn_tab_user.setChecked(False)
        self._btn_tab_user.setObjectName("loginTabInactive")
        self._btn_tab_user.style().unpolish(self._btn_tab_user)
        self._btn_tab_user.style().polish(self._btn_tab_user)
        self._panel_user_form.limpiar()
        self._stack.setCurrentIndex(0)

    def _cambiar_a_usuario(self) -> None:
        self._btn_tab_user.setChecked(True)
        self._btn_tab_user.setObjectName("loginTabActive")
        self._btn_tab_user.style().unpolish(self._btn_tab_user)
        self._btn_tab_user.style().polish(self._btn_tab_user)
        self._btn_tab_gym.setChecked(False)
        self._btn_tab_gym.setObjectName("loginTabInactive")
        self._btn_tab_gym.style().unpolish(self._btn_tab_gym)
        self._btn_tab_gym.style().polish(self._btn_tab_gym)
        self._panel_gym_form.limpiar()
        self._stack.setCurrentIndex(1)

    # ── Callbacks de autenticación ────────────────────────────────────────────

    def _on_gym_autenticado(self, sesion: SesionActiva) -> None:
        self._sesion_gym = sesion
        self.login_exitoso.emit({"tipo": "gym", "sesion": sesion})
        logger.info("[LOGIN_UNIF] Cerrando con resultado GYM")
        self.done(int(ResultadoLogin.GYM))

    def _on_gym_registro_solicitado(self) -> None:
        """Usuario pidió registrar un gym nuevo — delega a VentanaAccesoGym."""
        logger.info("[LOGIN_UNIF] Solicitado registro nuevo gym → delegando")
        # sesion_gym queda None; el llamador abrirá VentanaAccesoGym (registro)
        self.done(int(ResultadoLogin.GYM))

    def _on_usuario_autenticado(self, sesion: SesionActiva) -> None:
        self._sesion_usuario = sesion
        self.login_exitoso.emit({"tipo": "usuario", "sesion": sesion})
        logger.info("[LOGIN_UNIF] Cerrando con resultado USUARIO")
        self.done(int(ResultadoLogin.USUARIO))
