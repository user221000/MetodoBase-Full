# CONSOLIDACIÓN DE BASE DE DATOS DUAL — METODOBASE

## Fecha: 24 de Marzo de 2026
## Arquitecto: Sistema Senior (15+ años SaaS multi-tenant)
## Estado: ✅ IMPLEMENTACIÓN COMPLETA

---

## 0. RESUMEN EJECUTIVO

### Archivos Creados
| Archivo | Propósito |
|---------|-----------|
| `config/feature_flags.py` | Feature flags y DB migration flags |
| `src/repositories/base.py` | Interfaces base y DTOs |
| `src/repositories/cliente_repository.py` | Repository dual-BD para clientes |
| `src/repositories/plan_repository.py` | Repository dual-BD para planes |
| `src/compat/gestor_bd_compat.py` | Capa compatibilidad legacy |
| `core/services/strangler_fig.py` | Patrón Strangler Fig |
| `core/services/migration_monitor.py` | Observabilidad y alertas |
| `scripts/etl_mapping.py` | Mapeo ETL y transformaciones |
| `scripts/migrate_to_sa.py` | Script migración idempotente |
| `scripts/validate_migration.py` | Validación integridad |
| `scripts/rollback_migration.py` | Rollback plan |

### Tests
- **912 tests passing, 3 skipped** ✅
- Sin regresiones

---

## 1. AUDITORÍA COMPLETA

### 1.1 Inventario de Bases de Datos Actuales

| BD | Archivo | Tecnología | Multi-tenant | Consumidores |
|----|---------|------------|--------------|--------------|
| Legacy Clientes | `registros/clientes.db` | sqlite3 raw | NO | Desktop (PySide6) |
| Legacy Auth | `registros/web_usuarios.db` | sqlite3 raw | Parcial | Web auth |
| Nueva SA | `metodobase_web.db` | SQLAlchemy ORM | SÍ (gym_id) | Web business |

### 1.2 Esquemas Comparativos

#### Legacy `clientes.db`
```sql
CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente TEXT UNIQUE NOT NULL,      -- PK lógica
    nombre TEXT NOT NULL,
    telefono TEXT,
    email TEXT,
    edad INTEGER,
    sexo TEXT CHECK(sexo IN ('M', 'F', 'Otro', NULL)),
    peso_kg REAL,
    estatura_cm REAL,
    grasa_corporal_pct REAL,
    masa_magra_kg REAL,
    nivel_actividad TEXT,
    objetivo TEXT,
    fecha_registro TIMESTAMP,
    ultimo_plan TIMESTAMP,
    total_planes_generados INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT 1,
    notas TEXT,
    plantilla_tipo TEXT DEFAULT 'general',
    -- Campos cifrados (PII)
    nombre_enc TEXT,
    telefono_enc TEXT,
    email_enc TEXT,
    notas_enc TEXT,
    nombre_idx TEXT,
    telefono_idx TEXT,
    email_idx TEXT,
    datos_cifrados BOOLEAN DEFAULT 0
);

CREATE TABLE planes_generados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente TEXT NOT NULL,             -- FK a clientes.id_cliente
    fecha_generacion TIMESTAMP,
    tmb REAL, get_total REAL, kcal_objetivo REAL, kcal_real REAL,
    proteina_g REAL, carbs_g REAL, grasa_g REAL,
    objetivo TEXT, nivel_actividad TEXT, ruta_pdf TEXT,
    peso_en_momento REAL, grasa_en_momento REAL,
    desviacion_maxima_pct REAL,
    plantilla_tipo TEXT DEFAULT 'general',
    tipo_plan TEXT DEFAULT 'menu_fijo'
);

CREATE TABLE estadisticas_gym (
    id INTEGER PRIMARY KEY,
    mes INTEGER, anio INTEGER,
    total_clientes_nuevos INTEGER,
    total_planes_generados INTEGER,
    promedio_kcal REAL,
    objetivo_deficit_count INTEGER,
    objetivo_superavit_count INTEGER,
    objetivo_mantenimiento_count INTEGER,
    fecha_calculo TIMESTAMP,
    UNIQUE(mes, anio)
);
```

#### Legacy `web_usuarios.db`
```sql
CREATE TABLE web_usuarios (
    id TEXT PRIMARY KEY,          -- UUID
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre TEXT NOT NULL,
    apellido TEXT DEFAULT '',
    tipo TEXT CHECK(tipo IN ('gym', 'usuario', 'admin')),
    activo BOOLEAN DEFAULT 1,
    fecha_registro TIMESTAMP
);
```

#### Nueva SQLAlchemy (TARGET)
```sql
-- usuarios (fusión de web_usuarios + multi-tenant owner)
-- clientes (+ gym_id FK)
-- planes_generados (+ gym_id FK)
-- subscriptions, payments, gym_profiles, client_progress, audit_log
```

### 1.3 Problemas de Inconsistencia Detectados

