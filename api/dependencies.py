"""
Dependencias de FastAPI — inyección de servicios comunes.

Uso:
    from api.dependencies import get_gestor_bd, get_auth_service, require_token

    @router.get("/clientes")
    def listar(bd=Depends(get_gestor_bd), sesion=Depends(require_token)):
        ...
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from jose import JWTError, jwt
    _JWT_OK = True
except ImportError:
    _JWT_OK = False

from src.gestor_bd import GestorBDClientes

# ── Configuración JWT ────────────────────────────────────────────────────────

_SECRET_KEY: str = os.environ.get("MB_JWT_SECRET", "")
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 15
_REFRESH_TOKEN_EXPIRE_DAYS = 7

_bearer = HTTPBearer(auto_error=False)

# En producción, MB_JWT_SECRET debe ser una cadena aleatoria de al menos 32 chars.
# Si no está configurada, la API lanza un error claro en el primer request.
_SECRET_KEY_FALLBACK = "METODO_BASE_DEV_INSECURE_KEY_CAMBIAR_EN_PROD"
_IS_DEV = os.environ.get("MB_ENV", "development") == "development"


# ── Gestor de BD ─────────────────────────────────────────────────────────────

def get_gestor_bd() -> GestorBDClientes:
    """Devuelve una instancia del gestor de base de datos."""
    return GestorBDClientes()


# ── JWT helpers ───────────────────────────────────────────────────────────────

def _get_secret_key() -> str:
    """Retorna la clave JWT. En producción falla si no está configurada."""
    key = os.environ.get("MB_JWT_SECRET", "")
    if key:
        return key
    if not _IS_DEV:
        raise RuntimeError(
            "MB_JWT_SECRET no está configurado. "
            "Define esta variable de entorno en producción con una clave segura de 32+ caracteres."
        )
    # Solo en desarrollo se usa una clave insegura con advertencia visible
    import warnings
    warnings.warn(
        "MB_JWT_SECRET no configurado — usando clave insegura de desarrollo. "
        "NUNCA deploys en producción sin esta variable.",
        stacklevel=2,
    )
    return _SECRET_KEY_FALLBACK


def crear_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un JWT de acceso con expiración corta."""
    if not _JWT_OK:
        raise RuntimeError("Instala python-jose: pip install python-jose[cryptography]")
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, _get_secret_key(), algorithm=_ALGORITHM)


def _decodificar_token(token: str) -> dict:
    """Decodifica y valida un JWT. Lanza HTTPException si es inválido."""
    if not _JWT_OK:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="JWT no disponible — instala python-jose[cryptography]",
        )
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[_ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── Dependencia de autenticación ─────────────────────────────────────────────

class SesionToken:
    """Datos de sesión extraídos del JWT."""
    def __init__(self, id_usuario: str, rol: str, nombre_display: str) -> None:
        self.id_usuario = id_usuario
        self.rol = rol
        self.nombre_display = nombre_display


def require_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> SesionToken:
    """Valida el Bearer token y devuelve la sesión."""
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decodificar_token(creds.credentials)
    id_usuario = payload.get("sub")
    rol = payload.get("rol", "usuario")
    nombre_display = payload.get("nombre", "")
    if not id_usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")
    return SesionToken(id_usuario=id_usuario, rol=rol, nombre_display=nombre_display)


def require_rol_gym(sesion: SesionToken = Depends(require_token)) -> SesionToken:
    """Exige que la sesión tenga rol 'gym' o 'admin'."""
    if sesion.rol not in {"gym", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol 'gym' o 'admin'.",
        )
    return sesion


def require_admin(sesion: SesionToken = Depends(require_token)) -> SesionToken:
    """Exige que la sesión tenga rol 'admin'."""
    if sesion.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol 'admin'.",
        )
    return sesion
