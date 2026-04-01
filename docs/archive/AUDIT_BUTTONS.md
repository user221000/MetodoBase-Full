# AUDIT_BUTTONS.md — Auditoría de Botones UI
**Generado:** 2026-03-17  
**Alcance:** `ui_desktop/pyside/` y `gui/`  
**Agente:** Agente 4 — Auditor de Funcionalidad

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Total QPushButton creados (pyside/) | ~177 |
| Botones con `clicked.connect` | ~102 |
| Botones con `setToolTip` | ~15 |
| Módulo facturación | **Desactivado** (ENABLE_BILLING=False) |
| Botones huérfanos identificados | Ver tabla abajo |

---

## Tabla de Auditoría por Archivo

### `ui_desktop/pyside/ventana_login_unificada.py` ✅ NUEVO

| Botón | Handler | Estado | Tooltip |
|-------|---------|--------|---------|
| `_btn_tab_gym` "🏢 GYM" | `_cambiar_a_gym()` | ✅ Conectado | "Acceso para socios comerciales gym" |
| `_btn_tab_user` "👤 Usuario" | `_cambiar_a_usuario()` | ✅ Conectado | "Acceso para usuarios regulares" |
| `_btn_acceder` (GYM) | `_intentar_login()` | ✅ Conectado | "Inicia sesión con el correo y contraseña..." |
| `btn_login` (Usuario) | `_intentar_login()` | ✅ Conectado | "Inicia sesión con tu correo..." |
| `btn_reg` "Crear Cuenta" | `_intentar_registro()` | ✅ Conectado | "Crea tu cuenta de usuario regular" |
| Link "Registrarse" | `stack.setCurrentIndex(1)` | ✅ Conectado | — |
| Link "Volver" | `stack.setCurrentIndex(0)` | ✅ Conectado | — |
| Link "Registrar mi gym" | `solicitar_registro.emit()` | ✅ Conectado | — |

---

### `ui_desktop/pyside/panel_inicio.py`

> **NOTA:** Ya no se invoca desde el flujo principal. Reemplazado por
> `VentanaLoginUnificada`. El archivo se mantiene para compatibilidad.

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| Btn GYM card | `done(ResultadoInicio.GYM)` | ✅ Conectado | Ahora sólo accesible si se importa directamente |
| Btn Usuario card | `done(ResultadoInicio.USUARIO)` | ✅ Conectado | Idem |

---

### `ui_desktop/pyside/ventana_acceso_gym.py`

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| `_btn_acceder` "Acceder" | `_intentar_login()` | ✅ Conectado | Sólo se muestra en registro nuevo (primera vez) |
| `_btn_registrar` "Registrar Gym" | `_intentar_registrar()` | ✅ Conectado | |
| Btn "Mostrar/Ocultar contraseña" | `SecurePasswordInput` handler | ✅ Conectado | |

---

### `ui_desktop/pyside/ventana_auth.py`

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| `_btn_login` "Iniciar Sesión" | `_intentar_login()` | ✅ Conectado | Flujo usuario regular |
| `_btn_registrar` "Registrar" | `_intentar_registro()` | ✅ Conectado | |
| `_btn_copiar_id` "Copiar ID" | Clipboard + TTL 30s | ✅ Conectado | Seguridad: auto-ocultar |
| `_btn_privacidad` | `DialogoPrivacidad` | ✅ Conectado | |

---

### `ui_desktop/pyside/clientes_panel.py`

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| "👥 Nuevo Cliente" | `_nuevo_cliente()` | ✅ Conectado | |
| "✏️ Editar" (por fila) | `_editar_cliente(id)` | ✅ Conectado | |
| "🗑️ Eliminar" (por fila) | `_confirmar_eliminar(id)` | ✅ Conectado | Confirmación previa |
| "📋 Generar Plan" | `generar_plan_para.emit(id)` | ✅ Conectado | Signal cross-panel |
| "🔍 Buscar" | `_filtrar_clientes()` | ✅ Conectado | Live filter |

---

### `ui_desktop/pyside/generar_plan_panel.py`

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| "📋 Generar Plan" | `_generar_plan()` | ✅ Conectado | Thread separado |
| "💾 Exportar PDF" | `_exportar_pdf()` | ✅ Conectado | |
| "👁️ Vista Previa" | `_vista_previa()` | ✅ Conectado | |
| "📂 Abrir Carpeta" | `abrir_carpeta_pdf()` | ✅ Conectado | |

