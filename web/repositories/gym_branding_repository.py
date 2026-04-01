"""
web/repositories/gym_branding_repository.py — Repository for GymBranding

Manages per-gym branding configuration (white-labeling).

Usage:
    from web.repositories.gym_branding_repository import get_gym_branding, update_gym_branding
    
    branding = get_gym_branding(gym_id="abc-123")
    if not branding:
        branding = create_default_gym_branding(gym_id="abc-123", nombre_gym="FitnessGym Real del Valle")
    
    update_gym_branding(gym_id="abc-123", updates={
        "color_primario": "#FF5733",
        "whatsapp": "+525512345678"
    })
"""
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from web.database.engine import get_db
from web.database.models import GymBranding


# ── CRUD Operations ───────────────────────────────────────────────────────

def get_gym_branding(gym_id: str, db: Optional[Session] = None) -> Optional[GymBranding]:
    """
    Obtiene la configuración de branding de un gym.
    
    Args:
        gym_id: ID del gym
        db: Sesión SQLAlchemy
        
    Returns:
        GymBranding si existe, None si no
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        branding = db.execute(
            select(GymBranding).where(GymBranding.gym_id == gym_id)
        ).scalar_one_or_none()
        
        return branding
    
    finally:
        if should_close:
            db.close()


def create_default_gym_branding(
    gym_id: str,
    nombre_gym: str = "Método Base",
    db: Optional[Session] = None,
) -> GymBranding:
    """
    Crea configuración de branding por defecto para un gym.
    
    Args:
        gym_id: ID del gym
        nombre_gym: Nombre personalizado del gym
        db: Sesión SQLAlchemy
        
    Returns:
        GymBranding creado
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        branding = GymBranding(
            gym_id=gym_id,
            nombre_gym=nombre_gym,
            nombre_corto=nombre_gym[:100],  # Truncar si es muy largo
            tagline="Tu aliado en nutrición y fitness",
            telefono="",
            email="",
            whatsapp="",
            direccion_linea1="",
            direccion_linea2="",
            direccion_linea3="",
            instagram="",
            facebook="",
            tiktok="",
            cuota_mensual=0.0,
            logo_path="assets/logo.png",
            color_primario="#FFEB3B",  # Amarillo MetodoBase
            color_secundario="#FFD700",
        )
        
        db.add(branding)
        db.commit()
        db.refresh(branding)
        
        return branding
    
    finally:
        if should_close:
            db.close()


