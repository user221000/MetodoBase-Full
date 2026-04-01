"""
core/services/strangler_fig.py — Implementación del patrón Strangler Fig.

FASE 4 del plan de consolidación de BD.

El patrón Strangler Fig permite migrar gradualmente de legacy a nuevo sistema
sin downtime, redirigiendo tráfico incrementalmente.

Fases:
1. LEGACY_PRIMARY: Todo lee/escribe a legacy, shadow write a SA para validación
2. DUAL_WRITE: Escribe a ambos, lee de legacy (verificación de paridad)
3. SA_PRIMARY: Lee de SA, shadow write a legacy (rollback ready)
4. SA_ONLY: Legacy deprecated, solo SA

Cada fase es reversible excepto la final.
"""
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar

from config.feature_flags import get_migration_flags, DBMigrationFlags

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ── Enums ───────────────────────────────────────────────────────────────────

class MigrationPhase(Enum):
    """Fases de migración Strangler Fig."""
    LEGACY_PRIMARY = 1  # Legacy es fuente de verdad
    DUAL_WRITE = 2      # Escribe a ambos, verifica paridad
    SA_PRIMARY = 3      # SA es fuente de verdad
    SA_ONLY = 4         # Legacy deprecated


class DataSource(Enum):
    """Fuentes de datos."""
    LEGACY = "legacy"
    SQLALCHEMY = "sqlalchemy"
    BOTH = "both"


