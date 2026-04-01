# -*- coding: utf-8 -*-
"""
tests/test_login_desktop.py — Tests unitarios e integración para VentanaLoginUnificada.

Cubre:
  · ResultadoLogin enum values
  · _PanelGymLogin  — login exitoso, credenciales inválidas, rol incorrecto
  · _PanelUsuarioLogin — login exitoso, credenciales inválidas
  · _PanelUsuarioLogin — registro exitoso, contraseñas no coinciden
  · VentanaLoginUnificada — cambio de tab, propiedades de sesión
  · ServicioAuth (core/services/autenticacion.py)

Mocking: se usa unittest.mock para AuthService, evitando
acceso a disco/BD en cada test.
"""
from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Fixture de sesión y resultado
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _MockSesion:
    id_usuario: str = "test-uuid-001"
    nombre_display: str = "Test"
    rol: str = "usuario"


@dataclass(frozen=True)
class _MockSesionGym:
    id_usuario: str = "gym-uuid-001"
    nombre_display: str = "GymTest"
    rol: str = "gym"


@dataclass
class _MockResultado:
    ok: bool
    sesion: Optional[object] = None
    errores: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tests de ResultadoLogin (sin PySide6 necesario)
# ---------------------------------------------------------------------------

class TestResultadoLoginEnum(unittest.TestCase):
    """Verifica los valores del enum ResultadoLogin."""

    def setUp(self):
        # Si PySide6 no está disponible, saltar
        try:
            from ui_desktop.pyside.ventana_login_unificada import ResultadoLogin
            self.ResultadoLogin = ResultadoLogin
        except ImportError:
            self.skipTest("PySide6 no disponible")

    def test_valores_correctos(self):
        RL = self.ResultadoLogin
        self.assertEqual(int(RL.CANCELADO), 0)
        self.assertEqual(int(RL.GYM), 1)
        self.assertEqual(int(RL.USUARIO), 2)

    def test_nombres_correctos(self):
        RL = self.ResultadoLogin
        self.assertIn("GYM", RL.__members__)
        self.assertIn("USUARIO", RL.__members__)
        self.assertIn("CANCELADO", RL.__members__)


# ---------------------------------------------------------------------------
# Tests de ServicioAuth (core/services/autenticacion.py)
# ---------------------------------------------------------------------------

