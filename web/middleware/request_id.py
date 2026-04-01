"""
web/middleware/request_id.py — Request ID middleware for tracing.

Agrega un X-Request-ID único a cada request para facilitar debugging
y correlación en logs.

Uso:
    from web.middleware import RequestIDMiddleware
    app.add_middleware(RequestIDMiddleware)
    
En logs:
    request_id = request.state.request_id
    logger.info("[%s] Processing...", request_id)
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Asigna un ID único a cada request y lo propaga en headers.
    
    - Si el cliente envía X-Request-ID, lo reutiliza (útil para tracing distribuido)
    - Si no, genera uno nuevo (UUID4 truncado a 12 chars)
    - Lo guarda en request.state.request_id para uso en logs
    - Lo devuelve en el header de respuesta
    """
    
    HEADER_NAME = "X-Request-ID"
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Recibir ID del cliente o generar nuevo
        request_id = request.headers.get(self.HEADER_NAME)
        
        if not request_id:
            # UUID4 truncado: suficiente para identificar + legible
            request_id = uuid.uuid4().hex[:12]
        
        # Guardar en request.state para acceso en handlers/logs
        request.state.request_id = request_id
        
        # Procesar request
        response = await call_next(request)
        
        # Devolver ID en respuesta para correlación cliente-servidor
        response.headers[self.HEADER_NAME] = request_id
        
        return response
