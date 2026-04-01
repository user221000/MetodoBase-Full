# PROMPT: Hardening de Seguridad y Resiliencia — MetodoBase SaaS

## ROL Y CONTEXTO

Eres un **Arquitecto de Software Senior con 15+ años de experiencia construyendo plataformas SaaS multi-tenant competitivas** (Stripe, Linear, Vercel). Tu expertise incluye: seguridad OWASP Top 10 2025, hardening de APIs, compliance fiscal LATAM, zero-trust architecture, y operación de sistemas en producción con SLAs de 99.95%+.

Estás trabajando en **MetodoBase**, una plataforma SaaS de nutrición para gimnasios construida con:

- **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic (PostgreSQL en producción)
- **Auth:** HMAC-SHA256 tokens propios (access + refresh con rotación)
- **Frontend Web:** Jinja2 + HTMX + Chart.js (CDN)
- **Pagos:** Stripe + MercadoPago (mercado mexicano)
- **Infraestructura:** Docker → Railway (multi-pod)
- **Multi-tenant:** gym_id en JWT, RBAC con 4 roles (owner/admin/nutriologo/viewer)
- **DB Legacy:** SQLite para auth (`web_usuarios.db`), PostgreSQL para datos de negocio

El sistema tiene **1,030 tests pasando**. Tu trabajo es implementar fixes de seguridad y resiliencia **sin romper tests existentes**, con calidad de producción competitiva 2026.

---

## HALLAZGOS A RESOLVER (19 issues: 1 Crítico + 18 Altos)

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### C-11 | HEALTH CHECK EXPONE ERRORES INTERNOS
**Archivo:** `api/app.py` (líneas 145-165)

**Código actual:**
```python
@app.get("/health", tags=["System"])
async def health_check():
    status = {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
    checks = {}
    try:
        from web.database.engine import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "type": "sqlalchemy"}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}  # ← FUGA DE INFO
        status["status"] = "degraded"
    try:
        from config.feature_flags import get_migration_flags
        flags = get_migration_flags()
        checks["migration_phase"] = flags.current_phase()
    except Exception as e:
        checks["migration_phase"] = f"error: {e}"  # ← FUGA DE INFO
    checks["version"] = "2.0.0"
    status["checks"] = checks
    return status
```

**Problema:** `str(e)` en respuesta HTTP expone paths internos, queries SQL, y detalles de conexión a atacantes. Violación de OWASP A01:2021 (Broken Access Control) y principio de información mínima.

**Requerimiento:**
1. Eliminar `str(e)` de TODA respuesta HTTP — retornar solo `{"status": "error"}` sin detalles
2. Loguear el error completo internamente con `logger.error("Health check DB failed", exc_info=True)`
3. NO exponer `migration_phase` en producción — es información de arquitectura interna
4. Retornar HTTP 503 cuando status es "degraded" (no 200 con body degraded)
5. Mantener `/health/ready` como está (ya es correcto)

---

### H-01 | JWT TOKEN TYPE NO VALIDADO ESTRICTAMENTE
**Archivo:** `web/auth.py` (~línea 410)

**Código actual:**
```python
def verificar_token(token: str) -> Optional[dict]:
    payload = _decode_token(token)
    if not payload:
        return None
    token_type = payload.get("type", "access")  # ← DEFAULT INSEGURO
    if token_type != "access":
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload
```

**Problema:** Un token sin campo `"type"` es aceptado como access token. Un refresh token sin `type` (o un token forjado) pasa la validación. Esto es una vulnerabilidad de escalación de privilegios.

**Requerimiento:**
1. Cambiar a: `token_type = payload.get("type")` — sin default
2. Si `token_type` es `None`: `return None` inmediatamente
3. Mantener la validación `if token_type != "access": return None`
4. Agregar log: `logger.warning("[AUTH] Token sin type recibido sub=%s", payload.get("id", "?"))`
5. Lo mismo aplica para `verificar_refresh_token()` — ya valida `payload.get("type") != "refresh"`, verificar que no haya default