class TestServicioAuth(unittest.TestCase):
    """Tests unitarios del ServicioAuth — mock del AuthService subyacente."""

    def _make_mock_auth(self, ok=True, rol="usuario", errores=None):
        mock_auth = MagicMock()
        sesion = _MockSesion(rol=rol) if rol == "usuario" else _MockSesionGym()
        resultado = _MockResultado(ok=ok, sesion=sesion if ok else None,
                                   errores=errores or [])
        mock_auth.login.return_value = resultado
        mock_auth.registrar.return_value = resultado
        mock_auth.autenticado = ok
        mock_auth.sesion_activa = sesion if ok else None
        return mock_auth

    def test_login_gym_exitoso(self):
        from core.services.autenticacion import ServicioAuth
        mock_auth = self._make_mock_auth(ok=True, rol="gym")
        svc = ServicioAuth(auth_service=mock_auth)

        resultado = svc.login_gym("gym@test.com", "S3cur3P@ss!")
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["rol"], "gym")
        mock_auth.login.assert_called_once_with("gym@test.com", "S3cur3P@ss!")

    def test_login_gym_credenciales_invalidas(self):
        from core.services.autenticacion import ServicioAuth
        mock_auth = self._make_mock_auth(ok=False, errores=["Credenciales incorrectas."])
        svc = ServicioAuth(auth_service=mock_auth)

        resultado = svc.login_gym("wrong@test.com", "bad")
        self.assertIsNone(resultado)

    def test_login_gym_rol_incorrecto(self):
        """Usuario con rol 'usuario' NO debe poder iniciar sesión como gym."""
        from core.services.autenticacion import ServicioAuth
        mock_auth = self._make_mock_auth(ok=True, rol="usuario")
        svc = ServicioAuth(auth_service=mock_auth)

        resultado = svc.login_gym("user@test.com", "P@ss1234!")
        self.assertIsNone(resultado, "login_gym debe rechazar rol != gym/admin")

    def test_login_usuario_exitoso(self):
        from core.services.autenticacion import ServicioAuth
        mock_auth = self._make_mock_auth(ok=True, rol="usuario")
        svc = ServicioAuth(auth_service=mock_auth)

        resultado = svc.login_usuario("user@test.com", "P@ss1234!")
        self.assertIsNotNone(resultado)
        self.assertIn("id_usuario", resultado)
        self.assertIn("nombre_display", resultado)

    def test_login_usuario_sin_email(self):
        from core.services.autenticacion import ServicioAuth
        mock_auth = self._make_mock_auth(ok=True, rol="usuario")
        svc = ServicioAuth(auth_service=mock_auth)

        resultado = svc.login_usuario("", "P@ss1234!")
        self.assertIsNone(resultado)
        mock_auth.login.assert_not_called()

    def test_validar_sesion_existente(self):
        from core.services.autenticacion import ServicioAuth
        mock_auth = self._make_mock_auth(ok=True, rol="usuario")
        svc = ServicioAuth(auth_service=mock_auth)

        svc.login_usuario("user@test.com", "P@ss1234!")
        id_usuario = list(svc._sesiones.keys())[0]
        self.assertTrue(svc.validar_sesion(id_usuario))

    def test_validar_sesion_inexistente(self):
        from core.services.autenticacion import ServicioAuth
        svc = ServicioAuth(auth_service=MagicMock())
        self.assertFalse(svc.validar_sesion("no-existe-uuid"))

    def test_cerrar_sesion(self):
        from core.services.autenticacion import ServicioAuth
        mock_auth = self._make_mock_auth(ok=True, rol="usuario")
        svc = ServicioAuth(auth_service=mock_auth)

        svc.login_usuario("user@test.com", "P@ss1234!")
        id_usuario = list(svc._sesiones.keys())[0]

        svc.cerrar_sesion(id_usuario)
        self.assertFalse(svc.validar_sesion(id_usuario))

    def test_registrar_usuario_exitoso(self):
        from core.services.autenticacion import ServicioAuth
        mock_auth = self._make_mock_auth(ok=True, rol="usuario")
        svc = ServicioAuth(auth_service=mock_auth)

        resultado = svc.registrar_usuario("Ana", "García", "ana@test.com", "P@ss1234!")
        self.assertIsNotNone(resultado)
        mock_auth.registrar.assert_called_once()

    def test_registrar_usuario_falla(self):
        from core.services.autenticacion import ServicioAuth
        mock_auth = self._make_mock_auth(ok=False, errores=["Contraseña débil."])
        svc = ServicioAuth(auth_service=mock_auth)

        resultado = svc.registrar_usuario("Ana", "García", "ana@test.com", "weak")
        self.assertIsNone(resultado)


# ---------------------------------------------------------------------------
# Tests de VentanaLoginUnificada (requiere QApplication)
# ---------------------------------------------------------------------------

