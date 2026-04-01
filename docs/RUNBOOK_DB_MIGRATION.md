# RUNBOOK: Migración de BD a Producción

## Fecha Objetivo: [TBD]
## Responsable: [TBD]
## Tiempo Estimado: 2-4 horas (dependiendo de volumen de datos)

---

## PRE-REQUISITOS

- [ ] Tests pasando en CI (912+ tests)
- [ ] Backup completo de producción
- [ ] Ventana de mantenimiento comunicada (recomendado: domingo 2-6am)
- [ ] Acceso a logs y monitoring
- [ ] Canales de comunicación listos (Slack/Discord)

---

## FASE 0: PREPARACIÓN (1 día antes)

### 0.1 Backup Completo
```bash
# En servidor de producción
cd /app
mkdir -p backups/$(date +%Y%m%d)
cp registros/clientes.db backups/$(date +%Y%m%d)/
cp registros/metodobase_web.db backups/$(date +%Y%m%d)/
cp registros/web_usuarios.db backups/$(date +%Y%m%d)/

# Verificar backups
ls -la backups/$(date +%Y%m%d)/
```

### 0.2 Verificar Estado Actual
```bash
# Contar registros baseline
sqlite3 registros/clientes.db "SELECT COUNT(*) FROM clientes;"
sqlite3 registros/clientes.db "SELECT COUNT(*) FROM planes_generados;"
```

### 0.3 Variables de Entorno
```bash
# Verificar configuración actual
echo $DB_MIGRATION_PHASE  # Debe ser 1 o vacío
echo $DATABASE_URL
```

---

## FASE 1: MIGRACIÓN INICIAL (30-60 min)

### 1.1 Activar Modo Mantenimiento (Opcional)
```bash
# Si tienes flag de mantenimiento
export MAINTENANCE_MODE=true
# O bloquear tráfico en nginx/load balancer
```

### 1.2 Dry Run
```bash
python scripts/migrate_to_sa.py \
  --legacy-db registros/clientes.db \
  --gym-id gym_prod \
  --dry-run

# Revisar output: ¿Cuántos registros se migrarán?
# Debe mostrar 0 errores
```

### 1.3 Migración Real
```bash
python scripts/migrate_to_sa.py \
  --legacy-db registros/clientes.db \
  --gym-id gym_prod

# Guardar el archivo de resultados
cp migration_results_*.json backups/$(date +%Y%m%d)/
```

### 1.4 Validación Inmediata
```bash
python scripts/validate_migration.py \
  --legacy-db registros/clientes.db \
  --output backups/$(date +%Y%m%d)/validation_report.json

# DEBE mostrar: "Validación: PASS"
# Si falla, ir a ROLLBACK
```

---

## FASE 2: DUAL-WRITE (1-7 días)

### 2.1 Activar Dual-Write
```bash
export DB_MIGRATION_DUAL_WRITE=true
export DB_MIGRATION_PHASE=2

# Reiniciar aplicación
systemctl restart metodobase  # o tu método de deploy
```

### 2.2 Monitoreo Continuo
```bash
# Verificar métricas cada hora durante primeras 24h
curl http://localhost:8000/api/v1/admin/migration/status

# Debe mostrar:
# - operation_error_rate < 0.01
# - parity_mismatch_rate < 0.001
# - sync_lag_seconds < 60
```

### 2.3 Alertas a Vigilar
- `operation_error_rate > 0.05` → ROLLBACK
- `parity_mismatch_rate > 0.01` → Investigar
- `sync_lag_seconds > 300` → Investigar

---

## FASE 3: SA PRIMARY (después de 7 días sin incidentes)

### 3.1 Cambiar a SA como Primary
```bash
export DB_MIGRATION_SA_PRIMARY=true
export DB_MIGRATION_PHASE=3

# Reiniciar
systemctl restart metodobase
```

### 3.2 Verificación
```bash
# Crear un cliente de prueba via UI
# Verificar que aparece en SA
sqlite3 registros/metodobase_web.db "SELECT * FROM clientes ORDER BY id DESC LIMIT 1;"

# Verificar que también está en legacy (shadow write)
sqlite3 registros/clientes.db "SELECT * FROM clientes ORDER BY id DESC LIMIT 1;"
```

---

## FASE 4: LEGACY DEPRECATED (después de 14 días sin incidentes)

### 4.1 Desactivar Legacy
```bash
export DB_MIGRATION_LEGACY_DEPRECATED=true
export DB_MIGRATION_PHASE=4

systemctl restart metodobase
```

### 4.2 Cleanup (después de 30 días)
```bash
# Archivar legacy DB
mv registros/clientes.db registros/archive/clientes_deprecated_$(date +%Y%m%d).db

# Eliminar código legacy (PR separado)
# - Remover src/gestor_bd.py
# - Remover src/compat/
# - Actualizar imports
```

---

## ROLLBACK PROCEDURES

### Rollback Nivel 1: Volver a Fase Anterior
```bash
# Ver estado actual
python scripts/rollback_migration.py --status

# Rollback a fase específica
python scripts/rollback_migration.py --to-phase 2 --backup --execute

# Reiniciar
systemctl restart metodobase
```

### Rollback Nivel 2: Restaurar Backup
```bash
# Detener aplicación
systemctl stop metodobase

# Restaurar desde backup
python scripts/rollback_migration.py --restore 20260324_020000 --execute

# O manualmente:
cp backups/20260324/clientes.db registros/clientes.db
cp backups/20260324/metodobase_web.db registros/metodobase_web.db

# Volver a fase 1
export DB_MIGRATION_PHASE=1
export DB_MIGRATION_DUAL_WRITE=false

# Reiniciar
systemctl restart metodobase
```

### Rollback Nivel 3: Emergencia Total
```bash
# Desactivar TODA la lógica de migración
export DB_MIGRATION_DISABLED=true

# Forzar uso de legacy únicamente
# Esto requiere código de fallback en ClienteRepository
```

---

## TROUBLESHOOTING

### Error: "Parity mismatch detected"
1. Ejecutar `python scripts/validate_migration.py --output debug.json`
2. Revisar `debug.json` → sección `mismatches`
3. Si son pocos registros: corregir manualmente
4. Si son muchos: rollback y revisar transformadores ETL

### Error: "Sync lag > 300s"
1. Verificar carga del servidor
2. Verificar conectividad a BD
3. Si persiste: reducir batch_size en migración

### Error: "SQLAlchemy session error"
1. Verificar `DATABASE_URL`
2. Verificar que la BD existe y tiene permisos
3. Ejecutar `python -c "from web.database.engine import init_db; init_db()"`

---

## CONTACTOS DE ESCALACIÓN

| Nivel | Contacto | Criterio |
|-------|----------|----------|
| L1 | DevOps On-Call | Alertas automáticas |
| L2 | Backend Lead | Error rate > 5% |
| L3 | CTO | Data loss confirmado |

---

## POST-MIGRACIÓN CHECKLIST

- [ ] Todos los clientes visibles en dashboard web
- [ ] Generación de planes funciona end-to-end
- [ ] Reportes de gym muestran datos correctos
- [ ] Exportación CSV/PDF funciona
- [ ] Desktop app (si aplica) funciona con nueva BD
- [ ] Zero errores 500 en logs de últimas 24h
- [ ] Backup automatizado configurado para nueva BD
- [ ] Documentación actualizada
- [ ] Código legacy marcado como deprecated/removido
