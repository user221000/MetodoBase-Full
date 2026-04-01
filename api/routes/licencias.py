"""Rutas de activación y consulta de licencias."""
import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.constantes import PLANES_LICENCIA
from web.database.engine import get_db
from web.database.models import LicenseActivation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Licencias"])

# ── Schemas ───────────────────────────────────────────────────────────────────

_PLANES_VALIDOS = set(PLANES_LICENCIA.keys())


class ActivarLicenciaRequest(BaseModel):
    clave: str = Field(..., min_length=10, max_length=64, description="Clave de licencia")
    hardware_id: str = Field(..., min_length=8, max_length=128)
    email: str = Field(..., min_length=5, max_length=120)


class LicenciaResponse(BaseModel):
    activa: bool
    plan: str
    max_clientes: int
    multi_usuario: bool
    expira: str  # ISO date


class EstadoLicenciaResponse(BaseModel):
    activa: bool
    plan: str
    dias_restantes: int
    revocada: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/licencias/activar", response_model=LicenciaResponse)
async def activar_licencia(req: ActivarLicenciaRequest, db: Session = Depends(get_db)):
    """Activa una licencia vinculándola a un hardware_id."""
    plan = _plan_desde_clave(req.clave)
    if plan not in _PLANES_VALIDOS:
        raise HTTPException(status_code=400, detail="Clave de licencia inválida.")

    info_plan = PLANES_LICENCIA[plan]
    expira = datetime.now(timezone.utc) + timedelta(days=365)

    # Check if already activated
    existing = db.query(LicenseActivation).filter_by(hardware_id=req.hardware_id).first()
    if existing:
        # Update existing activation
        existing.clave_hash = hashlib.sha256(req.clave.encode()).hexdigest()
        existing.email = req.email
        existing.plan = plan
        existing.activa = True
        existing.revocada = False
        existing.expira = expira
    else:
        activation = LicenseActivation(
            hardware_id=req.hardware_id,
            clave_hash=hashlib.sha256(req.clave.encode()).hexdigest(),
            email=req.email,
            plan=plan,
            activa=True,
            revocada=False,
            expira=expira,
        )
        db.add(activation)

    db.flush()
    logger.info("Licencia activada plan=%s email=%s", plan, req.email)

    return LicenciaResponse(
        activa=True,
        plan=plan,
        max_clientes=info_plan["max_clientes"],
        multi_usuario=info_plan["multi_usuario"],
        expira=expira.date().isoformat(),
    )


@router.get("/licencias/estado/{hardware_id}", response_model=EstadoLicenciaResponse)
async def estado_licencia(hardware_id: str, db: Session = Depends(get_db)):
    """Consulta el estado de una licencia por hardware_id."""
    reg = db.query(LicenseActivation).filter_by(hardware_id=hardware_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Licencia no encontrada.")

    dias = max(0, (reg.expira - datetime.now(timezone.utc)).days)

    return EstadoLicenciaResponse(
        activa=reg.activa and dias > 0 and not reg.revocada,
        plan=reg.plan,
        dias_restantes=dias,
        revocada=reg.revocada,
    )


# ── Helpers internos ──────────────────────────────────────────────────────────

def _plan_desde_clave(clave: str) -> str:
    """Decodifica el plan desde el prefijo de la clave.

    Prefijos: STR → starter, PRO → profesional, CLN → clinica.
    """
    prefijo = clave[:3].upper()
    mapping = {"STR": "standard", "PRO": "gym_comercial", "CLN": "clinica"}
    return mapping.get(prefijo, "desconocido")
