# PROMPT: Implementación de correcciones críticas C-06 a C-10 — Auditoría de producción MetodoBase

---

## PERSONA Y CONTEXTO

Eres un **Ingeniero Senior de Seguridad SaaS** implementando correcciones críticas de producción en MetodoBase, una plataforma SaaS de nutrición para gimnasios en Guadalajara, México. Estas 5 correcciones (C-06 a C-10) son **bloqueantes para el despliegue a producción**. Sin ellas, el sistema es vulnerable a falsificación de licencias, credenciales débiles en producción, pérdida de datos por SQLite en multi-pod, y desincronización de migraciones.

**Restricciones obligatorias:**
- NO romper los tests existentes (~1030 pasando)
- NO cambiar el flujo de desarrollo — en `development`, todo debe seguir funcionando con defaults
- Todos los cambios deben ser retrocompatibles para entornos de desarrollo existentes
- Usar el patrón `from config.settings import get_settings` de forma consistente
- Respetar el estilo de código existente (docstrings en español, tipado, logging)
- `config/settings.py` ya tiene:
  - `self.is_production: bool` (True cuando `METODOBASE_ENV=production`)
  - `_require_in_prod()` que lanza `RuntimeError` si falta un env var en prod
  - `self.LICENSE_SALT` que ya usa `_require_in_prod("METODO_BASE_SALT", dev_default="METODO_BASE_2026_CH")`
  - `self.SEED_DEMO: bool` que lee `METODOBASE_SEED_DEMO`

---

## C-06 | SALT DE LICENCIA HARDCODEADO EN CÓDIGO

**Archivo:** `core/licencia.py`, línea 57  
**Riesgo:** Cualquiera puede forjar licencias válidas si conoce el salt por defecto.

### Código actual (BUSCAR EXACTO):
```python
    ARCHIVO_LICENCIA = os.path.join(APP_DATA_DIR, "licencia.lic")
    ARCHIVO_CONFIG = os.path.join(CARPETA_CONFIG, "licencia_config.json")
    SALT_MASTER: str = os.environ.get("METODO_BASE_SALT", "METODO_BASE_2026_CH")
    PERIODOS_VALIDOS_MESES = (3, 6, 9, 12)
```

### Código nuevo (REEMPLAZAR CON):
```python
    ARCHIVO_LICENCIA = os.path.join(APP_DATA_DIR, "licencia.lic")
    ARCHIVO_CONFIG = os.path.join(CARPETA_CONFIG, "licencia_config.json")
    PERIODOS_VALIDOS_MESES = (3, 6, 9, 12)
```

Y en el método `__init__` de `GestorLicencias`, agregar la resolución del salt vía settings. El `__init__` actual empieza así:

```python
    def __init__(self) -> None:
        self.ruta_licencia = Path(self.ARCHIVO_LICENCIA)
        self.ruta_config = Path(self.ARCHIVO_CONFIG)
```

**Reemplazar con:**
```python
    def __init__(self) -> None:
        from config.settings import get_settings
        self.SALT_MASTER = get_settings().LICENSE_SALT
        self.ruta_licencia = Path(self.ARCHIVO_LICENCIA)
        self.ruta_config = Path(self.ARCHIVO_CONFIG)
```

### Por qué importa
El valor `METODO_BASE_2026_CH` está en el código fuente público. Cualquier persona con acceso al repo puede generar licencias válidas. Al delegarlo a `settings.LICENSE_SALT`, en producción el salt viene del env var obligatorio; en desarrollo se usa el default de `settings.py` — sin cambio en el flujo dev.

### Casos borde
- `SALT_MASTER` era un **atributo de clase**. Ahora es un **atributo de instancia**, asignado en `__init__`. Verificar que ningún código acceda a `GestorLicencias.SALT_MASTER` sin instanciar (buscar con grep `SALT_MASTER` en todo el proyecto).
- Los tests que crean `GestorLicencias()` seguirán funcionando porque en dev `get_settings()` retorna el `dev_default`.

### Tests a verificar
```bash
pytest tests/ -k "licencia" -v
```

---

## C-07 | USUARIOS DEMO CON CREDENCIALES DÉBILES SE CREAN EN PRODUCCIÓN

