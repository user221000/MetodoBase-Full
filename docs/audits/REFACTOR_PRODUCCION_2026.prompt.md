# REFACTOR DE PRODUCCIÓN — MetodoBase SaaS Multi-Tenant
## Prompt de Arquitecto Senior — 15 años experiencia en SaaS competitivos

**Fecha:** 26 de marzo de 2026  
**Contexto:** Preparar MetodoBase para producción real. Multi-tenant SaaS para gyms en Guadalajara.  
**Equipo:** 4 agentes senior (Arquitecto → Implementador → QA → Implementador de ajustes)  
**Alcance:** Resolver TODAS las brechas críticas, medias, bajas + limpieza completa  

---

## 🎯 OBJETIVO FINAL

Transformar MetodoBase de MVP con datos hardcodeados a **SaaS multi-tenant production-ready** que pueda:
- Soportar múltiples gyms independientes con branding propio
- Cumplir compliance México (LFPDPPP, CFDI-ready)
- Escalar sin riesgo de seguridad
- Desplegar en Railway con CI/CD confidence
- Pasar auditoría de penetración

**Criterio de éxito:** Poder onboardear primer gym piloto en Guadalajara sin datos personales expuestos, sin secretos débiles, con branding dinámico, y con todos los tests pasando.

---

## 📋 MAPA DE PROBLEMAS (De AUDITORIA_PRODUCCION_2026-03-25.txt)

### CATEGORÍA A: BLOQUEANTES CRÍTICOS (NO deploy sin esto)
- **A1-Seguridad:** Datos personales hardcodeados en 9+ archivos (config/branding.json, LICENSE, README_COMERCIAL.md, api/factura_pdf.py, web/pages/)
- **A2-Seguridad:** Secretos débiles con defaults (SECRET_KEY, LICENSE_SALT)
- **A3-Multi-tenant:** Branding global (no per-gym) — imposible white-labeling
- **A4-Multi-tenant:** Licencias en memoria (no persistidas en DB)
- **A5-Deploy:** No se ejecutan migraciones en Dockerfile/Railway/Procfile
- **A6-Deploy:** Health check expone stack traces (C-11)
- **A7-Seguridad:** CSP con 'unsafe-inline' (H-04)
- **A8-Seguridad:** CSRF cookie no httponly (H-03)
- **A9-Seguridad:** No rate limiting en login (H-06)
- **A10-Seguridad:** /metrics sin auth (H-09)
- **A11-Seguridad:** CDN scripts sin SRI (H-05)
- **A12-Observabilidad:** exc_info=True en producción (M-08)

### CATEGORÍA B: DEUDA TÉCNICA ALTA
- **B1-Legacy:** ~40 bare except con solo logger.warning (L-01)
- **B2-Legacy:** 80+ print() en lugar de logger (M-01)
- **B3-Legacy:** 51 datetime.utcnow() deprecado → .now(UTC) (M-02)
- **B4-Multi-tenant:** RLS policies no activadas (H-15)
- **B5-Auth:** Access tokens de 30 días (H-08)
- **B6-Auth:** No audit logging de auth (H-07)
- **B7-Deploy:** psycopg2-binary en requirements_web.txt (cambiar a psycopg)
- **B8-Deploy:** Sin archivo de lock (poetry.lock / pip-compile)

### CATEGORÍA C: CÓDIGO MUERTO
- **C1:** utils/updater.py (DEPRECATED)
- **C2:** _test_imports.py, _test_panels.py, test_qss.py (scripts debug huérfanos)
- **C3:** web/static/js/charts.js.bak, styles.css.bak, dashboard.html.bak
- **C4:** core/services/security/ (directorio vacío)
- **C5:** Referencias CustomTkinter en docstrings (utils/helpers.py, utils/iconos.py)

### CATEGORÍA D: PARAMETRIZACIÓN
- **D1:** Stripe Price IDs placeholders (config/constantes.py) → env vars
- **D2:** Horarios de comida hardcodeados (M-15)
- **D3:** Trial días/clientes/modo estricto hardcodeados
- **D4:** APP_AUTHOR = "Consultoría Hernández" (build_config.py)

### CATEGORÍA E: INFRAESTRUCTURA
- **E1:** Dockerfile no valida env vars críticas
- **E2:** railway.toml sin releaseCommand para migraciones
- **E3:** Alembic migrations con UUID naming (no ordenables) (L-07)
- **E4:** ui_desktop/pyside/gym_app_window.py con localhost:8000/docs hardcoded (L-08)

### CATEGORÍA F: DATABASE & MULTI-TENANT
- **F1:** Crear tabla gym_branding (migrar de branding.json)
- **F2:** Crear tabla gym_settings (config per-gym)
- **F3:** Crear tabla gym_licenses (persistir licencias)
- **F4:** Activar RLS en PostgreSQL
- **F5:** No hay soft-delete audit timestamps (L-09)
- **F6:** Dashboard sin estado vacío para 0 clientes (L-02)

### CATEGORÍA G: TESTING & CALIDAD
- **G1:** Test fixtures usan mismas credenciales que demo users (L-03)
- **G2:** Falta logging estructurado (JSON) para producción
- **G3:** No hay cleanup de refresh tokens expirados

---

## 🏗️ ARQUITECTURA DEL REFACTOR

### PRINCIPIOS GUÍA (15 años de experiencia SaaS)
1. **Zero-downtime migrations:** Alembic debe ser idempotente
2. **Secrets via env vars:** NUNCA en código, validar al boot
3. **Multi-tenant by design:** gym_id en TODAS las queries, RLS como 2da capa
4. **Defense in depth:** CSP + httponly + SRI + rate limiting + audit logs
5. **Fail fast:** Validar env vars críticas antes de aceptar requests
6. **Observability first:** Structured logging, request IDs, no stack traces en producción
7. **Backward compatibility:** Migraciones no pueden romper despliegues activos

