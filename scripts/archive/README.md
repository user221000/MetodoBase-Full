# Scripts de Migración (Archivados)

> ⚠️ **Estos scripts se usaron para la migración de BD legacy → SQLAlchemy el 2026-03-24.**
> 
> Están archivados porque la migración fue completada exitosamente.
> Solo usar en caso de ROLLBACK DE EMERGENCIA.

## Contenido

| Script | Propósito |
|--------|-----------|
| `migrate_to_sa.py` | Migrar datos de clientes.db → SQLAlchemy |
| `validate_migration.py` | Validar integridad post-migración |
| `rollback_migration.py` | Revertir a BD legacy |
| `etl_mapping.py` | Transformadores de datos |

## Uso en Emergencia

### Si SQLAlchemy falla completamente:

```bash
# 1. Restaurar BD legacy desde archive
cp registros/archive/clientes_legacy_20260324.db registros/clientes.db

# 2. Ejecutar rollback
python scripts/archive/rollback_migration.py --target-phase 1 --confirm

# 3. Reiniciar con flags legacy
export DB_LEGACY_DEPRECATED=false
export DB_SA_PRIMARY=false
```

### Si necesitas re-migrar:

```bash
python scripts/archive/migrate_to_sa.py \
  --legacy-db registros/clientes.db \
  --gym-id gym_prod \
  --force

python scripts/archive/validate_migration.py \
  --legacy-db registros/clientes.db
```

## Migración Original (2026-03-24)

- **Clientes migrados:** 5 (demo) + 259 existentes
- **Validación:** 6/6 checks PASS
- **Tests:** 912 passed
- **Fase actual:** FASE_1_LEGACY_PRIMARY → transicionando a FASE_2
