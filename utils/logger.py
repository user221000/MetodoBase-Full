"""Sistema de logging centralizado para Método Base."""
import logging
import os
from logging.handlers import RotatingFileHandler


class SistemaLogging:
    """Configura y provee un logger único para toda la aplicación."""

    _logger: logging.Logger | None = None

    @staticmethod
    def configurar_logger(nombre: str = "metodo_base") -> logging.Logger:
        if SistemaLogging._logger is not None:
            return SistemaLogging._logger

        logger = logging.getLogger(nombre)
        logger.setLevel(logging.DEBUG)

        if logger.handlers:
            SistemaLogging._logger = logger
            return logger

        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "registros",
        )
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "metodo_base.log")

        fmt = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(fmt, datefmt=datefmt)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.propagate = False

        SistemaLogging._logger = logger
        return logger


# Instancia lista para importar directamente:
#   from utils.logger import logger
logger = SistemaLogging.configurar_logger()
