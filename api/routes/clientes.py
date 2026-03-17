"""CRUD endpoints /api/clientes."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from api.schemas import ClienteCreate, ClienteUpdate
from api.dependencies import get_gestor, build_cliente_from_dict
from src.gestor_bd import GestorBDClientes

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Clientes"])


@router.get("/clientes", summary="Listar clientes activos")
def listar_clientes(
    q: Optional[str] = Query(None, description="Busca por nombre, teléfono o ID"),
    limite: int = Query(100, ge=1, le=500),
    gestor: GestorBDClientes = Depends(get_gestor),
):
    """Lista clientes activos; acepta búsqueda opcional con ?q=."""
    termino = q.strip() if q else ""
    clientes = gestor.buscar_clientes(termino, solo_activos=True, limite=limite)
    return {"clientes": clientes, "total": len(clientes)}


@router.get("/clientes/{id_cliente}", summary="Obtener cliente por ID")
def obtener_cliente(
    id_cliente: str,
    gestor: GestorBDClientes = Depends(get_gestor),
):
    """Retorna todos los datos de un cliente."""
    cliente = gestor.obtener_cliente_por_id(id_cliente)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.post("/clientes", status_code=201, summary="Crear nuevo cliente")
def crear_cliente(
    data: ClienteCreate,
    gestor: GestorBDClientes = Depends(get_gestor),
):
    """
    Crea un nuevo cliente. Calcula macros (Katch-McArdle) automáticamente
    a partir de los datos antropométricos y los almacena junto con el perfil.
    """
    try:
        cliente = build_cliente_from_dict(data.model_dump())
        exito = gestor.registrar_cliente(cliente)
        if not exito:
            raise HTTPException(status_code=500, detail="Error guardando cliente en BD")

        logger.info("Cliente creado: %s (%s)", cliente.nombre, cliente.id_cliente)
        return {
            "success": True,
            "id_cliente": cliente.id_cliente,
            "message": f"Cliente '{cliente.nombre}' creado correctamente",
            "macros": {
                "tmb": round(cliente.tmb or 0, 1),
                "get_total": round(cliente.get_total or 0, 1),
                "kcal_objetivo": round(cliente.kcal_objetivo or 0, 0),
                "proteina_g": round(cliente.proteina_g or 0, 1),
                "carbs_g": round(cliente.carbs_g or 0, 1),
                "grasa_g": round(cliente.grasa_g or 0, 1),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error creando cliente: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/clientes/{id_cliente}", summary="Actualizar cliente existente")
def actualizar_cliente(
    id_cliente: str,
    data: ClienteUpdate,
    gestor: GestorBDClientes = Depends(get_gestor),
):
    """Actualiza los datos de un cliente existente (merge parcial)."""
    existing = gestor.obtener_cliente_por_id(id_cliente)
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    try:
        # Merge: solo sobreescribe campos no-None del body
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        merged = {**existing, **update_dict, "id_cliente": id_cliente}
        cliente = build_cliente_from_dict(merged)
        exito = gestor.registrar_cliente(cliente)
        if not exito:
            raise HTTPException(status_code=500, detail="Error actualizando cliente")

        logger.info("Cliente actualizado: %s", id_cliente)
        return {"success": True, "message": "Cliente actualizado correctamente"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error actualizando cliente %s: %s", id_cliente, exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/clientes/{id_cliente}", summary="Desactivar cliente (soft delete)")
def desactivar_cliente(
    id_cliente: str,
    gestor: GestorBDClientes = Depends(get_gestor),
):
    """Desactiva un cliente (lo oculta del listado; sus datos se conservan)."""
    existing = gestor.obtener_cliente_por_id(id_cliente)
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    try:
        import sqlite3
        conn = sqlite3.connect(gestor.db_path)
        conn.execute("UPDATE clientes SET activo = 0 WHERE id_cliente = ?", (id_cliente,))
        conn.commit()
        conn.close()
        logger.info("Cliente desactivado: %s", id_cliente)
        return {"success": True, "message": "Cliente desactivado"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
