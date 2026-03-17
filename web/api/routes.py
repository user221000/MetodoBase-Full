"""Endpoints REST de la API MetodoBase Web."""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

# Agregar el directorio raíz del proyecto al path para importar core/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web.api.schemas import (
    ClienteCreate, ClienteUpdate, ClienteResponse,
    PlanRequest, PlanResponse, EstadisticasResponse,
)
from web.api.dependencies import obtener_gestor_bd
from core.modelos import ClienteEvaluacion
from core.motor_nutricional import MotorNutricional
from core.procesador_cliente import NormalizadorCliente, ValidadorCliente
from config.constantes import FACTORES_ACTIVIDAD, CARPETA_SALIDA

router = APIRouter()


# ============================================================================
# UTILIDADES INTERNAS
# ============================================================================

def _construir_cliente_evaluacion(datos: dict) -> ClienteEvaluacion:
    """Construye un ClienteEvaluacion desde un dict (datos de la BD o request)."""
    cliente = ClienteEvaluacion()
    cliente.id_cliente = datos.get("id_cliente", cliente.id_cliente)
    cliente.nombre = datos.get("nombre", "")
    cliente.telefono = datos.get("telefono")
    cliente.edad = datos.get("edad")
    cliente.peso_kg = datos.get("peso_kg")
    cliente.estatura_cm = datos.get("estatura_cm")
    cliente.grasa_corporal_pct = datos.get("grasa_corporal_pct")
    cliente.nivel_actividad = datos.get("nivel_actividad", "")
    cliente.objetivo = datos.get("objetivo", "")
    cliente.factor_actividad = FACTORES_ACTIVIDAD.get(
        str(datos.get("nivel_actividad", "")).lower(), 1.2
    )
    return cliente


# ============================================================================
# ENDPOINT: ESTADÍSTICAS DEL DASHBOARD
# ============================================================================

@router.get("/api/estadisticas", response_model=EstadisticasResponse, tags=["dashboard"])
def obtener_estadisticas():
    """Retorna KPIs y estadísticas del gym para el dashboard."""
    gestor = obtener_gestor_bd()
    stats = gestor.obtener_estadisticas_gym()
    return EstadisticasResponse(
        total_clientes=stats.get("total_clientes", 0),
        clientes_nuevos=stats.get("clientes_nuevos", 0),
        clientes_activos=stats.get("clientes_activos", 0),
        planes_periodo=stats.get("planes_periodo", 0),
        promedio_kcal=stats.get("promedio_kcal", 0.0),
        objetivos=stats.get("objetivos", {}),
        top_clientes=stats.get("top_clientes", []),
        renovaciones=stats.get("renovaciones", 0),
        tasa_retencion=stats.get("tasa_retencion", 0.0),
        planes_por_tipo=stats.get("planes_por_tipo", {}),
    )


# ============================================================================
# ENDPOINTS DE CLIENTES
# ============================================================================

@router.get("/api/clientes", response_model=List[ClienteResponse], tags=["clientes"])
def listar_clientes(
    buscar: Optional[str] = Query(None, description="Término de búsqueda (nombre, teléfono, ID)"),
    solo_activos: bool = Query(True, description="Filtrar solo clientes activos"),
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(20, ge=1, le=100, description="Resultados por página"),
):
    """Lista clientes con búsqueda y paginación."""
    gestor = obtener_gestor_bd()

    if buscar and buscar.strip():
        clientes = gestor.buscar_clientes(
            termino=buscar.strip(),
            solo_activos=solo_activos,
            limite=por_pagina * pagina,
        )
    else:
        clientes = gestor.obtener_todos_clientes(solo_activos=solo_activos)

    # Paginación manual
    inicio = (pagina - 1) * por_pagina
    fin = inicio + por_pagina
    clientes_paginados = clientes[inicio:fin]

    return [ClienteResponse(**c) for c in clientes_paginados]


@router.get("/api/clientes/{id_cliente}", response_model=ClienteResponse, tags=["clientes"])
def obtener_cliente(id_cliente: str):
    """Obtiene los datos de un cliente por ID."""
    gestor = obtener_gestor_bd()
    cliente = gestor.obtener_cliente_por_id(id_cliente)
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente '{id_cliente}' no encontrado")
    return ClienteResponse(**cliente)


