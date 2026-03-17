"""
Router: reportes y estadísticas del gym.

GET /api/v1/reportes/estadisticas — KPIs y métricas del gym
"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException, status

from api.schemas.reportes import EstadisticasGymResponse, KPIsGym, DistribucionObjetivos
from api.dependencies import require_rol_gym, SesionToken, get_gestor_bd
from src.gestor_bd import GestorBDClientes
from utils.logger import logger

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get(
    "/estadisticas",
    response_model=EstadisticasGymResponse,
    summary="Estadísticas y KPIs del gym",
)
def estadisticas_gym(
    dias: int = Query(30, ge=1, le=365, description="Período de análisis en días"),
    gestor_bd: GestorBDClientes = Depends(get_gestor_bd),
    _sesion: SesionToken = Depends(require_rol_gym),
) -> EstadisticasGymResponse:
    """
    Devuelve los KPIs principales del gym para el dashboard:

    - Total de clientes activos
    - Clientes nuevos en el período
    - Planes generados en el período
    - Promedio de kcal por plan
    - Distribución de objetivos (déficit / mantenimiento / superávit)
    - Nuevos clientes por día (últimos 7 días)

    Requiere rol `gym` o `admin`.
    """
    try:
        fecha_inicio = datetime.now() - timedelta(days=dias)
        fecha_fin = datetime.now()
        datos = gestor_bd.obtener_estadisticas_gym(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        obj_dist_raw: dict = datos.get("distribucion_objetivos", {})
        dist = DistribucionObjetivos(
            deficit=obj_dist_raw.get("deficit", 0),
            mantenimiento=obj_dist_raw.get("mantenimiento", 0),
            superavit=obj_dist_raw.get("superavit", 0),
        )

        total_clientes = datos.get("total_clientes", 0)
        planes_periodo = datos.get("planes_periodo", 0)
        por_cliente = (
            round(planes_periodo / total_clientes, 2) if total_clientes > 0 else 0.0
        )

        kpis = KPIsGym(
            total_clientes=total_clientes,
            clientes_activos=datos.get("clientes_activos", total_clientes),
            clientes_nuevos_periodo=datos.get("clientes_nuevos", 0),
            planes_generados_periodo=planes_periodo,
            promedio_kcal=round(datos.get("promedio_kcal", 0), 1),
            objetivo_mas_comun=datos.get("objetivo_comun", "—"),
            tasa_retencion_pct=0.0,  # TODO: calcular con historial de accesos
            planes_por_cliente_promedio=por_cliente,
        )

        semana = datos.get("clientes_nuevos_semana", [0] * 7)
        # Normalizar a exactamente 7 elementos
        if len(semana) < 7:
            semana = semana + [0] * (7 - len(semana))

        return EstadisticasGymResponse(
            periodo_dias=dias,
            kpis=kpis,
            distribucion_objetivos=dist,
            clientes_nuevos_semana=semana[:7],
        )
    except Exception as exc:
        logger.error("[API][reportes] Error obteniendo estadísticas: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estadísticas del gym.",
        ) from exc
