# 🗺️ ROADMAP — Método Base

**Análisis de producto: MVP → Software Vendible (Web + Móvil)**  
**Última actualización:** Marzo 2026  
**Versión actual:** 1.0.0 (Desktop Windows)

---

## Contexto

Método Base es un MVP de escritorio (Windows) para gimnasios en el área metropolitana de Guadalajara. El objetivo es evolucionar a una plataforma web + app móvil vendible a escala nacional.

---

## ✅ LO QUE YA FUNCIONA (Producción-Ready)

### Motor Nutricional
- [x] Cálculo Katch-McArdle (TMB, GET, masa magra)
- [x] Distribución de macros (proteína, grasa, carbohidratos) por objetivo
- [x] Ajuste calórico mensual según progreso
- [x] Alertas de salud automáticas (déficit excesivo, carbs muy bajos)
- [x] Factores de actividad validados (sedentario → muy activo)

### Generación de Planes
- [x] Planes personalizados (déficit / mantenimiento / superávit)
- [x] Rotación inteligente de alimentos (evita monotonía)
- [x] Catálogo de ~80 alimentos con gramos y equivalencias
- [x] Plantillas de cliente (general, vegetariano, etc.)
- [x] Exportación PDF profesional con branding del gym
- [x] Exportación Excel (.xlsx) y CSV

### Infraestructura de Datos
- [x] SQLite local con respaldo automático (7 días)
- [x] Historial completo de clientes y planes
- [x] Seguridad: campos PII cifrados (Fernet), bcrypt para contraseñas
- [x] HMAC para búsqueda exacta sin exponer datos
- [x] Telemetría local (eventos de uso sin datos externos)

### UI de Escritorio
- [x] PySide6 dark theme responsivo con QSS
- [x] Sistema de temas (dark / light / aurora)
- [x] Splash screen con animación
- [x] Flujo onboarding (wizard colores/logo)
- [x] Panel de administración (Ctrl+Shift+A)
- [x] Módulo de reportes con gráficas (matplotlib)
- [x] Preview del plan antes de generar PDF
- [x] Integración WhatsApp (abrir chat con PDF)
- [x] Validación en tiempo real de formularios

### Licenciamiento
- [x] Sistema de keys por gimnasio (key_v2 con HMAC)
- [x] Períodos: 3, 6, 9, 12 meses
- [x] Activación offline
- [x] Sin auto-generación (el proveedor emite las keys)

### Autenticación
- [x] Registro y login seguro (bcrypt + cifrado AES-128)
- [x] Roles: admin / gym / usuario
- [x] Sesión en memoria (sin tokens en disco)
- [x] Modo GYM y modo Usuario Regular

---

## 🚨 URGENTE — Bajar a Producción (Sprint 1-2)

Estas son las brechas que impiden vender y escalar ahora mismo:

### 1. API REST (FastAPI) — `api/`
**Por qué es urgente:** Sin API no hay web ni móvil. El core ya está desacoplado de la UI; solo falta exponer los servicios existentes via HTTP.

- [ ] `POST /api/v1/planes/calcular` — Cálculo nutricional + generación de plan
- [ ] `GET  /api/v1/planes/{id}` — Obtener plan por ID
- [ ] `POST /api/v1/auth/login` — JWT access + refresh tokens
- [ ] `POST /api/v1/auth/register` — Registro de usuario
- [ ] `GET  /api/v1/clientes` — Listar clientes del gym (paginado)
- [ ] `POST /api/v1/clientes` — Registrar cliente
- [ ] `GET  /api/v1/reportes/estadisticas` — KPIs del gym
- [ ] `GET  /api/v1/licencias/validar` — Validación de licencia por gym_id
- [ ] Schemas Pydantic para request/response (ya existen dataclasses, migrar)
- [ ] Middleware de autenticación JWT + validación de licencia

**Archivos a crear:**
```
api/
  __init__.py
  main.py              ← FastAPI app + CORS + lifespan
  dependencies.py      ← Inyección de dependencias (BD, auth)
  routers/
    auth.py
    planes.py
    clientes.py
    reportes.py
    licencias.py
  schemas/
    auth.py
    planes.py
    clientes.py
    reportes.py
```

