"""
config/env_validator.py — Validación de variables de entorno críticas.

Falla rápido al arrancar el servidor si faltan variables requeridas o tienen formato inválido.
Principio: Fail fast en lugar de fallar en producción con errores crípticos.
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

CRITICAL_ENV_VARS = [
    "SECRET_KEY",
    "LICENSE_SALT",
]

CRITICAL_IF_PRODUCTION = [
    "DATABASE_URL",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    # SENTRY_DSN is optional - app works without it (no error tracking)
]

STRIPE_PRICE_VARS = [
    "STRIPE_PRICE_STANDARD",
    "STRIPE_PRICE_GYM_COMERCIAL",
    "STRIPE_PRICE_CLINICA",
]


def validate_env_vars():
    """Valida variables de entorno críticas al arrancar el servidor."""
    missing = []
    for var in CRITICAL_ENV_VARS:
        # Support legacy aliases: SECRET_KEY ← WEB_SECRET_KEY, LICENSE_SALT ← METODO_BASE_SALT
        aliases = {
            "SECRET_KEY": ["SECRET_KEY", "WEB_SECRET_KEY"],
            "LICENSE_SALT": ["LICENSE_SALT", "METODO_BASE_SALT"],
        }
        candidates = aliases.get(var, [var])
        if not any(os.getenv(c) for c in candidates):
            missing.append(var)
    
    is_production = os.getenv("METODOBASE_ENV", "development") == "production"
    
    if is_production:
        missing.extend([var for var in CRITICAL_IF_PRODUCTION if not os.getenv(var)])
        # En producción, Stripe Price IDs también son críticos
        missing.extend([var for var in STRIPE_PRICE_VARS if not os.getenv(var)])
    
    if missing:
        logger.error("=" * 60)
        logger.error("FATAL: Missing critical environment variables for production:")
        for var in missing:
            logger.error(f"  ❌ {var}")
        logger.error("")
        logger.error("Configure these variables in Railway Dashboard > Variables")
        logger.error("See .env.example for reference.")
        logger.error("=" * 60)
        sys.exit(1)
    
    # Validar formato de SECRET_KEY
    secret_key = os.getenv("SECRET_KEY") or os.getenv("WEB_SECRET_KEY") or ""
    if len(secret_key) < 32:
        logger.error("=" * 60)
        logger.error("FATAL: SECRET_KEY must be at least 32 characters")
        logger.error(f"  Current length: {len(secret_key)}")
        logger.error("  Generate with: openssl rand -hex 32")
        logger.error("=" * 60)
        sys.exit(1)
    
    # Validar formato de LICENSE_SALT
    license_salt = os.getenv("LICENSE_SALT") or os.getenv("METODO_BASE_SALT") or ""
    if len(license_salt) < 16:
        logger.error("=" * 60)
        logger.error("FATAL: LICENSE_SALT must be at least 16 characters")
        logger.error(f"  Current length: {len(license_salt)}")
        logger.error("  Generate with: openssl rand -hex 16")
        logger.error("=" * 60)
        sys.exit(1)
    
    # Validar DATABASE_URL scheme
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        logger.info("DATABASE_URL uses postgres:// scheme (will be auto-converted to postgresql://)")
    
    # Log de éxito
    logger.info("✓ Environment variables validated successfully")


def get_stripe_price_ids() -> dict:
    """Retorna los Price IDs de Stripe desde variables de entorno."""
    return {
        "standard": os.getenv("STRIPE_PRICE_STANDARD", ""),
        "gym_comercial": os.getenv("STRIPE_PRICE_GYM_COMERCIAL", ""),
        "clinica": os.getenv("STRIPE_PRICE_CLINICA", ""),
    }


if __name__ == "__main__":
    # Test del validador
    logging.basicConfig(level=logging.INFO)
    try:
        validate_env_vars()
        print("✅ All environment variables are valid")
    except SystemExit:
        print("❌ Environment validation failed")
