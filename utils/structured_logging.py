"""
utils/structured_logging.py — Structured JSON logging for production

Provides JSON-formatted logging for better observability in production.

Usage:
    from utils.structured_logging import setup_structured_logging
    
    # At app startup:
    setup_structured_logging()
    
    # Then use logger as normal:
    import logging
    logger = logging.getLogger(__name__)
    logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    Formatea logs como JSON para facilitar parsing en producción.
    
    Estructura:
        {
            "timestamp": "2026-03-26T10:30:45.123Z",
            "level": "INFO",
            "logger": "web.auth",
            "message": "User logged in",
            "request_id": "abc-123",
            "user_id": 42,
            "ip": "192.168.1.1",
            "exc_info": "..." # Solo si hay exception
        }
    """
    
    def __init__(self, include_exc_info: bool = False):
        """
        Args:
            include_exc_info: Si incluir stack traces en producción (default: False)
        """
        super().__init__()
        self.include_exc_info = include_exc_info
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatea el LogRecord como JSON."""
        
        # Base log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Agregar extra fields si existen
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, "gym_id"):
            log_entry["gym_id"] = record.gym_id
        
        if hasattr(record, "ip_address"):
            log_entry["ip_address"] = record.ip_address
        
        # Agregar cualquier otro extra field
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "request_id", "user_id", "gym_id", "ip_address"
            ]:
                try:
                    # Intentar serializar a JSON
                    json.dumps(value)
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)
        
        # Agregar exception info si existe (y si está habilitado)
        if record.exc_info and (self.include_exc_info or record.levelno >= logging.ERROR):
            log_entry["exc_info"] = self.formatException(record.exc_info)
        
        # Agregar location info en development
        try:
            from config.settings import get_settings
            _is_dev = not get_settings().is_production
        except Exception:
            _is_dev = os.getenv("METODOBASE_ENV", "development") == "development"
        if _is_dev:
            log_entry["location"] = f"{record.pathname}:{record.lineno}"
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Formatea logs con colores para desarrollo local.
    
    Usa colores ANSI para mejor legibilidad en terminal.
    """
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatea el LogRecord con colores."""
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Formato: [LEVEL] logger - message
        formatted = f"{color}[{record.levelname:8}]{self.RESET} {record.name:30} - {record.getMessage()}"
        
        # Agregar request_id si existe
        if hasattr(record, "request_id"):
            formatted += f" | req={record.request_id[:8]}"
        
        # Agregar exception si existe
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return formatted


def setup_structured_logging(
    level: str = None,
    use_json: bool = None,
    include_exc_info: bool = None,
) -> None:
    """
    Configura logging estructurado para la aplicación.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Default: INFO en producción, DEBUG en development
        use_json: Si usar formato JSON (True en producción por defecto)
        include_exc_info: Si incluir stack traces en producción (default: False)
    
    Example:
        # En main.py:
        from utils.structured_logging import setup_structured_logging
        setup_structured_logging()
    """
    
    # Detectar environment
    try:
        from config.settings import get_settings
        is_production = get_settings().is_production
    except Exception:
        is_production = os.getenv("METODOBASE_ENV", "development") == "production"
    
    # Defaults basados en environment
    if level is None:
        level = "INFO" if is_production else "DEBUG"
    
    if use_json is None:
        use_json = is_production
    
    if include_exc_info is None:
        include_exc_info = not is_production
    
    # Crear handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Seleccionar formatter
    if use_json:
        formatter = JSONFormatter(include_exc_info=include_exc_info)
    else:
        formatter = ColoredFormatter()
    
    handler.setFormatter(formatter)
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remover handlers existentes
    root_logger.handlers.clear()
    
    # Agregar nuevo handler
    root_logger.addHandler(handler)
    
    # Configurar niveles para loggers específicos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Log inicial
    logger = logging.getLogger(__name__)
    logger.info(
        "Structured logging configured",
        extra={
            "level": level,
            "format": "json" if use_json else "colored",
            "environment": "production" if is_production else os.getenv("METODOBASE_ENV", "development"),
        }
    )


# ── Context Manager para agregar campos a logs ────────────────────────────

class LogContext:
    """
    Context manager para agregar campos temporales a los logs.
    
    Usage:
        with LogContext(request_id="abc-123", user_id=42):
            logger.info("Processing request")
            # Log incluirá automáticamente request_id y user_id
    """
    
    def __init__(self, **kwargs):
        self.fields = kwargs
        self.old_factory = None
    
    def __enter__(self):
        # Guardar factory anterior
        self.old_factory = logging.getLogRecordFactory()
        
        # Crear nueva factory que agrega campos
        fields = self.fields
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in fields.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restaurar factory anterior
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)
