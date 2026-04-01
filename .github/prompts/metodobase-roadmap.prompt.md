---
name: "MetodoBase — Roadmap de Producción"
description: "Implementa tareas del roadmap de MetodoBase: licencias, build/distribución, correcciones técnicas urgentes y experiencia de compra. Uso: /metodobase-roadmap <area>"
agent: "agent"
argument-hint: "Área a trabajar: licencias | build | compra | precios | correcciones"
tools:
  - search
---

# MetodoBase — Roadmap de Producción

Eres un agente experto en Python, PySide6 y distribución de software desktop.
Trabaja en el área indicada por el argumento: **$este proyecto**

Si no se indica un área, presenta el menú de áreas disponibles y pide al usuario que elija una.

---

## Contexto del proyecto

- Entrada principal: `main.py`
- Licencias: `core/licencia.py`
- Constantes: `config/constantes.py`
- API servicios: `api/services.py`
- Build spec: `MetodoBase.spec`
- Instalador: `setup_installer.iss`
- Panel inicio: `ui_desktop/pyside/panel_inicio.py`

---

## Área 1 — `licencias`: Endurecimiento del sistema de licencias

Leer primero `core/licencia.py` y entender la estructura actual antes de modificar.

### Tareas

1. **Validación online** — Agregar método `validar_licencia_online(clave: str) -> tuple[bool, str]` que haga POST a `https://api.metodobase.app/v1/licencias/validar` con la clave y el `hardware_id`. Usar `urllib.request` (sin dependencias extra). Cachear resultado en SQLite local por 24 h para funcionar offline. Nunca exponer la clave en logs.

2. **Modelo por volumen** — Extender el modelo de licencia para incluir un campo `max_clientes: int` (0 = ilimitado). Al crear o actualizar un cliente en `src/gestor_usuarios.py`, verificar que `clientes_activos < licencia.max_clientes`. Lanzar `LicenciaExcedidaError` si se supera el límite.

3. **Trial 14 días / 3 clientes** — Si `licencia.tipo == "trial"`, limitar a 3 clientes activos y validar que `datetime.utcnow() < licencia.fecha_expiracion`. Mostrar banner en `GymAppWindow` con días restantes.

4. **Revocación remota** — En cada arranque, si la licencia está activa y hay conexión, consultar `/v1/licencias/estado/{hardware_id}`. Si el servidor responde `revocada`, marcar la licencia como inactiva en la BD local y redirigir al usuario a la ventana de activación.

5. **Ofuscación en build** — Documentar en `build_config.py` los pasos para ofuscar `core/licencia.py` con PyArmor antes de ejecutar PyInstaller. El script debe ser idempotente.

> Implementar en el orden 1 → 2 → 3 → 4 → 5. Agregar tests en `tests/test_licencia.py` para cada caso nuevo.

---

## Área 2 — `build`: Empaquetado y distribución

Leer `MetodoBase.spec` y `setup_installer.iss` antes de modificar.

### Tareas

1. **Afinar `MetodoBase.spec`** — Asegurar que `datas` incluya `fonts/Inter/`, `assets/styles/`, `config/branding.json` y `ui_desktop/pyside/styles/`. Activar `strip=True` y `upx=True` para reducir tamaño. Verificar que `hiddenimports` incluye todos los módulos dinámicos usados en `main.py`.

2. **Completar `setup_installer.iss`** — Agregar sección `[Icons]` para acceso directo en Escritorio y Menú Inicio. Agregar sección `[Run]` para ejecutar la app al finalizar la instalación. Configurar `AppVersion` tomando el valor de `config/constantes.py::VERSION`.

3. **Auto-actualización** — Crear `utils/updater.py` con función `check_for_update() -> dict | None` que consulte `https://cdn.metodobase.app/releases/latest.json` (campos: `version`, `url`, `sha256`). Si `version > VERSION_ACTUAL`, mostrar diálogo de confirmación y descargar el patch a una carpeta temporal, verificar SHA-256, y reemplazar el ejecutable al reiniciar. Usar threading para no bloquear la UI.

4. **Firma de código** — Agregar sección en `README_DISTRIBUCION.md` detallando los pasos para firmar el `.exe` con `signtool.exe` usando un certificado EV, y los comandos para notarizar el `.dmg` en macOS.

5. **Build macOS** — Agregar target `macos` en `build_all.bat` (o crear `build_all.sh`) que genere el `.app` bundle y lo empaquete como `.dmg` con `create-dmg`.

---

## Área 3 — `compra`: Experiencia de compra

### Tareas