class Operation(Enum):
    """Tipos de operación."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


# ── Routing Decision ────────────────────────────────────────────────────────

@dataclass
class RoutingDecision:
    """Decisión de routing para una operación."""
    read_from: DataSource
    write_to: List[DataSource]
    primary_write: DataSource
    shadow_write: Optional[DataSource] = None
    verify_parity: bool = False
    
    def should_write_legacy(self) -> bool:
        return DataSource.LEGACY in self.write_to
    
    def should_write_sa(self) -> bool:
        return DataSource.SQLALCHEMY in self.write_to
    
    def is_dual_write(self) -> bool:
        return len(self.write_to) == 2


def get_routing_decision(
    operation: Operation,
    flags: Optional[DBMigrationFlags] = None,
) -> RoutingDecision:
    """
    Determina routing basado en fase actual y tipo de operación.
    
    Esta es la función central del patrón Strangler Fig.
    """
    flags = flags or get_migration_flags()
    phase = flags.current_phase()
    
    if phase == 1:  # LEGACY_PRIMARY
        return RoutingDecision(
            read_from=DataSource.LEGACY,
            write_to=[DataSource.LEGACY, DataSource.SQLALCHEMY] if flags.shadow_write_legacy else [DataSource.LEGACY],
            primary_write=DataSource.LEGACY,
            shadow_write=DataSource.SQLALCHEMY if flags.shadow_write_legacy else None,
            verify_parity=False,
        )
    
    elif phase == 2:  # DUAL_WRITE
        return RoutingDecision(
            read_from=DataSource.LEGACY,
            write_to=[DataSource.LEGACY, DataSource.SQLALCHEMY],
            primary_write=DataSource.LEGACY,
            shadow_write=None,  # Ambos son principales
            verify_parity=True,  # Verificar que ambos tengan mismos datos
        )
    
    elif phase == 3:  # SA_PRIMARY
        return RoutingDecision(
            read_from=DataSource.SQLALCHEMY,
            write_to=[DataSource.SQLALCHEMY, DataSource.LEGACY] if flags.shadow_write_legacy else [DataSource.SQLALCHEMY],
            primary_write=DataSource.SQLALCHEMY,
            shadow_write=DataSource.LEGACY if flags.shadow_write_legacy else None,
            verify_parity=False,
        )
    
    else:  # SA_ONLY (phase 4)
        return RoutingDecision(
            read_from=DataSource.SQLALCHEMY,
            write_to=[DataSource.SQLALCHEMY],
            primary_write=DataSource.SQLALCHEMY,
            shadow_write=None,
            verify_parity=False,
        )


# ── Strangler Proxy ─────────────────────────────────────────────────────────

@dataclass
class OperationResult:
    """Resultado de una operación a través del proxy."""
    success: bool
    data: Any = None
    source: DataSource = DataSource.LEGACY
    duration_ms: float = 0
    errors: List[str] = field(default_factory=list)
    parity_check: Optional[bool] = None


class StranglerProxy:
    """
    Proxy que implementa Strangler Fig pattern.
    
    Encapsula la lógica de routing y las operaciones dual-write/read.
    
    Uso:
        proxy = StranglerProxy()
        
        # Lectura
        result = proxy.read(
            legacy_fn=lambda: legacy_db.get_cliente(id),
            sa_fn=lambda: sa_db.query(Cliente).get(id),
            entity_type="cliente",
        )
        
        # Escritura
        result = proxy.write(
            legacy_fn=lambda: legacy_db.save_cliente(data),
            sa_fn=lambda: sa_db.add(cliente),
            entity_type="cliente",
            entity_id=cliente_id,
        )
    """
    
    def __init__(self, flags: Optional[DBMigrationFlags] = None):
        self._flags = flags or get_migration_flags()
        self._metrics = MigrationMetrics()
    
    @property
    def phase(self) -> int:
        """Fase actual de migración."""
        return self._flags.current_phase()
    
    @property
    def metrics(self) -> "MigrationMetrics":
        """Métricas de migración."""
        return self._metrics
    
    def read(
        self,
        legacy_fn: Callable[[], T],
        sa_fn: Callable[[], T],
        entity_type: str = "entity",
        compare_fn: Optional[Callable[[T, T], bool]] = None,
    ) -> OperationResult:
        """
        Ejecuta operación de lectura según fase actual.
        
        En fase 2 (DUAL_WRITE), lee de ambos y compara para validación.
        """
        decision = get_routing_decision(Operation.READ, self._flags)
        start = datetime.now()
        
        try:
            if decision.read_from == DataSource.LEGACY:
                data = legacy_fn()
                source = DataSource.LEGACY
            else:
                data = sa_fn()
                source = DataSource.SQLALCHEMY
            
            # En fase de verificación, comparar ambas fuentes
            parity = None
            if decision.verify_parity and compare_fn:
                try:
                    legacy_data = legacy_fn()
                    sa_data = sa_fn()
                    parity = compare_fn(legacy_data, sa_data)
                    if not parity:
                        logger.warning(
                            "Parity mismatch for %s: legacy != SA",
                            entity_type
                        )
                        self._metrics.record_parity_mismatch(entity_type)
                except Exception as e:
                    logger.error("Parity check failed: %s", e)
            
            duration = (datetime.now() - start).total_seconds() * 1000
            self._metrics.record_read(entity_type, source, duration, True)
            
            return OperationResult(
                success=True,
                data=data,
                source=source,
                duration_ms=duration,
                parity_check=parity,
            )
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            self._metrics.record_read(entity_type, source, duration, False)
            logger.error("Read failed for %s: %s", entity_type, e)
            return OperationResult(
                success=False,
                errors=[str(e)],
                duration_ms=duration,
            )
    
    def write(
        self,
        legacy_fn: Callable[[], T],
        sa_fn: Callable[[], T],
        entity_type: str = "entity",
        entity_id: str = "",
        rollback_legacy: Optional[Callable[[], None]] = None,
        rollback_sa: Optional[Callable[[], None]] = None,
    ) -> OperationResult:
        """
        Ejecuta operación de escritura según fase actual.
        
        Maneja dual-write con rollback en caso de fallo parcial.
        """
        decision = get_routing_decision(Operation.WRITE, self._flags)
        start = datetime.now()
        results = {}
        errors = []
        
        # Escribir a destinos según decision
        for target in decision.write_to:
            try:
                if target == DataSource.LEGACY:
                    results[target] = legacy_fn()
                else:
                    results[target] = sa_fn()
            except Exception as e:
                errors.append(f"{target.value}: {e}")
                logger.error("Write to %s failed for %s[%s]: %s",
                            target.value, entity_type, entity_id, e)
                
                # En dual-write, hacer rollback si tenemos función
                if decision.is_dual_write():
                    if target == DataSource.LEGACY and rollback_sa:
                        try:
                            rollback_sa()
                        except Exception as rollback_err:
                            logger.warning("Rollback failed: %s", rollback_err)
                    elif target == DataSource.SQLALCHEMY and rollback_legacy:
                        try:
                            rollback_legacy()
                        except Exception as rollback_err:
                            logger.warning("Rollback failed: %s", rollback_err)
        
        duration = (datetime.now() - start).total_seconds() * 1000
        success = len(errors) == 0
        
        self._metrics.record_write(entity_type, decision.primary_write, duration, success)
        
        # Retornar resultado del primary
        primary_result = results.get(decision.primary_write)
        
        return OperationResult(
            success=success,
            data=primary_result,
            source=decision.primary_write,
            duration_ms=duration,
            errors=errors,
        )
    
    def delete(
        self,
        legacy_fn: Callable[[], bool],
        sa_fn: Callable[[], bool],
        entity_type: str = "entity",
        entity_id: str = "",
    ) -> OperationResult:
        """Ejecuta operación de delete según fase actual."""
        decision = get_routing_decision(Operation.DELETE, self._flags)
        start = datetime.now()
        errors = []
        success_count = 0
        
        for target in decision.write_to:
            try:
                if target == DataSource.LEGACY:
                    legacy_fn()
                else:
                    sa_fn()
                success_count += 1
            except Exception as e:
                errors.append(f"{target.value}: {e}")
        
        duration = (datetime.now() - start).total_seconds() * 1000
        
        return OperationResult(
            success=len(errors) == 0,
            source=decision.primary_write,
            duration_ms=duration,
            errors=errors,
        )


# ── Migration Metrics ───────────────────────────────────────────────────────

@dataclass 
class MetricEntry:
    """Entrada de métrica individual."""
    entity_type: str
    source: DataSource
    operation: Operation
    duration_ms: float
    success: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MigrationMetrics:
    """Recolecta métricas de migración para observabilidad."""
    
    def __init__(self, max_entries: int = 10000):
        self._entries: List[MetricEntry] = []
        self._max_entries = max_entries
        self._parity_mismatches: Dict[str, int] = {}
    
    def record_read(self, entity_type: str, source: DataSource, duration_ms: float, success: bool):
        self._add_entry(MetricEntry(
            entity_type=entity_type,
            source=source,
            operation=Operation.READ,
            duration_ms=duration_ms,
            success=success,
        ))
    
    def record_write(self, entity_type: str, source: DataSource, duration_ms: float, success: bool):
        self._add_entry(MetricEntry(
            entity_type=entity_type,
            source=source,
            operation=Operation.WRITE,
            duration_ms=duration_ms,
            success=success,
        ))
    
    def record_parity_mismatch(self, entity_type: str):
        self._parity_mismatches[entity_type] = self._parity_mismatches.get(entity_type, 0) + 1
    
    def _add_entry(self, entry: MetricEntry):
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
    
    def get_stats(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Obtiene estadísticas agregadas."""
        entries = self._entries
        if since:
            entries = [e for e in entries if e.timestamp >= since]
        
        if not entries:
            return {"total": 0}
        
        total = len(entries)
        successes = sum(1 for e in entries if e.success)
        avg_duration = sum(e.duration_ms for e in entries) / total
        
        by_source = {}
        for source in DataSource:
            source_entries = [e for e in entries if e.source == source]
            if source_entries:
                by_source[source.value] = {
                    "count": len(source_entries),
                    "success_rate": sum(1 for e in source_entries if e.success) / len(source_entries),
                    "avg_duration_ms": sum(e.duration_ms for e in source_entries) / len(source_entries),
                }
        
        return {
            "total": total,
            "success_rate": successes / total if total > 0 else 0,
            "avg_duration_ms": avg_duration,
            "by_source": by_source,
            "parity_mismatches": dict(self._parity_mismatches),
        }


