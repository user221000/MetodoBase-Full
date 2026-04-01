# MetodoBase — Roadmap Comercial y Evolución de Producto

> Documento estratégico basado en análisis del código fuente actual (v3.0, marzo 2026).
> Cubre el camino desde app desktop de pago → SaaS web → aplicación móvil.

---

## Estado actual del producto (Baseline)

| Componente | Tecnología | Estado |
|---|---|---|
| App de escritorio | PySide6 + QSS | ✅ Funcional |
| Motor nutricional | Python 3.12 | ✅ Sólido |
| API REST interna | FastAPI + Jinja2 | ✅ Funcional |
| Base de datos | SQLite local | ✅ Funcional |
| Sistema de licencias | `core/licencia.py` | ✅ Implementado |
| Generación de PDF | ReportLab | ✅ Funcional |
| Web UI | Tailwind + Chart.js | 🔄 En mejora |
| Autenticación | JWT + hash propio | ✅ Funcional |

**Fortalezas identificadas en el código:**
- Motor nutricional robusto con rotación inteligente de alimentos
- Sistema de licencias ya presente (base para monetización)
- API REST lista que puede exponerse como backend SaaS
- Exportador multi-formato (PDF profesional)
- Arquitectura de capas limpia (`core/`, `src/`, `api/`, `gui/`)

---

## FASE 1 — Desktop como producto vendible (0–3 meses)

**Objetivo:** Generar ingresos inmediatos con la app actual mientras se construye la base SaaS.

### 1.1 Endurecimiento del sistema de licencias

- [ ] Implementar validación online de licencia contra servidor propio (actualmente solo local)
- [ ] Soporte de licencias por cantidad de clientes activos (modelo por volumen)
- [ ] Licencia de prueba de 14 días con limitación a 3 clientes
- [ ] Revocación remota de licencias en caso de impago
- [ ] Ofuscar `core/licencia.py` en el build final (PyArmor o Nuitka)

### 1.2 Empaquetado y distribución

- [ ] Build reproducible con PyInstaller (`MetodoBase.spec` ya existe — afinar)
- [ ] Instalador con Inno Setup (`setup_installer.iss` ya existe — completar)
- [ ] Auto-actualización silenciosa (descargar parches desde CDN propio)
- [ ] Firma de código del ejecutable (certificado EV para Windows)
- [ ] Versión macOS con `.dmg` notarizado

### 1.3 Experiencia de compra

- [ ] Landing page de producto con demo en video
- [ ] Portal de licencias (página web simple): cliente ingresa clave → activa
- [ ] Integración de pago: Stripe o MercadoPago para LATAM
- [ ] Facturación automática con PDF

### 1.4 Modelo de precios desktop sugerido

| Plan | Precio sugerido | Límite |
|---|---|---|
| Starter | $29 USD / mes | 25 clientes |
| Profesional | $59 USD / mes | 100 clientes |
| Clínica | $129 USD / mes | Ilimitado + multi-usuario |

### 1.5 Correcciones técnicas urgentes (bloqueantes para venta)

Basadas en el análisis de código:

- [ ] **Crítico:** Eliminar clases duplicadas en `ui_desktop/pyside/panel_inicio.py` (líneas 34 y 338 — dos definiciones de `PanelInicio` y `ResultadoInicio`)
- [ ] **Crítico:** Quitar re-imports dentro de función en `main.py` (líneas 341, 349, 351, 359)
- [ ] **Importante:** `api/services.py` línea 282 — usar `OBJETIVOS_VALIDOS` de `config.constantes` en lugar de redefinirlo localmente
- [ ] **Importante:** Alinear `_NIVELES_ACTIVIDAD` en `panel_perfil_detalle.py` con los valores de `config.constantes`
- [ ] Limpiar ~70 imports sin usar (impacto en tiempo de arranque)

---

## FASE 2 — SaaS Web multi-tenant (3–9 meses)

**Objetivo:** Migrar el backend a arquitectura multi-tenant hosted, accesible desde navegador.

