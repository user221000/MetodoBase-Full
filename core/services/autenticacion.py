# -*- coding: utf-8 -*-
"""
ServicioAuth — Capa de autenticación unificada (Agente 6).

Wrapper de alto nivel sobre AuthService que expone los métodos
requeridos por el spec de la ventana de login unificada:

    - login_gym(email, password)     → dict | None
    - login_usuario(email, password) → dict | None
    - validar_sesion(id_usuario)     → bool

La sesión activa se mantiene en memoria durante la ejecución.
No se persisten tokens en disco por defecto.

Diferencias con auth_service.AuthService:
  · Devuelve ``dict`` simple (serializable) en lugar de SesionActiva.
  · Añade discriminación de rol directamente en login_gym/login_usuario.
  · Expone ``validar_sesion`` para comprobar si una sesión sigue activa.

Seguridad:
  · password nunca se almacena en atributos; se pasa directo al hasher.
  · Los logs no incluyen email ni nombre.
  · Mensajes de error genéricos (no revelan si el email existe).
"""
from __future__ import annotations

from typing import Optional

from core.services.auth_service import AuthService, SesionActiva, crear_auth_service
from utils.logger import logger


# ---------------------------------------------------------------------------
# Servicio de autenticación unificado
# ---------------------------------------------------------------------------

class ServicioAuth:
    """
    Servicio de autenticación unificado para ambas plataformas.

    Crea su propio AuthService interno; puede recibir uno inyectado
    para facilitar el testing.

    Ejemplo de uso::

        svc = ServicioAuth()

        resultado = svc.login_gym("gym@ejemplo.com", "S3cur3P@ss")
        if resultado:
            print("GYM autenticado:", resultado["nombre_display"])

        resultado = svc.login_usuario("user@ejemplo.com", "P@ss1234")
        if resultado:
            print("Usuario autenticado:", resultado["id_usuario"])

        ok = svc.validar_sesion("abc123-uuid")
    """

    def __init__(self, auth_service: Optional[AuthService] = None) -> None:
        self._auth: AuthService = auth_service or crear_auth_service()
        self._sesiones: dict[str, SesionActiva] = {}   # id_usuario → SesionActiva

    # ------------------------------------------------------------------
    # Propiedades de conveniencia
    # ------------------------------------------------------------------

    @property
    def sesion_activa(self) -> Optional[SesionActiva]:
        """Última sesión abierta (internalAuthService)."""
        return self._auth.sesion_activa

    # ------------------------------------------------------------------
    # Login GYM
    # ------------------------------------------------------------------

    def login_gym(self, email: str, password: str) -> Optional[dict]:
        """
        Autentica una cuenta de tipo 'gym' / 'admin'.

        Args:
            email:    Correo registrado del gym (str).
            password: Contraseña en texto plano (se hashea internamente).

        Returns:
            dict con {id_usuario, nombre_display, rol} si el login fue
            exitoso Y el rol es 'gym' o 'admin'.  None en caso contrario.
        """
        if not email or not password:
            return None

        resultado = self._auth.login(email.strip().lower(), password)
        if not resultado.ok or resultado.sesion is None:
            logger.warning("[SERV_AUTH] login_gym fallido")
            return None

        sesion = resultado.sesion
        if sesion.rol not in ("gym", "admin"):
            logger.warning("[SERV_AUTH] login_gym: rol incorrecto (%s)", sesion.rol)
            self._auth.logout()
            return None

        self._sesiones[sesion.id_usuario] = sesion
        logger.info("[SERV_AUTH] login_gym OK rol=%s", sesion.rol)
        return self._sesion_a_dict(sesion)

    # ------------------------------------------------------------------
    # Login Usuario Regular
    # ------------------------------------------------------------------

    def login_usuario(self, email: str, password: str) -> Optional[dict]:
        """
        Autentica una cuenta de usuario regular.

        Args:
            email:    Correo registrado del usuario.
            password: Contraseña en texto plano.

        Returns:
            dict con {id_usuario, nombre_display, rol} si el login fue
            exitoso.  None en caso contrario.
        """
        if not email or not password:
            return None

        resultado = self._auth.login(email.strip().lower(), password)
        if not resultado.ok or resultado.sesion is None:
            logger.warning("[SERV_AUTH] login_usuario fallido")
            return None

        sesion = resultado.sesion
        self._sesiones[sesion.id_usuario] = sesion
        logger.info("[SERV_AUTH] login_usuario OK rol=%s", sesion.rol)
        return self._sesion_a_dict(sesion)

    # ------------------------------------------------------------------
    # Registro Usuario
    # ------------------------------------------------------------------

    def registrar_usuario(
        self,
        nombre: str,
        apellido: str,
        email: str,
        password: str,
    ) -> Optional[dict]:
        """
        Registra un nuevo usuario regular (sin rol especial).

        Returns:
            dict de sesión si el registro fue exitoso. None en caso contrario.
        """
        resultado = self._auth.registrar(
            nombre=nombre,
            apellido=apellido,
            email=email.strip().lower(),
            password=password,
            rol="usuario",
        )
        if not resultado.ok or resultado.sesion is None:
            logger.warning("[SERV_AUTH] registrar_usuario fallido: %s", resultado.errores)
            return None

        sesion = resultado.sesion
        self._sesiones[sesion.id_usuario] = sesion
        logger.info("[SERV_AUTH] registrar_usuario OK id=***")
        return self._sesion_a_dict(sesion)

    # ------------------------------------------------------------------
    # Validación de sesión
    # ------------------------------------------------------------------

    def validar_sesion(self, id_usuario: str) -> bool:
        """
        Comprueba si existe una sesión activa en memoria para el id dado.

        Args:
            id_usuario: UUID del usuario.

        Returns:
            True si la sesión existe en el registro de sesiones activas.
        """
        return id_usuario in self._sesiones

    # ------------------------------------------------------------------
    # Cierre de sesión
    # ------------------------------------------------------------------

    def cerrar_sesion(self, id_usuario: str | None = None) -> None:
        """
        Cierra la sesión del usuario indicado (o la sesión activa si None).
        """
        if id_usuario and id_usuario in self._sesiones:
            del self._sesiones[id_usuario]
        if self._auth.autenticado:
            sesion = self._auth.sesion_activa
            if sesion and (id_usuario is None or sesion.id_usuario == id_usuario):
                self._auth.logout()
        logger.info("[SERV_AUTH] Sesión cerrada id=***")

    # ------------------------------------------------------------------
    # Helper privado
    # ------------------------------------------------------------------

    @staticmethod
    def _sesion_a_dict(sesion: SesionActiva) -> dict:
        return {
            "id_usuario":     sesion.id_usuario,
            "nombre_display": sesion.nombre_display,
            "rol":            sesion.rol,
        }


# ---------------------------------------------------------------------------
# Función de fábrica conveniente
# ---------------------------------------------------------------------------

def crear_servicio_auth(auth_service: Optional[AuthService] = None) -> ServicioAuth:
    """Crea un ServicioAuth completamente configurado."""
    return ServicioAuth(auth_service=auth_service)
