"""
config/feature_flags.py — Feature flags para migración de BD y funcionalidades.

Control centralizado de características en desarrollo o migración.
Permite activar/desactivar funcionalidades sin deploy.

Uso:
    from config.feature_flags import get_flag, set_flag, DBMigrationFlags
    
    if get_flag("use_sa_for_read"):
        # usar SQLAlchemy
    else:
        # usar legacy

IMPORTANTE: En producción, estos flags deben persistirse en BD o config externo.
"""
import os
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class DBMigrationFlags:
    """
    Flags de control para migración de base de datos dual.
    
    Fases de migración:
    - FASE 1 (default): Legacy es primary, SA es secondary
    - FASE 2 (dual_write): Escrituras van a ambas BDs
    - FASE 3 (sa_primary): SA es primary, legacy es shadow
    - FASE 4 (legacy_deprecated): Solo SA, legacy archivado
    """
    
    # FASE 2: Leer desde SA en lugar de legacy
    use_sa_for_read: bool = False
    
    # FASE 2: Escribir a ambas BDs simultáneamente
    dual_write_enabled: bool = False
    
    # FASE 3: SA es la fuente primaria de verdad
    sa_is_primary: bool = False
    
    # FASE 4: Legacy está deprecado (solo lectura para rollback)
    legacy_deprecated: bool = False
    
    # FASE 3: Shadow write a legacy (para rollback capability)
    shadow_write_legacy: bool = True
    
    # Modo de depuración: log todas las operaciones de sync
    debug_sync_operations: bool = False
    
    # Timeout para operaciones de sync (segundos)
    sync_timeout_seconds: int = 30
    
    # Máximo de reintentos en caso de fallo de sync
    max_sync_retries: int = 3
    
    # Batch size para migración masiva
    migration_batch_size: int = 100
    
    @classmethod
    def from_env(cls) -> "DBMigrationFlags":
        """Carga flags desde variables de entorno.
        
        Si DB_MIGRATION_PHASE está definido, usa el preset de esa fase.
        Si no, carga flags individuales para control granular.
        """
        phase_override = os.getenv("DB_MIGRATION_PHASE", "")
        if phase_override:
            try:
                phase = int(phase_override)
            except ValueError:
                logger.warning("[DB] Invalid DB_MIGRATION_PHASE=%r, defaulting to 1", phase_override)
                return cls()
            logger.info("[DB] Migration phase: %d (from DB_MIGRATION_PHASE)", phase)
            if phase == 1:
                return cls()
            elif phase == 2:
                return cls(use_sa_for_read=True, dual_write_enabled=True)
            elif phase == 3:
                return cls(use_sa_for_read=True, dual_write_enabled=True,
                           sa_is_primary=True)
            elif phase == 4:
                return cls(use_sa_for_read=True, sa_is_primary=True,
                           legacy_deprecated=True, shadow_write_legacy=False)
            else:
                logger.warning("[DB] Unknown migration phase %d, defaulting to 1", phase)
                return cls()
        
        # Individual flag control
        instance = cls(
            use_sa_for_read=os.getenv("DB_USE_SA_READ", "").lower() == "true",
            dual_write_enabled=os.getenv("DB_DUAL_WRITE", "").lower() == "true",
            sa_is_primary=os.getenv("DB_SA_PRIMARY", "").lower() == "true",
            legacy_deprecated=os.getenv("DB_LEGACY_DEPRECATED", "").lower() == "true",
            shadow_write_legacy=os.getenv("DB_SHADOW_WRITE", "true").lower() == "true",
            debug_sync_operations=os.getenv("DB_DEBUG_SYNC", "").lower() == "true",
            sync_timeout_seconds=int(os.getenv("DB_SYNC_TIMEOUT", "30")),
            max_sync_retries=int(os.getenv("DB_SYNC_RETRIES", "3")),
            migration_batch_size=int(os.getenv("DB_MIGRATION_BATCH", "100")),
        )
        
        # Warn if running below phase 3 in production
        from config.settings import get_settings as _gs
        prod = _gs().is_production
        if prod and not instance.sa_is_primary:
            logger.warning(
                "[DB] Production running below phase 3 — legacy DB is still primary. "
                "Set DB_MIGRATION_PHASE=4 for production (SQLAlchemy-only)."
            )
        
        return instance
    
    def current_phase(self) -> str:
        """Retorna la fase actual de migración."""
        if self.legacy_deprecated:
            return "FASE_4_DEPRECATED"
        if self.sa_is_primary:
            return "FASE_3_SA_PRIMARY"
        if self.dual_write_enabled or self.use_sa_for_read:
            return "FASE_2_DUAL_WRITE"
        return "FASE_1_LEGACY_PRIMARY"
    
    def should_read_from_sa(self) -> bool:
        """Determina si las lecturas deben ir a SA."""
        return self.use_sa_for_read or self.sa_is_primary or self.legacy_deprecated
    
    def should_write_to_legacy(self) -> bool:
        """Determina si las escrituras deben ir a legacy."""
        if self.legacy_deprecated:
            return False
        if self.sa_is_primary:
            return self.shadow_write_legacy
        return True  # Fase 1 y 2: siempre escribir a legacy
    
    def should_write_to_sa(self) -> bool:
        """Determina si las escrituras deben ir a SA."""
        return self.dual_write_enabled or self.sa_is_primary or self.legacy_deprecated