### FASES DE EJECUCIÓN

```
FASE 1: ARQUITECTURA & DISEÑO (Arquitecto)
├─ Diseñar schema DB para multi-tenant settings
├─ Diseñar migration strategy (orden crítico)
├─ Diseñar env vars architecture
├─ Diseñar CSP nonce implementation
├─ Diseñar audit logging schema
└─ Crear ADRs (Architecture Decision Records)

FASE 2: IMPLEMENTACIÓN (Implementador)
├─ Ejecutar cambios según diseño del Arquitecto
├─ Crear Alembic migrations
├─ Refactorizar código según nuevos patterns
├─ Actualizar Dockerfile/railway.toml/Procfile
└─ Implementar todos los fixes (A1-G3)

FASE 3: QA & VALIDACIÓN (QA)
├─ Ejecutar suite completa de tests
├─ Validar migraciones (up/down)
├─ Tests de seguridad (CSP, SRI, rate limiting)
├─ Tests de multi-tenant isolation
├─ Smoke tests de deploy
└─ Generar reporte de issues encontrados

FASE 4: AJUSTES & REFINAMIENTO (Implementador)
├─ Fix issues reportados por QA
├─ Re-ejecutar tests críticos
├─ Validación final
└─ Documentar cambios
```

---

## 📐 FASE 1: PROMPT PARA ARQUITECTO

**Rol:** Arquitecto Senior con 15 años en SaaS (Stripe, Notion, Linear)  
**Contexto:** Has revisado AUDITORIA_PRODUCCION_2026-03-25.txt completo  
**Tarea:** Diseñar la arquitectura de refactor antes de escribir código  

### ENTREGABLES REQUERIDOS

#### 1. DATABASE SCHEMA DESIGN

Diseñar migraciones de Alembic para:

**Migration 1: gym_branding table**
```sql
-- Objetivo: Eliminar config/branding.json, hacer branding per-gym
CREATE TABLE gym_branding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    business_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    whatsapp VARCHAR(20),
    address TEXT,
    logo_url TEXT,
    primary_color VARCHAR(7) DEFAULT '#3B82F6',
    secondary_color VARCHAR(7) DEFAULT '#10B981',
    monthly_fee DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(gym_id)
);
```

**Migration 2: gym_settings table**
```sql
-- Objetivo: Config per-gym (horarios, trial settings, etc)
CREATE TABLE gym_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    trial_days INTEGER DEFAULT 14,
    trial_max_clients INTEGER DEFAULT 50,
    strict_mode BOOLEAN DEFAULT TRUE,
    breakfast_time TIME DEFAULT '07:00',
    lunch_time TIME DEFAULT '14:00',
    dinner_time TIME DEFAULT '20:30',
    timezone VARCHAR(50) DEFAULT 'America/Mexico_City',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(gym_id)
);
```

**Migration 3: gym_licenses table**
```sql
-- Objetivo: Persistir licencias (no in-memory)
CREATE TABLE gym_licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    license_key VARCHAR(255) NOT NULL UNIQUE,
    plan_tier VARCHAR(20) NOT NULL, -- 'free', 'starter', 'pro', 'enterprise'
    max_clients INTEGER NOT NULL,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    payment_provider VARCHAR(20), -- 'stripe', 'mercadopago', 'manual'
    payment_reference VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP,
    INDEX idx_gym_licenses_gym_id (gym_id),
    INDEX idx_gym_licenses_active (is_active, expires_at)
);
```

**Migration 4: auth_audit_log table**
```sql
-- Objetivo: Cumplir compliance + detective controls
CREATE TABLE auth_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gym_id UUID REFERENCES gyms(id),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL, -- 'login_success', 'login_failed', 'password_change', etc
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(36),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_auth_audit_gym (gym_id, created_at),
    INDEX idx_auth_audit_user (user_id, created_at),
    INDEX idx_auth_audit_type (event_type, created_at)
);
```

**Migration 5: Soft delete timestamps**
```sql
-- Objetivo: Cumplir L-09 (audit timestamps)
ALTER TABLE clientes ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE meal_plans ADD COLUMN deleted_at TIMESTAMP;

CREATE INDEX idx_clientes_deleted ON clientes(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NULL;
```

**ORDEN DE EJECUCIÓN:** 1 → 2 → 3 → 4 → 5 (dependencias críticas)

#### 2. ENV VARS ARCHITECTURE

Diseñar validación al boot. Crear `config/env_validator.py`:

**Variables CRÍTICAS (app NO arranca sin ellas en producción):**
```python
CRITICAL_ENV_VARS = [
    "DATABASE_URL",           # PostgreSQL connection
    "SECRET_KEY",             # JWT signing (min 32 chars)
    "LICENSE_SALT",           # License generation (min 16 chars)
    "STRIPE_SECRET_KEY",      # Payment provider
    "STRIPE_WEBHOOK_SECRET",  # Webhook verification
]

CRITICAL_IF_PRODUCTION = [
    "SENTRY_DSN",             # Error tracking
    "RESEND_API_KEY",         # Transactional email
]

# Stripe Price IDs (mover de constantes.py)
STRIPE_PRICE_STARTER = os.getenv("STRIPE_PRICE_STARTER")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO")
STRIPE_PRICE_ENTERPRISE = os.getenv("STRIPE_PRICE_ENTERPRISE")
```

