"""
Método Base — API REST (FastAPI).

Punto de entrada de la aplicación web.

Ejecución en desarrollo:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

Ejecución en producción:
    uvicorn api.main:app --workers 2 --host 0.0.0.0 --port 8000

Documentación interactiva (solo en dev):
    http://localhost:8000/docs   ← Swagger UI
    http://localhost:8000/redoc  ← ReDoc
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth_router, planes_router, clientes_router, reportes_router
from utils.logger import logger

# ── Ciclo de vida ─────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Inicializa recursos al arrancar y los libera al detener."""
    logger.info("[API] Método Base API iniciando...")
    yield
    logger.info("[API] Método Base API detenida.")


# ── App ───────────────────────────────────────────────────────────────────────

_ENV = os.environ.get("MB_ENV", "development")
_IS_DEV = _ENV == "development"

app = FastAPI(
    title="Método Base API",
    description=(
        "API REST del sistema de planes nutricionales Método Base.\n\n"
        "Permite integrar el motor nutricional con clientes web y móviles.\n\n"
        "**Autenticación:** Bearer JWT  \n"
        "**Roles:** `usuario` · `gym` · `admin`"
    ),
    version="1.0.0",
    docs_url="/docs" if _IS_DEV else None,     # Swagger solo en dev
    redoc_url="/redoc" if _IS_DEV else None,   # ReDoc solo en dev
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

_ORIGINS_DEV = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"]
_ORIGINS_PROD = os.environ.get("MB_CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGINS_DEV if _IS_DEV else [o.strip() for o in _ORIGINS_PROD if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────

_PREFIX = "/api/v1"
app.include_router(auth_router,     prefix=_PREFIX)
app.include_router(planes_router,   prefix=_PREFIX)
app.include_router(clientes_router, prefix=_PREFIX)
app.include_router(reportes_router, prefix=_PREFIX)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Sistema"], summary="Estado de la API")
def health() -> dict:
    """Verifica que la API está en línea."""
    return {"status": "ok", "version": app.version, "env": _ENV}
