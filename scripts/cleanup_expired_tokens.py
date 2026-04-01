"""
scripts/cleanup_expired_tokens.py — Cleanup job for expired refresh tokens

Removes expired refresh tokens from database to prevent infinite growth.

Usage:
    # Manual run:
    python scripts/cleanup_expired_tokens.py
    
    # Cron job (daily at 3am):
    0 3 * * * cd /app && python scripts/cleanup_expired_tokens.py >> /var/log/token_cleanup.log 2>&1
"""
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

from sqlalchemy import text
from web.database.engine import get_engine

logger = logging.getLogger(__name__)


def cleanup_expired_tokens(days_to_keep: int = 30) -> int:
    """
    Elimina refresh tokens expirados de la base de datos.
    
    Args:
        days_to_keep: Mantener tokens de los últimos N días (default: 30)
        
    Returns:
        Número de tokens eliminados
    """
    engine = get_engine()
    
    # Calcular fecha de corte
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    
    logger.info(f"Cleaning up refresh tokens older than {cutoff_date.isoformat()}")
    
    try:
        with engine.connect() as conn:
            # Query para contar tokens expirados
            count_query = text("""
                SELECT COUNT(*) 
                FROM refresh_tokens 
                WHERE expires_at < :cutoff_date
            """)
            
            result = conn.execute(count_query, {"cutoff_date": cutoff_date})
            count = result.scalar()
            
            if count == 0:
                logger.info("No expired tokens to clean up")
                return 0
            
            # Delete tokens expirados
            delete_query = text("""
                DELETE FROM refresh_tokens 
                WHERE expires_at < :cutoff_date
            """)
            
            result = conn.execute(delete_query, {"cutoff_date": cutoff_date})
            conn.commit()
            
            deleted = result.rowcount
            logger.info(f"Deleted {deleted} expired refresh tokens")
            
            return deleted
    
    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {e}", exc_info=True)
        return 0


def cleanup_old_audit_logs(days_to_keep: int = 90) -> int:
    """
    Elimina auth audit logs antiguos (opcional, para compliance).
    
    Args:
        days_to_keep: Mantener logs de los últimos N días (default: 90)
        
    Returns:
        Número de logs eliminados
    """
    engine = get_engine()
    
    # Calcular fecha de corte
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    
    logger.info(f"Cleaning up auth audit logs older than {cutoff_date.isoformat()}")
    
    try:
        with engine.connect() as conn:
            # Count logs to delete
            count_query = text("""
                SELECT COUNT(*) 
                FROM auth_audit_log 
                WHERE created_at < :cutoff_date
            """)
            
            result = conn.execute(count_query, {"cutoff_date": cutoff_date})
            count = result.scalar()
            
            if count == 0:
                logger.info("No old audit logs to clean up")
                return 0
            
            # Delete old logs
            delete_query = text("""
                DELETE FROM auth_audit_log 
                WHERE created_at < :cutoff_date
            """)
            
            result = conn.execute(delete_query, {"cutoff_date": cutoff_date})
            conn.commit()
            
            deleted = result.rowcount
            logger.info(f"Deleted {deleted} old auth audit logs")
            
            return deleted
    
    except Exception as e:
        logger.error(f"Failed to cleanup old audit logs: {e}", exc_info=True)
        return 0


def main():
    """Main entry point for cleanup job."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("=" * 60)
    logger.info("CLEANUP JOB STARTED")
    logger.info("=" * 60)
    
    # Cleanup tokens
    tokens_deleted = cleanup_expired_tokens(days_to_keep=30)
    
    # Cleanup audit logs (mantener 90 días para compliance)
    logs_deleted = cleanup_old_audit_logs(days_to_keep=90)
    
    # Summary
    logger.info("=" * 60)
    logger.info("CLEANUP JOB COMPLETED")
    logger.info(f"Tokens deleted: {tokens_deleted}")
    logger.info(f"Audit logs deleted: {logs_deleted}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
