"""
Schemas Pydantic para clientes y reportes.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Clientes ─────────────────────────────────────────────────────────────────

class ClienteResumen(BaseModel):
    """Datos públicos de un cliente (sin PII sensible)."""
    id_cliente: str
    nombre: str
    telefono: Optional[str] = None
    edad: Optional[int] = None
    peso_kg: Optional[float] = None
    estatura_cm: Optional[float] = None
    objetivo: Optional[str] = None
    nivel_actividad: Optional[str] = None
    activo: bool = True
    fecha_registro: Optional[str] = None
    total_planes: int = 0


class ListaClientesResponse(BaseModel):
    """Lista paginada de clientes."""
    total: int
    pagina: int
    por_pagina: int
    clientes: list[ClienteResumen]


# ── Reportes ──────────────────────────────────────────────────────────────────

class KPIsGym(BaseModel):
    """KPIs principales del gimnasio para el dashboard."""
    total_clientes: int = 0
    clientes_activos: int = 0
    clientes_nuevos_periodo: int = 0
    planes_generados_periodo: int = 0
    promedio_kcal: float = 0.0
    objetivo_mas_comun: str = "—"
    tasa_retencion_pct: float = 0.0
    planes_por_cliente_promedio: float = 0.0


class DistribucionObjetivos(BaseModel):
    """Distribución de objetivos en la base de clientes."""
    deficit: int = 0
    mantenimiento: int = 0
    superavit: int = 0


class EstadisticasGymResponse(BaseModel):
    """Respuesta completa de estadísticas del gym."""
    periodo_dias: int
    kpis: KPIsGym
    distribucion_objetivos: DistribucionObjetivos
    clientes_nuevos_semana: list[int] = Field(default_factory=lambda: [0] * 7)