---

### H-02 | LICENCIAS ALMACENADAS EN MEMORIA
**Archivo:** `api/routes/licencias.py`

**Código actual:**
```python
_licencias_activas: dict[str, dict] = {}  # ← SE PIERDE AL REINICIAR

@router.post("/licencias/activar", response_model=LicenciaResponse)
async def activar_licencia(req: ActivarLicenciaRequest):
    plan = _plan_desde_clave(req.clave)
    # ...
    _licencias_activas[req.hardware_id] = registro  # ← EN MEMORIA
```

**Problema:** En Railway con múltiples pods o tras un redeploy, todas las activaciones de licencia se pierden. Los gimnasios pagan y pierden acceso.

**Requerimiento:**
1. Crear modelo SQLAlchemy `LicenseActivation` en `web/database/models.py`:
   ```python
   class LicenseActivation(Base):
       __tablename__ = "license_activations"
       id = Column(Integer, primary_key=True, autoincrement=True)
       hardware_id = Column(String(128), nullable=False, unique=True, index=True)
       clave_hash = Column(String(64), nullable=False)  # SHA-256
       email = Column(String(120), nullable=False)
       plan = Column(String(30), nullable=False)
       activa = Column(Boolean, default=True)
       revocada = Column(Boolean, default=False)
       expira = Column(DateTime, nullable=False)
       created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
   ```
2. Crear migración Alembic: `alembic revision --autogenerate -m "add_license_activations"`
3. Refactorizar endpoints para usar DB en lugar de `_licencias_activas`
4. Usar `datetime.now(timezone.utc)` en lugar de `datetime.utcnow()` (deprecated Python 3.12+)
5. Eliminar el dict `_licencias_activas` completamente

---

### H-03 | CSRF COOKIE ACCESIBLE POR JAVASCRIPT
**Archivo:** `web/middleware/csrf.py` (~línea 286)

**Código actual:**
```python
response.set_cookie(
    key=CSRF_COOKIE_NAME,
    value=token,
    max_age=TOKEN_EXPIRY_SECONDS,
    httponly=False,  # JavaScript needs to read for AJAX ← INSEGURO
    secure=self.cookie_secure,
    samesite=self.cookie_samesite,
)
```

**Problema:** Si existe cualquier XSS (y H-04 confirma que CSP permite `unsafe-inline`), el atacante lee el CSRF token del cookie y ejecuta CSRF attacks.

**Requerimiento:**
1. Cambiar a `httponly=True` en el cookie
2. Proveer el CSRF token al JavaScript vía **meta tag en HTML**:
   ```html
   <meta name="csrf-token" content="{{ csrf_token }}">
   ```
3. En `web/templates/base.html`, agregar el meta tag dentro de `<head>`
4. Actualizar los archivos JS que hacen AJAX para leer el token del meta tag:
   ```javascript
   const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
   // Incluir en headers: 'X-CSRF-Token': csrfToken
   ```
5. Verificar que `csrf_input_html()` sigue funcionando para forms HTML estándar

---

### H-04 | CSP PERMITE 'unsafe-inline' EN SCRIPTS
**Archivo:** `web/middleware/security_headers.py` (línea 55)

**Código actual:**
```python
directives = {
    "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
    "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
    # ...
}
```

**Problema:** `'unsafe-inline'` en `script-src` neutraliza completamente la protección CSP contra XSS. Cualquier inyección de `<script>` en la página se ejecuta.

**Requerimiento:**
1. **Implementar sistema de nonces CSP:**
   - Generar nonce único por request: `secrets.token_urlsafe(16)`
   - Almacenar en `request.state.csp_nonce`
   - CSP queda: `"script-src": "'self' 'nonce-{nonce}' https://cdn.jsdelivr.net"`
2. **Migrar inline scripts a archivos .js externos:**
   - En `base.html`, el auth guard inline:
     ```javascript
     const token = localStorage.getItem('mb_token');
     if (!token) { window.location.replace('/'); }
     ```
     Mover a `/static/js/auth-guard.js`
   - Buscar y migrar TODOS los `<script>` inline en templates