@router.post("/api/clientes", response_model=ClienteResponse, status_code=201, tags=["clientes"])
def crear_cliente(datos: ClienteCreate):
    """Registra un nuevo cliente en la base de datos."""
    gestor = obtener_gestor_bd()

    # Construir ClienteEvaluacion y validar
    cliente = ClienteEvaluacion()
    cliente.nombre = datos.nombre.strip()
    cliente.telefono = datos.telefono
    cliente.edad = datos.edad
    cliente.peso_kg = datos.peso_kg
    cliente.estatura_cm = datos.estatura_cm
    cliente.grasa_corporal_pct = datos.grasa_corporal_pct
    cliente.nivel_actividad = datos.nivel_actividad.lower().strip()
    cliente.objetivo = datos.objetivo.lower().strip()
    cliente.factor_actividad = FACTORES_ACTIVIDAD.get(cliente.nivel_actividad, 1.2)

    # Validar
    validador = ValidadorCliente()
    es_valido, errores = validador.validar_cliente(cliente)
    if not es_valido:
        raise HTTPException(status_code=422, detail={"errores": errores})

    # Normalizar y calcular motor
    cliente = NormalizadorCliente.normalizar(cliente)
    cliente.validado = True

    # Guardar en BD
    exito = gestor.registrar_cliente(cliente)
    if not exito:
        raise HTTPException(status_code=500, detail="Error guardando el cliente en la base de datos")

    # Retornar el cliente recién creado
    cliente_guardado = gestor.obtener_cliente_por_id(cliente.id_cliente)
    if not cliente_guardado:
        # Si no se puede obtener el cliente, construir la respuesta manualmente
        return ClienteResponse(
            id_cliente=cliente.id_cliente,
            nombre=cliente.nombre,
            telefono=cliente.telefono,
            edad=cliente.edad,
            peso_kg=cliente.peso_kg,
            estatura_cm=cliente.estatura_cm,
            grasa_corporal_pct=cliente.grasa_corporal_pct,
            nivel_actividad=cliente.nivel_actividad,
            objetivo=cliente.objetivo,
            total_planes_generados=0,
            activo=True,
        )
    return ClienteResponse(**cliente_guardado)


@router.put("/api/clientes/{id_cliente}", response_model=ClienteResponse, tags=["clientes"])
def actualizar_cliente(id_cliente: str, datos: ClienteUpdate):
    """Actualiza los datos de un cliente existente."""
    gestor = obtener_gestor_bd()

    # Verificar que el cliente exista
    cliente_actual = gestor.obtener_cliente_por_id(id_cliente)
    if not cliente_actual:
        raise HTTPException(status_code=404, detail=f"Cliente '{id_cliente}' no encontrado")

    # Fusionar datos actuales con los nuevos
    datos_actualizados = {**cliente_actual}
    campos_update = datos.model_dump(exclude_unset=True)
    for campo, valor in campos_update.items():
        if valor is not None:
            datos_actualizados[campo] = valor

    # Construir el objeto ClienteEvaluacion con los datos actualizados
    cliente = _construir_cliente_evaluacion(datos_actualizados)

    # Validar solo si se actualizaron campos clínicos
    campos_clinicos = {"peso_kg", "estatura_cm", "grasa_corporal_pct", "nivel_actividad", "objetivo"}
    if campos_clinicos & set(campos_update.keys()):
        validador = ValidadorCliente()
        es_valido, errores = validador.validar_cliente(cliente)
        if not es_valido:
            raise HTTPException(status_code=422, detail={"errores": errores})
        cliente = NormalizadorCliente.normalizar(cliente)

    # Guardar
    exito = gestor.registrar_cliente(cliente)
    if not exito:
        raise HTTPException(status_code=500, detail="Error actualizando el cliente")

    cliente_guardado = gestor.obtener_cliente_por_id(id_cliente)
    return ClienteResponse(**cliente_guardado)


# ============================================================================
# ENDPOINTS DE PLANES
# ============================================================================

