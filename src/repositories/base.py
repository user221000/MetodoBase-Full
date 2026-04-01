"""
src/repositories/base.py — Interfaces base y tipos para Repository Pattern.

Define contratos que todas las implementaciones de repository deben seguir.
Permite intercambiar backend de BD sin cambiar código cliente.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
import logging

logger = logging.getLogger(__name__)


# ── Excepciones ─────────────────────────────────────────────────────────────

class RepositoryError(Exception):
    """Error base de repository."""
    pass


class EntityNotFoundError(RepositoryError):
    """Entidad no encontrada."""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} con id '{entity_id}' no encontrado")


class DuplicateEntityError(RepositoryError):
    """Entidad ya existe."""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} con id '{entity_id}' ya existe")


class SyncError(RepositoryError):
    """Error de sincronización entre BDs."""
    def __init__(self, message: str, source: str, target: str, entity_id: str = None):
        self.source = source
        self.target = target
        self.entity_id = entity_id
        super().__init__(f"Sync error ({source} → {target}): {message}")


# ── Data Transfer Objects ───────────────────────────────────────────────────

@dataclass
class ClienteDTO:
    """
    DTO para transferir datos de cliente entre capas.
    
    Independiente de la implementación de BD (legacy o SA).
    """
    id_cliente: str
    nombre: str
    gym_id: Optional[str] = None  # Multi-tenant
    
    # Contacto
    telefono: Optional[str] = None
    email: Optional[str] = None
    
    # Antropométricos
    edad: Optional[int] = None
    sexo: Optional[str] = None  # 'M', 'F', 'Otro'
    peso_kg: Optional[float] = None
    estatura_cm: Optional[float] = None
    grasa_corporal_pct: Optional[float] = None
    masa_magra_kg: Optional[float] = None
    
    # Fitness
    nivel_actividad: Optional[str] = None
    objetivo: Optional[str] = None
    plantilla_tipo: str = "general"
    
    # Metadata
    fecha_registro: Optional[datetime] = None
    ultimo_plan: Optional[datetime] = None
    total_planes_generados: int = 0
    activo: bool = True
    notas: Optional[str] = None
    
    # PII cifrado (opcional)
    nombre_enc: Optional[str] = None
    telefono_enc: Optional[str] = None
    email_enc: Optional[str] = None
    notas_enc: Optional[str] = None
    datos_cifrados: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClienteDTO":
        """Crea instancia desde diccionario."""
        # Filtrar solo campos válidos
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class PlanDTO:
    """DTO para transferir datos de plan entre capas."""
    id: Optional[int] = None
    id_cliente: str = ""
    gym_id: Optional[str] = None
    
    # Fechas
    fecha_generacion: Optional[datetime] = None
    
    # Cálculos nutricionales
    tmb: Optional[float] = None
    get_total: Optional[float] = None
    kcal_objetivo: Optional[float] = None
    kcal_real: Optional[float] = None
    proteina_g: Optional[float] = None
    carbs_g: Optional[float] = None
    grasa_g: Optional[float] = None
    
    # Configuración
    objetivo: Optional[str] = None
    nivel_actividad: Optional[str] = None
    plantilla_tipo: str = "general"
    tipo_plan: str = "menu_fijo"
    
    # Resultado
    ruta_pdf: Optional[str] = None
    desviacion_maxima_pct: Optional[float] = None
    
    # Snapshot en momento de generación
    peso_en_momento: Optional[float] = None
    grasa_en_momento: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanDTO":
        """Crea instancia desde diccionario."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# ── Type Variables ──────────────────────────────────────────────────────────

T = TypeVar('T')  # Entity type
ID = TypeVar('ID')  # ID type


# ── Interface Base ──────────────────────────────────────────────────────────

class BaseRepository(ABC, Generic[T, ID]):
    """
    Interface base para todos los repositories.
    
    Implementa patrón Repository con soporte para:
    - CRUD básico
    - Búsqueda por criterios
    - Paginación
    - Multi-tenant (gym_id)
    """
    
    @abstractmethod
    def get_by_id(self, entity_id: ID, gym_id: Optional[str] = None) -> Optional[T]:
        """Obtiene entidad por ID."""
        pass
    
    @abstractmethod
    def get_all(
        self,
        gym_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[T]:
        """Lista entidades con paginación y filtros."""
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """Guarda entidad (create o update)."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: ID, gym_id: Optional[str] = None) -> bool:
        """Elimina entidad (soft delete preferido)."""
        pass
    
    @abstractmethod
    def exists(self, entity_id: ID, gym_id: Optional[str] = None) -> bool:
        """Verifica si entidad existe."""
        pass
    
    @abstractmethod
    def count(
        self,
        gym_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Cuenta entidades."""
        pass


# ── Sync Tracking ───────────────────────────────────────────────────────────

@dataclass
class SyncResult:
    """Resultado de operación de sincronización."""
    success: bool
    source: str
    target: str
    entity_type: str
    entity_id: str
    operation: str  # 'create', 'update', 'delete'
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"SyncResult({status} {self.operation} {self.entity_type}:{self.entity_id})"


class SyncTracker:
    """Rastrea operaciones de sincronización para debugging y auditoría."""
    
    def __init__(self, max_history: int = 1000):
        self._history: List[SyncResult] = []
        self._max_history = max_history
        self._error_count = 0
        self._success_count = 0
    
    def record(self, result: SyncResult) -> None:
        """Registra resultado de sync."""
        self._history.append(result)
        if result.success:
            self._success_count += 1
        else:
            self._error_count += 1
            logger.warning("Sync error: %s", result)
        
        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
    
    @property
    def error_rate(self) -> float:
        """Tasa de error (0.0 - 1.0)."""
        total = self._success_count + self._error_count
        if total == 0:
            return 0.0
        return self._error_count / total
    
    @property
    def recent_errors(self) -> List[SyncResult]:
        """Últimos errores de sync."""
        return [r for r in self._history[-100:] if not r.success]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de sync."""
        return {
            "total_operations": self._success_count + self._error_count,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "error_rate": self.error_rate,
            "recent_errors": len(self.recent_errors),
        }


# Singleton tracker
_sync_tracker: Optional[SyncTracker] = None


def get_sync_tracker() -> SyncTracker:
    """Obtiene el tracker singleton."""
    global _sync_tracker
    if _sync_tracker is None:
        _sync_tracker = SyncTracker()
    return _sync_tracker