3. **Para scripts que DEBEN ser inline** (edge cases), agregar atributo nonce:
   ```html
   <script nonce="{{ request.state.csp_nonce }}">...</script>
   ```
4. **Mantener `'unsafe-inline'` en `style-src`** — es aceptable para estilos y necesario para HTMX
5. Proveer el nonce como variable Jinja2 disponible en todos los templates

---

### H-05 | CDN SCRIPTS SIN SRI (Subresource Integrity)
**Archivo:** `web/templates/base.html`

**Código actual:**
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
```

**Problema:** Si jsdelivr es comprometido o sufre un MITM, código malicioso se ejecuta en TODOS los gyms. Supply-chain attack vector.

**Requerimiento:**
1. Generar hashes SRI para cada recurso CDN:
   ```bash
   curl -s https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js | openssl dgst -sha384 -binary | openssl base64 -A
   ```
2. Agregar `integrity` y `crossorigin` a TODOS los `<script>` y `<link>` CDN:
   ```html
   <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"
           integrity="sha384-{HASH_REAL}"
           crossorigin="anonymous"></script>
   ```
3. Agregar `crossorigin="anonymous"` también a Google Fonts `<link>`
4. **Incluir los CDN domains en CSP** (ya están en `script-src`)
5. Verificar que Google Fonts CSS import funciona con SRI (font CSS puede cambiar — evaluar si conviene self-host las fuentes)

---

### H-06 | NO HAY RATE LIMITING EN LOGIN
**Archivo:** `web/main_web.py`

**Contexto:** El middleware `RateLimitMiddleware` existe y aplica 60 req/min global, pero el endpoint de login NO tiene rate limiting específico. 5 req/min por IP serían 300 intentos/hora de fuerza bruta.

**Código actual de login (no tiene rate limit):**
```python
@app.post("/api/auth/login")
async def login(req: LoginRequest, request: Request):
    # ... verifica credenciales directamente
```

**Requerimiento:**
1. Aplicar rate limit **específico al login** usando `rate_limit_dependency`:
   ```python
   from web.middleware.rate_limiter import rate_limit_dependency
   
   @app.post("/api/auth/login", dependencies=[Depends(rate_limit_dependency(attempts=5, window=900))])
   ```
   → 5 intentos por 15 minutos por IP
2. Aplicar lo mismo a `/api/auth/login-gym` y `/api/auth/login-usuario`
3. **Implementar lockout exponencial:** tras 5 intentos fallidos, bloquear la IP por `window` segundos. Tras 10, bloquear por 1 hora.
4. Retornar `429 Too Many Requests` con header `Retry-After`
5. NO aplicar rate limit a `/api/auth/refresh` ni `/api/auth/logout` (no son vectores de fuerza bruta)

---

### H-07 | NO HAY AUDIT LOG DE AUTENTICACIÓN
**Archivo:** `web/auth.py`

**Código actual:** La función `verificar_credenciales()` no loguea nada.

**Requerimiento:**
1. En `verificar_credenciales()`, agregar logging:
   - **Login exitoso:** `logger.info("[AUTH] Login exitoso: email=%s tipo=%s ip=%s", email, tipo, ip)`
   - **Password incorrecto:** `logger.warning("[AUTH] Login fallido (password): email=%s ip=%s", email, ip)`
   - **Usuario no encontrado:** `logger.warning("[AUTH] Login fallido (no existe): email=%s ip=%s", email, ip)`
   - **Tipo incorrecto:** `logger.warning("[AUTH] Login fallido (tipo): email=%s tipo_req=%s ip=%s", email, tipo_requerido, ip)`
2. **NO loguear el password** — nunca, bajo ninguna circunstancia
3. Pasar `ip` como parámetro opcional a `verificar_credenciales()` — el endpoint lo extrae de `request.client.host`
4. Estos logs deben ser parseables por herramientas de monitoreo (Sentry, Datadog). Usar formato estructurado consistente con prefijo `[AUTH]`
5. **Tabla AuditLog ya existe** en `web/database/models.py` — considerar también persistir los eventos de auth críticos ahí (login fallido, lockout)

---

### H-08 | REMEMBER-ME TOKEN VÁLIDO 30 DÍAS
**Archivo:** `web/auth.py` (~línea 370)

**Código actual:**
```python
def crear_access_token(usuario: dict, remember_me: bool = False) -> str:
    if remember_me:
        exp = time.time() + 30 * 86400  # 30 días ← EXCESIVO
    else:
        exp = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 15 min