**Validator function:**
```python
def validate_env_vars():
    """Called at app startup. Crashes if critical vars missing in production."""
    missing = [var for var in CRITICAL_ENV_VARS if not os.getenv(var)]
    
    if os.getenv("ENVIRONMENT") == "production":
        missing.extend([var for var in CRITICAL_IF_PRODUCTION if not os.getenv(var)])
    
    if missing:
        raise RuntimeError(f"Missing critical env vars: {', '.join(missing)}")
    
    # Validate formats
    if len(os.getenv("SECRET_KEY", "")) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    
    # Validate DATABASE_URL scheme
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        logger.warning("DATABASE_URL uses deprecated postgres:// scheme. Consider postgresql://")
```

#### 3. CSP NONCE IMPLEMENTATION

Diseñar estrategia para eliminar 'unsafe-inline':

**Problema actual (H-04):** Templates tienen `<script>` inline

**Solución:**
1. Generar nonce por request: `nonce = secrets.token_urlsafe(16)`
2. Inyectar nonce en Jinja2 context
3. Agregar `nonce="{{ csp_nonce }}"` a todos los scripts inline
4. CSP header: `script-src 'self' 'nonce-{{ nonce }}' cdn.jsdelivr.net`
5. SRI hashes para CDN scripts

**Archivos a refactorizar:**
- web/templates/*.html (buscar `<script>` sin src)
- web/middleware/security.py (agregar nonce generation)

#### 4. RATE LIMITING ARCHITECTURE

Diseñar rate limiting sin Redis (MVP) y con Redis (scale):

**MVP (in-memory, single instance):**
```python
# utils/rate_limiter.py
from collections import defaultdict
from datetime import datetime, timedelta

class InMemoryRateLimiter:
    def __init__(self):
        self.attempts = defaultdict(list)  # {key: [timestamp, ...]}
    
    def is_allowed(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Clean old attempts
        self.attempts[key] = [ts for ts in self.attempts[key] if ts > cutoff]
        
        if len(self.attempts[key]) >= max_attempts:
            return False
        
        self.attempts[key].append(now)
        return True
```

**Aplicar a:**
- `/auth/login` → 5 attempts per IP per 15 min
- `/auth/register` → 3 attempts per IP per 60 min
- `/api/*` → 1000 requests per user per hour

**Scale plan:** Cuando tengan 50+ gyms → migrar a Redis con `aioredis`

#### 5. LOGGING ARCHITECTURE

**Problema actual:** 80+ print(), sin structured logging

**Solución:**
```python
# config/logging_config.py
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "gym_id": getattr(record, "gym_id", None),
            "user_id": getattr(record, "user_id", None),
        }
        
        if record.exc_info and os.getenv("ENVIRONMENT") != "production":
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logging():
    if os.getenv("ENVIRONMENT") == "production":
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)
```

**Estrategia de migración:**
1. Buscar todos los `print()` → reemplazar por `logger.info()`
2. Buscar `except Exception` bare → agregar tipos específicos
3. Buscar `exc_info=True` → condicionar a `!= production`

#### 6. MULTI-TENANT RLS ACTIVATION

**Problema (H-15):** RLS policies creadas pero no activadas

**Solución:**
```python
# web/repositories/base_repository.py

async def set_current_tenant(db: AsyncSession, gym_id: str):
    """Set app.current_tenant for RLS enforcement."""
    await db.execute(text(f"SET app.current_tenant = '{gym_id}'"))

# Middleware
@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        current_user = get_current_user_from_jwt(request)
        if current_user and current_user.gym_id:
            await set_current_tenant(request.state.db, current_user.gym_id)
    
    response = await call_next(request)
    return response
```

**Validar con tests:**
- User de gym A no puede ver datos de gym B
- Query sin gym_id falla (RLS enforcement)

#### 7. DEPLOYMENT FIXES

**Dockerfile changes:**
```dockerfile
# Agregar validation step
RUN python -c "from config.env_validator import validate_env_vars; validate_env_vars()" || echo "Env validation skipped in build"

# Remove fonts/ copy if not needed
# COPY fonts/ /app/fonts/  # <-- comentar si web no usa
```

**railway.toml changes:**
```toml
[build]
builder = "dockerfile"

[deploy]
releaseCommand = "alembic upgrade head"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 5
```

**Procfile changes:**
```
web: alembic upgrade head && python web/main_web.py --no-browser
```

#### 8. ALEMBIC MIGRATION NAMING

**Problema (L-07):** UUID naming no ordena por fecha

**Fix:**
```ini
# alembic.ini
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(slug)s

# Ejemplo: 20260326_1430_add_gym_branding_table.py
```

#### 9. ARCHITECTURE DECISION RECORDS (ADRs)

Crear `docs/architecture/decisions/`:

**ADR-001: Multi-tenant shared database**
- Contexto: 10-50 gyms esperados
- Decisión: Shared DB con gym_id + RLS
- Alternativas consideradas: Schema per tenant, DB per tenant
- Consecuencias: Más simple de operar, suficiente para escala objetivo

**ADR-002: In-memory rate limiting para MVP**
- Contexto: Single instance Railway para empezar
- Decisión: In-memory limiter, migrar a Redis cuando horizontalmente escale
- Consecuencias: Limita a 1 pod hasta implementar Redis

**ADR-003: Branding dinámico en DB**
- Contexto: Cada gym necesita white-labeling
- Decisión: Tabla gym_branding con config per-gym
- Consecuencias: Jinja2 templates deben cargar dinámicamente

**ADR-004: Separación requirements.txt**
- Contexto: 4 archivos requirements confusos
- Decisión: Mantener separación (web/api/build/dev) pero agregar pip-compile
- Consecuencias: Lockfile requirements.lock para reproducibilidad

#### 10. SECURITY CHECKLIST

Crear `docs/SECURITY_CHECKLIST.md`:

```markdown
# Pre-Deploy Security Checklist

## Secrets Management
- [ ] SECRET_KEY es random, >= 32 chars, no está en código
- [ ] LICENSE_SALT es random, >= 16 chars, no está en código
- [ ] Stripe keys son production keys, no test keys
- [ ] DATABASE_URL no contiene password en logs

## Authentication
- [ ] Access tokens max 7 días
- [ ] Refresh token rotation implementado
- [ ] Rate limiting activo en /auth/*
- [ ] Audit logging de auth events funcionando

## Multi-Tenant Isolation
- [ ] RLS policies activadas en PostgreSQL
- [ ] Tests de cross-tenant access pasan
- [ ] Branding es per-gym, no global

## Headers & CSP
- [ ] CSP sin 'unsafe-inline'
- [ ] SRI hashes en CDN scripts
- [ ] CSRF cookie es httponly
- [ ] HSTS header presente

## Endpoints
- [ ] /metrics requiere autenticación
- [ ] /health no expone stack traces
- [ ] /docs solo disponible en dev/staging

## Infrastructure
- [ ] Migraciones se ejecutan pre-deploy
- [ ] Health check timeout es razonable
- [ ] No hay datos personales en código

## Compliance México
- [ ] Aviso de privacidad en landing
- [ ] RFC field en gym_settings para CFDI
- [ ] Branding permite customización completa
```

---

## 🛠️ FASE 2: PROMPT PARA IMPLEMENTADOR

**Rol:** Implementador Senior con 15 años en Python/FastAPI/PostgreSQL  
**Contexto:** Has recibido el diseño completo del Arquitecto (FASE 1)  
**Tarea:** Implementar TODOS los cambios con calidad producción  

### ORDEN DE IMPLEMENTACIÓN (CRÍTICO)

#### BLOQUE 1: Database Migrations (30 min)
1. Crear migration 1: `alembic revision -m "add_gym_branding_table"`
2. Crear migration 2: `alembic revision -m "add_gym_settings_table"`
3. Crear migration 3: `alembic revision -m "add_gym_licenses_table"`
4. Crear migration 4: `alembic revision -m "add_auth_audit_log_table"`
5. Crear migration 5: `alembic revision -m "add_soft_delete_timestamps"`
6. Fix `alembic.ini` file_template para naming por fecha
7. Crear migration 6: `alembic revision -m "migrate_branding_data"` (data migration)

**Data migration strategy:**
```python
# migrations/20260326_xxxx_migrate_branding_data.py
def upgrade():
    import json
    branding_path = "config/branding.json"
    if os.path.exists(branding_path):
        with open(branding_path) as f:
            data = json.load(f)
        
        # Insert into gym_branding for default gym
        op.execute(f"""
            INSERT INTO gym_branding (gym_id, business_name, phone, email, address, monthly_fee)
            SELECT id, '{data["gym_name"]}', '{data["phone"]}', '{data["email"]}', 
                   '{data["address"]}', {data.get("monthly_fee", 0)}
            FROM gyms
            WHERE email = 'demo@metodobase.com'  -- o identificador único
        """)
```

#### BLOQUE 2: Env Vars & Validation (20 min)
1. Crear `config/env_validator.py` según diseño Arquitecto
2. Actualizar `config/settings.py`:
   - Remover SECRET_KEY default
   - Remover LICENSE_SALT default  
   - Mover Stripe Price IDs a env vars
3. Actualizar `web/main_web.py`:
   ```python
   from config.env_validator import validate_env_vars
   
   def main():
       validate_env_vars()  # Fail fast!
       # ... resto del código
   ```
4. Crear `.env.example`:
   ```bash
   DATABASE_URL=postgresql://user:pass@localhost/metodobase
   SECRET_KEY=<generate-with-openssl-rand-hex-32>
   LICENSE_SALT=<generate-with-openssl-rand-hex-16>
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_PRICE_STARTER=price_...
   STRIPE_PRICE_PRO=price_...
   STRIPE_PRICE_ENTERPRISE=price_...
   ENVIRONMENT=production
   SENTRY_DSN=https://...
   RESEND_API_KEY=re_...
   ```

#### BLOQUE 3: Limpieza de Datos Personales (30 min)
1. **config/branding.json** → Convertir en template:
   ```json
   {
     "gym_name": "{{ GYM_NAME }}",
     "phone": "{{ GYM_PHONE }}",
     "email": "{{ GYM_EMAIL }}",
     "address": "{{ GYM_ADDRESS }}",
     "whatsapp": "{{ GYM_WHATSAPP }}",
     "monthly_fee": 0,
     "note": "This is a template. Real branding is stored in gym_branding table."
   }
   ```

2. **build_config.py**:
   ```python
   APP_NAME = "MetodoBase"
   APP_AUTHOR = "MetodoBase"  # Remover "Consultoría Hernández"
   ```

3. **README_COMERCIAL.md**:
   ```markdown
   Para consultas: [VENDOR_EMAIL]
   ```

4. **LICENSE**:
   ```
   Copyright (c) 2026 MetodoBase Contributors
   Contact: legal@metodobase.com
   ```

5. **web/pages/landing.html** (línea 219):
   ```html
   <a href="mailto:{{ gym.email }}">{{ gym.email }}</a>
   ```

6. **web/templates/suscripciones.html** (líneas 203, 208):
   ```html
   <a href="https://wa.me/{{ gym.whatsapp }}">
   ```

7. **api/factura_pdf.py** (línea 161):
   ```python
   gym_branding = await get_gym_branding(db, user.gym_id)
   pdf_data["gym_email"] = gym_branding.email
   ```

#### BLOQUE 4: Security Fixes (45 min)
1. **CSP nonce implementation:**
   - `web/middleware/security.py`: Agregar nonce generation
   - Actualizar CSP header: remover 'unsafe-inline', agregar 'nonce-{nonce}'
   - Templates: agregar `nonce="{{ csp_nonce }}"` a scripts inline

2. **SRI hashes (H-05):**
   ```html
   <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"
           integrity="sha384-..."
           crossorigin="anonymous"></script>
   ```
   Generar hashes: `curl <URL> | openssl dgst -sha384 -binary | openssl base64 -A`

3. **CSRF httponly (H-03):**
   ```python
   response.set_cookie(
       "csrf_token",
       value=token,
       httponly=True,  # <-- agregar
       secure=True,
       samesite="lax"
   )
   ```

4. **Rate limiting (H-06):**
   - Crear `utils/rate_limiter.py`
   - Aplicar a `/auth/login`, `/auth/register`
   - Decorator: `@rate_limit(max_attempts=5, window_seconds=900)`

5. **Auth audit logging (H-07):**
   - Crear `web/services/auth_audit.py`
   - Log en: login success/failed, password change, user created/deleted
   - Incluir: IP, user agent, request ID

6. **Access token expiry (H-08):**
   ```python
   ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 días (antes 30 días)
   ```

7. **/metrics auth (H-09):**
   ```python
   @app.get("/metrics")
   async def metrics(current_user: User = Depends(require_admin)):
       # Solo admins pueden ver métricas
   ```

