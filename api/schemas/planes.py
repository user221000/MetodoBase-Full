"""
Schemas Pydantic para generación de planes nutricionales.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator


_NIVELES_ACTIVIDAD = {"nula", "leve", "moderada", "intensa"}
_OBJETIVOS = {"deficit", "mantenimiento", "superavit"}


class PlanRequest(BaseModel):
    """Datos del cliente para generar un plan nutricional."""
    nombre: str = Field(..., min_length=2, max_length=100)
    telefono: Optional[str] = None
    edad: int = Field(..., ge=14, le=80)
    peso_kg: float = Field(..., ge=30, le=250)
    estatura_cm: float = Field(..., ge=100, le=250)
    grasa_corporal_pct: float = Field(..., ge=3, le=60)
    nivel_actividad: str
    objetivo: str
    plantilla_tipo: str = "general"
    alimentos_excluidos: list[str] = Field(default_factory=list)

    @field_validator("nivel_actividad")
    @classmethod
    def nivel_valido(cls, v: str) -> str:
        if v not in _NIVELES_ACTIVIDAD:
            raise ValueError(f"nivel_actividad inválido. Válidos: {sorted(_NIVELES_ACTIVIDAD)}")
        return v

    @field_validator("objetivo")
    @classmethod
    def objetivo_valido(cls, v: str) -> str:
        if v.lower() not in _OBJETIVOS:
            raise ValueError(f"objetivo inválido. Válidos: {sorted(_OBJETIVOS)}")
        return v.lower()


class MacrosResponse(BaseModel):
    """Distribución de macronutrientes calculada."""
    proteina_g: float
    grasa_g: float
    carbs_g: float
    kcal_proteina: float
    kcal_grasa: float
    kcal_carbs: float


class AlertaSaludResponse(BaseModel):
    """Alerta de salud generada por el motor nutricional."""
    nivel: str   # 'warning' | 'error'
    codigo: str
    mensaje: str
    detalle: str = ""


class ResultadoNutricionalResponse(BaseModel):
    """Resultado del cálculo nutricional (no incluye detalle de alimentos)."""
    masa_magra: float
    tmb: float
    get_total: float
    kcal_objetivo: float
    macros: MacrosResponse
    alertas: list[AlertaSaludResponse] = Field(default_factory=list)


class ComidaResponse(BaseModel):
    """Una comida dentro del plan diario."""
    nombre: str
    kcal_real: float
    desviacion_pct: float
    alimentos: list[dict]


class PlanResponse(BaseModel):
    """Respuesta completa de un plan nutricional generado."""
    id_cliente: str
    nombre_cliente: str
    resultado_nutricional: ResultadoNutricionalResponse
    comidas: dict[str, ComidaResponse]
    alertas: list[AlertaSaludResponse] = Field(default_factory=list)