# ── Context Managers ────────────────────────────────────────────────────────

@contextmanager
def migration_phase(phase: int) -> Generator[None, None, None]:
    """
    Context manager para temporalmente cambiar la fase de migración.
    
    Útil para testing y rollback manual.
    
    Usage:
        with migration_phase(1):
            # Todo se ejecuta como si estuviéramos en fase 1
            result = proxy.read(...)
    """
    flags = get_migration_flags()
    original = flags.current_phase()
    
    # Temporarily set phase flags
    if phase == 1:
        flags.use_sa_for_read = False
        flags.dual_write_enabled = False
        flags.sa_is_primary = False
        flags.legacy_deprecated = False
    elif phase == 2:
        flags.use_sa_for_read = False
        flags.dual_write_enabled = True
        flags.sa_is_primary = False
        flags.legacy_deprecated = False
    elif phase == 3:
        flags.use_sa_for_read = True
        flags.dual_write_enabled = True
        flags.sa_is_primary = True
        flags.legacy_deprecated = False
    elif phase == 4:
        flags.use_sa_for_read = True
        flags.dual_write_enabled = False
        flags.sa_is_primary = True
        flags.legacy_deprecated = True
    
    try:
        yield
    finally:
        # Restore original phase
        if original == 1:
            flags.use_sa_for_read = False
            flags.dual_write_enabled = False
        elif original == 2:
            flags.use_sa_for_read = False
            flags.dual_write_enabled = True
        elif original == 3:
            flags.use_sa_for_read = True
            flags.dual_write_enabled = True
        elif original == 4:
            flags.use_sa_for_read = True
            flags.dual_write_enabled = False
            flags.legacy_deprecated = True


# ── Singleton ───────────────────────────────────────────────────────────────

_proxy: Optional[StranglerProxy] = None


def get_strangler_proxy() -> StranglerProxy:
    """Obtiene el proxy singleton."""
    global _proxy
    if _proxy is None:
        _proxy = StranglerProxy()
    return _proxy