def update_gym_branding(
    gym_id: str,
    updates: Dict[str, Any],
    db: Optional[Session] = None,
) -> Optional[GymBranding]:
    """
    Actualiza configuración de branding de un gym.
    
    Args:
        gym_id: ID del gym
        updates: Dict con campos a actualizar
        db: Sesión SQLAlchemy
        
    Returns:
        GymBranding actualizado, o None si no existe
        
    Example:
        update_gym_branding(
            gym_id="abc-123",
            updates={
                "color_primario": "#FF5733",
                "whatsapp": "+525512345678",
                "nombre_gym": "FitnessGym Deluxe"
            }
        )
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        branding = get_gym_branding(gym_id, db)
        if not branding:
            return None
        
        # Actualizar solo campos permitidos
        allowed_fields = {
            "nombre_gym", "nombre_corto", "tagline", "telefono", "email", "whatsapp",
            "direccion_linea1", "direccion_linea2", "direccion_linea3",
            "instagram", "facebook", "tiktok", "cuota_mensual",
            "logo_path", "color_primario", "color_secundario"
        }
        
        for key, value in updates.items():
            if key in allowed_fields and hasattr(branding, key):
                setattr(branding, key, value)
        
        db.commit()
        db.refresh(branding)
        
        return branding
    
    finally:
        if should_close:
            db.close()


def get_or_create_gym_branding(
    gym_id: str,
    nombre_gym: str = "Método Base",
    db: Optional[Session] = None,
) -> GymBranding:
    """
    Obtiene branding de un gym, o crea defaults si no existe.
    
    Args:
        gym_id: ID del gym
        nombre_gym: Nombre del gym (usado si se crea)
        db: Sesión SQLAlchemy
        
    Returns:
        GymBranding (existente o recién creado)
    """
    branding = get_gym_branding(gym_id, db)
    if not branding:
        branding = create_default_gym_branding(gym_id, nombre_gym, db)
    return branding


# ── Conversion Helpers ────────────────────────────────────────────────────

def branding_to_dict(branding: GymBranding) -> Dict[str, Any]:
    """
    Convierte GymBranding model a dict (compatible con legacy branding.json format).
    
    Args:
        branding: GymBranding model instance
        
    Returns:
        Dict con estructura compatible con core/branding.py
        
    Example Output:
        {
            "nombre": "FitnessGym Real del Valle",
            "nombre_corto": "FitnessGym",
            "tagline": "Tu aliado en nutrición",
            "colores": {
                "primario": "#FFEB3B",
                "secundario": "#FFD700"
            },
            "contacto": {
                "telefono": "+525512345678",
                "email": "contacto@fitnessgym.mx",
                "whatsapp": "+525512345678",
                "direccion": {
                    "linea1": "Av. Principal 123",
                    "linea2": "Col. Centro",
                    "linea3": "Ciudad de México, CDMX 12345"
                },
                "instagram": "@fitnessgym_mx",
                "facebook": "https://facebook.com/fitnessgym.mx",
                "tiktok": "@fitnessgym_mx"
            },
            "cuota_mensual": 1200.0,
            "logo_path": "assets/logo.png"
        }
    """
    return {
        "nombre": branding.nombre_gym,
        "nombre_corto": branding.nombre_corto,
        "tagline": branding.tagline,
        "colores": {
            "primario": branding.color_primario,
            "secundario": branding.color_secundario,
        },
        "contacto": {
            "telefono": branding.telefono,
            "email": branding.email,
            "whatsapp": branding.whatsapp,
            "direccion": {
                "linea1": branding.direccion_linea1,
                "linea2": branding.direccion_linea2,
                "linea3": branding.direccion_linea3,
            },
            "instagram": branding.instagram,
            "facebook": branding.facebook,
            "tiktok": branding.tiktok,
        },
        "cuota_mensual": branding.cuota_mensual,
        "logo_path": branding.logo_path,
    }


# ── Migration Helpers (JSON → DB) ─────────────────────────────────────────

def migrate_branding_from_json(
    gym_id: str,
    json_data: Dict[str, Any],
    db: Optional[Session] = None,
) -> GymBranding:
    """
    Migra branding desde config/branding.json (legacy) a DB.
    
    Args:
        gym_id: ID del gym
        json_data: Dict con datos del branding.json
        db: Sesión SQLAlchemy
        
    Returns:
        GymBranding creado en DB
        
    Example:
        with open("config/branding.json", "r") as f:
            legacy_branding = json.load(f)
        
        migrate_branding_from_json(gym_id="abc-123", json_data=legacy_branding)
    """
    should_close = False
    if db is None:
        db = next(get_db())
        should_close = True
    
    try:
        # Extraer datos del legacy format
        contacto = json_data.get("contacto", {})
        direccion = contacto.get("direccion", {})
        colores = json_data.get("colores", {})
        
        branding = GymBranding(
            gym_id=gym_id,
            nombre_gym=json_data.get("nombre", "Método Base"),
            nombre_corto=json_data.get("nombre_corto", "Método Base"),
            tagline=json_data.get("tagline", ""),
            telefono=contacto.get("telefono", ""),
            email=contacto.get("email", ""),
            whatsapp=contacto.get("whatsapp", ""),
            direccion_linea1=direccion.get("linea1", ""),
            direccion_linea2=direccion.get("linea2", ""),
            direccion_linea3=direccion.get("linea3", ""),
            instagram=contacto.get("instagram", ""),
            facebook=contacto.get("facebook", ""),
            tiktok=contacto.get("tiktok", ""),
            cuota_mensual=json_data.get("cuota_mensual", 0.0),
            logo_path=json_data.get("logo_path", "assets/logo.png"),
            color_primario=colores.get("primario", "#FFEB3B"),
            color_secundario=colores.get("secundario", "#FFD700"),
        )
        
        db.add(branding)
        db.commit()
        db.refresh(branding)
        
        return branding
    
    finally:
        if should_close:
            db.close()
