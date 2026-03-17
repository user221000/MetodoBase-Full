"""
Schemas Pydantic — re-exportaciones para facilitar imports.
"""
from api.schemas.auth import RegistroRequest, LoginRequest, TokenResponse
from api.schemas.planes import (
    PlanRequest, PlanResponse, ResultadoNutricionalResponse,
    MacrosResponse, AlertaSaludResponse, ComidaResponse,
)
from api.schemas.reportes import (
    ClienteResumen, ListaClientesResponse,
    KPIsGym, DistribucionObjetivos, EstadisticasGymResponse,
)

__all__ = [
    "RegistroRequest", "LoginRequest", "TokenResponse",
    "PlanRequest", "PlanResponse", "ResultadoNutricionalResponse",
    "MacrosResponse", "AlertaSaludResponse", "ComidaResponse",
    "ClienteResumen", "ListaClientesResponse",
    "KPIsGym", "DistribucionObjetivos", "EstadisticasGymResponse",
]
