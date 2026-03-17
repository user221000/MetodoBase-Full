# -*- coding: utf-8 -*-
"""
FlowController — Orquestador del flujo de usuarios regulares.

Gestiona la secuencia de paneles para el flujo "Usuario Regular":

  VentanaLoginUnificada ──login──▶ PanelPerfilDetalle ──▶ PanelMetodoBase
                                                              │
                                              ┌───────────────▼───────────────┐
                                              │ PanelPreferenciasAlimentos     │
                                              └───────────────────────────────┘

Para el flujo GYM devuelve RESULTADO_MODO_GYM; si la autenticación GYM ya
se completó en VentanaLoginUnificada, expone ``sesion_gym`` para que main.py
pueda omitir VentanaAccesoGym.

Uso mínimo:
    ctrl = FlowController()
    resultado = ctrl.exec()
    if resultado == FlowController.RESULTADO_SESION_OK:
        # sesion disponible en ctrl.sesion_activa
        ...
    elif resultado == FlowController.RESULTADO_MODO_GYM:
        # gym session en ctrl.sesion_gym (puede ser None si es registro nuevo)
        ...
"""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QWidget

from core.services.auth_service import AuthService, SesionActiva, crear_auth_service
from ui_desktop.pyside.ventana_login_unificada import (
    VentanaLoginUnificada,
    ResultadoLogin,
)
from utils.logger import logger

if TYPE_CHECKING:
    from ui_desktop.pyside.panel_metodo_base import PanelMetodoBase


