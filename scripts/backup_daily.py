#!/usr/bin/env python3
"""
scripts/backup_daily.py — Sistema de backup automático diario.

Uso:
    # Manual
    python scripts/backup_daily.py
    
    # Con cron (agregar a crontab -e):
    0 3 * * * cd /path/to/MetodoBase && /path/to/venv/bin/python scripts/backup_daily.py >> /var/log/metodobase_backup.log 2>&1

    # Con systemd timer (crear /etc/systemd/system/metodobase-backup.timer)

Características:
- Backup de BD SQLAlchemy y legacy (si existe)
- Compresión gzip
- Retención configurable (default: 30 días)
- Notificación de errores
- Verificación de integridad
"""

import os
import sys
import gzip
import shutil
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Agregar root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constantes import CARPETA_REGISTROS

# ── Configuración ────────────────────────────────────────────────────────────

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backups/daily"))
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
COMPRESS_BACKUPS = os.getenv("BACKUP_COMPRESS", "true").lower() == "true"

# Archivos a respaldar
BACKUP_TARGETS = [
    "metodobase_web.db",  # BD principal (SQLAlchemy)
    "clientes.db",        # BD legacy (si existe)
    "web_usuarios.db",    # BD usuarios web (si existe)
]

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Funciones ────────────────────────────────────────────────────────────────

def get_file_checksum(filepath: Path) -> str:
    """Calcula SHA256 del archivo."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def backup_file(source: Path, dest_dir: Path, compress: bool = True) -> Optional[Path]:
    """
    Realiza backup de un archivo.
    
    Returns:
        Path del backup creado o None si falla.
    """
    if not source.exists():
        logger.debug(f"Archivo no existe, omitiendo: {source}")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{source.stem}_{timestamp}{source.suffix}"
    
    if compress:
        backup_name += ".gz"
        dest = dest_dir / backup_name
        
        logger.info(f"Comprimiendo: {source} → {dest}")
        with open(source, "rb") as f_in:
            with gzip.open(dest, "wb", compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)
    else:
        dest = dest_dir / backup_name
        logger.info(f"Copiando: {source} → {dest}")
        shutil.copy2(source, dest)
    
    # Verificar integridad
    if compress:
        # Descomprimir y verificar
        with gzip.open(dest, "rb") as f:
            backup_data = f.read()
        with open(source, "rb") as f:
            original_data = f.read()
        if backup_data != original_data:
            logger.error(f"¡Verificación de integridad fallida para {dest}!")
            dest.unlink()
            return None
    else:
        original_checksum = get_file_checksum(source)
        backup_checksum = get_file_checksum(dest)
        if original_checksum != backup_checksum:
            logger.error(f"¡Checksum no coincide para {dest}!")
            dest.unlink()
            return None
    
    logger.info(f"✓ Backup verificado: {dest} ({dest.stat().st_size / 1024:.1f} KB)")
    return dest


def cleanup_old_backups(backup_dir: Path, retention_days: int) -> int:
    """
    Elimina backups más antiguos que retention_days.
    
    Returns:
        Número de archivos eliminados.
    """
    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted = 0
    
    for backup_file in backup_dir.glob("*_????????_??????.*"):
        try:
            # Extraer timestamp del nombre
            parts = backup_file.stem.replace(".db", "").split("_")
            if len(parts) >= 3:
                date_str = parts[-2]
                time_str = parts[-1].split(".")[0]
                file_date = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                
                if file_date < cutoff:
                    backup_file.unlink()
                    logger.info(f"Eliminado backup antiguo: {backup_file.name}")
                    deleted += 1
        except (ValueError, IndexError):
            continue
    
    return deleted


def run_backup() -> dict:
    """
    Ejecuta el proceso de backup completo.
    
    Returns:
        Diccionario con resultados.
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "success": [],
        "skipped": [],
        "failed": [],
        "deleted_old": 0,
    }
    
    # Crear directorio de backups
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Directorio de datos
    data_dir = Path(CARPETA_REGISTROS)
    
    logger.info("=" * 60)
    logger.info("INICIANDO BACKUP DIARIO")
    logger.info("=" * 60)
    logger.info(f"Directorio origen: {data_dir}")
    logger.info(f"Directorio destino: {BACKUP_DIR}")
    logger.info(f"Compresión: {'Sí' if COMPRESS_BACKUPS else 'No'}")
    logger.info(f"Retención: {RETENTION_DAYS} días")
    
    # Backup de cada archivo
    for target in BACKUP_TARGETS:
        source = data_dir / target
        if source.exists():
            backup_path = backup_file(source, BACKUP_DIR, COMPRESS_BACKUPS)
            if backup_path:
                results["success"].append(str(backup_path))
            else:
                results["failed"].append(str(source))
        else:
            results["skipped"].append(str(source))
            logger.debug(f"Omitido (no existe): {source}")
    
    # Limpiar backups antiguos
    results["deleted_old"] = cleanup_old_backups(BACKUP_DIR, RETENTION_DAYS)
    
    # Resumen
    logger.info("=" * 60)
    logger.info("RESUMEN DE BACKUP")
    logger.info("=" * 60)
    logger.info(f"✓ Exitosos: {len(results['success'])}")
    logger.info(f"- Omitidos: {len(results['skipped'])}")
    logger.info(f"✗ Fallidos: {len(results['failed'])}")
    logger.info(f"🗑 Antiguos eliminados: {results['deleted_old']}")
    
    if results["failed"]:
        logger.error(f"¡ATENCIÓN! Backups fallidos: {results['failed']}")
    
    return results


def send_alert(message: str, level: str = "error"):
    """
    Envía alerta de backup (placeholder para integración).
    
    En producción, implementar con:
    - Slack webhook
    - Email (via Resend)
    - PagerDuty
    - etc.
    """
    # Placeholder - implementar según necesidad
    if level == "error":
        logger.error(f"[ALERTA] {message}")
    else:
        logger.info(f"[NOTIFICACIÓN] {message}")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        results = run_backup()
        
        if results["failed"]:
            send_alert(
                f"Backup fallido para: {', '.join(results['failed'])}",
                level="error"
            )
            sys.exit(1)
        else:
            logger.info("Backup completado exitosamente.")
            sys.exit(0)
            
    except Exception as e:
        logger.exception(f"Error crítico en backup: {e}")
        send_alert(f"Error crítico en backup: {e}", level="error")
        sys.exit(1)