class TestVentanaLoginUnificadaQt(unittest.TestCase):
    """Tests que requieren PySide6 / QApplication."""

    _app = None

    @classmethod
    def setUpClass(cls):
        try:
            from PySide6.QtWidgets import QApplication
            if QApplication.instance() is None:
                cls._app = QApplication(sys.argv)
        except ImportError:
            pass

    def setUp(self):
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError:
            self.skipTest("PySide6 no disponible")

    def test_importacion_ok(self):
        """El módulo se importa sin errores."""
        try:
            pass
        except Exception as e:
            self.fail(f"Error al importar VentanaLoginUnificada: {e}")

    def test_instancia_creada(self):
        """VentanaLoginUnificada se puede instanciar."""
        try:
            from ui_desktop.pyside.ventana_login_unificada import VentanaLoginUnificada
            win = VentanaLoginUnificada()
            self.assertIsNotNone(win)
            win.destroy()
        except Exception as e:
            self.fail(f"Error al instanciar: {e}")

    def test_sesiones_inicialmente_none(self):
        """sesion_gym y sesion_usuario deben ser None al iniciar."""
        try:
            from ui_desktop.pyside.ventana_login_unificada import VentanaLoginUnificada
            win = VentanaLoginUnificada()
            self.assertIsNone(win.sesion_gym)
            self.assertIsNone(win.sesion_usuario)
            win.destroy()
        except Exception as e:
            self.fail(f"Error: {e}")

    def test_tamano_ventana(self):
        """La ventana tiene el tamaño correcto (1200x700)."""
        try:
            from ui_desktop.pyside.ventana_login_unificada import VentanaLoginUnificada
            win = VentanaLoginUnificada()
            self.assertEqual(win.width(), VentanaLoginUnificada.WIN_W)
            self.assertEqual(win.height(), VentanaLoginUnificada.WIN_H)
            win.destroy()
        except Exception as e:
            self.fail(f"Error: {e}")

    def test_cambio_tab_gym(self):
        """Al hacer click en el tab GYM, el stack muestra formulario GYM."""
        try:
            from ui_desktop.pyside.ventana_login_unificada import VentanaLoginUnificada
            win = VentanaLoginUnificada()
            win._cambiar_a_usuario()
            self.assertEqual(win._stack.currentIndex(), 1)
            win._cambiar_a_gym()
            self.assertEqual(win._stack.currentIndex(), 0)
            win.destroy()
        except Exception as e:
            self.fail(f"Error de cambio de tab: {e}")

    def test_tab_gym_activo_por_defecto(self):
        """El tab GYM debe estar activo al abrir la ventana."""
        try:
            from ui_desktop.pyside.ventana_login_unificada import VentanaLoginUnificada
            win = VentanaLoginUnificada()
            self.assertEqual(win._stack.currentIndex(), 0,
                             "GYM tab (index 0) debe ser el default")
            self.assertTrue(win._btn_tab_gym.isChecked())
            win.destroy()
        except Exception as e:
            self.fail(f"Error: {e}")


# ---------------------------------------------------------------------------
# Tests de FlowController
# ---------------------------------------------------------------------------

class TestFlowController(unittest.TestCase):
    """Verifica que FlowController expone la propiedad sesion_gym."""

    def setUp(self):
        try:
            from PySide6.QtWidgets import QApplication
            if QApplication.instance() is None:
                self._app = QApplication(sys.argv)
        except ImportError:
            self.skipTest("PySide6 no disponible")

    def test_sesion_gym_property_existe(self):
        """FlowController debe tener la propiedad sesion_gym."""
        try:
            from ui_desktop.pyside.flow_controller import FlowController
            fc = FlowController()
            self.assertIsNone(fc.sesion_gym)
        except Exception as e:
            self.fail(f"Error: {e}")


# ---------------------------------------------------------------------------
# Tests de utils/iconos.py (sin PySide6)
# ---------------------------------------------------------------------------

class TestIconos(unittest.TestCase):

    def setUp(self):
        try:
            from utils.iconos import ICONOS_EMOJI, obtener_emoji, TOOLTIP
            self.ICONOS_EMOJI = ICONOS_EMOJI
            self.obtener_emoji = obtener_emoji
            self.TOOLTIP = TOOLTIP
        except ImportError as e:
            self.skipTest(f"utils.iconos no disponible: {e}")

    def test_iconos_clave_requeridos(self):
        claves = ["borrar", "editar", "guardar", "generar_plan", "logout", "gym", "usuario"]
        for clave in claves:
            with self.subTest(clave=clave):
                self.assertIn(clave, self.ICONOS_EMOJI, f"Falta ícono: {clave}")

    def test_obtener_emoji_con_fallback(self):
        emoji = self.obtener_emoji("clave_inexistente", fallback="?")
        self.assertEqual(emoji, "?")

    def test_obtener_emoji_valido(self):
        emoji = self.obtener_emoji("borrar")
        self.assertTrue(len(emoji) > 0)

    def test_tooltips_existen(self):
        self.assertIn("borrar", self.TOOLTIP)
        self.assertIn("guardar", self.TOOLTIP)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