**Stack recomendado:**
- `fastapi >= 0.110` + `uvicorn[standard]`
- `python-jose[cryptography]` para JWT
- `pydantic v2` (ya compatible con dataclasses existentes)

### 2. Dashboard de Resultados Nutricionales
**Por qué es urgente:** Actualmente el usuario regular ve solo 4 tarjetas de datos (peso, IMC, actividad, objetivo) sin ver su TMB, GET ni macros. Esto es el valor central del producto.

- [x] `PanelMetodoBase` — Añadir sección "TUS CALORÍAS" con: TMB, GET, Kcal objetivo, macros (P/G/C en gramos)
- [ ] Barra visual de macros (proporcional) en el panel de usuario
- [ ] Historial del último plan generado (fecha, kcal, objetivo)

### 3. Modo Multi-Gym / Multitenancy
**Por qué es urgente:** Un solo gym puede agotar la oportunidad; el modelo SaaS requiere múltiples tenants.

- [ ] Campo `gym_id` en todas las tablas (clientes, planes, usuarios)
- [ ] Middleware de aislamiento por tenant en la API
- [ ] Dashboard por gym independiente
- [ ] Plan de precios SaaS (mensual por gym o por plan generado)

### 4. Corrección de TODOs Críticos en Catálogo
**Por qué es urgente:** Hay inconsistencias en el catálogo de alimentos que pueden causar errores en planes.

- [ ] Verificar nombres: `atun` vs `atun_en_agua`, `carne_molida` vs `carne_magra_res`
- [ ] Unificar nombres en `ALIMENTOS_BASE`, `constantes.py`, y `MINIMOS_POR_ALIMENTO`
- [ ] Añadir unit tests que validen integridad del catálogo

### 5. Ventana Principal Responsiva
**Por qué es urgente:** `MainWindow` tiene tamaño fijo (840×920), no funciona bien en pantallas menores a 1080p.

- [ ] Cambiar `setFixedSize(840, 920)` por `setMinimumSize(840, 700)` + `resize()`
- [ ] Layout de formulario en 2 columnas para pantallas anchas
- [ ] Scrollable cuando la ventana es pequeña

---

## ⏳ NO TAN URGENTE — Sprint 3-5

Mejoras que incrementan el valor pero no bloquean el lanzamiento:

### Dashboard del Gym (Admin) — Mejoras
- [ ] Gráfica de tendencia de kcal promedio por semana
- [ ] Tabla de retención: clientes que generaron plan en los últimos 30/60/90 días
- [ ] Distribución de IMC de la base de clientes
- [ ] Alerta automática si un cliente lleva más de 45 días sin nuevo plan
- [ ] Exportar dashboard completo a PDF

### Módulo de Progreso del Cliente
- [ ] Registro de peso y grasa semanal/mensual
- [ ] Gráfica de progreso temporal (peso vs. kcal vs. fecha)
- [ ] Ajuste automático del plan cada 4 semanas (ya existe `AjusteCaloricoMensual`)
- [ ] Notificación al gym cuando un cliente cumple su objetivo

### Web Frontend (SPA)
- [ ] React 18 + Vite + TailwindCSS
- [ ] Autenticación con JWT (access + refresh)
- [ ] Dashboard gym: KPIs + tabla de clientes
- [ ] Formulario de generación de planes (mismo flujo que el desktop)
- [ ] Historial de planes del cliente
- [ ] Responsive para tablet y móvil

### App Móvil
- [ ] React Native (comparte lógica con la web SPA)
- [ ] Pantalla de perfil del usuario
- [ ] Vista de su plan actual (macros, alimentos, porciones)
- [ ] Notificaciones push cuando hay un plan nuevo
- [ ] Escáner de código QR para recibir el plan en la consulta

### Mejoras al Sistema de Licencias
- [ ] Licencias SaaS (validación online en lugar de solo offline)
- [ ] Portal web para el proveedor: emitir/revocar/renovar keys
- [ ] Webhook de expiración 30/15/7 días antes
- [ ] Plan freemium: 10 planes/mes gratis, ilimitado con suscripción

### Seguridad y Compliance
- [ ] Cifrado en tránsito (HTTPS obligatorio en producción)
- [ ] Rate limiting en la API (previnir brute-force)
- [ ] Auditoría de accesos (quién generó qué plan, cuándo)
- [ ] Política de retención de datos (LFPDPPP / GDPR básico)
- [ ] Penetration test básico antes del lanzamiento web

