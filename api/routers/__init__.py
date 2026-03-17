"""
Routers — re-exportaciones.
"""
from api.routers.auth import router as auth_router
from api.routers.planes import router as planes_router
from api.routers.clientes import router as clientes_router
from api.routers.reportes import router as reportes_router

__all__ = ["auth_router", "planes_router", "clientes_router", "reportes_router"]
