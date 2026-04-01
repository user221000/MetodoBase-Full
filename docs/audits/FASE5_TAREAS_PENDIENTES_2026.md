# FASE 5: TAREAS PENDIENTES — Refactor de Producción
## MetodoBase SaaS — 26 de Marzo 2026

---

## 📊 Estado Actual (Post-FASE 4)

**Completado:** 45 de 63 issues (71%) ✅  
**Pendiente:** 18 issues (29%) ⚠️  
**Bloqueantes resueltos:** 10 de 10 ✅  

---

## 🎯 TAREAS PENDIENTES PRIORIZADAS

### BLOQUE A: Seguridad Crítica (ALTA PRIORIDAD)
**Tiempo estimado:** 2-3 horas  
**Impacto:** Protección contra ataques, compliance

#### A1. Rate Limiting en Login (H-06)
**Status:** ⚠️ No implementado  
**Riesgo:** Ataques de fuerza bruta en /auth/login  
**Solución:** Crear utils/rate_limiter.py + decorator

#### A2. CSP Nonce Implementation (H-04)
**Status:** ⚠️ CSP tiene 'unsafe-inline'  
**Riesgo:** Vulnerabilidad XSS  
**Solución:** Generar nonce por request, actualizar templates

#### A3. SRI Hashes para CDN Scripts (H-05)
**Status:** ⚠️ CDN scripts sin integrity  
**Riesgo:** Supply chain attacks  
**Solución:** Agregar integrity="sha384-..." a todos los <script src="cdn...">

#### A4. Auth Audit Logging Service (H-07)
**Status:** ⚠️ Tabla creada pero service no implementado  
**Riesgo:** No compliance, sin detective controls  
**Solución:** Crear web/services/auth_audit.py + integrar en login/register

#### A5. CSRF Cookie httponly (H-03)
**Status:** ⚠️ Cookie no tiene httponly=True  
**Riesgo:** XSS puede robar CSRF token  
**Solución:** 1 línea en web/middleware/csrf.py

#### A6. /metrics Authentication (H-09)
**Status:** ⚠️ Endpoint público  
**Riesgo:** Information disclosure  
**Solución:** Agregar dependency require_admin

#### A7. Access Token Expiry (H-08)
**Status:** ⚠️ 30 días es demasiado  
**Riesgo:** Tokens robados válidos por mucho tiempo  
**Solución:** Cambiar a 7 días (10080 minutos)

---

### BLOQUE B: Multi-Tenant Completo (ALTA PRIORIDAD)
**Tiempo estimado:** 2-3 horas  
**Impacto:** Aislamiento de datos, escalabilidad

#### B1. RLS Activation en PostgreSQL (H-15)
**Status:** ⚠️ Policies creadas pero no activadas en app  
**Riesgo:** Cross-tenant data leak si SQL mal escrito  
**Solución:** Middleware que ejecuta SET app.current_tenant

#### B2. Branding Dinámico Completo
**Status:** ⚠️ Tabla gym_branding existe pero core/branding.py sigue usando JSON  
**Riesgo:** No es verdadero white-labeling  
**Solución:** Refactorizar core/branding.py para cargar de DB

#### B3. Licencias Persistidas en DB
**Status:** ⚠️ Tabla gym_licenses creada pero core/licencia.py sigue en memoria  
**Riesgo:** Licencias se pierden al reiniciar  
**Solución:** Migrar core/licencia.py a usar gym_licenses table

#### B4. Gym Settings Repository
**Status:** ⚠️ Tabla gym_settings creada pero sin repository  
**Riesgo:** No se pueden customizar horarios/trial per-gym  
**Solución:** Crear web/repositories/gym_settings_repository.py

---

### BLOQUE C: Código Legacy & Limpieza (MEDIA PRIORIDAD)
**Tiempo estimado:** 1-2 horas  
**Impacto:** Mantenibilidad, deuda técnica