# ── Singleton global ────────────────────────────────────────────────────────

_flags: Optional[DBMigrationFlags] = None


def get_db_migration_flags() -> DBMigrationFlags:
    """Obtiene la instancia singleton de flags de migración."""
    global _flags
    if _flags is None:
        _flags = DBMigrationFlags.from_env()
        logger.info("[FLAGS] DB Migration phase: %s", _flags.current_phase())
    return _flags


def reset_flags() -> None:
    """Reset flags (para testing)."""
    global _flags
    _flags = None


def set_flag(name: str, value: Any) -> None:
    """Establece un flag dinámicamente (para testing/admin)."""
    flags = get_db_migration_flags()
    if hasattr(flags, name):
        setattr(flags, name, value)
        logger.info("[FLAGS] Set %s = %s (phase: %s)", name, value, flags.current_phase())
    else:
        raise ValueError(f"Unknown flag: {name}")


def get_flag(name: str) -> Any:
    """Obtiene el valor de un flag."""
    flags = get_db_migration_flags()
    if hasattr(flags, name):
        return getattr(flags, name)
    raise ValueError(f"Unknown flag: {name}")


# ── Feature flags generales (no DB) ─────────────────────────────────────────

@dataclass
class FeatureFlags:
    """Feature flags para funcionalidades de la aplicación."""
    
    # PDF con opciones múltiples
    pdf_multi_options: bool = True
    
    # Dashboard con gráficos avanzados
    dashboard_charts: bool = True
    
    # Exportación a Excel
    export_excel: bool = True
    
    # Notificaciones push (web)
    push_notifications: bool = False
    
    # Multi-idioma
    i18n_enabled: bool = False
    
    # Dark mode (desktop)
    dark_mode_default: bool = True
    
    # Stripe test mode
    stripe_test_mode: bool = True
    
    @classmethod
    def from_env(cls) -> "FeatureFlags":
        """Carga flags desde variables de entorno."""
        return cls(
            pdf_multi_options=os.getenv("FF_PDF_MULTI", "true").lower() == "true",
            dashboard_charts=os.getenv("FF_DASHBOARD_CHARTS", "true").lower() == "true",
            export_excel=os.getenv("FF_EXPORT_EXCEL", "true").lower() == "true",
            push_notifications=os.getenv("FF_PUSH_NOTIF", "false").lower() == "true",
            i18n_enabled=os.getenv("FF_I18N", "false").lower() == "true",
            dark_mode_default=os.getenv("FF_DARK_MODE", "true").lower() == "true",
            stripe_test_mode=os.getenv("STRIPE_TEST_MODE", "true").lower() == "true",
        )


_feature_flags: Optional[FeatureFlags] = None


# Known feature flag names for strict validation
KNOWN_FEATURE_FLAGS: frozenset = frozenset(
    f.name for f in __import__("dataclasses").fields(FeatureFlags)
)


def get_feature_flags() -> FeatureFlags:
    """Obtiene la instancia singleton de feature flags."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags.from_env()
    return _feature_flags


def is_feature_enabled(name: str) -> bool:
    """Verifica si un feature está habilitado.

    In strict mode (FEATURE_FLAGS_STRICT=true), raises ValueError for
    unknown flag names to catch typos early.
    """
    flags = get_feature_flags()
    if hasattr(flags, name):
        return bool(getattr(flags, name))
    # Strict mode: raise on unknown flags
    from config.settings import get_settings
    if get_settings().FEATURE_FLAGS_STRICT:
        raise ValueError(
            f"Unknown feature flag: {name!r}. "
            f"Known flags: {sorted(KNOWN_FEATURE_FLAGS)}"
        )
    return False


# ── DB Migration Flags Singleton ────────────────────────────────────────────

_migration_flags: Optional[DBMigrationFlags] = None


def get_migration_flags() -> DBMigrationFlags:
    """Obtiene la instancia singleton de flags de migración de BD."""
    global _migration_flags
    if _migration_flags is None:
        _migration_flags = DBMigrationFlags.from_env()
    return _migration_flags


def reset_migration_flags() -> None:
    """Resetea los flags de migración (útil para testing)."""
    global _migration_flags
    _migration_flags = None
