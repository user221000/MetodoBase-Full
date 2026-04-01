# Variables de Entorno para Railway Deploy

## Variables OBLIGATORIAS en Producción

Configurar en Railway Dashboard > Service > Variables:

### Core
| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `METODOBASE_ENV` | Ambiente | `production` |
| `WEB_SECRET_KEY` | JWT secret (≥32 chars) | `openssl rand -hex 32` |
| `METODO_BASE_SALT` | License salt (≥16 chars) | `openssl rand -hex 16` |
| `DATABASE_URL` | PostgreSQL URL (auto-set si usas Railway Postgres) | `postgresql://...` |
| `CORS_ORIGINS` | Orígenes permitidos | `https://app.metodobase.com` |
| `BASE_URL` | URL pública del app | `https://app.metodobase.com` |

### Stripe (Pagos)
| Variable | Descripción |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Clave secreta LIVE (`sk_live_...`) |
| `STRIPE_PUBLISHABLE_KEY` | Clave pública LIVE (`pk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | Secret del webhook (`whsec_...`) |
| `STRIPE_PRICE_STANDARD` | Price ID plan Standard |
| `STRIPE_PRICE_GYM_COMERCIAL` | Price ID plan Gym Comercial |
| `STRIPE_PRICE_CLINICA` | Price ID plan Clínica |
| `STRIPE_PRICE_PRO_USUARIO` | Price ID plan Pro Usuario |

### Observabilidad
| Variable | Descripción |
|----------|-------------|
| `SENTRY_DSN` | DSN de Sentry para error tracking |

---

## Variables OPCIONALES

| Variable | Default | Descripción |
|----------|---------|-------------|
| `REDIS_URL` | (none) | Redis para rate limiting distribuido |
| `MERCADOPAGO_ACCESS_TOKEN` | (none) | Token de MercadoPago |
| `GOOGLE_CLIENT_ID` | (none) | Google OAuth client ID |
| `RESEND_API_KEY` | (none) | API key de Resend para emails |

---

## Configuración de Railway

```toml
# railway.toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 60
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 5
releaseCommand = "python db_bootstrap.py"
numReplicas = 1
```

### Health Endpoints

- `/health` - Liveness check (siempre 200 si el proceso está vivo)
- `/health/ready` - Readiness check (503 si BD no está lista)

---

## Troubleshooting

### El deploy falla con "Missing critical environment variables"

1. Ve a Railway Dashboard > Service > Variables
2. Verifica que TODAS las variables obligatorias estén configuradas
3. Genera nuevos secrets si es necesario:
   ```bash
   openssl rand -hex 32  # para WEB_SECRET_KEY
   openssl rand -hex 16  # para METODO_BASE_SALT
   ```

### El deploy falla con "STRIPE_SECRET_KEY es una clave de prueba"

En producción se requieren claves LIVE de Stripe (no `sk_test_*`).
Obtén las claves live en: https://dashboard.stripe.com/apikeys

### Health check falla

Revisa los logs de Railway para ver el error específico. El endpoint `/health` 
ahora siempre retorna 200 (liveness), pero loggea si la BD falla.

### DATABASE_URL no está configurada

Si usas Railway Postgres, la variable se configura automáticamente al vincular 
el servicio de Postgres. Verifica en Variables que aparezca.
