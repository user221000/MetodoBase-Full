"""
web/routes/gym_profile.py — Perfil del gimnasio: datos, logo y branding.

Endpoints:
    GET  /api/gym/profile       — Obtener perfil del gym autenticado
    PUT  /api/gym/profile       — Actualizar perfil del gym
    POST /api/gym/logo          — Subir logo del gym (imagen)
"""
import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from web.auth_deps import get_usuario_actual, get_effective_gym_id
from web.database.engine import get_db
from web.database import repository as repo
from web.services.permissions import verify_permission
from web.routes._utils import get_gym_id
from web.constants import UPLOAD_ALLOWED_IMAGE_EXTENSIONS, UPLOAD_MAX_LOGO_SIZE_BYTES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/gym", tags=["GymProfile"])

# Directorio para logos subidos
_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads" / "logos"
_ALLOWED_EXTENSIONS = UPLOAD_ALLOWED_IMAGE_EXTENSIONS
_MAX_LOGO_SIZE = UPLOAD_MAX_LOGO_SIZE_BYTES


class GymProfileUpdate(BaseModel):
    nombre_negocio: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=50)
    direccion: Optional[str] = Field(None, max_length=500)
    ciudad: Optional[str] = Field(None, max_length=150)
    estado: Optional[str] = Field(None, max_length=100)
    pais: Optional[str] = Field(None, max_length=100)
    color_primario: Optional[str] = Field(None, max_length=7)
    color_secundario: Optional[str] = Field(None, max_length=7)
    sitio_web: Optional[str] = Field(None, max_length=500)
    rfc: Optional[str] = Field(None, max_length=20)
    instagram: Optional[str] = Field(None, max_length=255)
    facebook: Optional[str] = Field(None, max_length=255)
    tiktok: Optional[str] = Field(None, max_length=255)


@router.get("/profile", summary="Obtener perfil del gym")
def obtener_perfil(
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_usuario_actual),
):
    verify_permission(usuario, "read", "gym_profile")
    gym_id = get_gym_id(usuario)
    profile = repo.obtener_gym_profile(db, gym_id)
    if not profile:
        # Auto-crear perfil vacío
        profile = repo.crear_gym_profile(db, gym_id)
    return profile


@router.put("/profile", summary="Actualizar perfil del gym")
def actualizar_perfil(
    data: GymProfileUpdate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_usuario_actual),
):
    verify_permission(usuario, "update", "gym_profile")
    gym_id = get_gym_id(usuario)
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(400, "No hay campos para actualizar")
    profile = repo.actualizar_gym_profile(db, gym_id, update_dict)
    return {"success": True, "profile": profile}


@router.post("/logo", summary="Subir logo del gym")
async def subir_logo(
    file: UploadFile = File(..., description="Imagen del logo (PNG/JPG/WebP, máx 2MB)"),
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_usuario_actual),
):
    verify_permission(usuario, "update", "gym_profile")
    gym_id = get_gym_id(usuario)

    # Validar extensión
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Formato no permitido. Use: {', '.join(_ALLOWED_EXTENSIONS)}")

    # Leer y validar tamaño
    content = await file.read()
    if len(content) > _MAX_LOGO_SIZE:
        raise HTTPException(400, "El logo no debe exceder 2 MB")

    # Validate file content matches extension (prevent disguised uploads)
    _MAGIC_BYTES = {
        b'\x89PNG': {".png"},
        b'\xff\xd8\xff': {".jpg", ".jpeg"},
        b'RIFF': {".webp"},  # WebP starts with RIFF
    }
    ext_valid = False
    for magic, valid_exts in _MAGIC_BYTES.items():
        if content[:len(magic)] == magic and ext in valid_exts:
            ext_valid = True
            break
    if not ext_valid:
        raise HTTPException(400, "El contenido del archivo no coincide con la extensión")

    # Guardar archivo con nombre único
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{gym_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = _UPLOAD_DIR / filename
    filepath.write_bytes(content)

    # Eliminar logo anterior si existe
    profile = repo.obtener_gym_profile(db, gym_id)
    if profile and profile.get("logo_url"):
        old_relative = profile["logo_url"].removeprefix("/static/")
        old_path = Path(__file__).resolve().parent.parent / "static" / old_relative
        # Prevent path traversal: ensure old_path is within _UPLOAD_DIR
        try:
            old_path = old_path.resolve()
            if old_path.is_relative_to(_UPLOAD_DIR.resolve()) and old_path.exists() and old_path != filepath.resolve():
                old_path.unlink()
        except (OSError, ValueError):
            pass

    # Actualizar URL en DB
    logo_url = f"/static/uploads/logos/{filename}"
    repo.actualizar_gym_profile(db, gym_id, {"logo_url": logo_url})

    logger.info("Logo subido para gym %s: %s", gym_id, logo_url)
    return {"success": True, "logo_url": logo_url}


# ── Planes de suscripción (precios configurables) ────────────────────────────

class PlanSuscripcionUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    precio: Optional[float] = Field(None, ge=0)
    moneda: Optional[str] = Field(None, max_length=10)
    activo: Optional[bool] = None


@router.get("/planes-suscripcion", summary="Listar planes de suscripción del gym")
def listar_planes(
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_usuario_actual),
):
    verify_permission(usuario, "read", "gym_profile")
    gym_id = get_gym_id(usuario)
    planes = repo.listar_planes_suscripcion(db, gym_id)
    return {"planes": planes}


@router.put("/planes-suscripcion/{plan_id}", summary="Actualizar precio de un plan")
def actualizar_plan(
    plan_id: int,
    data: PlanSuscripcionUpdate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_usuario_actual),
):
    verify_permission(usuario, "update", "gym_profile")
    gym_id = get_gym_id(usuario)
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(400, "No hay campos para actualizar")
    result = repo.actualizar_plan_suscripcion(db, gym_id, plan_id, update_dict)
    if not result:
        raise HTTPException(404, "Plan no encontrado")
    return {"success": True, "plan": result}
