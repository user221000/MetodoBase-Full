"""
web/repositories/gym_settings_repository.py — Repository for GymSettings

Manages gym-specific operational settings (trial config, timezone, locale).

Usage:
    from web.repositories.gym_settings_repository import get_gym_settings, update_gym_settings
    
    settings = get_gym_settings(gym_id="abc-123")
    if not settings:
        settings = create_default_gym_settings(gym_id="abc-123")
    
    update_gym_settings(gym_id="abc-123", trial_days=30, timezone="America/New_York")
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from web.database.engine import get_db
from web.database.models import GymSettings


# ── CRUD Operations ───────────────────────────────────────────────────────

def get_gym_settings(gym_id: str, db: Optional[Session] = None) -> Optional[GymSettings]:
    """
    Obtiene la configuración de un gym.
    
    Args:
        gym_id: ID del gym (usuario tipo='gym')
        db: Sesión SQLAlchemy (opcional, se crea si no se provee)
        
    Returns:
        GymSettings si existe, None si no
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        settings = db.execute(
            select(GymSettings).where(GymSettings.gym_id == gym_id)
        ).scalar_one_or_none()
        
        return settings
    
    finally:
        if should_close:
            db.close()


def create_default_gym_settings(
    gym_id: str,
    trial_days: int = 14,
    trial_max_clients: int = 50,
    strict_mode: bool = True,
    tz_name: str = "America/Mexico_City",
    locale: str = "es_MX",
    db: Optional[Session] = None,
) -> GymSettings:
    """
    Crea configuración por defecto para un gym.
    
    Se debe llamar automáticamente al registrar un nuevo gym.
    
    Args:
        gym_id: ID del gym
        trial_days: Días de trial (default: 14)
        trial_max_clients: Max clientes en trial (default: 50)
        strict_mode: Si el gym blockea features al exceder límites (default: True)
        timezone: Timezone del gym (default: America/Mexico_City)
        locale: Locale para i18n (default: es_MX)
        db: Sesión SQLAlchemy
        
    Returns:
        GymSettings creado
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        settings = GymSettings(
            gym_id=gym_id,
            trial_days=trial_days,
            trial_max_clients=trial_max_clients,
            strict_mode=strict_mode,
            timezone=tz_name,
            locale=locale,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        
        db.add(settings)
        db.commit()
        db.refresh(settings)
        
        return settings
    
    finally:
        if should_close:
            db.close()


def update_gym_settings(
    gym_id: str,
    updates: Dict[str, Any],
    db: Optional[Session] = None,
) -> Optional[GymSettings]:
    """
    Actualiza configuración de un gym.
    
    Args:
        gym_id: ID del gym
        updates: Dict con campos a actualizar (ej: {"trial_days": 30, "timezone": "UTC"})
        db: Sesión SQLAlchemy
        
    Returns:
        GymSettings actualizado, o None si no existe
        
    Example:
        update_gym_settings(
            gym_id="abc-123",
            updates={"trial_days": 30, "timezone": "America/New_York"}
        )
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        settings = get_gym_settings(gym_id, db)
        if not settings:
            return None
        
        # Actualizar solo campos permitidos
        allowed_fields = {
            "trial_days", "trial_max_clients", "strict_mode", "timezone", "locale"
        }
        
        for key, value in updates.items():
            if key in allowed_fields and hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.updated_at = datetime.now(tz=timezone.utc)
        
        db.commit()
        db.refresh(settings)
        
        return settings
    
    finally:
        if should_close:
            db.close()


def get_or_create_gym_settings(gym_id: str, db: Optional[Session] = None) -> GymSettings:
    """
    Obtiene settings de un gym, o crea defaults si no existen.
    
    Args:
        gym_id: ID del gym
        db: Sesión SQLAlchemy
        
    Returns:
        GymSettings (existente o recién creado)
    """
    settings = get_gym_settings(gym_id, db)
    if not settings:
        settings = create_default_gym_settings(gym_id=gym_id, db=db)
    return settings


# ── Helpers ───────────────────────────────────────────────────────────────

def is_trial_expired(gym_id: str, db: Optional[Session] = None) -> bool:
    """
    Verifica si el trial de un gym ha expirado.
    
    Requiere comparar created_at del gym con trial_days del settings.
    Para implementación completa, necesita acceso a tabla Usuario.
    
    Args:
        gym_id: ID del gym
        db: Sesión SQLAlchemy
        
    Returns:
        True si trial expirado, False si aún válido
    """
    # TODO: Implementar lógica comparando Usuario.created_at con GymSettings.trial_days
    # Por ahora retorna False (asumir trial válido)
    return False


def get_max_clients_for_gym(gym_id: str, db: Optional[Session] = None) -> int:
    """
    Obtiene el límite de clientes para un gym.
    
    Verifica primero si tiene licencia activa, si no, usa trial_max_clients.
    
    Args:
        gym_id: ID del gym
        db: Sesión SQLAlchemy
        
    Returns:
        Número máximo de clientes permitidos
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        # TODO: Verificar GymLicense activa primero
        # Por ahora solo retorna trial_max_clients de settings
        
        settings = get_or_create_gym_settings(gym_id, db)
        return settings.trial_max_clients
    
    finally:
        if should_close:
            db.close()
