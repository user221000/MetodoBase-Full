"""
MetodoBase Web App — Punto de entrada FastAPI.
Corre en http://localhost:8000
NO modifica ni afecta la app desktop PySide6 existente.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path para poder importar core/, src/, config/
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from web.api.routes import router

# ============================================================================
# INICIALIZACIÓN DE LA APP
# ============================================================================

app = FastAPI(
    title="MetodoBase Web",
    version="2.0.0",
    description="API REST y frontend web para MetodoBase Gym Management",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS para desarrollo local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ARCHIVOS ESTÁTICOS Y TEMPLATES
# ============================================================================

_web_dir = Path(__file__).parent

app.mount(
    "/static",
    StaticFiles(directory=str(_web_dir / "static")),
    name="static",
)

templates = Jinja2Templates(directory=str(_web_dir / "templates"))

# ============================================================================
# INCLUIR RUTAS DE LA API
# ============================================================================

app.include_router(router)

# ============================================================================
# RUTAS DE PÁGINAS HTML
# ============================================================================


@app.get("/", response_class=HTMLResponse, tags=["pages"])
async def dashboard(request: Request):
    """Página principal: Dashboard con KPIs."""
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/clientes", response_class=HTMLResponse, tags=["pages"])
async def pagina_clientes(request: Request):
    """Página de gestión de clientes."""
    return templates.TemplateResponse(request, "clientes.html")


@app.get("/generar-plan", response_class=HTMLResponse, tags=["pages"])
async def pagina_generar_plan(request: Request):
    """Página para generar un plan nutricional."""
    return templates.TemplateResponse(request, "generar-plan.html")


# ============================================================================
# HEALTH CHECK
# ============================================================================


@app.get("/health", tags=["health"])
async def health_check():
    """Verifica que el servidor esté corriendo correctamente."""
    return {"status": "ok", "app": "MetodoBase Web", "version": "2.0.0"}


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    print("🚀 MetodoBase Web App iniciando...")
    print("📍 URL: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    uvicorn.run(
        "web.main_web:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(_web_dir)],
    )