def crear_refresh_token(usuario: dict, remember_me: bool = False) -> str:
    if remember_me:
        exp = time.time() + 90 * 86400  # 90 días ← EXCESIVO
    else:
        exp = time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 86400  # 7 días
```

**Problema:** Un access token de 30 días es efectivamente una sesión permanente. Si se roba (XSS, MITM, log leak), el atacante tiene acceso por un mes sin posibilidad de revocación (los access tokens no se verifican contra BD).

**Requerimiento:**
1. **Access token máximo:** 7 días con remember_me (no 30). Sin remember_me: 15 min (mantener)
2. **Refresh token máximo:** 30 días con remember_me (no 90). Sin remember_me: 7 días (mantener)
3. **Leer duraciones de `settings`** en vez de hardcodear:
   ```python
   settings = get_settings()
   if remember_me:
       exp = time.time() + settings.REMEMBER_ME_ACCESS_DAYS * 86400  # 7 days
   ```
4. Agregar a `config/settings.py`:
   ```python
   self.REMEMBER_ME_ACCESS_DAYS: int = int(os.getenv("REMEMBER_ME_ACCESS_DAYS", "7"))
   self.REMEMBER_ME_REFRESH_DAYS: int = int(os.getenv("REMEMBER_ME_REFRESH_DAYS", "30"))
   ```
5. **Documentar en settings** que access tokens NO son revocables (stateless), por eso su duración debe ser corta

---

### H-09 | /metrics Y /health SIN AUTENTICACIÓN
**Archivo:** `api/app.py` (líneas 136-220)

**Código actual:** Los endpoints `/metrics`, `/alerts`, y `/health/circuits` son públicos.

**Requerimiento:**
1. **`/health`** → mantener público (requerido por Railway health check y load balancers)
2. **`/health/ready`** → mantener público (Kubernetes readiness probe)
3. **`/metrics`** → proteger con API key:
   ```python
   METRICS_API_KEY = os.getenv("METRICS_API_KEY", "")
   
   async def verify_metrics_key(request: Request):
       key = request.headers.get("X-Metrics-Key", "")
       if not key or not hmac.compare_digest(key, METRICS_API_KEY):
           raise HTTPException(status_code=403, detail="Forbidden")
   
   @app.get("/metrics", tags=["System"], dependencies=[Depends(verify_metrics_key)])
   ```
4. **`/alerts`** → misma protección que `/metrics`
5. **`/health/circuits`** → misma protección que `/metrics`
6. En producción, si `METRICS_API_KEY` no está configurado, estos endpoints deben retornar 403 siempre
7. NO usar JWT auth para metrics — debe ser accesible desde herramientas de monitoreo externas (Datadog, Grafana)

---

### H-10 | STRIPE SESSIONS EN MEMORIA
**Archivo:** `api/routes/pagos.py` (~línea 69)

**Código actual:**
```python
_sesiones: dict[str, dict] = {}  # ← SE PIERDE AL REINICIAR
```

**Problema:** Idéntico a H-02. Las sesiones de checkout se almacenan en memoria. Si el pod reinicia durante un checkout, el usuario paga pero el sistema no lo registra.

**Requerimiento:**
1. Crear modelo `CheckoutSession` en `web/database/models.py`:
   ```python
   class CheckoutSession(Base):
       __tablename__ = "checkout_sessions"
       id = Column(String(64), primary_key=True)  # Session ID interno
       gym_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False, index=True)
       stripe_session_id = Column(String(255), unique=True)
       plan = Column(String(30), nullable=False)
       email = Column(String(120), nullable=False)
       status = Column(String(30), default="pending")  # pending | completed | expired
       created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
       completed_at = Column(DateTime, nullable=True)
   ```
2. Crear migración Alembic
3. Refactorizar `crear_sesion_stripe()` para persistir en DB
4. El webhook de Stripe ya busca por `stripe_session_id` — ajustar para consultar DB
5. Agregar cleanup job para sesiones expiradas (>24h en status pending)

---

### H-11 | DUAL DATABASE SIN COMPLETAR (Strangler Fig)
**Archivos:** `config/feature_flags.py`, `src/gestor_bd.py`, `src/repositories/cliente_repository.py`

**Estado actual:**
```python
class DBMigrationFlags:
    use_sa_for_read: bool = False        # FASE 1
    dual_write_enabled: bool = False     # FASE 1
    sa_is_primary: bool = False          # FASE 1
    legacy_deprecated: bool = False      # FASE 1
