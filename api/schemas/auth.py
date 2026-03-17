"""
Schemas Pydantic para autenticación.
"""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator


class RegistroRequest(BaseModel):
    """Datos para registrar un nuevo usuario."""
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    rol: str = "usuario"

    @field_validator("password")
    @classmethod
    def password_minimo(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return v

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        validos = {"admin", "usuario", "gym"}
        if v not in validos:
            raise ValueError(f"Rol inválido. Válidos: {sorted(validos)}")
        return v


class LoginRequest(BaseModel):
    """Credenciales de inicio de sesión."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Tokens de acceso retornados tras un login exitoso."""
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre_display: str
