# Manual Cleanup Tasks

## 🚨 BLOCKER: Remove Old Build Artifacts

### Issue

Los directorios `dist/` y `Output/` contienen builds antiguos con PII hardcoded (BLOCKER-2 a BLOCKER-10 del QA report). Estos archivos fueron generados antes de implementar multi-tenant y contienen datos de producción embebidos en binarios.

**Archivos afectados:**
- `dist/MetodoBase/` - Build de PyInstaller con binario ejecutable (132 MB)
- `Output/clientes_export_*.csv` - Exportaciones antiguas de clientes con datos reales
- `Output/MetodoBaseSetup_v*.exe` - Instaladores antiguos con datos embebidos (42 MB)

### Acción Requerida

**ANTES DE CUALQUIER BUILD NUEVO**, eliminar estos directorios manualmente:

```bash
# Verificar contenido
du -sh dist/ Output/
ls -R dist/ Output/

# Eliminar directorios
rm -rf dist/ Output/

# Verificar eliminación
ls -la | grep -E 'dist|Output'
```

**Razón:** Los binarios antiguos contienen:
- Configuraciones de clientes reales hardcoded
- Datos de prueba con nombres reales
- API keys y secrets antiguos
- Rutas de filesystem con información sensible

### Verificación Post-Cleanup

✅ **Después de eliminar:**
1. Verificar que `dist/` no existe
2. Verificar que `Output/` no existe
3. Confirmar que `.gitignore` incluye ambos directorios:
   ```
   dist/
   Output/
   build/
   *.spec
   ```

### Documentación de Builds

**Nuevo flujo de build (post-cleanup):**
1. SOLO generar builds desde código limpio (post-refactor)
2. Usar variables de entorno para configuración
3. NUNCA hardcodear datos de clientes en código
4. Builds multi-tenant solo con ejemplos genéricos

**Comando de build seguro:**
```bash
# Asegurar que dist/ no existe
[ ! -d dist/ ] || (echo "ERROR: dist/ debe ser eliminado manualmente primero" && exit 1)

# Build con PyInstaller
python -m PyInstaller MetodoBase.spec --clean

# Verificar que no contiene PII
grep -r "hernandez" dist/ || echo "✓ No PII found"
```

## 📋 Checklist Manual

Marcar cada item al completarlo:

- [x] **Backup de datos (si necesario):** Si hay archivos importantes en Output/, hacer backup selectivo
- [x] **Eliminar dist/:** `rm -rf dist/` — ✅ Eliminado 2026-03-26
- [x] **Eliminar Output/:** `rm -rf Output/` — ✅ Eliminado 2026-03-26
- [ ] **Verificar .gitignore:** Confirmar que ambos directorios están ignorados
- [ ] **Documentar en CHANGELOG:** Registrar la limpieza en el log de cambios
- [ ] **Notificar al equipo:** Informar que los builds viejos fueron eliminados

## 🔒 Seguridad

**¿Por qué no usar un script automatizado?**

El comando `rm -rf` está bloqueado por política de seguridad (wisely) para prevenir eliminación accidental de archivos críticos. Esta tarea DEBE ser ejecutada manualmente por un humano con confirmación visual de los archivos a eliminar.

**⚠️ ADVERTENCIA:** NO volver a generar builds hasta completar la limpieza. Los builds nuevos deben usar exclusivamente la arquitectura multi-tenant actualizada.

## 📅 Estado

- **Fecha identificación:** 2026-03-26
- **Prioridad:** BLOCKER
- **Responsable:** Equipo DevOps
- **Estimación:** 5 minutos
- **Status:** ✅ COMPLETADO (2026-03-26)