```

**Problema:** La migración está congelada en Fase 1. `gestor_bd.py` (SQLite legacy) es el primary y no hay timeline para avanzar. Esto duplica code paths y crea bugs de sincronización.

**Requerimiento:**
1. **NO completar la migración en este sprint** — es un esfuerzo separado
2. **Agregar mecanismo de avance de fases** en `feature_flags.py`:
   ```python
   @classmethod
   def from_env(cls) -> "DBMigrationFlags":
       phase = int(os.getenv("DB_MIGRATION_PHASE", "1"))
       if phase == 1:
           return cls()  # defaults = Fase 1
       elif phase == 2:
           return cls(use_sa_for_read=True, dual_write_enabled=True)
       elif phase == 3:
           return cls(use_sa_for_read=True, dual_write_enabled=True,
                      sa_is_primary=True)
       elif phase == 4:
           return cls(use_sa_for_read=True, sa_is_primary=True,
                      legacy_deprecated=True, shadow_write_legacy=False)
   ```
3. **Agregar log al arrancar** indicando la fase activa:
   `logger.info("[DB] Migration phase: %d", phase)`
4. **Documentar en README** el proceso para avanzar fases
5. Agregar un WARNING log si `phase < 3` en producción

---

### H-12 | PORT MISMATCH DOCKER vs CÓDIGO
**Archivo:** `config/settings.py` (línea 91)

**Código actual:**
```python
self.PORT: int = int(os.getenv("WEB_PORT", "8001"))  # ← Default 8001
```

**Dockerfile:** `EXPOSE ${PORT}` (default 8000 por Railway)

**Problema:** Si `WEB_PORT` no está en env, la app escucha en 8001 pero Docker expone 8000. Health check falla, Railway reinicia en loop.

**Requerimiento:**
1. Cambiar default a `"8000"`:
   ```python
   self.PORT: int = int(os.getenv("PORT", os.getenv("WEB_PORT", "8000")))
   ```
   **Nota:** Railway inyecta `PORT` (sin prefijo). Leer `PORT` primero, luego `WEB_PORT` como fallback.
2. Actualizar `Dockerfile` si es necesario para alinearse
3. Buscar y actualizar cualquier referencia hardcodeada a `8001` en el proyecto
4. En `web/main_web.py`, verificar que `uvicorn.run()` usa `settings.PORT`

---

### H-13 | CORS_ORIGINS INCLUYE LOCALHOST POR DEFAULT
**Archivo:** `config/settings.py` (línea 53)

**Código actual:**
```python
raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8000,http://localhost:8001,http://127.0.0.1:8000,http://127.0.0.1:8001",
)
```

**Problema:** Si `CORS_ORIGINS` no está en env en producción, el browser permite requests cross-origin desde localhost, facilitando ataques CSRF desde máquina local.

**Requerimiento:**
1. En desarrollo: mantener localhost defaults
2. En producción: requerir `CORS_ORIGINS` explícito:
   ```python
   if self.is_production:
       raw_origins = os.getenv("CORS_ORIGINS", "")
       if not raw_origins:
           raise RuntimeError("FATAL: CORS_ORIGINS requerido en producción")
   else:
       raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://localhost:8001,...")
   ```
3. **Validar formato:** cada origin debe empezar con `https://` en producción (excepto si explícitamente se permite HTTP)
4. Loguear los origins configurados al arrancar: `logger.info("[CORS] Origins: %s", self.CORS_ORIGINS)`