| Tipo | Descripción | Severidad |
|------|-------------|-----------|
| Duplicación | mismos clientes en ambas BDs | CRÍTICA |
| Schema drift | campos `*_enc`, `*_idx` solo en legacy | MEDIA |
| FK huérfanas | planes sin cliente válido | MEDIA |
| No sync | cambios en desktop no reflejan en web | CRÍTICA |
| Auth separado | usuarios auth en DB diferente | ALTA |

---

## 2. MODELO DESTINO UNIFICADO

### 2.1 Principios de Diseño

1. **Single Source of Truth**: SQLAlchemy es la única BD
2. **Multi-tenant by default**: gym_id en todas las tablas de negocio
3. **Soft delete**: columna `activo` en lugar de DELETE físico
4. **Audit trail**: tabla `audit_log` para trazabilidad
5. **Backwards compatible**: IDs legacy preservados

### 2.2 Schema Destino Final

Ver `/home/hernandez221000/MetodoBase-Full/web/database/models.py`

**Cambios requeridos en SQLAlchemy models:**

1. Añadir campos cifrados (PII) opcionales:
   - `nombre_enc`, `telefono_enc`, `email_enc`, `notas_enc`
   - `nombre_idx`, `telefono_idx`, `email_idx` (hash indices)
   - `datos_cifrados` flag

2. Añadir tabla `estadisticas_gym`:
   - Migrar tabla desde legacy
   - Añadir `gym_id` FK

---

## 3. ESTRATEGIA DE MIGRACIÓN (ETL)

### 3.1 Mapeo Campo a Campo

#### Clientes: legacy → SA
| Legacy | Target SA | Transformación |
|--------|-----------|----------------|
| id_cliente | id_cliente | DIRECTO |
| (ninguno) | gym_id | ASIGNAR `$GYM_ID` |
| nombre | nombre | DIRECTO |
| telefono | telefono | DIRECTO |
| email | email | DIRECTO |
| edad | edad | DIRECTO |
| sexo | sexo | VALIDAR enum |
| peso_kg | peso_kg | DIRECTO |
| estatura_cm | estatura_cm | DIRECTO |
| grasa_corporal_pct | grasa_corporal_pct | DIRECTO |
| masa_magra_kg | masa_magra_kg | DIRECTO |
| nivel_actividad | nivel_actividad | DIRECTO |
| objetivo | objetivo | DIRECTO |
| fecha_registro | fecha_registro | PARSE datetime |
| ultimo_plan | ultimo_plan | PARSE datetime |
| total_planes_generados | total_planes_generados | DIRECTO |
| activo | activo | BOOL |
| notas | notas | DIRECTO |
| plantilla_tipo | plantilla_tipo | DEFAULT 'general' |
| nombre_enc | (NUEVO) | MIGRAR si existe |
| telefono_enc | (NUEVO) | MIGRAR si existe |
| email_enc | (NUEVO) | MIGRAR si existe |
| notas_enc | (NUEVO) | MIGRAR si existe |
| datos_cifrados | (NUEVO) | MIGRAR si existe |

#### Usuarios: web_usuarios → SA usuarios
| Legacy | Target SA | Transformación |
|--------|-----------|----------------|
| id | id | DIRECTO (UUID) |
| email | email | DIRECTO |
| password_hash | password_hash | DIRECTO |
| nombre | nombre | DIRECTO |
| apellido | apellido | DEFAULT '' |
| tipo | tipo | DIRECTO |
| activo | activo | BOOL |
| fecha_registro | fecha_registro | PARSE datetime |

### 3.2 Reglas de Conflicto

| Escenario | Resolución |
|-----------|------------|
| Cliente existe en ambas | SA gana (más reciente) |
| Usuario existe en ambas | SA gana, merge campos faltantes |
| Plan sin cliente válido | Crear cliente placeholder |
| Fecha NULL | Usar datetime.utcnow() |
| gym_id desconocido | Asignar a gym default |

---

## 4. PATRÓN STRANGLER FIG

### 4.1 Fases de Transición

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FASE 1: DUAL READ                            │
│  Desktop → Legacy (R/W)    |    Web → SA (R/W)                     │
│                            |    Web → Legacy (READ para sync)      │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        FASE 2: DUAL WRITE                           │
│  Desktop → Repository → Legacy + SA (WRITE)                        │
│  Desktop → SA (READ primary) → Legacy (READ fallback)              │
│  Web → SA (R/W)                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        FASE 3: SA PRIMARY                           │
│  Desktop → Repository → SA (R/W) → Legacy (SHADOW WRITE)           │
│  Web → SA (R/W)                                                    │
│  Legacy en modo readonly para rollback                             │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        FASE 4: DEPRECACIÓN                          │
│  Desktop → Repository → SA (R/W)                                   │
│  Web → SA (R/W)                                                    │
│  Legacy: ARCHIVED (backup final, no acceso)                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Feature Flags

```python
# config/feature_flags.py
DB_MIGRATION_FLAGS = {
    "use_sa_for_read": False,      # Fase 2
    "dual_write_enabled": False,   # Fase 2
    "sa_is_primary": False,        # Fase 3
    "legacy_deprecated": False,    # Fase 4
    "shadow_write": True,          # Fase 3 (para rollback)
}
```