8. **Health check no exponer errores (C-11):**
   ```python
   @app.get("/health")
   async def health_check():
       try:
           await db.execute(text("SELECT 1"))
           return {"status": "ok"}
       except Exception:
           return JSONResponse(
               status_code=503,
               content={"status": "error"}  # NO incluir str(e)
           )
   ```

9. **exc_info en producción (M-08):**
   ```python
   except Exception as e:
       logger.error(
           "Error processing request",
           exc_info=(os.getenv("ENVIRONMENT") != "production")
       )
   ```

#### BLOQUE 5: Multi-Tenant Fixes (40 min)
1. **Crear repositories para gym_branding, gym_settings, gym_licenses:**
   - `web/repositories/gym_branding_repository.py`
   - `web/repositories/gym_settings_repository.py`
   - `web/repositories/gym_licenses_repository.py`

2. **Activar RLS (H-15):**
   - Middleware para `SET app.current_tenant`
   - Tests de cross-tenant isolation

3. **Branding dinámico:**
   - Actualizar `core/branding.py` para cargar de DB
   - Cache de branding (TTL 5 min)

4. **Licencias persistidas (H-02):**
   - Migrar `core/licencia.py` de in-memory a gym_licenses table
   - Crear service: `web/services/license_service.py`

#### BLOQUE 6: Logging & Observability (30 min)
1. **Structured logging:**
   - Crear `config/logging_config.py`
   - Setup en `web/main_web.py`

