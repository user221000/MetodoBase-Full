"""Endpoint de estadísticas /api/estadisticas."""
import logging

from fastapi import APIRouter, Depends

from api.dependencies import get_gestor
from src.gestor_bd import GestorBDClientes

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Estadísticas"])


@router.get("/estadisticas", summary="KPIs del dashboard")
def obtener_estadisticas(gestor: GestorBDClientes = Depends(get_gestor)):
    """
    Retorna métricas de los últimos 30 días:
    - Clientes activos totales
    - Clientes nuevos en el período
    - Planes generados en el período
    - Promedio de kcal objetivo
    - Tasa de retención
    """
    try:
        stats = gestor.obtener_estadisticas_gym()
        return stats
    except Exception as exc:
        logger.error("Error obteniendo estadísticas: %s", exc, exc_info=True)
        # Retorna estructura vacía válida para el dashboard
        return {
            "total_clientes": 0,
            "clientes_nuevos": 0,
            "planes_periodo": 0,
            "promedio_kcal": 0,
            "clientes_activos": 0,
            "renovaciones": 0,
            "tasa_retencion": 0.0,
            "top_clientes": [],
            "objetivos": {},
            "planes_por_tipo": {},
        }
