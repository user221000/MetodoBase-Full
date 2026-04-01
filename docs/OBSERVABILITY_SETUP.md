# Observability & Monitoring Setup

Documentación de las herramientas de observabilidad y monitoreo implementadas en MetodoBase.

## 📊 Structured Logging (JSON)

### Configuración

El sistema usa logging estructurado en JSON para producción, lo que facilita el parsing y análisis de logs.

**Activación automática:** Los logs se formatean en JSON si `METODOBASE_ENV=production`.

```python
# En web/main_web.py
from utils.structured_logging import setup_structured_logging

setup_structured_logging(
    level="INFO" if is_production else "DEBUG",
    use_json=is_production,
    include_exc_info=not is_production,
)
```

### Formato de Logs

**Development (colored console):**
```
[INFO    ] web.auth                    - User logged in | req=a1b2c3d4
```

**Production (JSON):**
```json
{
  "timestamp": "2026-03-26T10:30:45.123Z",
  "level": "INFO",
  "logger": "web.auth",
  "message": "User logged in",
  "request_id": "a1b2c3d4e5f6",
  "user_id": 42,
  "gym_id": 10,
  "ip_address": "192.168.1.1"
}
```

### Context Manager para Logs

Usa `LogContext` para agregar campos automáticamente a todos los logs:

```python
from utils.structured_logging import LogContext

with LogContext(request_id="abc-123", user_id=42):
    logger.info("Processing request")
    # Log incluye automáticamente request_id y user_id
    do_something()
```

## 🔍 Request Tracking

### Request IDs

Cada request HTTP recibe un ID único para correlación de logs:

- **Header:** `X-Request-ID` (generado automáticamente si no existe)
- **Acceso:** `request.state.request_id`
- **Logs:** Incluido automáticamente en logs de error
- **Error responses:** Incluido en JSON de respuesta

**Ejemplo de error response:**
```json
{
  "detail": "Error interno del servidor",
  "request_id": "a1b2c3d4e5f6"
}
```

### Correlación de Logs con Sentry

Los request IDs también se envían a Sentry para correlación entre logs y traces.

## 🧹 Cleanup Jobs

### Token Cleanup Job

Script automatizado para eliminar refresh tokens expirados y mantener la base de datos limpia.

**Ubicación:** `scripts/cleanup_expired_tokens.py`

**Ejecución manual:**
```bash
cd /home/hernandez221000/MetodoBase-Full
python scripts/cleanup_expired_tokens.py
```

**Output esperado:**
```
============================================================
CLEANUP JOB STARTED
============================================================
2026-03-26 10:30:45 - cleanup_expired_tokens - INFO - Cleaning up refresh tokens older than 2026-02-24T10:30:45.123Z
2026-03-26 10:30:45 - cleanup_expired_tokens - INFO - Deleted 42 expired refresh tokens
2026-03-26 10:30:45 - cleanup_expired_tokens - INFO - Cleaning up auth audit logs older than 2025-12-26T10:30:45.123Z
2026-03-26 10:30:45 - cleanup_expired_tokens - INFO - Deleted 156 old auth audit logs
============================================================
CLEANUP JOB COMPLETED
Tokens deleted: 42
Audit logs deleted: 156
============================================================
```

### Configuración de Cron Job

**Recomendación:** Ejecutar diariamente a las 3 AM.

**Crontab entry:**
```cron
# MetodoBase: Cleanup expired tokens daily at 3 AM
0 3 * * * cd /home/hernandez221000/MetodoBase-Full && python scripts/cleanup_expired_tokens.py >> /var/log/metodobase/token_cleanup.log 2>&1
```

**Con Docker/Railway:**
```dockerfile
# En Dockerfile, agregar cron job
RUN apt-get update && apt-get install -y cron
COPY scripts/cleanup_expired_tokens.py /app/scripts/
RUN echo "0 3 * * * cd /app && python scripts/cleanup_expired_tokens.py >> /var/log/token_cleanup.log 2>&1" | crontab -
CMD service cron start && uvicorn web.main_web:app --host 0.0.0.0 --port $PORT
```

**Railway Cron (alternativa):**
```toml
# railway.toml
[build]
builder = "DOCKERFILE"

[[services]]
name = "web"
command = "uvicorn web.main_web:app --host 0.0.0.0 --port $PORT"

[[services]]
name = "cleanup-job"
command = "python scripts/cleanup_expired_tokens.py"
schedule = "0 3 * * *"  # Daily at 3 AM
```

### Políticas de Retención

| Tipo | Retención | Razón |
|------|-----------|-------|
| **Refresh tokens** | 30 días después de expirar | Los tokens tienen 7-90 días de vida, mantener 30 días adicionales para debugging |
| **Auth audit logs** | 90 días | Compliance y análisis de seguridad |
| **Error logs (Sentry)** | 30 días | Plan Sentry gratuito, ajustar según plan |
| **Access logs** | 7 días | Alta volumetría, solo para debugging inmediato |

## 🔒 Security Best Practices

### Exception Information (exc_info)

Los stack traces **NO** se incluyen en logs de producción para evitar leakage de información:

```python
# ✅ Correcto: exc_info conditional
logger.error(
    "Error processing request",
    exc_info=(os.getenv("METODOBASE_ENV") != "production")
)

# ❌ Incorrecto: siempre incluye stack trace
logger.error("Error processing request", exc_info=True)
```

**Razón:** Los stack traces pueden revelar:
- Rutas de archivos internos
- Variables locales con datos sensibles
- Estructura del código (security through obscurity)

**En producción:** Los stack traces se envían a Sentry (donde están protegidos por auth) pero NO a logs stdout.

## 📈 Monitoring Recommendations

### Métricas Clave

1. **Auth Events:**
   - `auth_audit_log` table: COUNT por `event_type`
   - Alert: >10 failed logins en 5 minutos desde misma IP

2. **Token Usage:**
   - `refresh_tokens` table: COUNT total
   - Alert: >1000 tokens activos (posible abuse)

3. **Request Errors:**
   - HTTP 500 responses: tasa <0.1%
   - HTTP 429 responses: rate limiting activo

4. **Database Performance:**
   - Query duration: p95 <200ms
   - Connection pool: <80% uso

### Herramientas Recomendadas

| Herramienta | Propósito | Integración |
|------------|-----------|-------------|
| **Sentry** | Error tracking + Performance | ✅ Activo |
| **Grafana** | Dashboards + Alerting | ⚠️ Pendiente |
| **Prometheus** | Métricas + Time series | ⚠️ Pendiente |
| **ELK Stack** | Log aggregation + Search | ⚠️ Opcional |
| **Railway Logs** | Log viewer integrado | ✅ Activo |

## 🚀 Deployment Checklist

Antes de deploy a producción, verificar:

- [ ] `METODOBASE_ENV=production` está configurado
- [ ] Logs se están generando en formato JSON
- [ ] Sentry DSN está configurado y recibe eventos
- [ ] Cron job de cleanup está configurado
- [ ] Stack traces NO aparecen en logs stdout
- [ ] Request IDs se incluyen en error responses
- [ ] Health check responde correctamente: `/health`
- [ ] Secrets (SECRET_KEY, SENTRY_DSN) están en variables de entorno, NO en código

## 📚 Referencias

- [Structured Logging Best Practices](https://www.structlog.org/)
- [Request ID Patterns](https://www.nginx.com/blog/application-tracing-nginx-plus/)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Railway Cron Jobs](https://docs.railway.app/reference/cron-jobs)