---

### H-14 | SUBSCRIPTION MODEL SIN CAMPOS FISCALES (CFDI México)
**Archivo:** `web/database/models.py`

**Contexto:** Para vender legalmente en Guadalajara, cada gym necesita poder emitir CFDI (factura fiscal mexicana). Necesitan almacenar datos fiscales del gym.

**Modelo actual `GymProfile`:**
```python
class GymProfile(Base):
    __tablename__ = "gym_profiles"
    # ... tiene nombre_negocio, telefono, direccion, rfc (ya existe!)
    rfc = Column(String(20), default="")
    # FALTA: razón social, régimen fiscal, código postal fiscal, uso CFDI
```

**Requerimiento:**
1. **Agregar campos fiscales a `GymProfile`** (no crear tabla nueva — ya tiene `rfc`):
   ```python
   # ── Datos Fiscales (CFDI México) ──
   razon_social = Column(String(255), default="")  # Nombre fiscal oficial
   regimen_fiscal = Column(String(10), default="")  # Clave SAT: "601", "612", etc.
   codigo_postal_fiscal = Column(String(5), default="")  # CP del domicilio fiscal
   uso_cfdi = Column(String(10), default="G03")  # Uso CFDI default: "G03" (Gastos en general)
   ```
2. **Crear migración Alembic** con estos campos
3. **NO implementar generación de CFDI** en este sprint — solo la estructura de datos
4. Los campos son opcionales (default="") porque no todos los gyms necesitan CFDI inmediatamente
5. Agregar validación de formato RFC en el schema de API (regex: `^[A-ZÑ&]{3,4}\d{6}[A-Z\d]{3}$`)

---

### H-15 | RLS POLICIES NO ENFORZADAS A NIVEL APP
**Contexto:** Las migraciones Alembic crean Row-Level Security policies en PostgreSQL, pero el código Python nunca ejecuta `SET app.current_tenant` en la sesión de DB. Las policies existen pero no filtran nada.

**Requerimiento:**
1. En el dependency de base de datos (donde se crea la sesión SQLAlchemy), después de obtener la sesión, ejecutar:
   ```python
   async def get_db(request: Request):
       # ... obtener sesión
       gym_id = request.state.gym_id  # Extraído del JWT
       if gym_id:
           session.execute(text("SET app.current_tenant = :tenant"), {"tenant": gym_id})
       yield session
   ```
2. **Extraer `gym_id` del JWT** y almacenarlo en `request.state` en un middleware de auth
3. **En desarrollo (SQLite):** no ejecutar SET (SQLite no soporta RLS). Condicionar:
   ```python
   if "postgresql" in str(engine.url):
       session.execute(text("SET app.current_tenant = :tenant"), {"tenant": gym_id})
   ```
4. **Agregar test** que verifica que un gym NO puede ver datos de otro gym cuando RLS está activo
5. **Loguear warning** si RLS policies existen pero no se está seteando tenant

---

### H-16 | PAYMENT GATEWAY KEYS VACÍAS POR DEFAULT
**Archivo:** `config/settings.py` (líneas 66-75)

**Código actual:**
```python
self.STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
self.STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
self.MERCADOPAGO_ACCESS_TOKEN: str = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
```

**Problema:** Si las keys no están configuradas, los endpoints de pago fallan silenciosamente con errores crípticos en vez de fallar ruidosamente al arrancar.