**Archivo:** `web/auth.py`, función `_seed_demo_users()`, líneas 171-188  
**Riesgo:** Si alguien configura `METODOBASE_SEED_DEMO=1` en producción, se crean cuentas con `test123` que dan acceso completo.

### Código actual (BUSCAR EXACTO):
```python
def _seed_demo_users() -> None:
    """Crea usuarios demo si la tabla está vacía y METODOBASE_SEED_DEMO=1."""
    if os.getenv("METODOBASE_SEED_DEMO", "") != "1":
        return
    with _conn() as conn:
```

### Código nuevo (REEMPLAZAR CON):
```python
def _seed_demo_users() -> None:
    """Crea usuarios demo si la tabla está vacía y METODOBASE_SEED_DEMO=1."""
    from config.settings import get_settings
    if get_settings().is_production:
        return
    if os.getenv("METODOBASE_SEED_DEMO", "") != "1":
        return
    with _conn() as conn:
```

### Por qué importa
Es una defensa en profundidad. Incluso si un operador configura mal el env var `METODOBASE_SEED_DEMO=1` en Railway, la función sale inmediatamente sin crear cuentas débiles. La guarda de producción va **antes** de cualquier otro chequeo — no hay ruta de ejecución que la evite.

### Casos borde
- En desarrollo, `is_production` es `False`, así que el comportamiento no cambia.
- En tests con `METODOBASE_ENV=test`, `is_production` es `False` — los tests que dependen de seed demo siguen funcionando.
- No hay impacto de rendimiento: `get_settings()` está cacheado con `@lru_cache`.

### Tests a verificar
```bash
pytest tests/ -k "auth or login or demo or seed" -v
```

---

## C-08 | DATABASE_URL CAE A SQLITE EN PRODUCCIÓN

**Archivo:** `web/database/engine.py`, función `_get_database_url()`, líneas 22-41  
**Riesgo:** En Railway con múltiples pods, si `DATABASE_URL` no está o tiene un typo, cada pod crea su propia SQLite vacía. Los datos se pierden en cada redeploy.

### Código actual (BUSCAR EXACTO):
```python
def _get_database_url() -> str:
    """Resuelve la URL de la base de datos desde settings."""
    from config.settings import get_settings
    settings = get_settings()

    # DATABASE_URL explícita tiene prioridad
    import os
    url = os.getenv("DATABASE_URL", "")
    if url:
        # Railway usa postgres:// pero SQLAlchemy requiere postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # Fallback: SQLite local (desarrollo)
    from config.constantes import CARPETA_REGISTROS
    from pathlib import Path
    db_path = Path(CARPETA_REGISTROS) / "metodobase_web.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"
```

### Código nuevo (REEMPLAZAR CON):
```python
def _get_database_url() -> str:
    """Resuelve la URL de la base de datos desde settings."""
    from config.settings import get_settings
    settings = get_settings()

    # DATABASE_URL explícita tiene prioridad
    import os
    url = os.getenv("DATABASE_URL", "")
    if url:
        # Railway usa postgres:// pero SQLAlchemy requiere postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # En producción, PostgreSQL es obligatorio — no permitir fallback a SQLite
    if settings.is_production:
        raise RuntimeError(
            "FATAL: DATABASE_URL no está configurada o está vacía. "
            "PostgreSQL es obligatorio en producción. "
            "Configure DATABASE_URL en las variables de entorno del despliegue."
        )

    # Fallback: SQLite local (solo desarrollo)
    from config.constantes import CARPETA_REGISTROS
    from pathlib import Path
    db_path = Path(CARPETA_REGISTROS) / "metodobase_web.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"
```

### Por qué importa
SQLite en producción multi-pod = pérdida total de datos. Cada pod tiene su propio filesystem efímero. Un `RuntimeError` en startup es infinitamente mejor que descubrir que cada pod tiene clientes distintos.

### Casos borde
- En desarrollo sin `DATABASE_URL`, el fallback a SQLite sigue funcionando (no es producción).
- Si `DATABASE_URL` tiene un typo pero está definida (e.g., `postgresss://...`), la conexión fallará en SQLAlchemy con un error claro — no es responsabilidad de esta función validar el driver, solo asegurar que no se caiga silenciosamente a SQLite.
- `settings` ya se importa pero no se usaba antes del fallback. Ahora sí.