class FlowController(QDialog):
    """Orquestador modal del flujo completo de la aplicación."""

    # Códigos de retorno de exec()
    RESULTADO_CANCELADO   = 0
    RESULTADO_SESION_OK   = 1   # usuario regular autenticado y con perfil
    RESULTADO_MODO_GYM    = 2   # el usuario eligió "GYM"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._auth_service: AuthService | None = None
        self._sesion: SesionActiva | None = None
        self._sesion_gym: SesionActiva | None = None   # autenticación GYM ya hecha
        self._perfil: dict = {}
        self._excluidos: list[str] = []
        self._resultado_final = self.RESULTADO_CANCELADO

        self.setWindowTitle("Método Base")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        # El diálogo es "invisible" — sólo orquesta modales hijos
        self.setVisible(False)

    # ── API pública ───────────────────────────────────────────────────────

    @property
    def sesion_activa(self) -> SesionActiva | None:
        return self._sesion

    @property
    def sesion_gym(self) -> SesionActiva | None:
        """Sesión GYM autenticada en VentanaLoginUnificada (o None si es primer registro)."""
        return self._sesion_gym

    @property
    def perfil(self) -> dict:
        return self._perfil

    @property
    def excluidos(self) -> list[str]:
        return self._excluidos

    # ── Punto de entrada ──────────────────────────────────────────────────

    def exec(self) -> int:  # type: ignore[override]
        """Lanza el flujo completo; devuelve el código de resultado."""
        resultado = self._ejecutar_flujo()
        self._resultado_final = resultado
        return resultado

    # ── Flujo principal ───────────────────────────────────────────────────

    def _ejecutar_flujo(self) -> int:
        # 1) Ventana de login unificada (modo selector + formulario integrado)
        login = VentanaLoginUnificada(self.parent())
        code = login.exec()

        if code == ResultadoLogin.GYM:
            # Puede traer sesion (login exitoso) o None (registro nuevo solicitado)
            self._sesion_gym = login.sesion_gym
            logger.info("[FLOW] Flujo GYM — sesion_previa=%s", self._sesion_gym is not None)
            return self.RESULTADO_MODO_GYM

        if code != ResultadoLogin.USUARIO:
            logger.info("[FLOW] Login unificado cancelado.")
            return self.RESULTADO_CANCELADO

        # 2) Sesión de usuario regular ya obtenida en VentanaLoginUnificada
        self._sesion = login.sesion_usuario
        if not self._sesion:
            logger.error("[FLOW] USUARIO code pero sesion_usuario es None.")
            return self.RESULTADO_CANCELADO

        logger.info("[FLOW] Autenticado id=%s rol=%s",
                    self._sesion.id_usuario, self._sesion.rol)

        # 3) Cargar preferencias guardadas
        self._cargar_prefs()

        # 4) Perfil detalle (usuario nuevo sin perfil → forzado; con prefs → omitible)
        has_perfil = bool(self._perfil.get("peso_kg"))
        if not has_perfil:
            if not self._mostrar_perfil_detalle():
                return self.RESULTADO_CANCELADO

        # 5) Dashboard MetodoBase (permanece abierto mientras el usuario trabaje)
        self._mostrar_metodo_base()

        return self.RESULTADO_SESION_OK

    # ── Pasos individuales ────────────────────────────────────────────────

    def _cargar_prefs(self) -> None:
        if not self._sesion:
            return
        try:
            from src.gestor_preferencias import GestorPreferencias
            gp = GestorPreferencias(self._sesion.id_usuario)
            datos = gp.cargar()
            # Separar perfil corporal de exclusiones
            self._excluidos = datos.get("alimentos_excluidos", [])
            self._perfil = {k: v for k, v in datos.items() if k != "alimentos_excluidos"}
        except Exception as exc:
            logger.warning("[FLOW] No se pudo cargar prefs: %s", exc)

    def _guardar_perfil(self, perfil: dict) -> None:
        """Persiste el perfil en GestorPreferencias."""
        self._perfil = perfil
        if not self._sesion:
            return
        try:
            from src.gestor_preferencias import GestorPreferencias
            gp = GestorPreferencias(self._sesion.id_usuario)
            datos_actuales = gp.cargar()
            datos_actuales.update(perfil)
            gp.guardar(datos_actuales)
        except Exception as exc:
            logger.warning("[FLOW] No se pudo guardar perfil: %s", exc)

    def _mostrar_perfil_detalle(self) -> bool:
        """Muestra el diálogo de perfil. Retorna False si el usuario cancela."""
        from ui_desktop.pyside.panel_perfil_detalle import PanelPerfilDetalle
        dlg = PanelPerfilDetalle(
            sesion=self._sesion,
            prefs_actuales=self._perfil,
            parent=self.parent(),
        )
        dlg.perfil_guardado.connect(self._guardar_perfil)
        resultado = dlg.exec()
        return resultado != QDialog.Rejected or self._perfil  # omitir es válido si hay datos

    def _mostrar_metodo_base(self) -> None:
        """Muestra el dashboard MetodoBase y gestiona sus señales."""
        from ui_desktop.pyside.panel_metodo_base import PanelMetodoBase
        dashboard = PanelMetodoBase(
            sesion=self._sesion,
            perfil=self._perfil,
            alimentos_excluidos=self._excluidos,
            parent=self.parent(),
        )
        dashboard.abrir_preferencias.connect(
            lambda: self._mostrar_preferencias(dashboard)
        )
        dashboard.editar_perfil.connect(
            lambda: self._editar_perfil(dashboard)
        )
        dashboard.generar_plan.connect(
            lambda: self._generar_plan(dashboard)
        )
        dashboard.cerrar_sesion.connect(dashboard.reject)
        dashboard.exec()

    def _mostrar_preferencias(self, dashboard: "PanelMetodoBase") -> None:
        from ui_desktop.pyside.panel_preferencias_alimentos import PanelPreferenciasAlimentos
        dlg = PanelPreferenciasAlimentos(
            id_usuario=self._sesion.id_usuario,
            excluidos_actuales=self._excluidos,
            parent=dashboard,
        )
        dlg.excluidos_actualizados.connect(self._on_excluidos_actualizados)
        dlg.exec()
        # Refrescar badge en dashboard
        dashboard.actualizar_excluidos(self._excluidos)

    def _on_excluidos_actualizados(self, excluidos: list[str]) -> None:
        self._excluidos = excluidos

    def _editar_perfil(self, dashboard: "PanelMetodoBase") -> None:
        from ui_desktop.pyside.panel_perfil_detalle import PanelPerfilDetalle
        dlg = PanelPerfilDetalle(
            sesion=self._sesion,
            prefs_actuales=self._perfil,
            parent=dashboard,
        )
        dlg.perfil_guardado.connect(self._guardar_perfil)
        dlg.exec()

    def _generar_plan(self, dashboard: "PanelMetodoBase") -> None:
        """Abre el dialogo de generación de plan nutricional para el usuario."""
        from ui_desktop.pyside.dialogo_generar_plan import DialogoGenerarPlan
        dlg = DialogoGenerarPlan(
            sesion=self._sesion,
            perfil=self._perfil,
            excluidos=self._excluidos,
            parent=dashboard,
        )
        dlg.exec()
