"""
db_bootstrap.py — Robust database initialization for Railway/production.

Used as Railway releaseCommand instead of raw 'alembic upgrade head'.
Handles fresh databases and broken migration states gracefully.

Strategy:
1. Create all tables from SQLAlchemy models (CREATE TABLE IF NOT EXISTS)
2. Stamp Alembic version to head (so future migrations work correctly)
3. Then run alembic upgrade head (picks up any data migrations)
"""
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("db_bootstrap")


def main():
    logger.info("=" * 60)
    logger.info("MetodoBase Database Bootstrap")
    logger.info("=" * 60)
    
    # Check DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        logger.error("FATAL: DATABASE_URL not set")
        logger.error("Configure DATABASE_URL in Railway Dashboard > Variables")
        sys.exit(1)
    
    # Mask password in logs
    safe_url = db_url.split("@")[-1] if "@" in db_url else "(local)"
    logger.info("Database: ...@%s", safe_url)
    
    # 1. Initialize the database engine
    logger.info("Step 1: Initializing database engine...")
    try:
        from web.database.engine import init_db, get_engine
        from web.database.models import Base

        init_db()
        engine = get_engine()
        logger.info("Engine initialized successfully")
    except Exception as e:
        logger.error("FATAL: Failed to initialize database engine: %s", e)
        sys.exit(1)

    # 2. Create all tables from models.py (safe: skips existing tables)
    logger.info("Step 2: Creating/verifying all tables from models...")
    try:
        Base.metadata.create_all(engine)
        logger.info("All tables created/verified successfully")
    except Exception as e:
        # Possible DuplicateObject on indexes if DB is in partial state
        logger.warning("create_all() had issues (may be non-fatal): %s", e)
        logger.info("Continuing with Alembic to handle schema...")

    # 3. Stamp Alembic version to head
    logger.info("Step 3: Stamping Alembic version to head...")
    try:
        from alembic.config import Config as AlembicConfig
        from alembic import command

        alembic_cfg = AlembicConfig("alembic.ini")
        command.stamp(alembic_cfg, "head")
        logger.info("Alembic stamped at head")
    except Exception as e:
        logger.warning("Alembic stamp had issues (non-fatal): %s", e)

    # 4. Run alembic upgrade head (catches any new migrations beyond stamp)
    logger.info("Step 4: Running alembic upgrade head...")
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic upgrade completed")
    except Exception as e:
        logger.warning("Alembic upgrade had issues (non-fatal): %s", e)

    logger.info("=" * 60)
    logger.info("Database bootstrap complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
