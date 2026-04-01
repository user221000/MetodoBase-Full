"""
web/repositories/gym_license_repository.py — Repository for GymLicense

Manages persistent licenses in database (replaces in-memory license system).

Usage:
    from web.repositories.gym_license_repository import create_license, get_active_license
    
    # Crear licencia al completar pago
    license = create_license(
        gym_id="abc-123",
        plan_tier="pro",
        max_clients=100,
        duration_days=365,
        payment_provider="stripe",
        payment_reference="sub_1234567890"
    )
    
    # Verificar licencia activa
    active = get_active_license(gym_id="abc-123")
    if not active:
        # Gym en trial o sin licencia
        pass
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import logging
import secrets

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from web.database.engine import get_db
from web.database.models import GymLicense


# ── License Generation ────────────────────────────────────────────────────

def generate_license_key(prefix: str = "MB") -> str:
    """
    Genera una license key única.
    
    Formato: MB-XXXX-XXXX-XXXX-XXXX
    
    Args:
        prefix: Prefijo de la licencia (default: MB)
        
    Returns:
        License key en formato MB-XXXX-XXXX-XXXX-XXXX
    """
    parts = []
    for _ in range(4):
        part = secrets.token_hex(2).upper()  # 4 caracteres hex
        parts.append(part)
    return f"{prefix}-{'-'.join(parts)}"


# ── CRUD Operations ───────────────────────────────────────────────────────

def create_license(
    gym_id: str,
    plan_tier: str,
    max_clients: int,
    duration_days: Optional[int] = None,
    payment_provider: Optional[str] = None,
    payment_reference: Optional[str] = None,
    license_key: Optional[str] = None,
    db: Optional[Session] = None,
) -> GymLicense:
    """
    Crea una nueva licencia para un gym.
    
    Args:
        gym_id: ID del gym
        plan_tier: Tier del plan ('free', 'starter', 'pro', 'enterprise')
        max_clients: Número máximo de clientes permitidos
        duration_days: Duración en días (None = sin expiración)
        payment_provider: Proveedor de pago ('stripe', 'mercadopago', 'manual')
        payment_reference: Referencia del pago (subscription_id, payment_id, etc)
        license_key: License key específica (se genera automáticamente si no se provee)
        db: Sesión SQLAlchemy
        
    Returns:
        GymLicense creada
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        # Generar license key si no se provee
        if not license_key:
            license_key = generate_license_key()
        
        # Calcular fecha de expiración
        expires_at = None
        if duration_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
        
        license = GymLicense(
            gym_id=gym_id,
            license_key=license_key,
            plan_tier=plan_tier,
            max_clients=max_clients,
            expires_at=expires_at,
            is_active=True,
            payment_provider=payment_provider,
            payment_reference=payment_reference,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        db.add(license)
        db.commit()
        db.refresh(license)
        
        return license
    
    finally:
        if should_close:
            db.close()


def get_active_license(gym_id: str, db: Optional[Session] = None) -> Optional[GymLicense]:
    """
    Obtiene la licencia activa de un gym.
    
    Una licencia es activa si:
    - is_active = True
    - expires_at es None O es futuro
    - revoked_at es None
    
    Args:
        gym_id: ID del gym
        db: Sesión SQLAlchemy
        
    Returns:
        GymLicense activa, o None si no tiene
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        now = datetime.now(timezone.utc)
        
        license = db.execute(
            select(GymLicense).where(
                and_(
                    GymLicense.gym_id == gym_id,
                    GymLicense.is_active == True,
                    GymLicense.revoked_at.is_(None),
                    # expires_at es None O es futuro
                    (GymLicense.expires_at.is_(None) | (GymLicense.expires_at > now))
                )
            ).order_by(GymLicense.created_at.desc())
        ).scalar_one_or_none()
        
        return license
    
    finally:
        if should_close:
            db.close()


def get_all_licenses(gym_id: str, db: Optional[Session] = None) -> List[GymLicense]:
    """
    Obtiene todas las licencias de un gym (activas e inactivas).
    
    Args:
        gym_id: ID del gym
        db: Sesión SQLAlchemy
        
    Returns:
        Lista de GymLicense
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        licenses = db.execute(
            select(GymLicense)
            .where(GymLicense.gym_id == gym_id)
            .order_by(GymLicense.created_at.desc())
        ).scalars().all()
        
        return list(licenses)
    
    finally:
        if should_close:
            db.close()


def revoke_license(
    license_id: str,
    db: Optional[Session] = None,
) -> Optional[GymLicense]:
    """
    Revoca una licencia (soft delete).
    
    Args:
        license_id: ID de la licencia a revocar
        db: Sesión SQLAlchemy
        
    Returns:
        GymLicense revocada, o None si no existe
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        license = db.execute(
            select(GymLicense).where(GymLicense.id == license_id)
        ).scalar_one_or_none()
        
        if not license:
            return None
        
        license.is_active = False
        license.revoked_at = datetime.now(timezone.utc)
        license.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(license)
        
        return license
    
    finally:
        if should_close:
            db.close()


def extend_license(
    license_id: str,
    additional_days: int,
    db: Optional[Session] = None,
) -> Optional[GymLicense]:
    """
    Extiende la duración de una licencia.
    
    Args:
        license_id: ID de la licencia
        additional_days: Días adicionales a agregar
        db: Sesión SQLAlchemy
        
    Returns:
        GymLicense actualizada, o None si no existe
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        license = db.execute(
            select(GymLicense).where(GymLicense.id == license_id)
        ).scalar_one_or_none()
        
        if not license:
            return None
        
        # Si no tiene expires_at, establecer desde ahora
        if not license.expires_at:
            license.expires_at = datetime.now(timezone.utc) + timedelta(days=additional_days)
        else:
            # Si ya tiene expires_at, agregar días
            license.expires_at = license.expires_at + timedelta(days=additional_days)
        
        license.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(license)
        
        return license
    
    finally:
        if should_close:
            db.close()


# ── Helpers ───────────────────────────────────────────────────────────────

def check_license_valid(gym_id: str, db: Optional[Session] = None) -> bool:
    """
    Verifica si un gym tiene licencia válida.
    
    Args:
        gym_id: ID del gym
        db: Sesión SQLAlchemy
        
    Returns:
        True si tiene licencia válida, False si no
    """
    license = get_active_license(gym_id, db)
    return license is not None


def get_max_clients_from_license(gym_id: str, db: Optional[Session] = None) -> Optional[int]:
    """
    Obtiene el límite de clientes desde la licencia activa.
    
    Args:
        gym_id: ID del gym
        db: Sesión SQLAlchemy
        
    Returns:
        max_clients de la licencia activa, o None si no tiene licencia
    """
    license = get_active_license(gym_id, db)
    return license.max_clients if license else None


def get_plan_tier(gym_id: str, db: Optional[Session] = None) -> str:
    """
    Obtiene el plan tier del gym.
    
    Args:
        gym_id: ID del gym
        db: Sesión SQLAlchemy
        
    Returns:
        Plan tier ('free', 'starter', 'pro', 'enterprise'), o 'free' si no tiene licencia
    """
    license = get_active_license(gym_id, db)
    return license.plan_tier if license else "free"


# ── Migration Helpers (Legacy → DB) ───────────────────────────────────────

def migrate_legacy_license_to_db(
    gym_id: str,
    legacy_license_data: dict,
    db: Optional[Session] = None,
) -> GymLicense:
    """
    Migra una licencia del sistema legacy (core/licencia.py in-memory) a DB.
    
    Args:
        gym_id: ID del gym
        legacy_license_data: Dict con datos de la licencia legacy
        db: Sesión SQLAlchemy
        
    Returns:
        GymLicense creada en DB
        
    Example:
        legacy_data = {
            "plan": "pro",
            "max_clientes": 100,
            "expira": "2025-12-31 23:59:59"  # string datetime
        }
        migrate_legacy_license_to_db(gym_id="abc-123", legacy_license_data=legacy_data)
    """
    # Extraer datos del legacy format
    plan_tier = legacy_license_data.get("plan", "free")
    max_clients = legacy_license_data.get("max_clientes", 50)
    expira_str = legacy_license_data.get("expira", None)
    
    # Parsear fecha de expiración
    expires_at = None
    if expira_str:
        try:
            expires_at = datetime.fromisoformat(expira_str)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse expira date '{expira_str}': {e}")
            pass
    
    return create_license(
        gym_id=gym_id,
        plan_tier=plan_tier,
        max_clients=max_clients,
        duration_days=None,  # La fecha ya está en expires_at
        payment_provider="manual",
        payment_reference="migrated_from_legacy",
        db=db,
    )