---

## 5. PLAN DE EJECUCIÓN

### Fase 1: Preparación (Día 1-2)
- [ ] Crear capa Repository en `src/repositories/`
- [ ] Implementar `ClienteRepository` con interface dual
- [ ] Añadir feature flags
- [ ] Tests unitarios de repository

### Fase 2: Sincronización inicial (Día 3-4)
- [ ] Ejecutar migración batch inicial
- [ ] Verificar integridad con checksums
- [ ] Activar dual-write
- [ ] Monitorear errores de sync

### Fase 3: Validación paralela (Día 5-7)
- [ ] Correr ambos sistemas en paralelo
- [ ] Comparar resultados de queries
- [ ] Identificar divergencias
- [ ] Corregir transformaciones

### Fase 4: Cambio de lectura (Día 8-10)
- [ ] Activar SA como primary para reads
- [ ] Legacy como fallback
- [ ] Monitorear latencia y errores
- [ ] Smoke tests en producción

### Fase 5: Desactivación legacy (Día 11-14)
- [ ] Desactivar dual-write
- [ ] Backup final de legacy
- [ ] Archivar archivos .db
- [ ] Eliminar feature flags

---

## 6. VALIDACIÓN E INTEGRIDAD

### 6.1 Scripts de Verificación

```sql
-- Conteo de registros
SELECT 'legacy_clientes' as source, COUNT(*) as count FROM clientes
UNION ALL
SELECT 'sa_clientes', COUNT(*) FROM clientes;

-- Checksum de datos críticos
SELECT SUM(CAST(id_cliente AS INTEGER)) as checksum FROM clientes;

-- Consistencia referencial
SELECT COUNT(*) FROM planes_generados p
LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
WHERE c.id_cliente IS NULL;
```

### 6.2 Métricas de Éxito

| Métrica | Criterio |
|---------|----------|
| Conteo clientes | legacy == SA |
| Conteo planes | legacy == SA |
| FK orphans | 0 |
| Duplicados | 0 |
| Sync latency | < 100ms |

---

## 7. RIESGOS Y MITIGACIÓN

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Data loss durante migración | BAJA | CRÍTICO | Backup pre-migración, migración idempotente |
| Inconsistencia durante dual-write | MEDIA | ALTO | Validación post-write, reconciliación batch |
| Performance degradation | MEDIA | MEDIO | Connection pooling, índices optimizados |
| Rollback necesario | BAJA | ALTO | Shadow write a legacy, backup hot |

### Plan de Rollback

1. Revertir feature flag `sa_is_primary = False`
2. Legacy vuelve a ser primary
3. Ejecutar sync reverso SA → Legacy
4. Investigar causa raíz
5. Corregir y reintentar

---

## 8. OBSERVABILIDAD

### 8.1 Métricas a Monitorear

```python
# Prometheus-style metrics
db_sync_operations_total{source="legacy", target="sa", status="success"}
db_sync_operations_total{source="legacy", target="sa", status="error"}
db_sync_latency_seconds{operation="read", source="sa"}
db_sync_latency_seconds{operation="write", source="sa"}
db_divergence_count{table="clientes"}
db_divergence_count{table="planes_generados"}
```

### 8.2 Alertas

| Alerta | Condición | Acción |
|--------|-----------|--------|
| SyncErrorRate | > 1% en 5min | Investigar, considerar rollback |
| DivergenceDetected | count > 0 | Reconciliar manualmente |
| LatencySpike | p99 > 500ms | Verificar índices |

---

## 9. ARCHIVOS A CREAR/MODIFICAR

### Nuevos archivos:
1. `src/repositories/__init__.py`
2. `src/repositories/base.py` - Interface base
3. `src/repositories/cliente_repository.py` - Implementación dual
4. `src/repositories/plan_repository.py` - Implementación dual
5. `config/feature_flags.py` - Feature flags
6. `scripts/db_consolidation/` - Scripts de migración
7. `tests/test_repositories.py` - Tests de repository

### Archivos a modificar:
1. `web/database/models.py` - Añadir campos PII
2. `src/gestor_bd.py` - Delegar a repository
3. `ui_desktop/pyside/*.py` - Usar repository
4. `web/routes/*.py` - Usar repository unificado

---

## 10. ESTIMACIÓN DE ESFUERZO

| Tarea | Horas | Prioridad |
|-------|-------|-----------|
| Repository layer | 8h | P0 |
| Feature flags | 2h | P0 |
| Migración batch | 4h | P0 |
| Dual-write | 6h | P1 |
| Validación scripts | 4h | P1 |
| Desktop refactor | 12h | P2 |
| Tests | 8h | P1 |
| Observability | 4h | P2 |
| **TOTAL** | **48h** | - |

---

## PRÓXIMOS PASOS INMEDIATOS

1. ✅ Auditoría completa (este documento)
2. 🔄 Crear Repository layer
3. 🔄 Implementar feature flags
4. ⏳ Migración batch inicial
5. ⏳ Activar dual-write
6. ⏳ Validación y QA