@router.post("/api/generar-plan", response_model=PlanResponse, tags=["planes"])
def generar_plan(request: PlanRequest):
    """Genera un plan nutricional completo y retorna la URL del PDF."""
    gestor = obtener_gestor_bd()

    # 1. Obtener cliente de la BD (primero la validación, luego imports pesados)
    cliente_data = gestor.obtener_cliente_por_id(request.id_cliente)
    if not cliente_data:
        raise HTTPException(status_code=404, detail=f"Cliente '{request.id_cliente}' no encontrado")

    # Importar módulos pesados solo cuando se necesiten
    from core.generador_planes import ConstructorPlanNuevo
    from core.exportador_salida import GeneradorPDFProfesional

    # 2. Construir ClienteEvaluacion con posibles actualizaciones del request
    cliente = _construir_cliente_evaluacion(cliente_data)

    # Aplicar overrides del request si se proporcionaron
    if request.peso_kg is not None:
        cliente.peso_kg = request.peso_kg
    if request.grasa_corporal_pct is not None:
        cliente.grasa_corporal_pct = request.grasa_corporal_pct
    if request.nivel_actividad is not None:
        cliente.nivel_actividad = request.nivel_actividad.lower().strip()
        cliente.factor_actividad = FACTORES_ACTIVIDAD.get(cliente.nivel_actividad, 1.2)
    if request.objetivo is not None:
        cliente.objetivo = request.objetivo.lower().strip()

    # 3. Calcular motor nutricional
    cliente = MotorNutricional.calcular_motor(cliente)

    # 4. Determinar número de plan
    historial = gestor.obtener_historial_planes(request.id_cliente)
    plan_numero = len(historial) + 1

    # 5. Generar plan
    plan = ConstructorPlanNuevo.construir(cliente, plan_numero=plan_numero)

    # 6. Crear carpeta de salida
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    # 7. Generar PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_pdf = f"plan_{cliente.id_cliente}_{timestamp}.pdf"
    ruta_pdf_completa = os.path.join(CARPETA_SALIDA, nombre_pdf)

    generador_pdf = GeneradorPDFProfesional(ruta_pdf_completa)
    ruta_pdf = generador_pdf.generar(cliente, plan)

    if not ruta_pdf:
        raise HTTPException(status_code=500, detail="Error generando el PDF")

    # 8. Registrar en BD
    gestor.registrar_cliente(cliente)
    gestor.registrar_plan_generado(cliente, plan, ruta_pdf)

    # 9. Calcular macros para el preview
    macros = {
        "kcal_objetivo": round(cliente.kcal_objetivo, 1),
        "proteina_g": round(cliente.proteina_g, 1),
        "carbs_g": round(cliente.carbs_g, 1),
        "grasa_g": round(cliente.grasa_g, 1),
        "tmb": round(cliente.tmb, 1),
        "get_total": round(cliente.get_total, 1),
    }

    return PlanResponse(
        success=True,
        id_cliente=cliente.id_cliente,
        pdf_url=f"/api/descargar-pdf/{nombre_pdf}",
        macros=macros,
        mensaje=f"Plan #{plan_numero} generado exitosamente",
    )


@router.get("/api/planes/{id_cliente}", tags=["planes"])
def obtener_planes_cliente(id_cliente: str):
    """Retorna el historial de planes generados para un cliente."""
    gestor = obtener_gestor_bd()

    cliente = gestor.obtener_cliente_por_id(id_cliente)
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente '{id_cliente}' no encontrado")

    historial = gestor.obtener_historial_planes(id_cliente)
    return {"id_cliente": id_cliente, "planes": historial}


@router.get("/api/descargar-pdf/{nombre_pdf}", tags=["planes"])
def descargar_pdf(nombre_pdf: str):
    """Descarga el PDF de un plan generado."""
    # Validar que el nombre no contenga traversal de directorios
    if "/" in nombre_pdf or "\\" in nombre_pdf or ".." in nombre_pdf:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    ruta_pdf = os.path.join(CARPETA_SALIDA, nombre_pdf)

    if not os.path.exists(ruta_pdf):
        raise HTTPException(status_code=404, detail=f"PDF '{nombre_pdf}' no encontrado")

    return FileResponse(
        path=ruta_pdf,
        media_type="application/pdf",
        filename=nombre_pdf,
    )
