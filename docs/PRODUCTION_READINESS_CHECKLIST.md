# 🚀 Checklist de Producción - MetodoBase

> Estado: **FASE 2 ACTIVA (Dual-Write)** | Fecha: 2026-03-24

---

## ✅ COMPLETADO

| Item | Estado | Evidencia |
|------|--------|-----------|
| Arquitectura de consolidación BD | ✅ | 10 fases implementadas |
| Scripts de migración idempotentes | ✅ | `scripts/archive/migrate_to_sa.py` |
| Sistema de feature flags | ✅ | `config/feature_flags.py` |
| Validación post-migración | ✅ | 6/6 checks PASS |
| Tests unitarios | ✅ | 912 passed |
| Backup pre-migración | ✅ | `backups/20260324/` |
| Datos migrados (demo) | ✅ | 5 clientes → SQLAlchemy |
| Runbook documentado | ✅ | `docs/RUNBOOK_DB_MIGRATION.md` |
| Rollback procedures | ✅ | `scripts/archive/rollback_migration.py` |
| Migration monitor | ✅ | `core/services/migration_monitor.py` |
| Health check endpoints | ✅ | `/health`, `/health/ready` |
| Limpieza de código legacy | ✅ | 17 archivos archivados |
| Deprecation warnings | ✅ | `src/gestor_bd.py` marcado |
| BD legacy archivada | ✅ | `registros/archive/` |
| **FASE 2 Dual-Write activa** | ✅ | `.env` configurado |

---

## 🔄 PRÓXIMOS PASOS PARA PRODUCCIÓN

### FASE 2: Activar Dual-Write (Recomendado: 1-7 días)

```bash
# Variables de entorno para Fase 2
export DB_DUAL_WRITE=true
export DB_USE_SA_READ=false  # Aún lee de legacy
export DB_DEBUG_SYNC=true     # Logs de operaciones

# Verificar
python -c "from config.feature_flags import get_migration_flags; print(get_migration_flags().current_phase())"
# Debe mostrar: FASE_2_DUAL_WRITE
```

**Criterios para avanzar a Fase 3:**
- [ ] 0 errores de sync en 48 horas
- [ ] Métricas de latencia < 200ms
- [ ] Validación de paridad 100%

---

### FASE 3: SQLAlchemy Primary (Recomendado: 3-7 días)

```bash
# Variables de entorno para Fase 3
export DB_SA_PRIMARY=true
export DB_DUAL_WRITE=false
export DB_SHADOW_WRITE=true  # Mantiene legacy sincronizado para rollback

# Verificar
python -c "from config.feature_flags import get_migration_flags; print(get_migration_flags().current_phase())"
# Debe mostrar: FASE_3_SA_PRIMARY
```

**Criterios para avanzar a Fase 4:**
- [ ] 0 incidentes en 7 días
- [ ] Rendimiento mejorado vs legacy
- [ ] Stakeholders confirmados

---

### FASE 4: Legacy Deprecated (Después de 30 días estables)

```bash
export DB_LEGACY_DEPRECATED=true
export DB_SHADOW_WRITE=false

# Archivar BD legacy
mv registros/clientes.db registros/archive/clientes_deprecated_$(date +%Y%m%d).db
```

---

## 📋 CHECKLIST DE INFRAESTRUCTURA

### Seguridad
- [ ] HTTPS configurado (certificado SSL válido)
- [ ] Variables sensibles en secrets manager (no .env)
- [ ] Rate limiting configurado
- [ ] CORS configurado para dominios permitidos
- [ ] Headers de seguridad (CSP, X-Frame-Options, etc.)

### Base de Datos
- [ ] Backups automáticos configurados (diarios)
- [ ] Política de retención definida (30 días mínimo)
- [ ] Conexión segura a PostgreSQL (producción)
- [ ] Pool de conexiones optimizado

### Monitoreo
- [ ] Health check endpoint (`/health`)
- [ ] Métricas de latencia configuradas
- [ ] Alertas de errores críticos
- [ ] Dashboard de migración activo
- [ ] Logs estructurados (JSON)

### CI/CD
- [ ] Pipeline de tests automático
- [ ] Deploy automático a staging
- [ ] Deploy manual a producción (con approval)
- [ ] Rollback automático en caso de fallo

### Documentación
- [x] Runbook de migración
- [x] Rollback procedures
- [ ] Documentación de API (`/docs`)
- [ ] Manual de usuario actualizado

---

## 🔧 COMANDOS RÁPIDOS DE PRODUCCIÓN

### Verificar Estado
```bash
# Estado de flags
python -c "from config.feature_flags import get_migration_flags; f=get_migration_flags(); print(f'Fase: {f.current_phase()}')"

# Contar registros
python -c "
from web.database.engine import init_db, get_engine
from web.database.models import Cliente
from sqlalchemy.orm import sessionmaker
init_db()
s = sessionmaker(bind=get_engine())()
print(f'Clientes SA: {s.query(Cliente).count()}')
s.close()
"

# Tests rápidos
python -m pytest tests/ -q --tb=no -x
```

### Monitoreo de Migración
```bash
# Métricas de sync
python -c "
from core.services.migration_monitor import MigrationMonitor
m = MigrationMonitor()
print(m.get_metrics_summary())
"

# Validar paridad
python scripts/validate_migration.py --legacy-db registros/clientes.db
```

### Rollback de Emergencia
```bash
# SOLO EN CASO DE INCIDENTE CRÍTICO
python scripts/rollback_migration.py --target-phase 1 --confirm

# Restaurar backup
cp backups/YYYYMMDD/clientes.db registros/clientes.db
```

---

## 📊 MÉTRICAS DE ÉXITO

| Métrica | Objetivo | Actual |
|---------|----------|--------|
| Tests pasando | 100% | ✅ 912/912 |
| Latencia API (p95) | < 200ms | TBD |
| Disponibilidad | 99.9% | TBD |
| Errores de sync | 0 | N/A (Fase 1) |
| Clientes migrados | 100% | 5/5 demo |

---

## 📅 TIMELINE SUGERIDO

| Día | Actividad |
|-----|-----------|
| D+0 | Activar Fase 2 (Dual-Write) en staging |
| D+2 | Validar métricas, promover a producción |
| D+7 | Si estable → Activar Fase 3 (SA Primary) |
| D+14 | Validar rendimiento, confirmar estabilidad |
| D+30 | Activar Fase 4 (Legacy Deprecated) |
| D+60 | Archivar BD legacy |

---

## 🆘 CONTACTOS DE EMERGENCIA

| Rol | Contacto |
|-----|----------|
| Desarrollador Principal | [TBD] |
| DBA | [TBD] |
| SRE/DevOps | [TBD] |
| Product Owner | [TBD] |

---

*Generado automáticamente post-migración. Actualizar con datos reales antes de producción.*