#### C1. Reemplazar print() → logger (M-01)
**Status:** ⚠️ ~80 print() en código productivo  
**Riesgo:** No logs estructurados, difícil debugging en producción  
**Solución:** Script automatizado: `git grep -n "print(" | sed ...`

#### C2. Fix datetime.utcnow() → datetime.now(UTC) (M-02)
**Status:** ⚠️ ~51 deprecation warnings  
**Riesgo:** Warnings molestos, deprecado en Python 3.12+  
**Solución:** Script automatizado: `sed -i 's/datetime.utcnow()/datetime.now(timezone.utc)/g'`

#### C3. Fix bare except Exception (L-01)
**Status:** ⚠️ ~40 bare excepts  
**Riesgo:** Oculta errores reales, difícil debugging  
**Solución:** Revisar uno por uno, especificar tipos

#### C4. Empty States en Dashboard (L-02)
**Status:** ⚠️ Sin estado vacío cuando 0 clientes  
**Riesgo:** UX pobre para nuevos usuarios  
**Solución:** Agregar template con ilustración + CTA

#### C5. Test Fixtures Únicas (L-03)
**Status:** ⚠️ Fixtures usan mismas credenciales que demo users  
**Riesgo:** Tests podrían modificar datos demo  
**Solución:** fixtures con UUID único: `test_{uuid}@test.com`

#### C6. Alembic Migration Data (L-07)
**Status:** ✅ Naming fixed, pero falta data migration  
**Riesgo:** Gym demo no tiene gym_branding/settings  
**Solución:** Crear migration que pobla datos de config/branding.json

#### C7. Desktop App Hardcoded URL (L-08)
**Status:** ⚠️ ui_desktop/pyside/gym_app_window.py abre localhost:8000/docs  
**Riesgo:** URL hardcodeada  
**Solución:** Usar env var API_DOCS_URL

#### C8. Soft Delete Audit Timestamps (L-09)
**Status:** ✅ Columnas deleted_at agregadas  
**Riesgo:** Ninguno (ya resuelto)  
**Solución:** N/A

---

### BLOQUE D: Infrastructure & Dependencies (MEDIA PRIORIDAD)
**Tiempo estimado:** 1 hora  
**Impacto:** Reproducibilidad, producción

#### D1. Stripe Price IDs en Env Vars
**Status:** ⚠️ Placeholders en config/constantes.py  
**Riesgo:** No funciona en producción sin price_ids reales  
**Solución:** Ya movido a env vars, documentar en .env.example

#### D2. psycopg2-binary → psycopg (B-07)
**Status:** ⚠️ requirements_web.txt usa psycopg2-binary  
**Riesgo:** Warnings en producción, peor performance  
**Solución:** Cambiar a psycopg[binary]

#### D3. pip-compile Lock File (B-08)
**Status:** ⚠️ Sin requirements.lock  
**Riesgo:** No reproducibilidad de builds  
**Solución:** `pip-compile requirements_web.txt -o requirements_web.lock`

#### D4. Railway releaseCommand
**Status:** ✅ Ya agregado  
**Solución:** N/A

#### D5. Dockerfile Env Validation
**Status:** ⚠️ No valida env vars al build  
**Riesgo:** Deploy puede fallar tarde  
**Solución:** Agregar RUN python config/env_validator.py || true

---

### BLOQUE E: Observabilidad & Logging (BAJA PRIORIDAD)
**Tiempo estimado:** 1 hora  
**Impacto:** Debugging, troubleshooting

#### E1. Structured Logging JSON
**Status:** ⚠️ StructuredFormatter creado pero no activo  
**Riesgo:** Logs no parseables en producción  
**Solución:** Activar en web/main_web.py con setup_logging()

#### E2. Request ID en Errores (M-09)
**Status:** ⚠️ Exception handlers no incluyen request_id  
**Riesgo:** Difícil tracear errores  
**Solución:** Agregar request_id a JSONResponse de errores

