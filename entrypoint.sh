#!/bin/bash
set -e

echo "=== MetodoBase: Container starting ==="
echo "  RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-'(not set)'}"
echo "  METODOBASE_ENV: ${METODOBASE_ENV:-'(not set)'}"
echo "  PORT: ${PORT:-'(not set)'}"
echo "  DATABASE_URL: ${DATABASE_URL:+'(configured)'}"
echo "  WEB_SECRET_KEY: ${WEB_SECRET_KEY:+'(configured)'}"

# Railway usa releaseCommand para migraciones; solo ejecutar aquí si no es Railway
if [ -z "$RAILWAY_ENVIRONMENT" ]; then
    echo "=== MetodoBase: Ejecutando migraciones Alembic ==="
    alembic upgrade head || echo "WARNING: Alembic migrations failed (may be non-fatal)"
else
    echo "=== MetodoBase: Migraciones gestionadas por Railway releaseCommand ==="
fi

echo "=== MetodoBase: Iniciando servidor en 0.0.0.0:${PORT:-8000} ==="
exec python web/main_web.py --no-browser
