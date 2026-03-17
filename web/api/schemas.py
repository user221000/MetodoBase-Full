"""Modelos Pydantic para la API REST de MetodoBase Web."""
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# SCHEMAS DE CLIENTE
# ============================================================================

class ClienteCreate(BaseModel):
    """Datos requeridos para crear un nuevo cliente."""
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre completo del cliente")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    email: Optional[str] = Field(None, max_length=100, description="Correo electrónico")
    edad: int = Field(..., ge=14, le=80, description="Edad (14-80 años)")
    sexo: Optional[str] = Field(None, description="Sexo: M, F, Otro")
    peso_kg: float = Field(..., gt=30, description="Peso en kilogramos (>30 kg)")
    estatura_cm: float = Field(..., ge=100, le=230, description="Estatura en centímetros (100-230 cm)")
    grasa_corporal_pct: float = Field(..., ge=3, le=60, description="Porcentaje de grasa corporal (3-60%)")
    nivel_actividad: str = Field(..., description="Nivel de actividad: nula, leve, moderada, intensa")
    objetivo: str = Field(..., description="Objetivo: deficit, mantenimiento, superavit")
    notas: Optional[str] = Field(None, max_length=500, description="Notas adicionales")


class ClienteUpdate(BaseModel):
    """Datos opcionales para actualizar un cliente."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    edad: Optional[int] = Field(None, ge=14, le=80)
    peso_kg: Optional[float] = Field(None, gt=30)
    estatura_cm: Optional[float] = Field(None, ge=100, le=230)
    grasa_corporal_pct: Optional[float] = Field(None, ge=3, le=60)
    nivel_actividad: Optional[str] = None
    objetivo: Optional[str] = None
    notas: Optional[str] = Field(None, max_length=500)


class ClienteResponse(BaseModel):
    """Respuesta de datos del cliente."""
    id_cliente: str
    nombre: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    edad: Optional[int] = None
    peso_kg: Optional[float] = None
    estatura_cm: Optional[float] = None
    grasa_corporal_pct: Optional[float] = None
    nivel_actividad: Optional[str] = None
    objetivo: Optional[str] = None
    plantilla_tipo: Optional[str] = None
    fecha_registro: Optional[str] = None
    ultimo_plan: Optional[str] = None
    total_planes_generados: Optional[int] = 0
    activo: Optional[bool] = True


# ============================================================================
# SCHEMAS DE PLAN
# ============================================================================

class PlanRequest(BaseModel):
    """Datos para generar un plan nutricional."""
    id_cliente: str = Field(..., description="ID del cliente")
    peso_kg: Optional[float] = Field(None, gt=30, description="Peso actual (opcional, usa datos del cliente si no se provee)")
    grasa_corporal_pct: Optional[float] = Field(None, ge=3, le=60, description="Grasa corporal actual")
    nivel_actividad: Optional[str] = Field(None, description="Nivel de actividad (opcional)")
    objetivo: Optional[str] = Field(None, description="Objetivo nutricional (opcional)")


class PlanResponse(BaseModel):
    """Respuesta con el plan generado."""
    success: bool
    id_cliente: str
    pdf_url: Optional[str] = None
    macros: Optional[dict] = None
    mensaje: Optional[str] = None


# ============================================================================
# SCHEMAS DE ESTADÍSTICAS
# ============================================================================

class EstadisticasResponse(BaseModel):
    """Respuesta de estadísticas del gym."""
    total_clientes: int = 0
    clientes_nuevos: int = 0
    clientes_activos: int = 0
    planes_periodo: int = 0
    promedio_kcal: float = 0.0
    objetivos: dict = {}
    top_clientes: list = []
    renovaciones: int = 0
    tasa_retencion: float = 0.0
    planes_por_tipo: dict = {}