#### E3. exc_info Conditional (M-08)
**Status:** ⚠️ exc_info=True en producción  
**Riesgo:** Stack traces en logs de producción  
**Solución:** `exc_info=(os.getenv("ENVIRONMENT") != "production")`

#### E4. Refresh Token Cleanup
**Status:** ⚠️ No hay job que elimine tokens expirados  
**Riesgo:** DB crece indefinidamente  
**Solución:** Crear scripts/cleanup_expired_tokens.py + cron job

---

## 📋 ORDEN DE EJECUCIÓN RECOMENDADO

### Sprint 1: Seguridad Crítica (BLOQUE A)
**Duración:** 1 día  
**Entregables:** 7 fixes de seguridad implementados y testeados

1. A5 → CSRF httponly (5 min)
2. A7 → Access token expiry (5 min)
3. A6 → /metrics auth (10 min)
4. A1 → Rate limiting (1 hora)
5. A4 → Auth audit logging (1 hora)
6. A2 → CSP nonce (1.5 horas)
7. A3 → SRI hashes (30 min)

### Sprint 2: Multi-Tenant Completo (BLOQUE B)
**Duración:** 1 día  
**Entregables:** Sistema multi-tenant 100% funcional

1. B4 → Gym settings repository (30 min)
2. B2 → Branding dinámico (1 hora)
3. B3 → Licencias en DB (1 hora)
4. B1 → RLS activation (1 hora)

### Sprint 3: Limpieza de Código (BLOQUE C)
**Duración:** 0.5 días  
**Entregables:** Código limpio, 0 warnings

1. C2 → datetime.utcnow() automated (10 min)
2. C1 → print() → logger automated (30 min)
3. C7 → Desktop app URL (5 min)
4. C4 → Empty states (30 min)
5. C5 → Test fixtures (15 min)
6. C6 → Data migration (30 min)
7. C3 → Bare excepts (1 hora manual)

### Sprint 4: Infrastructure (BLOQUE D)
**Duración:** 0.5 días  
**Entregables:** Deploy reproducible

1. D2 → psycopg upgrade (5 min)
2. D3 → pip-compile (10 min)
3. D5 → Dockerfile validation (10 min)

### Sprint 5: Observabilidad (BLOQUE E)
**Duración:** 0.5 días  
**Entregables:** Logging production-ready

1. E3 → exc_info conditional (15 min automated)
2. E1 → Structured logging (20 min)
3. E2 → Request ID en errores (30 min)
4. E4 → Refresh token cleanup (30 min)

---

## 🎯 Métricas de Éxito

Al completar FASE 5:
- [ ] 63 de 63 issues resueltos (100%)
- [ ] 0 bloqueantes
- [ ] 0 print() en código productivo
- [ ] 0 datetime.utcnow()
- [ ] 0 bare except sin justificación
- [ ] Rate limiting activo en login
- [ ] CSP sin 'unsafe-inline'
- [ ] RLS activado y testeado
- [ ] Branding 100% dinámico
- [ ] Licencias persistidas en DB
- [ ] Tests pasan: 1030+ ✅
- [ ] Coverage: >80%

---

## 🚀 Deploy Strategy Post-FASE 5

1. **Staging Deploy:** Validar en staging.metodobase.com
2. **Smoke Tests:** Endpoints críticos + login + dashboard
3. **Load Testing:** k6 con 100 usuarios concurrentes
4. **Security Scan:** OWASP ZAP automated scan
5. **Pilot:** FitnessGym Real del Valle (1 semana)
6. **Production:** Deploy final + monitoreo 24/7

---

## ✍️ Documento Creado Por

**Arquitecto Senior:** GitHub Copilot (Claude Sonnet 4.5)  
**Fecha:** 26 de Marzo 2026  
**Basado en:** AUDITORIA_PRODUCCION_2026-03-25.txt + reportes de FASE 1-4

**Listo para ejecución:** ✅ Proceder con Sprint 1
