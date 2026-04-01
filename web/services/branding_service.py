"""Servicio para cargar branding dinámico per-gym desde la base de datos."""
from sqlalchemy.orm import Session
from web.database.models import GymBranding


def get_gym_branding(db: Session, gym_id: str) -> dict:
    """Retorna branding del gym como dict. Usa defaults si no existe."""
    row = db.query(GymBranding).filter(GymBranding.gym_id == gym_id).first()
    if not row:
        return {
            "nombre_gym": "",
            "nombre_corto": "Método Base",
            "tagline": "",
            "contacto": {"telefono": "", "email": "", "whatsapp": "",
                         "direccion_linea1": "", "direccion_linea2": "",
                         "direccion_linea3": ""},
            "redes_sociales": {"instagram": "", "facebook": "", "tiktok": ""},
            "cuota_mensual": 0.0,
            "color_primario": "#FFEB3B",
        }
    return {
        "nombre_gym": row.nombre_gym,
        "nombre_corto": row.nombre_corto,
        "tagline": row.tagline,
        "contacto": {
            "telefono": row.telefono,
            "email": row.email,
            "whatsapp": row.whatsapp,
            "direccion_linea1": row.direccion_linea1,
            "direccion_linea2": row.direccion_linea2,
            "direccion_linea3": row.direccion_linea3,
        },
        "redes_sociales": {
            "instagram": row.instagram,
            "facebook": row.facebook,
            "tiktok": row.tiktok,
        },
        "cuota_mensual": row.cuota_mensual,
        "color_primario": row.color_primario,
    }