### Tests a verificar
```bash
pytest tests/ -k "database or engine or db" -v
```

---

## C-09 | MIGRACIONES ALEMBIC NO SE EJECUTAN EN DEPLOY

**Archivos:** `railway.toml`, nuevo `entrypoint.sh`, `Dockerfile`  
**Riesgo:** Cambios de esquema requieren intervención manual. Si se olvidan, la app arranca con un esquema viejo y lanza errores 500.

### Cambio 1: `railway.toml`

**Código actual (BUSCAR EXACTO):**
```toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 10
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 5
```

**Código nuevo (REEMPLAZAR CON):**
```toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 10
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 5
releaseCommand = "alembic upgrade head"
```

### Cambio 2: Crear `entrypoint.sh` (archivo nuevo en la raíz del proyecto)

```bash
#!/bin/bash
set -e

echo "=== MetodoBase: Ejecutando migraciones Alembic ==="
alembic upgrade head

echo "=== MetodoBase: Iniciando servidor ==="
exec python web/main_web.py --no-browser
```

**Nota:** El archivo debe tener permisos de ejecución. Ejecutar `chmod +x entrypoint.sh` después de crearlo. Alternativamente, el Dockerfile puede usar `RUN chmod +x entrypoint.sh`.

### Cambio 3: `Dockerfile` — Actualizar CMD y agregar entrypoint

**Código actual al final del Dockerfile (BUSCAR EXACTO):**
```dockerfile
# Non-root user
USER appuser

# Health check para Docker / Railway
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

EXPOSE ${PORT}

# Ejecutar — Railway inyecta PORT automáticamente
CMD ["python", "web/main_web.py", "--no-browser"]
```

**Código nuevo (REEMPLAZAR CON):**
```dockerfile
# Copiar entrypoint y asignar permisos
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copiar Alembic config y migraciones
COPY alembic.ini /app/alembic.ini

# Non-root user
USER appuser

# Health check para Docker / Railway
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

EXPOSE ${PORT}

# Ejecutar — Railway usa releaseCommand para migraciones; Docker usa entrypoint
CMD ["/app/entrypoint.sh"]
```

**IMPORTANTE:** El `COPY entrypoint.sh` y el `COPY alembic.ini` deben ir **antes** de `USER appuser` porque después de cambiar de usuario, no se pueden hacer operaciones que requieran root. El `RUN chmod +x` también debe ir antes.

### Por qué importa
Sin migraciones automáticas, cada release con cambios de esquema va a provocar errores 500 en producción. Con Railway, `releaseCommand` ejecuta la migración como paso previo al deploy — si falla, el deploy se cancela automáticamente. Para Docker genérico, `entrypoint.sh` resuelve lo mismo.

### Casos borde
- Si la base de datos está completamente nueva, `alembic upgrade head` aplica todas las migraciones en orden. No hay problema.
- Si la migración falla, en Railway el deploy se cancela. En Docker, `set -e` en entrypoint.sh causa que el container muera antes de iniciar la app.
- El `alembic.ini` ya existe en la raíz del proyecto y apunta a `web/database/alembic` como `script_location`.
- El directorio `web/database/alembic/` y sus versiones ya están copiados por `COPY web/ web/` del Dockerfile existente.

### Tests a verificar
```bash
# Verificar que las migraciones siguen aplicándose correctamente
alembic check  # Si disponible, o:
alembic upgrade head --sql  # Genera SQL sin ejecutar, para validar
```

---

## C-10 | `create_all()` BYPASA EL SISTEMA DE MIGRACIONES

**Archivo:** `web/main_web.py`, línea ~220  
**Riesgo:** `create_all()` crea tablas fuera del control de Alembic. Si Alembic cree que el esquema es X pero `create_all()` modificó tablas, las migraciones futuras fallan o producen un estado inconsistente.

### Código actual (BUSCAR EXACTO):
```python
    # Inicializar base de datos SA + crear tablas
    from web.database.engine import init_db, get_engine
    from web.database.models import Base
    init_db()
    Base.metadata.create_all(bind=get_engine())
```

