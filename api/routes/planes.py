"""Generación de planes y descarga de PDF — /api/generar-plan, /api/descargar-pdf."""
import asyncio
import logging
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse

from api.schemas import PlanRequest
from api.dependencies import get_gestor, build_cliente_from_dict
from src.gestor_bd import GestorBDClientes
from config.constantes import CARPETA_SALIDA, CARPETA_PLANES

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Planes"])


def _generar_plan_sync(id_cliente: str, plan_numero: int) -> dict:
    """
    Función CPU-bound que se ejecuta en un thread executor.
    No comparte estado con el event loop de asyncio.
    """
    # Importaciones locales al thread para evitar problemas de estado
    from src.gestor_bd import GestorBDClientes as _GBD
    from core.generador_planes import ConstructorPlanNuevo
    from core.exportador_salida import GeneradorPDFProfesional

    gestor = _GBD()
    row = gestor.obtener_cliente_por_id(id_cliente)
    if not row:
        raise ValueError(f"Cliente '{id_cliente}' no encontrado")

    cliente = build_cliente_from_dict(row)

    # Generar plan nutricional
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    plan = ConstructorPlanNuevo.construir(
        cliente,
        plan_numero=plan_numero,
        directorio_planes=CARPETA_PLANES,
    )

    # Generar PDF
    nombre_pdf = (
        f"plan_{cliente.nombre.replace(' ', '_')}"
        f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    ruta_pdf_completa = os.path.join(CARPETA_SALIDA, nombre_pdf)
    generador = GeneradorPDFProfesional(ruta_pdf_completa)
    ruta_pdf = generador.generar(cliente, plan)

    # Persistir en BD
    gestor.registrar_cliente(cliente)
    gestor.registrar_plan_generado(cliente, plan, ruta_pdf)

    # Armar respuesta
    comidas = ["desayuno", "almuerzo", "comida", "cena"]
    kcal_real = sum(plan.get(c, {}).get("kcal_real", 0) for c in comidas)

    return {
        "success": True,
        "id_cliente": cliente.id_cliente,
        "nombre": cliente.nombre,
        "ruta_pdf": str(ruta_pdf),
        "macros": {
            "tmb": round(cliente.tmb or 0, 1),
            "get_total": round(cliente.get_total or 0, 1),
            "kcal_objetivo": round(cliente.kcal_objetivo or 0, 0),
            "kcal_real": round(kcal_real, 0),
            "proteina_g": round(cliente.proteina_g or 0, 1),
            "carbs_g": round(cliente.carbs_g or 0, 1),
            "grasa_g": round(cliente.grasa_g or 0, 1),
        },
        "plan": {
            comida: {
                "kcal_objetivo": round(plan[comida].get("kcal_objetivo", 0), 0),
                "kcal_real": round(plan[comida].get("kcal_real", 0), 0),
                "alimentos": {
                    k: round(v, 0)
                    for k, v in plan[comida].get("alimentos", {}).items()
                    if v > 0
                },
            }
            for comida in comidas
            if comida in plan
        },
    }


@router.post("/generar-plan", summary="Generar plan nutricional + PDF")
async def generar_plan(
    data: PlanRequest,
    gestor: GestorBDClientes = Depends(get_gestor),
):
    """
    Genera un plan nutricional diario para un cliente existente.
    La generación es CPU-bound (~5–15 seg); se ejecuta en un thread executor
    para no bloquear el event loop.
    """
    loop = asyncio.get_event_loop()
    try:
        resultado = await loop.run_in_executor(
            None, _generar_plan_sync, data.id_cliente, data.plan_numero
        )
        logger.info("Plan generado para cliente: %s", data.id_cliente)
        return resultado
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(
            "Error generando plan para %s: %s", data.id_cliente, exc, exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Error en generación: {exc}")


@router.get("/descargar-pdf/{id_cliente}", summary="Descargar último PDF del cliente")
async def descargar_pdf(
    id_cliente: str,
    gestor: GestorBDClientes = Depends(get_gestor),
):
    """Descarga el PDF del plan más reciente generado para el cliente."""
    historial = gestor.obtener_historial_planes(id_cliente, limite=1)
    if not historial:
        raise HTTPException(
            status_code=404, detail="No hay planes generados para este cliente"
        )

    ruta_pdf = historial[0].get("ruta_pdf")
    if not ruta_pdf or not os.path.exists(ruta_pdf):
        raise HTTPException(status_code=404, detail="Archivo PDF no encontrado en disco")

    filename = os.path.basename(ruta_pdf)
    return FileResponse(
        path=ruta_pdf,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