**Requerimiento:**
1. **En producción, validar al arrancar:**
   ```python
   if self.is_production:
       if not self.STRIPE_SECRET_KEY:
           logger.critical("[PAYMENTS] STRIPE_SECRET_KEY no configurada")
           raise RuntimeError("STRIPE_SECRET_KEY requerida en producción")
       if not self.STRIPE_WEBHOOK_SECRET:
           logger.critical("[PAYMENTS] STRIPE_WEBHOOK_SECRET no configurada")
           raise RuntimeError("STRIPE_WEBHOOK_SECRET requerida en producción")
       # MercadoPago es opcional (puede que no todos los deployments lo usen)
       if not self.MERCADOPAGO_ACCESS_TOKEN:
           logger.warning("[PAYMENTS] MERCADOPAGO_ACCESS_TOKEN no configurada — MP desactivado")
   ```
2. **En los endpoints de pago**, verificar antes de intentar crear sesión:
   ```python
   if not settings.STRIPE_SECRET_KEY:
       raise HTTPException(503, detail="Pagos no configurados")
   ```
3. **NO exponer el nombre de la key faltante** en la respuesta HTTP — solo "pagos no configurados"

---

### H-17 | REFRESH TOKEN CLEANUP INCOMPLETO
**Archivos:** `web/middleware/rate_limiter.py`, `web/auth.py`

**Código actual en auth.py:**
```python
# Hay funciones de creación y revocación de refresh tokens, pero...
# _cleanup_old_buckets() existe en rate_limiter.py pero nunca se ejecuta
# No hay tarea de limpieza para refresh_tokens expirados en la tabla SQLite
```

**Problema:** La tabla `refresh_tokens` crece indefinidamente. Tokens expirados y revocados se acumulan. En SQLite esto degrada performance.

**Requerimiento:**
1. **Crear función de limpieza en `web/auth.py`:**
   ```python
   def cleanup_expired_tokens() -> int:
       """Elimina refresh tokens expirados y revocados. Retorna count."""
       cutoff = time.time()
       with _conn() as conn:
           cursor = conn.execute(
               "DELETE FROM refresh_tokens WHERE expires_at < ? OR revoked = 1",
               (cutoff,)
           )
           conn.commit()
           return cursor.rowcount
   ```
2. **Programar ejecución periódica** al arrancar la app:
   ```python
   from contextlib import asynccontextmanager
   
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # Startup: limpieza inicial
       from web.auth import cleanup_expired_tokens
       cleaned = cleanup_expired_tokens()
       logger.info("[AUTH] Cleaned %d expired tokens on startup", cleaned)
       
       # Tarea periódica cada 6 horas
       import asyncio
       async def periodic_cleanup():
           while True:
               await asyncio.sleep(6 * 3600)
               try:
                   count = cleanup_expired_tokens()
                   if count > 0:
                       logger.info("[AUTH] Periodic cleanup: %d tokens removed", count)
               except Exception:
                   logger.exception("[AUTH] Cleanup failed")
       task = asyncio.create_task(periodic_cleanup())
       yield
       task.cancel()
   ```
3. **Activar `_cleanup_old_buckets()`** del rate limiter con el mismo patrón
4. En el futuro, migrar a Redis para tokens (no en este sprint)

---

### H-18 | FACTURA PDF CON DATOS PERSONALES
**Archivo:** `api/factura_pdf.py` (~línea 161)

**Código actual del footer:**
```python
elements.append(Paragraph(
    "Este recibo es un comprobante de pago digital generado por Método Base.",
    styles["SubGris"],
))
```

**Contexto:** El footer actualmente solo tiene texto genérico (verificado — no contiene datos personales directamente). PERO el PDF necesita mostrar datos del gym que genera la factura, no datos estáticos.

**Requerimiento:**
1. **Parametrizar `generar_factura_pdf()`** para recibir datos del gym:
   ```python
   def generar_factura_pdf(
       datos_factura: dict,
       gym_branding: dict,  # ← NUEVO: nombre, telefono, email, direccion del gym
       ruta_salida: Path,
   ) -> Path:
   ```
