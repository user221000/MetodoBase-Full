"""FastAPI application factory para MetodoBase."""
import os
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from api.exceptions import MetodoBaseException
from api.routes import clientes as clientes_routes
from api.routes import stats as stats_routes
from api.routes import planes as planes_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

_BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = _BASE_DIR / "static"
PAGES_DIR = STATIC_DIR / "pages"


def create_app() -> FastAPI:
    app = FastAPI(
        title="MetodoBase API",
        description="API para gestión de planes nutricionales en gimnasios",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Por defecto solo permite localhost durante el MVP; configurable via .env
    allowed = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

    # ── Global error handlers ─────────────────────────────────────────────────
    @app.exception_handler(MetodoBaseException)
    async def _metodobase_error(request: Request, exc: MetodoBaseException):
        logging.getLogger("api").warning(
            "MetodoBaseException [%s]: %s", exc.error_code, exc.message
        )
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(Exception)
    async def _global_error(request: Request, exc: Exception):
        logging.getLogger("api").error("Unhandled: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"},
        )

    # ── Static files ──────────────────────────────────────────────────────────
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # ── API routes ────────────────────────────────────────────────────────────
    app.include_router(clientes_routes.router, prefix="/api")
    app.include_router(stats_routes.router, prefix="/api")
    app.include_router(planes_routes.router, prefix="/api")

    # ── Page routes (sirven los HTML) ─────────────────────────────────────────
    @app.get("/", response_class=FileResponse, include_in_schema=False)
    async def index():
        return FileResponse(str(PAGES_DIR / "dashboard.html"))

    @app.get("/nuevo-cliente", response_class=FileResponse, include_in_schema=False)
    async def nuevo_cliente():
        return FileResponse(str(PAGES_DIR / "nuevo-cliente.html"))

    @app.get("/generar-plan/{id_cliente}", response_class=FileResponse, include_in_schema=False)
    async def generar_plan_page(id_cliente: str):
        return FileResponse(str(PAGES_DIR / "generar-plan.html"))

    return app