---

## 📐 ARQUITECTURA TARGET (6-12 meses)

```
┌─────────────────────────────────────────────────────┐
│                   CLIENTES                          │
│   Desktop (Windows)  │  Web SPA  │  App Móvil      │
│   PySide6 + Qt       │  React 18 │  React Native   │
└────────────┬─────────────────┬────────────┬────────┘
             │                 │            │
             └────────────┬────┘            │
                          │                 │
             ┌────────────▼─────────────────▼────────┐
             │          API REST (FastAPI)            │
             │   /api/v1/planes  /api/v1/clientes     │
             │   /api/v1/auth    /api/v1/reportes     │
             │   JWT Auth + Licencia middleware        │
             └────────────────────┬──────────────────┘
                                  │
             ┌────────────────────▼──────────────────┐
             │          SERVICIOS CORE (Python)       │
             │  MotorNutricional  │  GeneradorPlanes  │
             │  ExportadorPDF     │  RotacionService  │
             │  AuthService       │  LicenciaService  │
             └────────────────────┬──────────────────┘
                                  │
             ┌────────────────────▼──────────────────┐
             │           BASE DE DATOS               │
             │  SQLite (dev/local)                   │
             │  PostgreSQL (prod / SaaS)             │
             │  S3/R2 para PDFs generados            │
             └───────────────────────────────────────┘
```

### Ventaja clave: el core ya está desacoplado
Los módulos `core/`, `core/services/` y `src/` **no tienen imports de PySide6 ni de customtkinter**.  
Esto significa que el mismo motor nutricional sirve tanto al desktop como a la API web sin cambios.

---

## 🏗️ PRÓXIMOS PASOS INMEDIATOS

### Semana 1
1. Instalar FastAPI: `pip install fastapi uvicorn[standard] python-jose[cryptography]`
2. Crear `api/main.py` con los 3 endpoints más críticos:  
   - `POST /api/v1/planes/calcular`  
   - `POST /api/v1/auth/login`  
   - `GET  /api/v1/reportes/estadisticas`
3. Probar con Swagger UI (`/docs`)

### Semana 2
4. Desplegar en Railway.app o Render (free tier) para demo a gyms
5. Configurar CI/CD básico (GitHub Actions: lint + tests)
6. Crear landing page sencilla que llame a la API

### Semana 3-4
7. Dashboard web mínimo (React + shadcn/ui)
8. Migrar SQLite → PostgreSQL en producción
9. Documentar API con OpenAPI (FastAPI lo genera automáticamente)

---

## 💡 Decisiones de Arquitectura Importantes

| Decisión | Recomendación | Razón |
|----------|---------------|-------|
| API framework | **FastAPI** | Pydantic v2 compatible con dataclasses existentes; auto-docs |
| Auth web | **JWT (access 15min + refresh 7d)** | Stateless; compatible con móvil |
| DB producción | **PostgreSQL** | Multi-tenant; JSONB para planes; migraciones con Alembic |
| Storage PDFs | **Cloudflare R2 / AWS S3** | Los PDFs pueden crecer 100MB+/gym/mes |
| Frontend | **React 18 + TailwindCSS** | Ecosistema maduro; componentes reutilizables |
| Móvil | **React Native + Expo** | Comparte lógica con web; publicación App Store/Play Store |
| Hosting API | **Railway.app** (inicio) → **VPS propio** (escala) | Costo-beneficio |
| Modelo de precios | **SaaS mensual por gym** | Ingresos predecibles; valor comprobado |

---

## 📊 Modelo de Negocio Recomendado

### Tier 1: Starter — $999 MXN/mes
- Hasta 50 planes/mes
- 1 usuario admin
- PDF con branding
- Sin web ni app

### Tier 2: Pro — $2,499 MXN/mes
- Planes ilimitados
- 3 usuarios staff
- Dashboard web
- Exportación Excel
- Soporte WhatsApp

### Tier 3: Business — $4,999 MXN/mes
- Todo lo de Pro
- App móvil para clientes
- Módulo de progreso
- API acceso directo
- Soporte prioritario

---

*Este roadmap es un documento vivo. Actualizar al completar cada etapa.*
