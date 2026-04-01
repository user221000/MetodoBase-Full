"""
web/middleware/tenant.py — Middleware para contexto de tenant en multi-tenancy.

Detecta gym_id del JWT y configura contexto para aislamiento de datos.
RLS activation happens inside get_db() which reads the ContextVar set here.
"""
from contextvars import ContextVar
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

# Context var para tenant actual (usado por RLS en PostgreSQL via get_db())
current_tenant: ContextVar[str] = ContextVar("current_tenant", default="")


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Detecta tenant desde JWT y configura contexto.
    
    Flujo:
    1. Extrae gym_id del token JWT (si existe)
    2. Almacena en contextvars (read by get_db() for RLS)
    3. Almacena en request.state para dependencies
    """
    
    def __init__(self, app, exclude_paths: list[str] | None = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health", "/health/ready", "/docs", "/redoc", "/openapi.json",
            "/web/", "/static/", "/metrics"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip para rutas públicas
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Extraer tenant del token
        tenant_id = await self._extract_tenant(request)
        
        if tenant_id:
            # Guardar en contextvars (get_db() reads this to SET LOCAL for RLS)
            token = current_tenant.set(tenant_id)
            # Guardar en request.state (para dependencies)
            request.state.tenant_id = tenant_id
            
            try:
                response = await call_next(request)
            finally:
                current_tenant.reset(token)
        else:
            request.state.tenant_id = None
            response = await call_next(request)
        
        return response
    
    async def _extract_tenant(self, request: Request) -> str | None:
        """Extrae tenant_id del JWT token."""
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        
        try:
            from web.auth import verificar_token
            token = auth_header[7:]
            payload = verificar_token(token)
            if payload and payload.get("tipo") in ("gym", "admin"):
                return payload.get("id")
            # Team members: use their gym association
            if payload and payload.get("team_gym_id"):
                return payload.get("team_gym_id")
        except Exception as e:
            logger.debug(f"Error extrayendo tenant: {e}")
        
        return None


def get_current_tenant() -> str:
    """Obtiene el tenant actual del contexto."""
    return current_tenant.get()