2. **Reemplazar print():**
   - Buscar: `git grep -n "print(" | grep -v "# print" | grep "\.py:"`
   - Reemplazar por `logger.info()` / `logger.debug()`
   - ~80 instancias

3. **Fix datetime.utcnow():**
   - Buscar: `git grep -n "datetime.utcnow()"`
   - Reemplazar por `datetime.now(timezone.utc)`
   - ~51 instancias

4. **Request ID en errores:**
   ```python
   @app.exception_handler(Exception)
   async def global_exception_handler(request: Request, exc: Exception):
       request_id = request.state.request_id
       return JSONResponse(
           status_code=500,
           content={
               "error": "Internal server error",
               "request_id": request_id
           }
       )
   ```

#### BLOQUE 7: Code Cleanup (25 min)
1. **Eliminar archivos muertos:**
   ```bash
   rm utils/updater.py
   rm _test_imports.py _test_panels.py test_qss.py
   rm web/static/js/charts.js.bak
   rm web/static/css/styles.css.bak
   rm web/templates/dashboard.html.bak
   rmdir core/services/security/
   ```

2. **Fix docstrings CustomTkinter:**
   - `utils/helpers.py` línea 40
   - `utils/iconos.py` línea 6

3. **Fix bare excepts (L-01):**
   - Buscar: `except Exception:`
   - Especificar tipos: `except (ValueError, KeyError) as e:`
   - ~40 instancias

#### BLOQUE 8: Infrastructure (20 min)
1. **Dockerfile:**
   ```dockerfile
   # Validar env vars (sin crash en build)
   RUN python -c "import os; print('Env validation will run at runtime')"
   
   # Comentar fonts si no se usan en web
   # COPY fonts/ /app/fonts/
   ```

2. **railway.toml:**
   ```toml
   [deploy]
   releaseCommand = "alembic upgrade head"
   ```

3. **Procfile:**
   ```
   web: python web/main_web.py --no-browser
   ```
   (migraciones via railway.toml releaseCommand)

4. **requirements_web.txt:**
   - Cambiar `psycopg2-binary` → `psycopg2` (o `psycopg[binary]`)
   - Agregar `python-jose[cryptography]` (si falta)

5. **Crear requirements.lock:**
   ```bash
   pip-compile requirements_web.txt -o requirements_web.lock
   ```

#### BLOQUE 9: Parametrization (15 min)
1. **Mover a env vars:**
   - Stripe Price IDs (ya hecho en BLOQUE 2)
   - Trial settings → table gym_settings
   - Horarios comida → table gym_settings