### 2.1 Migración de base de datos

```
SQLite local  →  PostgreSQL (Supabase o Railway)
```

- [ ] Crear migraciones con Alembic (`src/gestor_bd.py` es el punto de entrada)
- [ ] Añadir tabla `tenants` (una fila por gimnasio/nutriólogo)
- [ ] Aislar datos por tenant con Row-Level Security (RLS) en PostgreSQL
- [ ] Migración automática de datos SQLite existentes al onboarding

### 2.2 Backend API — hardening para producción

La API FastAPI (`api/app.py`, `api/routes/`) ya existe; requiere:

- [ ] Autenticación con OAuth2 + refresh tokens (el JWT actual es básico)
- [ ] Rate limiting por tenant (`slowapi` o middleware propio)
- [ ] Logs de auditoría (quién hizo qué y cuándo) — `security logging`
- [ ] Endpoints de webhook para notificaciones (plan listo → email al cliente)
- [ ] Versionado de API (`/api/v1/`, `/api/v2/`)
- [ ] Documentación OpenAPI completada (`api/schemas.py` ya tiene base)

### 2.3 Frontend Web

El frontend Jinja2 actual (`web/templates/`) sirve como base; evolucionar a:

- [ ] **SPA React o Vue** que consuma la API REST (separación total frontend/backend)
- [ ] Dashboard de administración multi-usuario (dueño del gym + nutriólogos)
- [ ] Vista de cliente final con su plan (link privado, sin login)
- [ ] Generación de PDF en el servidor (el `api/pdf_generator.py` ya existe)
- [ ] Firma electrónica básica de planes nutricionales

### 2.4 Infraestructura cloud

```
Recomendado para LATAM:
  - Backend: Railway.app o Render.com (Python nativo, deploy desde Git)
  - DB: Supabase (PostgreSQL + storage + auth)
  - CDN / assets: Cloudflare R2
  - Email transaccional: Resend.com o SendGrid
  - Dominio: metodobase.app (o .io, .co)
```

### 2.5 Modelo de precios SaaS

| Plan | Precio | Incluye |
|---|---|---|
| Solo | $19 USD / mes | 1 nutriólogo, 50 clientes |
| Equipo | $49 USD / mes | 5 nutriólogos, 300 clientes |
| Gym | $99 USD / mes | Ilimitado, branding propio, API |
| Enterprise | Custom | SLA, instancia dedicada |

---

## FASE 3 — Aplicación móvil (9–18 meses)

**Objetivo:** App para clientes finales (seguimiento del plan) y app para profesionales (gestión en campo).

### 3.1 App para clientes finales

```
React Native (Expo)  ←  reutiliza el backend FastAPI existente
```

**Funcionalidades clave (MVP):**
- [ ] Ver plan nutricional del día (desayuno / comida / cena / snacks)
- [ ] Marcar comida como completada (check diario)
- [ ] Ver macros del día con gráfico de dona (Chart.js → Victory Native)
- [ ] Notificaciones push de recordatorio de comida
- [ ] Chat básico con el nutriólogo (via WebSocket o Pusher)

**Funcionalidades fase 2 móvil:**
- [ ] Registro de peso y medidas con gráfico de progreso
- [ ] Escáner de código de barras para logging de alimentos
- [ ] Biblioteca de recetas vinculadas al plan
- [ ] Integración con Apple Health / Google Fit

### 3.2 App para profesionales (nutriólogos en ruta)

- [ ] Crear/editar cliente desde el móvil
- [ ] Generar plan exprés con parámetros básicos
- [ ] Ver agenda del día
- [ ] Enviar plan por WhatsApp/email desde el móvil

### 3.3 Estrategia técnica mobile

```
Recomendado:
  - Expo (React Native) — build iOS + Android desde un solo codebase
  - Expo EAS Build — CI/CD para ambas tiendas desde GitHub Actions
  - Supabase Realtime — sincronización en tiempo real del plan
  - Expo Notifications — push notifications sin servidor propio
```

