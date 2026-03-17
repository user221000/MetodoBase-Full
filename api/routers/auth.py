"""
Router: autenticación de usuarios.

POST /api/v1/auth/register  — Registrar nuevo usuario
POST /api/v1/auth/login     — Obtener JWT de acceso
GET  /api/v1/auth/me        — Datos de la sesión activa
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.auth import LoginRequest, RegistroRequest, TokenResponse
from api.dependencies import crear_access_token, require_token, SesionToken, get_gestor_bd
from src.gestor_bd import GestorBDClientes
from utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
)
def registrar_usuario(body: RegistroRequest) -> dict:
    """
    Registra un nuevo usuario con email y contraseña.

    - La contraseña se almacena como hash bcrypt (nunca en texto plano).
    - Los campos nombre y email se cifran con AES-128.
    - Retorna `{"ok": true, "id_usuario": "..."}` si fue exitoso.
    """
    try:
        from core.services.auth_service import AuthService
        from core.services.crypto_service import CryptoService
        from core.services.key_manager import KeyManager
        from core.services.password_hasher import PasswordHasher
        from src.gestor_usuarios import GestorUsuarios

        key_manager = KeyManager()
        crypto = CryptoService(key_manager)
        gestor_usr = GestorUsuarios(crypto_service=crypto)
        hasher = PasswordHasher()
        auth = AuthService(gestor_usuarios=gestor_usr, password_hasher=hasher)

        resultado = auth.registrar(
            nombre=body.nombre,
            apellido=body.apellido,
            email=body.email,
            password=body.password,
            rol=body.rol,
        )
        if not resultado.ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=resultado.errores,
            )
        return {"ok": True, "id_usuario": resultado.sesion.id_usuario}
    except ImportError as exc:
        logger.error("[API][auth] Dependencia faltante: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Dependencia no instalada: {exc}",
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
)
def login(body: LoginRequest) -> TokenResponse:
    """
    Valida credenciales y retorna un JWT de acceso (15 min) con los datos de sesión.

    El token debe enviarse en el header `Authorization: Bearer <token>`.
    """
    try:
        from core.services.auth_service import AuthService
        from core.services.crypto_service import CryptoService
        from core.services.key_manager import KeyManager
        from core.services.password_hasher import PasswordHasher
        from src.gestor_usuarios import GestorUsuarios

        key_manager = KeyManager()
        crypto = CryptoService(key_manager)
        gestor_usr = GestorUsuarios(crypto_service=crypto)
        hasher = PasswordHasher()
        auth = AuthService(gestor_usuarios=gestor_usr, password_hasher=hasher)

        resultado = auth.login(email=body.email, password=body.password)
        if not resultado.ok or resultado.sesion is None:
            # Siempre el mismo mensaje para no revelar si el email existe
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        sesion = resultado.sesion
        token = crear_access_token({
            "sub": sesion.id_usuario,
            "rol": sesion.rol,
            "nombre": sesion.nombre_display,
        })
        return TokenResponse(
            access_token=token,
            rol=sesion.rol,
            nombre_display=sesion.nombre_display,
        )
    except ImportError as exc:
        logger.error("[API][auth] Dependencia faltante: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Dependencia no instalada: {exc}",
        ) from exc


@router.get(
    "/me",
    summary="Datos de la sesión activa",
)
def me(sesion: SesionToken = Depends(require_token)) -> dict:
    """Devuelve los datos no sensibles de la sesión activa."""
    return {
        "id_usuario": sesion.id_usuario,
        "rol": sesion.rol,
        "nombre_display": sesion.nombre_display,
    }