2. **Config constantes.py:**
   - Keep: MACROS, food categories (shared baseline)
   - Move: trial_days, trial_max_clients, horarios → DB

#### BLOQUE 10: Empty States (10 min)
1. **Dashboard 0 clientes (L-02):**
   ```html
   {% if clientes|length == 0 %}
   <div class="empty-state">
     <img src="/static/img/empty-clients.svg" alt="No clients yet">
     <h3>Aún no tienes clientes</h3>
     <p>Comienza agregando tu primer cliente para generar planes nutricionales.</p>
     <a href="/clientes/nuevo" class="btn btn-primary">Agregar Cliente</a>
   </div>
   {% endif %}
   ```

#### BLOQUE 11: Test Fixtures (10 min)
1. **Credenciales únicas (L-03):**
   ```python
   # conftest.py
   TEST_USER_EMAIL = f"test_{uuid.uuid4().hex[:8]}@test.com"
   DEMO_USER_EMAIL = "demo@metodobase.com"  # Separar concerns
   ```

#### BLOQUE 12: Desktop App Fix (5 min)
1. **gym_app_window.py línea hardcoded (L-08):**
   ```python
   API_DOCS_URL = os.getenv("API_DOCS_URL", "http://localhost:8000/docs")
   ```

#### BLOQUE 13: Documentation (10 min)
1. Crear `CHANGELOG.md`:
   ```markdown
   ## [2.0.0] - 2026-03-26
   
   ### BREAKING CHANGES
   - Branding moved from config/branding.json to gym_branding table
   - Licenses now persisted in database
   - SECRET_KEY and LICENSE_SALT must be provided via env vars
   
   ### Added
   - Multi-tenant branding system
   - Auth audit logging
   - Rate limiting on authentication endpoints
   - CSP nonce-based implementation
   - SRI hashes for CDN scripts
   - Structured logging (JSON in production)
   - Soft delete timestamps
   - Empty states for dashboard
   
   ### Fixed
   - Health check no longer exposes stack traces
   - CSRF cookie now httponly
   - Access tokens reduced to 7 days max
   - /metrics endpoint now requires authentication
   - RLS policies now activated
   - 80+ print() replaced with logger
   - 51 datetime.utcnow() replaced with datetime.now(UTC)
   - 40 bare except Exception handlers now specific
   
   ### Removed
   - Dead code: utils/updater.py, test scripts, .bak files
   - Personal data from all files
   - CustomTkinter references in docstrings
   
   ### Security
   - Eliminated hardcoded secrets
   - Implemented defense in depth (CSP + httponly + SRI + rate limiting)
   - Added auth audit trail
   ```

2. Actualizar `README.md`:
   - Agregar sección "Environment Variables"
   - Agregar sección "Production Deployment"
   - Agregar link a SECURITY_CHECKLIST.md

---

## 🧪 FASE 3: PROMPT PARA QA

**Rol:** QA/Test Engineer Senior con 15 años en testing de SaaS críticos  
**Contexto:** Implementador completó TODOS los cambios de FASE 2  
**Tarea:** Validar exhaustivamente antes de producción  

### TEST PLAN

#### 1. DATABASE MIGRATIONS (CRÍTICO)
```bash
# Test upgrade
alembic upgrade head
echo $?  # debe ser 0

# Test downgrade (cada migration)
alembic downgrade -1
alembic upgrade +1

# Test data integrity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM gym_branding;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM gym_settings;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM gym_licenses;"
```

**Validaciones:**
- [ ] Todas las migrations se ejecutan sin errores
- [ ] Downgrade funciona (rollback safety)
- [ ] Data migration pobló gym_branding correctamente
- [ ] Foreign keys están bien definidas
- [ ] Indexes existen

#### 2. ENV VARS VALIDATION
```bash
# Test sin SECRET_KEY
unset SECRET_KEY
python web/main_web.py  # debe fallar con error claro

# Test con SECRET_KEY corto
export SECRET_KEY="tooshort"
python web/main_web.py  # debe fallar

# Test con todas las vars
export SECRET_KEY=$(openssl rand -hex 32)
export LICENSE_SALT=$(openssl rand -hex 16)
python web/main_web.py  # debe arrancar
```

**Validaciones:**
- [ ] App no arranca sin SECRET_KEY en producción
- [ ] App valida longitud mínima de secretos
- [ ] Error messages son claros
- [ ] .env.example tiene todas las vars necesarias

#### 3. SECURITY TESTS
```bash
# CSP test
curl -I http://localhost:8000/ | grep "Content-Security-Policy"
# debe tener: script-src 'self' 'nonce-...' (NO 'unsafe-inline')

# SRI test
curl http://localhost:8000/ | grep 'integrity="sha384-'
# debe tener hashes en scripts CDN

# CSRF httponly test
curl -I http://localhost:8000/login | grep "Set-Cookie"
# debe tener: csrf_token=...; HttpOnly; Secure

# Rate limiting test
for i in {1..10}; do
  curl -X POST http://localhost:8000/auth/login \
    -d '{"email":"test@test.com","password":"wrong"}' \
    -H "Content-Type: application/json"
done
# request 6+ deben retornar 429 Too Many Requests

# /metrics auth test
curl http://localhost:8000/metrics
# debe retornar 401 Unauthorized

# Health check no expone errors
# (simular DB down)
curl http://localhost:8000/health
# debe retornar {"status": "error"} sin stack trace
```