2. **El footer debe usar datos del gym:**
   ```python
   footer_text = (
       f"{gym_branding.get('nombre_gym', 'Método Base')} | "
       f"{gym_branding.get('telefono', '')} | "
       f"{gym_branding.get('email', '')}"
   )
   ```
3. **El caller debe cargar GymBranding desde DB** y pasarlo como dict
4. **Fallback:** Si no hay branding configurado, usar "Método Base" sin datos personales
5. Buscar y eliminar cualquier referencia hardcodeada a datos personales del desarrollador en todo `api/factura_pdf.py`

---

## REGLAS ARQUITECTÓNICAS (OBLIGATORIAS)

### Seguridad
- **Zero Trust:** Nunca confiar en datos del cliente. Validar todo server-side.
- **Fail Closed:** Si una validación de seguridad falla o tiene un error, denegar acceso (no permitir).
- **Least Privilege:** Exponer la mínima información necesaria en cada respuesta.
- **Defense in Depth:** Cada capa debe tener su propia validación (middleware + endpoint + DB).
- **Constant Time:** Todas las comparaciones de tokens deben usar `hmac.compare_digest()`.
- **No secrets in defaults:** Ningún secret puede tener un valor por defecto funcional.

### Código
- **Cada fix es un commit atómico** con mensaje descriptivo: `fix(security): H-01 validate JWT token type strictly`
- **NO romper tests existentes.** Si un test falla por el cambio, actualizar el test.
- **Agregar tests para cada fix** — mínimo 2 tests por hallazgo (happy path + attack path)
- **Usar `datetime.now(timezone.utc)`** en todo código nuevo (no `datetime.utcnow()`)
- **Logging estructurado** con prefijos consistentes: `[AUTH]`, `[PAYMENTS]`, `[DB]`, `[SECURITY]`
- **Type hints** en todas las funciones nuevas
- **Docstrings** en funciones públicas

### Migraciones
- **Toda tabla nueva** requiere migración Alembic (`alembic revision --autogenerate`)
- **Los campos nuevos en tablas existentes** deben ser nullable o tener default (migration backwards-compatible)
- **Nombrar migraciones descriptivamente:** `add_license_activations`, `add_fiscal_fields_gym_profile`

### Orden de Implementación (por impacto y dependencias)

```
FASE 1 — SECURITY CRITICAL (Bloquean producción)
├── C-11  Health check info leak
├── H-01  JWT token type validation
├── H-03  CSRF httponly
├── H-04  CSP nonces (unsafe-inline removal)
├── H-06  Rate limiting login
├── H-07  Auth audit logging
├── H-08  Remember-me token duration
└── H-09  Metrics auth

FASE 2 — DATA PERSISTENCE (Pérdida de datos)
├── H-02  License activations → DB
├── H-10  Stripe sessions → DB
└── H-17  Token cleanup

FASE 3 — CONFIGURATION HARDENING
├── H-12  Port mismatch
├── H-13  CORS production
├── H-16  Payment keys validation
└── H-05  CDN SRI hashes

FASE 4 — ARCHITECTURE & COMPLIANCE
├── H-11  DB migration phases
├── H-14  Fiscal fields (CFDI)
├── H-15  RLS enforcement
└── H-18  Factura PDF branding
```

### Validación Final

Después de implementar TODAS las fases:
1. `pytest` — 1030+ tests pasando (0 failures)
2. Verificar manualmente: `/health` no expone errores
3. Verificar: token sin `type` es rechazado
4. Verificar: CSRF cookie tiene `httponly=True`
5. Verificar: CSP header no contiene `unsafe-inline` en `script-src`
6. Verificar: login retorna 429 después de 5 intentos
7. Verificar: `/metrics` retorna 403 sin API key
8. Verificar: `CORS_ORIGINS` falla sin env var en producción
9. Verificar: `STRIPE_SECRET_KEY` falla sin env var en producción
10. `docker build . && docker run` — arranca sin errores