**Reutilización del backend:**
El motor nutricional Python (`core/motor_nutricional.py`, `core/generador_planes.py`) **no se toca** — la app móvil solo consume la API REST existente. Cero lógica duplicada.

---

## FASE 4 — Plataforma y marketplace (18–36 meses)

**Objetivo:** Convertir MetodoBase en una plataforma, no solo una herramienta.

### 4.1 Branding blanco (White-label)

- [ ] Gimnasios pueden publicar la app bajo su propio nombre en App Store/Play Store
- [ ] Logo, colores, y dominio personalizable por tenant (el `config/branding.json` ya existe como semilla)
- [ ] Plan de reseller: nutriólogos revenden a sus propios clientes

### 4.2 Marketplace de planes

- [ ] Nutriólogos pueden publicar plantillas de planes nutricionales
- [ ] Otros profesionales las compran y adaptan (revenue share 70/30)
- [ ] Sistema de rating y reviews

### 4.3 Integraciones de ecosistema

| Integración | Valor |
|---|---|
| MyFitnessPal API | Importar historial alimenticio del cliente |
| Garmin / Fitbit | Datos de actividad física en tiempo real |
| Shopify / WooCommerce | Vender suplementos recomendados desde el plan |
| WhatsApp Business API | Envío automático del plan semanal |
| Google Calendar | Agendar citas de seguimiento |

### 4.4 IA y personalización

- [ ] Ajuste automático de plan basado en progreso semanal (ML)
- [ ] Sugerencia de alimentos alternativos por disponibilidad regional
- [ ] Detección de riesgo de abandono del cliente (churn prediction)
- [ ] Generación de recetas con ingredientes del plan usando LLM

---

## Métricas clave de seguimiento

| Métrica | Fase 1 objetivo | Fase 2 objetivo | Fase 3 objetivo |
|---|---|---|---|
| Clientes de pago | 20 | 200 | 1,000 |
| MRR | $1,000 USD | $15,000 USD | $80,000 USD |
| Churn mensual | < 10% | < 5% | < 3% |
| NPS | > 40 | > 50 | > 60 |
| Tiempo de onboarding | < 30 min | < 10 min | < 5 min |

---

## Deuda técnica a resolver antes de escalar

Prioridad alta (bloquean crecimiento):

1. **Tests de integración** — `tests/` existe pero cobertura es parcial; alcanzar 80% antes de exponer API pública
2. **Validación de entrada en API** — `api/dependencies.py` y `api/schemas.py` deben cubrir 100% de los endpoints
3. **Manejo de errores consistente** — `api/exceptions.py` existe pero no está aplicado uniformemente
4. **Secrets management** — migrar claves hardcodeadas a variables de entorno con `python-dotenv` y vault en producción
5. **CORS configurado correctamente** — antes de exponer la API al cliente SPA
6. **Backup automático de BD** — antes de tener datos de clientes en producción

---

## Stack tecnológico recomendado por fase

```
FASE 1 (desktop)
  └── Python 3.12 + PySide6 + PyInstaller + Inno Setup

FASE 2 (SaaS web)
  ├── Backend: FastAPI + PostgreSQL + Alembic + Redis (caché)
  ├── Frontend: React 19 + Vite + Tailwind CSS + Recharts
  ├── Auth: Supabase Auth o Auth0
  └── Deploy: Railway + Cloudflare

FASE 3 (móvil)
  ├── React Native (Expo SDK 53+)
  ├── Mismo backend FastAPI
  └── Push: Expo Notifications + Firebase FCM

FASE 4 (plataforma)
  ├── Microservicios opcionales (solo si el monolito lo justifica)
  ├── ML: Python + scikit-learn o servicio externo (OpenAI / Anthropic)
  └── Data warehouse: BigQuery o ClickHouse para analytics
```

---

*Generado a partir del análisis de código fuente de MetodoBase-Full — marzo 2026.*
*Revisión recomendada: cada trimestre o ante cambio de estrategia.*
