"""
Router: generación de planes nutricionales.

POST /api/v1/planes/calcular    — Generar plan a partir de datos del cliente
GET  /api/v1/planes/{id_plan}   — Obtener plan por ID (futuro)
"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.planes import (
    PlanRequest, PlanResponse, ResultadoNutricionalResponse,
    MacrosResponse, AlertaSaludResponse, ComidaResponse,
)
from api.dependencies import require_token, SesionToken
from config.constantes import FACTORES_ACTIVIDAD, CARPETA_PLANES
from core.modelos import ClienteEvaluacion
from core.motor_nutricional import MotorNutricional
from core.generador_planes import ConstructorPlanNuevo
from utils.logger import logger

router = APIRouter(prefix="/planes", tags=["Planes Nutricionales"])

_COMIDAS_ORDEN = ["desayuno", "almuerzo", "comida", "cena"]


def _mapear_alerta(alerta) -> AlertaSaludResponse:
    return AlertaSaludResponse(
        nivel=alerta.nivel,
        codigo=alerta.codigo,
        mensaje=alerta.mensaje,
        detalle=getattr(alerta, "detalle", ""),
    )


@router.post(
    "/calcular",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar plan nutricional personalizado",
)
def calcular_plan(
    body: PlanRequest,
    sesion: SesionToken = Depends(require_token),
) -> PlanResponse:
    """
    Genera un plan nutricional completo a partir de los datos del cliente.

    **Flujo:**
    1. Crea `ClienteEvaluacion` con los datos recibidos.
    2. Ejecuta el motor Katch-McArdle (TMB, GET, macros).
    3. Construye el plan diario con rotación inteligente de alimentos.
    4. Devuelve el plan como JSON estructurado.

    **Notas:**
    - La generación de PDF es opcional y se realiza en un endpoint separado (`/planes/{id}/pdf`).
    - Los `alimentos_excluidos` permiten personalizar el catálogo por cliente.
    """
    try:
        factor = FACTORES_ACTIVIDAD.get(body.nivel_actividad, 1.2)
        cliente = ClienteEvaluacion(
            nombre=body.nombre,
            telefono=body.telefono,
            edad=body.edad,
            peso_kg=body.peso_kg,
            estatura_cm=body.estatura_cm,
            grasa_corporal_pct=body.grasa_corporal_pct,
            nivel_actividad=body.nivel_actividad,
            objetivo=body.objetivo,
            plantilla_tipo=body.plantilla_tipo,
            factor_actividad=factor,
        )

        # Motor nutricional
        cliente = MotorNutricional.calcular_motor(cliente)

        # Generador de plan de alimentos
        plan = ConstructorPlanNuevo.construir(
            cliente, plan_numero=1, directorio_planes=CARPETA_PLANES
        )

        # Alertas combinadas (motor + plan)
        alertas_motor = [_mapear_alerta(a) for a in getattr(cliente, "alertas_salud", [])]
        alertas_plan: list[AlertaSaludResponse] = []
        for comida_key in _COMIDAS_ORDEN:
            if comida_key in plan:
                for a in plan[comida_key].get("alertas", []):
                    if hasattr(a, "nivel"):
                        alertas_plan.append(_mapear_alerta(a))

        # Resultado nutricional
        resultado = ResultadoNutricionalResponse(
            masa_magra=round(cliente.masa_magra or 0, 2),
            tmb=round(cliente.tmb or 0, 2),
            get_total=round(cliente.get_total or 0, 2),
            kcal_objetivo=round(cliente.kcal_objetivo or 0, 2),
            macros=MacrosResponse(
                proteina_g=round(cliente.proteina_g or 0, 1),
                grasa_g=round(cliente.grasa_g or 0, 1),
                carbs_g=round(cliente.carbs_g or 0, 1),
                kcal_proteina=round((cliente.proteina_g or 0) * 4, 1),
                kcal_grasa=round((cliente.grasa_g or 0) * 9, 1),
                kcal_carbs=round((cliente.carbs_g or 0) * 4, 1),
            ),
            alertas=alertas_motor,
        )

        # Comidas
        comidas: dict[str, ComidaResponse] = {}
        for key in _COMIDAS_ORDEN:
            if key not in plan:
                continue
            c = plan[key]
            comidas[key] = ComidaResponse(
                nombre=key.capitalize(),
                kcal_real=round(c.get("kcal_real", 0), 1),
                desviacion_pct=round(c.get("desviacion_pct", 0), 2),
                alimentos=c.get("alimentos", []),
            )

        return PlanResponse(
            id_cliente=cliente.id_cliente,
            nombre_cliente=cliente.nombre or "",
            resultado_nutricional=resultado,
            comidas=comidas,
            alertas=alertas_motor + alertas_plan,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("[API][planes] Error generando plan: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar el plan. Contacta soporte.",
        ) from exc
