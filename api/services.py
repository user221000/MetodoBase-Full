"""
api/services.py — Capa de servicios de MetodoBase.

Abstrae toda la lógica de negocio del código legacy (src/ y core/).
Las routes importan funciones de este módulo en lugar de llamar
directamente a gestor_bd, motor_nutricional, etc.

Beneficios:
  - Testeable sin FastAPI (TestClient no necesario)
  - Un único lugar para logging de performance
  - Fácil de mockear en unit tests
  - `lru_cache` en helpers de lectura frecuente
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from api.exceptions import (
    BaseDatosError,
    ClienteNoEncontradoError,
    DatosInvalidosError,
    GeneracionPlanError,
    PDFGenerationError,
)

logger = logging.getLogger(__name__)


# ── Helpers de acceso a gestor_bd ─────────────────────────────────────────────

def _get_gestor():
    """
    Instancia de GestorBDClientes para código legacy/interno.
    
    NOTA: Para endpoints de API, usar web.database.repository con autenticación.
    Este helper es para tests y scripts internos que no tienen contexto de tenant.
    """
    import os
    from src.gestor_bd import GestorBDClientes
    db_path = os.getenv("DB_PATH", None)
    return GestorBDClientes(db_path=db_path)


# ── 1. Crear cliente completo ─────────────────────────────────────────────────

def crear_cliente_completo(datos: dict) -> str:
    """
    Valida, construye y persiste un cliente con macros calculados.

    Args:
        datos: dict compatible con ClienteCreate (nombre, edad, peso_kg, …)

    Returns:
        id_cliente (str) del registro creado.

    Raises:
        DatosInvalidosError: Si faltan campos obligatorios.
        BaseDatosError: Si la persistencia falla.
    """
    _validar_campos_requeridos(datos)

    from api.dependencies import build_cliente_from_dict
    t0 = time.perf_counter()
    try:
        cliente = build_cliente_from_dict(datos)
    except Exception as exc:
        raise DatosInvalidosError(f"No se pudo construir el cliente: {exc}") from exc

    gestor = _get_gestor()
    exito = gestor.registrar_cliente(cliente)
    if not exito:
        raise BaseDatosError("Error al persistir el cliente en la base de datos")

    elapsed = time.perf_counter() - t0
    logger.info("crear_cliente_completo: '%s' (%s) en %.3fs", cliente.nombre, cliente.id_cliente, elapsed)
    return cliente.id_cliente


# ── 2. Obtener cliente por ID ─────────────────────────────────────────────────

def obtener_cliente_por_id(id_cliente: str) -> dict:
    """
    Busca un cliente por ID y lo devuelve como dict serializable.

    Raises:
        ClienteNoEncontradoError: Si el ID no existe.
    """
    gestor = _get_gestor()
    row = gestor.obtener_cliente_por_id(id_cliente)
    if not row:
        raise ClienteNoEncontradoError(id_cliente)
    return dict(row)


# ── 3. Listar clientes activos ────────────────────────────────────────────────

def listar_clientes_activos(termino: str = "", limit: int = 50) -> list[dict]:
    """
    Devuelve clientes activos, con búsqueda opcional por nombre/teléfono/email.

    Returns:
        Lista de dicts con los campos del cliente.
    """
    gestor = _get_gestor()
    rows = gestor.buscar_clientes(termino, solo_activos=True, limite=limit)
    return [dict(r) for r in rows]


# ── 4. Generar plan nutricional ───────────────────────────────────────────────

def generar_plan_nutricional(id_cliente: str, plan_numero: int = 1, opciones: Optional[dict] = None) -> dict:
    """
    Orquesta el flujo completo: macros → plan de comidas → PDF → persistencia.

    Args:
        id_cliente:  ID del cliente existente.
        plan_numero: Número de plan (para rotación de alimentos).
        opciones:    Reservado para futuras opciones (plantilla, restricciones, etc.)

    Returns:
        Dict con keys: success, id_cliente, nombre, macros, plan, ruta_pdf,
        tiempo_generacion_s.

    Raises:
        ClienteNoEncontradoError: Si el cliente no existe.
        GeneracionPlanError:      Si falla el motor nutricional.
        PDFGenerationError:       Si falla la creación del PDF.
    """
    t_total = time.perf_counter()

    # 1. Obtener cliente
    row = obtener_cliente_por_id(id_cliente)  # raises ClienteNoEncontradoError si no existe
    logger.info("[generar_plan] Cliente encontrado: %s (%s)", row.get("nombre"), id_cliente)

    # 2. Reconstruir ClienteEvaluacion con macros
    from api.dependencies import build_cliente_from_dict
    try:
        cliente = build_cliente_from_dict(row)
    except Exception as exc:
        raise GeneracionPlanError(f"Error calculando macros: {exc}") from exc

    # 3. Generar plan de comidas (CPU-bound)
    from config.constantes import CARPETA_SALIDA, CARPETA_PLANES
    from core.generador_planes import ConstructorPlanNuevo
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    try:
        t_plan = time.perf_counter()
        plan = ConstructorPlanNuevo.construir(
            cliente,
            plan_numero=plan_numero,
            directorio_planes=CARPETA_PLANES,
        )
        logger.info("[generar_plan] Plan construido en %.2fs", time.perf_counter() - t_plan)
    except Exception as exc:
        raise GeneracionPlanError(f"ConstructorPlanNuevo falló: {exc}") from exc

    # 4. Generar PDF
    nombre_pdf = (
        f"plan_{cliente.nombre.replace(' ', '_')}"
        f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    ruta_pdf_str = str(Path(CARPETA_SALIDA) / nombre_pdf)
    try:
        t_pdf = time.perf_counter()
        from api.pdf_generator import PDFGenerator
        pdf_gen = PDFGenerator()
        datos_pdf = PDFGenerator.datos_from_cliente(cliente, plan)
        ruta_pdf = pdf_gen.generar_plan(datos_pdf, Path(ruta_pdf_str))
        logger.info("[generar_plan] PDF generado en %.2fs → %s", time.perf_counter() - t_pdf, ruta_pdf)
    except Exception as exc:
        raise PDFGenerationError(f"PDFGenerator falló: {exc}") from exc

    # 5. Persistir plan en BD
    gestor = _get_gestor()
    gestor.registrar_cliente(cliente)
    gestor.registrar_plan_generado(cliente, plan, ruta_pdf)

    # 6. Armar respuesta
    comidas_keys = ["desayuno", "almuerzo", "comida", "cena"]
    kcal_real = sum(plan.get(c, {}).get("kcal_real", 0) for c in comidas_keys)
    elapsed = round(time.perf_counter() - t_total, 2)
    logger.info("[generar_plan] TOTAL: %.2fs para %s", elapsed, id_cliente)

    return {
        "success": True,
        "id_cliente": cliente.id_cliente,
        "nombre": cliente.nombre,
        "ruta_pdf": str(ruta_pdf),
        "tiempo_generacion_s": elapsed,
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
            c: {
                "kcal_objetivo": round(plan[c].get("kcal_objetivo", 0), 0),
                "kcal_real": round(plan[c].get("kcal_real", 0), 0),
                "alimentos": {
                    k: round(v, 0)
                    for k, v in plan[c].get("alimentos", {}).items()
                    if v > 0
                },
            }
            for c in comidas_keys
            if c in plan
        },
    }


# ── 5. Estadísticas del gym ───────────────────────────────────────────────────

def calcular_estadisticas_gym() -> dict:
    """
    Retorna KPIs del dashboard: clientes activos, planes generados, etc.

    No lanza excepciones — devuelve estructura vacía si falla.
    """
    try:
        gestor = _get_gestor()
        return gestor.obtener_estadisticas_gym()
    except Exception as exc:
        logger.warning("calcular_estadisticas_gym: %s", exc)
        return {
            "total_clientes": 0,
            "clientes_activos": 0,
            "clientes_nuevos": 0,
            "planes_periodo": 0,
            "promedio_kcal": 0,
            "objetivos": {},
            "top_clientes": [],
            "renovaciones": 0,
            "tasa_retencion": 0.0,
            "planes_por_tipo": {},
        }


# ── 6. Validación de datos antropométricos ────────────────────────────────────

def validar_datos_antropometricos(datos: dict) -> tuple[bool, str]:
    """
    Pre-valida datos antes de enviarlos al motor nutricional.

    Returns:
        (True, "") si los datos son válidos.
        (False, "mensaje de error") si hay algún problema.
    """
    REQUIRED = ["nombre", "edad", "peso_kg", "estatura_cm", "nivel_actividad", "objetivo"]
    for campo in REQUIRED:
        if datos.get(campo) is None or datos.get(campo) == "":
            return False, f"Campo requerido faltante: '{campo}'"

    # Rangos
    checks = [
        ("edad", 15, 80),
        ("peso_kg", 40, 200),
        ("estatura_cm", 140, 220),
    ]
    for campo, minv, maxv in checks:
        val = datos.get(campo)
        if val is not None:
            try:
                val = float(val)
            except (TypeError, ValueError):
                return False, f"'{campo}' debe ser numérico"
            if not (minv <= val <= maxv):
                return False, f"'{campo}' fuera de rango ({minv}–{maxv})"

    grasa = datos.get("grasa_corporal_pct")
    if grasa is not None:
        try:
            grasa = float(grasa)
        except (TypeError, ValueError):
            return False, "'grasa_corporal_pct' debe ser numérico"
        if not (5.0 <= grasa <= 60.0):
            return False, "'grasa_corporal_pct' debe estar entre 5% y 60%"

    from config.constantes import NIVELES_ACTIVIDAD as NIVELES_VALIDOS, OBJETIVOS_VALIDOS
    nivel = str(datos.get("nivel_actividad", "")).lower()
    objetivo = str(datos.get("objetivo", "")).lower()
    if nivel not in NIVELES_VALIDOS:
        return False, f"'nivel_actividad' debe ser uno de: {sorted(NIVELES_VALIDOS)}"
    if objetivo not in OBJETIVOS_VALIDOS:
        return False, f"'objetivo' debe ser uno de: {sorted(OBJETIVOS_VALIDOS)}"

    return True, ""


# ── Helpers internos ──────────────────────────────────────────────────────────

def _validar_campos_requeridos(datos: dict) -> None:
    valido, mensaje = validar_datos_antropometricos(datos)
    if not valido:
        raise DatosInvalidosError(mensaje)
