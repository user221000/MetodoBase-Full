"""Pydantic schemas para MetodoBase API v2."""
import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

_NIVELES = {"nula", "leve", "moderada", "intensa"}
_OBJETIVOS = {"deficit", "mantenimiento", "superavit"}


class ClienteCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo")
    telefono: Optional[str] = Field(None, description="Teléfono 10 dígitos")
    email: Optional[str] = Field(None, description="Correo electrónico")
    edad: int = Field(..., ge=15, le=80, description="Edad en años (15–80)")
    sexo: Optional[str] = Field(None, description="M / F / Otro")
    peso_kg: float = Field(..., ge=40.0, le=200.0, description="Peso en kg (40–200)")
    estatura_cm: float = Field(..., ge=140.0, le=220.0, description="Estatura en cm (140–220)")
    grasa_corporal_pct: Optional[float] = Field(None, ge=5.0, le=60.0, description="% grasa corporal (5–60)")
    nivel_actividad: str = Field(..., description="nula | leve | moderada | intensa")
    objetivo: str = Field(..., description="deficit | mantenimiento | superavit")
    notas: Optional[str] = Field(None, max_length=500)

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        return v.title()

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if not v or v.strip() == "":
            return None
        digits = re.sub(r"\D", "", v)
        if len(digits) not in (10, 12):
            raise ValueError("Teléfono debe tener 10 dígitos")
        return digits

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        if not v or v.strip() == "":
            return None
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v.strip()):
            raise ValueError("Email inválido")
        return v.strip().lower()

    @field_validator("sexo")
    @classmethod
    def validar_sexo(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        v = v.strip().upper()
        if v not in {"M", "F", "OTRO"}:
            raise ValueError("Sexo debe ser M, F, u Otro")
        return v

    @field_validator("nivel_actividad")
    @classmethod
    def validar_nivel(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in _NIVELES:
            raise ValueError(f"nivel_actividad debe ser uno de: {sorted(_NIVELES)}")
        return v

    @field_validator("objetivo")
    @classmethod
    def validar_objetivo(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in _OBJETIVOS:
            raise ValueError(f"objetivo debe ser uno de: {sorted(_OBJETIVOS)}")
        return v


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = None
    email: Optional[str] = None
    edad: Optional[int] = Field(None, ge=15, le=80)
    peso_kg: Optional[float] = Field(None, ge=40.0, le=200.0)
    estatura_cm: Optional[float] = Field(None, ge=140.0, le=220.0)
    grasa_corporal_pct: Optional[float] = Field(None, ge=5.0, le=60.0)
    nivel_actividad: Optional[str] = None
    objetivo: Optional[str] = None
    notas: Optional[str] = Field(None, max_length=500)

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return v.strip().title()

    @field_validator("nivel_actividad")
    @classmethod
    def validar_nivel(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower()
        if v not in _NIVELES:
            raise ValueError(f"nivel_actividad debe ser uno de: {sorted(_NIVELES)}")
        return v

    @field_validator("objetivo")
    @classmethod
    def validar_objetivo(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower()
        if v not in _OBJETIVOS:
            raise ValueError(f"objetivo debe ser uno de: {sorted(_OBJETIVOS)}")
        return v


class PlanRequest(BaseModel):
    id_cliente: str = Field(..., min_length=1, description="ID del cliente")
    plan_numero: int = Field(1, ge=1, le=9999, description="Número de plan para rotación")
