---
name: auditoria-proyecto
description: "Auditoría completa del proyecto MetodoBase: sintaxis, código duplicado, código muerto, inconsistencias de diseño, conflictos de dependencias, y brechas de testing. Use when: revisa el proyecto, auditoría completa, busca problemas, analiza calidad, limpieza general, find issues across project, full project review."
argument-hint: "Opcional: área específica a auditar (ej: 'solo core/', 'gui y design_system', 'tests y build')"
---

# Auditoría Completa del Proyecto MetodoBase

Workflow para realizar una revisión exhaustiva de todo el proyecto, detectando errores de sintaxis, código duplicado, código muerto, inconsistencias y problemas de configuración.

## Cuándo usar

- Antes de un release o merge importante
- Cuando se sospecha de deuda técnica acumulada
- Al integrar cambios de múltiples agentes (ej: UX/UI + backend)
- Revisiones periódicas de calidad

## Estructura del proyecto

| Capa | Carpetas | Rol |
|------|----------|-----|
| Core | `core/` | Lógica nutricional: generadores, motor, modelos |
| Datos | `src/` | SQLite, gestores, repositorios, seeds |
| API | `api/`, `api_server.py` | REST API con FastAPI |
| GUI Desktop | `ui_desktop/` | Interfaz PySide6 desktop |
| Diseño | `design_system/tokens.py` | Tokens de diseño (colores, tipografía) |
| Config | `config/` | Constantes, catálogos, branding |
| Utils | `utils/` | Utilidades transversales |
| Tests | `tests/`, `conftest.py` | Suite de pruebas pytest |
| Build | `build.py`, `build_config.py`, `setup.py`, `*.spec` | Empaquetado PyInstaller |
| Web | `web/`, `static/` | Interfaz web opcional |

## Procedimiento

### Paso 1: Planificación

Crear un todo list con las áreas a revisar. Si el usuario pidió un área específica, limitarse a ella. Si no, revisar todo en este orden:

1. `core/` y `config/` (lógica central)
2. `src/` (capa de datos)
3. `ui_desktop/` y `design_system/tokens.py` (interfaz)
4. `api/` (API REST)
5. `utils/` (utilidades)
6. `tests/` y build (calidad y empaquetado)

### Paso 2: Análisis por capa

Para cada capa, buscar estos problemas:

#### 2a. Errores de sintaxis y calidad
- Imports no utilizados o duplicados
- Variables/funciones definidas pero nunca usadas
- F-strings mal formadas
- Type hints incorrectos o contradictorios
- Indentación inconsistente

#### 2b. Código duplicado (DRY violations)
- Funciones con lógica idéntica en distintos módulos
- Constantes redefinidas en varios archivos
- Validación repetida en múltiples capas (api, gui, core)
- Clases modelo duplicadas (`core/modelos.py` vs `api/schemas.py`)

**Patrones conocidos a verificar:**
- Distribución de macros duplicada entre `generador_comidas.py`, `generador_planes.py`, `generador_opciones.py`
- Validación energética triplicada en `generador_comidas.py` y `estructura_comida.py`
- Generación de planes duplicada entre `api/services.py` y `api/routes/planes.py`
- PDF generators duplicados: `api/pdf_generator.py` vs `core/exportador_salida.py`

#### 2c. Código muerto
- Clases marcadas DEPRECATED pero no eliminadas (ej: `ConstructorPlan`)
- Funciones nunca llamadas (ej: `aplicar_penalizacion_semana()`)
- Métodos `_v1` reemplazados por `_v2` pero no eliminados
- Archivos `.backup` residuales
- TODOs/FIXMEs sin resolver

#### 2d. Inconsistencias de diseño (GUI/UX)
- Colores hardcodeados vs tokens del design system (`design_system/tokens.py`)
- Ventanas que no importan los tokens de diseño
- Estilos de botones/inputs inconsistentes entre ventanas

#### 2e. Configuración y dependencias
- Conflictos de versión entre `requirements.txt`, `requirements_api.txt`, `requirements_build.txt`
- Entry points contradictorios entre `setup.py` y `build.py`
- Version number mismatches
- Hidden imports faltantes para PyInstaller

#### 2f. Tests y cobertura
- Módulos sin tests (exportadores, GUI windows, api_server)
- Fixtures duplicadas entre archivos de test
- Test data repetida (consolidar en conftest.py)
- Build validation superficial

### Paso 3: Clasificar hallazgos

Agrupar por severidad:

| Severidad | Criterio |
|-----------|----------|
| 🔴 Crítico | Error de runtime, crash potencial, conflicto de build, data loss |
| 🟡 Importante | Código duplicado significativo, función muerta grande, inconsistencia visible al usuario |
| 🟢 Menor | Naming inconsistency, test gap menor, TODO pendiente |

### Paso 4: Reporte

Generar un reporte con:

1. **Resumen ejecutivo**: Conteo total de issues por severidad
2. **Tabla de hallazgos**: Archivo, línea, descripción, severidad, acción recomendada
3. **Acciones prioritarias**: Top 5-10 fixes ordenados por impacto

### Paso 5: Coordinación con otros agentes

Si hay un agente UX/UI trabajando en paralelo:
- Verificar que los cambios de UI usen los tokens de `design_system/tokens.py` (no hardcoded)
- Validar que no se hayan introducido imports circulares
- Confirmar que nuevos componentes sigan la estructura de `ui_desktop/pyside/widgets/`
- Revisar que no se dupliquen estilos ya definidos en `amarillo_neon.qss`

## Problemas conocidos del proyecto

Referencia rápida de issues recurrentes para verificar si persisten:

| Issue | Ubicación | Estado |
|-------|-----------|--------|
| Design system consolidado | `design_system/tokens.py` | ✅ Resuelto — fuente única de verdad |
| Colores hardcodeados en ventanas | `ui_desktop/pyside/` | ✅ Migrados a tokens |
| `ConstructorPlan` deprecated | `core/generador_planes.py` | Pendiente eliminar |
| PyInstaller version conflict | `requirements.txt` vs `requirements_build.txt` | Pendiente alinear |
| Entry point conflict | `setup.py` (main.py) vs `build.py` (api_server.py) | Pendiente resolver |
| Telemetría sin rotación activa | `utils/telemetria.py` | `rotar_si_necesario()` nunca se llama |
| SQLite fallback silencioso | `src/alimentos_base.py` | Warning solo en log, no visible al usuario |

## Checklist de completitud

Antes de cerrar la auditoría, verificar:

- [ ] Todas las capas revisadas (o las solicitadas)
- [ ] Hallazgos clasificados por severidad
- [ ] No hay imports circulares nuevos
- [ ] Design tokens consistentes entre ventanas
- [ ] Build config coherente (versiones, entry points)
- [ ] Tests no duplican fixtures innecesariamente
- [ ] Reporte entregado al usuario con acciones priorizadas