1. **Landing page** — Crear `web/pages/landing.html` con secciones: hero, características, precios (tabla del área 4), CTA de compra. Usar el sistema de diseño existente en `web/static/css/`.

2. **Portal de licencias** — Crear endpoint `POST /api/licencias/activar` en `api/routes/` que reciba `{clave, hardware_id, email}`, valide contra la base de datos de licencias del servidor, y devuelva `{activa: bool, max_clientes: int, expira: str}`.

3. **Integración de pago** — Crear `web/pages/checkout.html` + `api/routes/pagos.py` con endpoints para iniciar sesión de pago en Stripe (`/api/pagos/stripe/session`) y en MercadoPago (`/api/pagos/mp/preference`). Los webhooks deben crear automáticamente una licencia al confirmar el pago. Nunca loguear datos de tarjeta.

4. **Facturación PDF** — Reutilizar `api/pdf_generator.py` para generar un PDF de factura con: número de folio, datos del comprador, plan adquirido, precio, IVA y QR de verificación.

---

## Área 4 — `precios`: Modelo de precios

Documentar el modelo de precios en `README_COMERCIAL.md` y sincronizarlo con las constantes del sistema.

### Tareas

1. **Constantes de planes** — Agregar en `config/constantes.py`:
   ```python
   PLANES_LICENCIA = {
       "starter":      {"precio_usd": 29, "max_clientes": 25,   "multi_usuario": False},
       "profesional":  {"precio_usd": 59, "max_clientes": 100,  "multi_usuario": False},
       "clinica":      {"precio_usd": 129,"max_clientes": 0,    "multi_usuario": True},
   }
   ```
2. **Tabla en README** — Actualizar `README_COMERCIAL.md` con la tabla de precios formateada en Markdown.
3. **UI de planes** — En la ventana de activación de licencia (`ui_desktop/pyside/ventana_licencia.py`), mostrar los planes disponibles con su precio y límite usando `PLANES_LICENCIA`.

---

## Área 5 — `correcciones`: Correcciones técnicas urgentes

Estas correcciones son **bloqueantes para venta**. Resolverlas en orden de severidad.

### 5.1 Crítico — Clases duplicadas en `panel_inicio.py`

```
ui_desktop/pyside/panel_inicio.py — dos definiciones de PanelInicio y ResultadoInicio
```

1. Leer el archivo completo.
2. Identificar cuál de las dos definiciones es la más reciente / completa.
3. Eliminar la definición redundante manteniendo la funcional.
4. Verificar que no hay imports rotos con `get_errors`.

### 5.2 Crítico — Re-imports dentro de función en `main.py`

Las líneas ~341, ~349, ~351, ~359 de `main.py` contienen imports dentro del bloque `else` (modo consola) que ya se importan al inicio del archivo.

1. Leer `main.py` completo para verificar los imports duplicados exactos.
2. Eliminarlos del bloque `else` y asegurarse de que los imports top-level los cubren.
3. Ejecutar `python -c "import main"` para confirmar que no hay errores de importación.

### 5.3 Importante — `OBJETIVOS_VALIDOS` redefinido en `api/services.py`

```
api/services.py línea ~282 — lista local que duplica config.constantes.OBJETIVOS_VALIDOS
```

1. Leer `api/services.py` alrededor de la línea 282.
2. Sustituir la definición local por `from config.constantes import OBJETIVOS_VALIDOS`.
3. Verificar con `get_errors` que no hay efectos secundarios.

### 5.4 Importante — Alinear `_NIVELES_ACTIVIDAD` en `panel_perfil_detalle.py`

1. Leer `ui_desktop/pyside/panel_perfil_detalle.py` y localizar `_NIVELES_ACTIVIDAD`.
2. Leer `config/constantes.py` y obtener `FACTORES_ACTIVIDAD`.
3. Reemplazar la definición local con los valores de `FACTORES_ACTIVIDAD` para garantizar consistencia.

### 5.5 Limpieza de imports sin usar

1. Ejecutar `python -m pyflakes .` (o `ruff check . --select F401`) para listar los ~70 imports sin usar.
2. Eliminarlos archivo por archivo, verificando con `get_errors` después de cada archivo.
3. No eliminar imports que puedan ser usados dinámicamente (e.g., en `__init__.py` como re-exports).

---

## Reglas de trabajo

- Leer siempre el archivo antes de modificarlo.
- Usar `get_errors` después de cada cambio para verificar que no se introdujeron errores.
- Los tests existentes en `tests/` deben seguir pasando (`python -m pytest tests/ -x -q`).
- No agregar dependencias nuevas sin actualizar `requirements.txt`.
- No sobre-ingeniería: implementar exactamente lo descrito, sin funciones extra.
