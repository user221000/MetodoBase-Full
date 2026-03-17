"""
Router: clientes del gym.

GET  /api/v1/clientes            — Listar clientes (paginado)
GET  /api/v1/clientes/{id}       — Obtener cliente por ID
GET  /api/v1/clientes/{id}/planes — Historial de planes del cliente
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.schemas.reportes import ClienteResumen, ListaClientesResponse
from api.dependencies import require_rol_gym, SesionToken, get_gestor_bd
from src.gestor_bd import GestorBDClientes
from utils.logger import logger

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get(
    "",
    response_model=ListaClientesResponse,
    summary="Listar clientes del gym",
)
def listar_clientes(
    pagina: int = Query(1, ge=1, description="Número de página (empieza en 1)"),
    por_pagina: int = Query(20, ge=1, le=100, description="Resultados por página"),
    solo_activos: bool = Query(True, description="Solo clientes activos"),
    buscar: str = Query("", description="Buscar por nombre o teléfono"),
    gestor_bd: GestorBDClientes = Depends(get_gestor_bd),
    _sesion: SesionToken = Depends(require_rol_gym),
) -> ListaClientesResponse:
    """
    Lista los clientes registrados en el gym con paginación.

    Requiere rol `gym` o `admin`.
    """
    try:
        if buscar:
            todos = gestor_bd.buscar_clientes(buscar)
        else:
            todos = gestor_bd.obtener_todos_clientes(solo_activos=solo_activos)

        total = len(todos)
        inicio = (pagina - 1) * por_pagina
        pagina_datos = todos[inicio: inicio + por_pagina]

        clientes = [
            ClienteResumen(
                id_cliente=c.get("id_cliente", ""),
                nombre=c.get("nombre", ""),
                telefono=c.get("telefono"),
                edad=c.get("edad"),
                peso_kg=c.get("peso_kg"),
                estatura_cm=c.get("estatura_cm"),
                objetivo=c.get("objetivo"),
                nivel_actividad=c.get("nivel_actividad"),
                activo=bool(c.get("activo", 1)),
                fecha_registro=str(c.get("fecha_registro", "")),
                total_planes=int(c.get("total_planes", 0)),
            )
            for c in pagina_datos
        ]
        return ListaClientesResponse(
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            clientes=clientes,
        )
    except Exception as exc:
        logger.error("[API][clientes] Error listando clientes: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la lista de clientes.",
        ) from exc


@router.get(
    "/{id_cliente}/planes",
    summary="Historial de planes de un cliente",
)
def historial_planes(
    id_cliente: str,
    gestor_bd: GestorBDClientes = Depends(get_gestor_bd),
    _sesion: SesionToken = Depends(require_rol_gym),
) -> dict:
    """
    Devuelve el historial de planes generados para un cliente específico.

    Requiere rol `gym` o `admin`.
    """
    try:
        historial = gestor_bd.obtener_historial_planes(id_cliente)
        return {"id_cliente": id_cliente, "total": len(historial), "planes": historial}
    except Exception as exc:
        logger.error("[API][clientes] Error obteniendo historial: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el historial de planes.",
        ) from exc