### Código nuevo (REEMPLAZAR CON):
```python
    # Inicializar base de datos SA
    from web.database.engine import init_db, get_engine
    from web.database.models import Base
    init_db()
    # create_all() solo en desarrollo — en producción Alembic gestiona el esquema
    from config.settings import get_settings
    if not get_settings().is_production:
        Base.metadata.create_all(bind=get_engine())
```

### Por qué importa
`create_all()` es útil en desarrollo porque permite arrancar rápido sin correr migraciones. Pero en producción es un anti-patrón peligroso: crea tablas que Alembic no conoce, no actualiza columnas existentes, y puede esconder errores de migración (la app arranca pero con un esquema incompleto o desalineado).

### Casos borde
- En desarrollo, `create_all()` sigue ejecutándose — no hay cambio en el flujo dev.
- En producción, las tablas deben existir porque `alembic upgrade head` las creó (C-09). Si no existen, la app falla rápido con un error claro en lugar de crear tablas silenciosas.
- Si hay tests que dependen de `create_all()`, siguen funcionando porque tests corren en `development` o `test`, no en `production`.

### Tests a verificar
```bash
pytest tests/ -k "web or main" -v
```

---

## CHECKLIST DE VERIFICACIÓN POST-IMPLEMENTACIÓN

Ejecuta cada paso en orden y verifica que pasa:

```bash
# 1. Verificar que no hay errores de sintaxis
python -m py_compile core/licencia.py
python -m py_compile web/auth.py
python -m py_compile web/database/engine.py
python -m py_compile web/main_web.py

# 2. Verificar que SALT_MASTER no está hardcodeado en ningún lado
grep -rn "METODO_BASE_2026_CH" --include="*.py" | grep -v "config/settings.py" | grep -v "__pycache__"
# ESPERADO: 0 resultados (solo settings.py debe tener el default)

# 3. Verificar la guarda de producción en seed demo
grep -n "is_production" web/auth.py
# ESPERADO: aparece dentro de _seed_demo_users

# 4. Verificar la guarda de producción en engine.py
grep -n "is_production" web/database/engine.py
# ESPERADO: aparece en _get_database_url con RuntimeError

# 5. Verificar que create_all tiene guarda de producción
grep -n "is_production" web/main_web.py
# ESPERADO: aparece antes de create_all

# 6. Verificar el releaseCommand en railway.toml
grep "releaseCommand" railway.toml
# ESPERADO: releaseCommand = "alembic upgrade head"

# 7. Verificar que entrypoint.sh existe y tiene permisos
test -x entrypoint.sh && echo "OK" || echo "FALTA chmod +x"

# 8. Verificar que Dockerfile usa entrypoint.sh
grep "entrypoint.sh" Dockerfile
# ESPERADO: aparece en COPY y CMD

# 9. Suite completa de tests
pytest tests/ -x -q
# ESPERADO: ~1030 tests pasando, 0 fallos

# 10. Verificar comportamiento en modo desarrollo (no debe romper nada)
METODOBASE_ENV=development python -c "
from config.settings import get_settings
s = get_settings()
assert not s.is_production
assert s.LICENSE_SALT == 'METODO_BASE_2026_CH'
print('DEV settings: OK')
"

# 11. Verificar que producción sin env vars falla correctamente
METODOBASE_ENV=production python -c "
try:
    from config.settings import get_settings
    get_settings()
    print('ERROR: debería haber fallado')
except RuntimeError as e:
    print(f'CORRECTO: {e}')
"
```

---

## RESUMEN DE ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---|---|
| `core/licencia.py` | Eliminar salt hardcodeado, resolver vía `get_settings().LICENSE_SALT` en `__init__` |
| `web/auth.py` | Agregar guarda `if get_settings().is_production: return` al inicio de `_seed_demo_users()` |
| `web/database/engine.py` | Agregar `RuntimeError` si producción sin `DATABASE_URL` |
| `web/main_web.py` | Condicionar `create_all()` a `not is_production` |
| `railway.toml` | Agregar `releaseCommand = "alembic upgrade head"` |
| `Dockerfile` | Copiar `entrypoint.sh` y `alembic.ini`, cambiar CMD a entrypoint |
| `entrypoint.sh` | **NUEVO** — Script que corre migraciones y luego arranca la app |

**Total: 6 archivos modificados + 1 archivo nuevo. Cero features nuevas, cero dependencias nuevas, cero cambios de API.**