**Validaciones:**
- [ ] CSP no tiene 'unsafe-inline'
- [ ] CDN scripts tienen SRI hashes válidos
- [ ] CSRF cookie es httponly
- [ ] Rate limiting funciona (5 intentos max)
- [ ] /metrics requiere autenticación
- [ ] Health check no filtra información sensible

#### 4. MULTI-TENANT ISOLATION
```python
# tests/test_multi_tenant_isolation.py
import pytest

async def test_cross_tenant_data_leak(client, gym_a_user, gym_b_user):
    """User de gym A no puede ver clientes de gym B."""
    # Login como gym A
    token_a = await get_jwt_token(client, gym_a_user)
    
    # Crear cliente en gym A
    client_a = await create_client(client, token=token_a, name="Cliente A")
    
    # Login como gym B
    token_b = await get_jwt_token(client, gym_b_user)
    
    # Intentar acceder a cliente de gym A
    response = await client.get(
        f"/api/clientes/{client_a.id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    
    assert response.status_code == 404  # o 403

async def test_rls_enforcement(db):
    """RLS debe prevenir queries sin gym_id."""
    # NO establecer app.current_tenant
    with pytest.raises(Exception):  # RLS debe bloquear
        await db.execute(text("SELECT * FROM clientes"))
```

**Validaciones:**
- [ ] Cross-tenant access retorna 404/403
- [ ] RLS policies están activas
- [ ] Branding es per-gym (no leak entre gyms)
- [ ] Licencias son per-gym

#### 5. AUTH & AUDIT
```python
async def test_auth_audit_log(client, db):
    """Login exitoso debe crear audit log."""
    await client.post("/auth/login", json={
        "email": "test@test.com",
        "password": "correct"
    })
    
    logs = await db.execute(
        text("SELECT * FROM auth_audit_log WHERE event_type='login_success'")
    )
    assert len(logs.fetchall()) > 0

async def test_failed_login_audit(client, db):
    """Login fallido debe crear audit log."""
    await client.post("/auth/login", json={
        "email": "test@test.com",
        "password": "wrong"
    })
    
    logs = await db.execute(
        text("SELECT * FROM auth_audit_log WHERE event_type='login_failed'")
    )
    assert len(logs.fetchall()) > 0
```

**Validaciones:**
- [ ] Login success logueado
- [ ] Login failed logueado
- [ ] Logs incluyen IP, user agent, request ID
- [ ] Access token expiry es <= 7 días

#### 6. LOGGING
```bash
# Test structured logging en producción
export ENVIRONMENT=production
python web/main_web.py &
PID=$!

curl http://localhost:8000/api/clientes

# Logs deben ser JSON
kill $PID

# Test no stack traces en producción
# (simular error)
# logs NO deben tener exc_info
```

**Validaciones:**
- [ ] Logs en producción son JSON
- [ ] No hay print() en stdout (solo logger)
- [ ] No hay exc_info=True en producción
- [ ] Request IDs en todos los logs

#### 7. CODE QUALITY
```bash
# No print() en código (excepto debug scripts)
git grep -n "print(" -- '*.py' | grep -v "# print" | grep -v "test_" | wc -l
# debe ser 0

# No datetime.utcnow()
git grep -n "datetime.utcnow()" -- '*.py' | wc -l
# debe ser 0

# No bare except Exception
git grep -n "except Exception:" -- '*.py' | wc -l
# debe ser 0 o muy pocos con justificación

# No archivos muertos
ls utils/updater.py _test_imports.py 2>/dev/null
# no deben existir

# No .bak files
find . -name "*.bak" | wc -l
# debe ser 0
```

**Validaciones:**
- [ ] 0 print() en código productivo
- [ ] 0 datetime.utcnow()
- [ ] 0 bare except sin justificación
- [ ] 0 archivos muertos
- [ ] 0 referencias CustomTkinter

#### 8. FULL TEST SUITE
```bash
python -m pytest -v --tb=short --cov=.
```

**Validaciones:**
- [ ] Todos los tests pasan
- [ ] Coverage >= 80%
- [ ] No warnings críticos

#### 9. SMOKE TESTS
```bash
# Build Docker image
docker build -t metodobase:test .

# Run con env vars
docker run -d \
  -e DATABASE_URL=$DATABASE_URL \
  -e SECRET_KEY=$SECRET_KEY \
  -e LICENSE_SALT=$LICENSE_SALT \
  -p 8000:8000 \
  metodobase:test

# Wait for health
sleep 10
curl http://localhost:8000/health

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@metodobase.com","password":"demo123"}'

# Test API
curl http://localhost:8000/api/clientes \
  -H "Authorization: Bearer <token>"

docker stop <container>
```

**Validaciones:**
- [ ] Docker build exitoso
- [ ] Migraciones se ejecutan en container
- [ ] Health check responde OK
- [ ] Auth funciona
- [ ] API responde correctamente

#### 10. SECURITY CHECKLIST
Validar `docs/SECURITY_CHECKLIST.md`:
- [ ] Todos los items marcados
- [ ] Screenshot/evidencia de cada check

### REPORTE DE QA

Al finalizar, crear `QA_REPORT_2026-03-26.md`:

```markdown
# QA Report — Production Refactor 2026-03-26

## Executive Summary
- Total tests executed: X
- Passed: Y
- Failed: Z
- Blockers: N

## Test Results

### ✅ PASSED
- Database migrations (up/down)
- Env vars validation
- CSP implementation
- SRI hashes
- Rate limiting
- Multi-tenant isolation
- Auth audit logging
- Code cleanup
- (lista completa)

### ❌ FAILED
- (si hay fallos, detallar con pasos para reproducir)

### ⚠️ WARNINGS
- (issues no bloqueantes pero a considerar)

## Performance
- Startup time: X ms
- Migration time: Y s
- API response time avg: Z ms

## Recommendations
1. (sugerencias para FASE 4)
2. ...

## Sign-off
Ready for production: YES/NO

QA Engineer: [nombre]
Date: 2026-03-26
```