---

### `ui_desktop/pyside/dashboard_panel.py`

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| `_btn_nuevo_plan` "➕ Nuevo Plan" | `navigate_to('generar_plan')` | ✅ Conectado | Reconectado en `GymAppWindow._conectar_senales()` |
| "👥 Ver Clientes" (secondaryButton) | `navigate_to('clientes')` | ✅ Conectado | |

---

### `ui_desktop/pyside/facturacion_panel.py`

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| "➕ Nuevo Cobro" | *(sin handler)* | ⚠️ Huérfano | **Módulo DESACTIVADO** — no se muestra |

> **Módulo desactivado** — Ver `ENABLE_BILLING = False` en `config/constantes.py`.
> El código permanece para futura reactivación.

---

### `ui_desktop/pyside/suscripciones_panel.py`

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| "➕ Nueva Suscripción" | `_nueva_suscripcion()` | ✅ Conectado | |
| "🗑️ Cancelar" | `_cancelar_suscripcion()` | ✅ Conectado | |

---

### `ui_desktop/pyside/configuracion_panel.py`

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| "💾 Guardar" | `_guardar_config()` | ✅ Conectado | |
| "🔄 Restaurar" | `_restaurar_defaults()` | ✅ Conectado | |
| ThemeSwitcher btns | `ThemeManager.set_theme()` | ✅ Conectado | |

---

### `ui_desktop/pyside/main_window.py`

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| "📋 Generar Plan" | `_generar_plan_thread()` | ✅ Conectado | Thread separado |
| "💾 Guardar PDF" | `_guardar_pdf()` | ✅ Conectado | |
| "📂 Abrir Carpeta" | `abrir_carpeta_pdf()` | ✅ Conectado | |
| "🔄 Nuevo Cliente" | `_limpiar_form()` | ✅ Conectado | |

---

### `gui/app_gui.py` (CustomTkinter)

| Botón | Handler | Estado | Observaciones |
|-------|---------|--------|---------------|
| "Generar Plan" | `_generar_plan()` | ✅ Conectado | |
| "Exportar PDF" | `_exportar()` | ✅ Conectado | |
| "Limpiar" | `_limpiar_campos()` | ✅ Conectado | |

---

## Botones Huérfanos Detectados

| # | Archivo | Botón | Problema | Acción Recomendada |
|---|---------|-------|----------|--------------------|
| 1 | `facturacion_panel.py:66` | "➕ Nuevo Cobro" | Sin handler `clicked.connect` | **Módulo desactivado** — ignorar |

---

## Tooltips Faltantes

Los siguientes botones deberían tener `setToolTip()` para mejor UX:

| Archivo | Botón | Tooltip sugerido |
|---------|-------|-----------------|
| `clientes_panel.py` | "🗑️ Eliminar" | "Eliminar cliente permanentemente" |
| `clientes_panel.py` | "✏️ Editar" | "Editar datos del cliente" |
| `generar_plan_panel.py` | "📋 Generar Plan" | "Generar plan nutricional personalizado" |
| `main_window.py` | "📋 Generar Plan" | "Calcular y generar plan nutricional" |

---

## Iconografía Aplicada

Los íconos están definidos en `utils/iconos.py` (nuevo). Para aplicar a botones:

```python
from utils.iconos import aplicar_icono_btn, TOOLTIP

# Ejemplo en QPushButton:
btn_borrar = QPushButton("Eliminar")
aplicar_icono_btn(btn_borrar, "borrar")
# Resultado: btn con ícono + tooltip "Eliminar permanentemente"
```

---

## Conclusiones

1. **~102/177 botones** tienen handler `clicked.connect` — ratio 58%.
2. El resto corresponde principalmente a **botones de utilidad** creados en helpers
   (ej. `_btn()`) que reciben el connect externamente.
3. **Único huérfano real**: "Nuevo Cobro" en `facturacion_panel.py` —
   ignorado porque el módulo está desactivado.
4. **Facturación desactivada** correctamente vía `ENABLE_BILLING = False`.
5. Se recomienda agregar `setToolTip()` a los 4 botones listados arriba.
