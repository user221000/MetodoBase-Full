"""
Middleware para setear contexto de usuario en Sentry por cada request.

Extrae información del usuario autenticado y la propaga a Sentry
para tener trazas contextualizadas.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from web.observability.sentry_setup import set_user_context


class SentryContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware que configura el contexto de usuario en Sentry.
    
    Busca el usuario en request.state (seteado por auth middleware)
    y propaga user_id, gym_id, y role a Sentry para traces.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        user = getattr(request.state, "user", None)
        if user:
            # Soporta tanto dict como objeto con atributos
            if isinstance(user, dict):
                user_id = user.get("id", "")
                gym_id = user.get("gym_id") or user.get("team_gym_id", "")
                role = user.get("role", "unknown")
            else:
                user_id = getattr(user, "id", "")
                gym_id = getattr(user, "gym_id", None) or getattr(user, "team_gym_id", "")
                role = getattr(user, "role", "unknown")
            
            set_user_context(
                user_id=str(user_id),
                gym_id=str(gym_id) if gym_id else "",
                role=str(role),
            )
        
        return await call_next(request)