---

## 🔧 FASE 4: PROMPT PARA IMPLEMENTADOR (AJUSTES)

**Rol:** Implementador Senior (mismo de FASE 2)  
**Contexto:** QA encontró issues en QA_REPORT_2026-03-26.md  
**Tarea:** Fix TODOS los issues reportados  

### WORKFLOW

Para cada issue reportado por QA:

1. **Reproducir el problema:**
   ```bash
   # Usar pasos exactos del QA report
   ```

2. **Identificar root cause:**
   - ¿Error en implementación?
   - ¿Test incorrecto?
   - ¿Edge case no considerado?

3. **Implementar fix:**
   - Escribir el código
   - Agregar test que cubra el caso
   - Validar localmente

4. **Actualizar CHANGELOG.md:**
   ```markdown
   ### Fixed (Post-QA)
   - [Issue #1]: Descripción del problema y solución
   - [Issue #2]: ...
   ```

5. **Re-ejecutar tests afectados:**
   ```bash
   pytest tests/test_specific.py -v
   ```

6. **Notificar a QA para re-validación:**
   - Crear comentario en issue
   - Marcar como "Ready for Re-test"

### CRITERIO DE SALIDA

- [ ] TODOS los issues de QA resueltos
- [ ] Todos los tests pasan
- [ ] QA sign-off recibido
- [ ] CHANGELOG actualizado
- [ ] Lista para merge a main

---

## 📊 MÉTRICAS DE ÉXITO

Al completar las 4 fases, validar:

### CHECKLIST FINAL

#### Seguridad
- [ ] 0 datos personales en código
- [ ] 0 secretos hardcodeados
- [ ] CSP sin 'unsafe-inline'
- [ ] SRI en todos los CDN scripts
- [ ] Rate limiting activo
- [ ] Auth audit logging funcionando
- [ ] /metrics protegido
- [ ] Health check seguro

#### Multi-Tenant
- [ ] Branding dinámico per-gym
- [ ] Licencias persistidas en DB
- [ ] RLS policies activas
- [ ] Tests de isolation pasan

#### Calidad
- [ ] 0 print() en código
- [ ] 0 datetime.utcnow()
- [ ] 0 bare except sin justificación
- [ ] 0 código muerto
- [ ] Logging estructurado
- [ ] Request IDs en errores

#### Infraestructura
- [ ] Migraciones automáticas en deploy
- [ ] Env vars validadas al boot
- [ ] Docker build exitoso
- [ ] Railway deploy exitoso

#### Compliance
- [ ] Sin datos personales expuestos
- [ ] Aviso de privacidad presente
- [ ] RFC field para CFDI
- [ ] Branding customizable

### EVIDENCIA REQUERIDA

1. Screenshot de todos los tests pasando
2. Screenshot de Docker build exitoso
3. Screenshot de Railway deploy exitoso
4. Screenshot de health check respondiendo
5. Output de security scans (opcional: OWASP ZAP)
6. QA sign-off document

---

## 🚀 POST-REFACTOR (Bonus)

Una vez completadas las 4 fases:

### Siguiente nivel (Fase 5+)
- [ ] Onboarding wizard para nuevos gyms
- [ ] Email transaccional (welcome, payment confirmation, etc)
- [ ] Dashboard analytics avanzado
- [ ] White-labeling completo (custom domain)
- [ ] App móvil / PWA
- [ ] API pública documentada
- [ ] Sistema CFDI integrado

### Monitoreo post-deploy
- [ ] Configurar alertas en Sentry
- [ ] Configurar uptime monitoring
- [ ] Configurar performance monitoring (Datadog/New Relic)
- [ ] Establecer SLOs (99.9% uptime, p95 < 500ms)

### Load testing
```bash
# k6 script
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 }, // ramp up
    { duration: '5m', target: 100 }, // stay
    { duration: '2m', target: 0 },   // ramp down
  ],
};

export default function() {
  let res = http.get('https://metodobase.com/health');
  check(res, { 'status 200': (r) => r.status === 200 });
}
```

---

## 📞 SOPORTE & ESCALACIÓN

Si encuentras problemas:

1. **Bloqueantes de arquitectura:** Consultar con Arquitecto Senior
2. **Bugs complejos:** Pair programming con otro Implementador
3. **Tests fallando:** Consultar con QA para clarificar expectativas
4. **Dudas de producto:** Consultar Product Owner / Stakeholder

**Principio:** No avanzar si hay dudas arquitectónicas. Mejor pausar y clarificar que implementar incorrectamente.

---

## ✅ SIGN-OFF

Este prompt ha sido diseñado por un Arquitecto Senior con 15 años de experiencia en SaaS competitivos (Stripe-level, Notion-level, Linear-level).

**Garantías:**
- ✅ Cubre TODOS los issues de AUDITORIA_PRODUCCION_2026-03-25.txt
- ✅ Arquitectura production-ready
- ✅ Security-first approach
- ✅ Multi-tenant desde el núcleo
- ✅ Estrategia de testing exhaustiva
- ✅ Plan de rollback (migrations down)
- ✅ Documentación completa

**Revisión:** Marzo 26, 2026  
**Autor:** Senior SaaS Architect  
**Versión:** 1.0  

**INICIO DE EJECUCIÓN:** Proceder con FASE 1 (Arquitecto) →

