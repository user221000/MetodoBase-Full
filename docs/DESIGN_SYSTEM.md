# 🎨 Aurora Fitness Design System

Sistema de diseño para Método Base MVP SaaS.

**Versión:** 1.0.0  
**Última actualización:** 2026-03

---

## 🎯 Filosofía

- **Minimalista:** Enfoque en contenido, menos distracción
- **Profesional:** Colores serios y corporativos
- **Accesible:** Contraste WCAG 2.1 AA en todos los elementos
- **Escalable:** Tokens centralizados para multi-tenancy

---

## 🎨 Paleta de Colores

Archivo fuente: [`gui/design_tokens.py`](../gui/design_tokens.py)

### Neutrales (Base)

| Token | Hex | Descripción |
|-------|-----|-------------|
| `Colors.BG_PRIMARY` | `#0A0A0B` | Fondo principal |
| `Colors.BG_SECONDARY` | `#121214` | Cards principales |
| `Colors.BG_TERTIARY` | `#1A1A1C` | Cards secundarios |
| `Colors.BORDER_DEFAULT` | `#2A2A2E` | Inputs / borders |
| `Colors.TEXT_PRIMARY` | `#E8E8EC` | Texto principal |
| `Colors.TEXT_SECONDARY` | `#94949C` | Texto secundario |

### Aurora Mint (Primario)

| Token | Hex | Descripción |
|-------|-----|-------------|
| `Colors.ACTION_PRIMARY` | `#00897B` | Color principal (CTA, links) |
| `Colors.ACTION_PRIMARY_HOVER` | `#006B5F` | Hover state |

### Verde Bosque (Secundario)

| Token | Hex | Descripción |
|-------|-----|-------------|
| `Colors.ACTION_SECONDARY` | `#7CB342` | Confirmaciones, éxito |
| `Colors.ACTION_SECONDARY_HOVER` | `#3D7D52` | Hover state |

### Estados Semánticos

| Token | Hex | Descripción |
|-------|-----|-------------|
| `Colors.SUCCESS` | `#4CAF50` | Operación exitosa |
| `Colors.WARNING` | `#F59E0B` | Advertencia |
| `Colors.ERROR` | `#EF4444` | Error |
| `Colors.INFO` | `#3B82F6` | Información |

---

## 📐 Tipografía

**Familia principal:** Inter  
**Variable font:** `fonts/Inter/InterVariable.ttf`  
**Fallback:** Segoe UI, system-ui, sans-serif

```python
Typography.FONT_STACK  # "Inter, Segoe UI, system-ui, sans-serif"
```

### Escala

| Token | Tamaño | Uso |
|-------|--------|-----|
| `Typography.SIZE_XS` | 11px | Captions |
| `Typography.SIZE_SM` | 13px | Labels secundarios |
| `Typography.SIZE_BASE` | 15px | Body, inputs |
| `Typography.SIZE_LG` | 18px | Subtítulos |
| `Typography.SIZE_XL` | 22px | Títulos H3 |
| `Typography.SIZE_2XL` | 28px | Títulos H2 |
| `Typography.SIZE_3XL` | 36px | Títulos H1 |
| `Typography.SIZE_4XL` | 48px | Hero |

### Pesos

| Token | Valor | Uso |
|-------|-------|-----|
| `Typography.WEIGHT_NORMAL` | 400 | Body text |
| `Typography.WEIGHT_MEDIUM` | 500 | Botones |
| `Typography.WEIGHT_SEMIBOLD` | 600 | Énfasis |
| `Typography.WEIGHT_BOLD` | 700 | Títulos |

### Fuentes disponibles en `fonts/Inter/`

| Archivo | Peso | Cobertura |
|---------|------|-----------|
| `Inter-Regular.ttf` | 400 | Body text |
| `Inter-Medium.ttf` | 500 | Botones, labels |
| `Inter-Bold.ttf` | 700 | Títulos |
| `InterVariable.ttf` | 100–900 | Todos los pesos (preferido) |

---

## 📏 Espaciado

Sistema basado en múltiplos de 4px:

| Token | Valor | Uso |
|-------|-------|-----|
| `Spacing.XS` | 4px | Gaps mínimos |
| `Spacing.SM` | 8px | Padding interno |
| `Spacing.MD` | 12px | Separación elementos |
| `Spacing.LG` | 16px | Padding cards |
| `Spacing.XL` | 24px | Margen secciones |
| `Spacing.XL2` | 32px | Bloques grandes |
| `Spacing.XL3` | 48px | Márgenes externos |
| `Spacing.XL4` | 64px | Secciones hero |

---

## 🔲 Border Radius

| Token | Valor | Uso |
|-------|-------|-----|
| `Radius.SM` | 6px | Inputs, tags |
| `Radius.MD` | 10px | Cards, botones |
| `Radius.LG` | 16px | Modales |
| `Radius.XL` | 24px | Hero sections |
| `Radius.FULL` | 9999px | Avatares circulares |

---

## 📦 Componentes

### Botón

```python
from gui.componentes import crear_boton

# Primario (CTA principal)
btn = crear_boton(parent, "Guardar Plan", command=guardar, variant="primary", size="lg")

# Secundario
btn = crear_boton(parent, "Cancelar", command=cancelar, variant="secondary")

# Éxito
btn = crear_boton(parent, "Confirmar", command=confirmar, variant="success")

# Peligro
btn = crear_boton(parent, "Eliminar", command=eliminar, variant="danger")

# Ghost
btn = crear_boton(parent, "Ver más", command=ver, variant="ghost")
```

**Variantes:** `primary` | `secondary` | `success` | `danger` | `ghost`  
**Tamaños:** `sm` | `md` | `lg`

### Sección / Card

```python
from gui.componentes import crear_seccion

section = crear_seccion(
    parent,
    titulo="Datos del Cliente",
    icono="👤",
    descripcion="Información básica para el plan"
)
```

### Input con Label y Validación

```python
from gui.componentes import crear_input_con_label, aplicar_estilo_error, limpiar_estilo_helper

entry, lbl_helper = crear_input_con_label(
    section,
    label_text="Nombre completo",
    placeholder="Ej: Juan Pérez",
    row=0,
)

# Mostrar error
aplicar_estilo_error(lbl_helper, "❌ Campo requerido")

# Mostrar éxito
from gui.componentes import aplicar_estilo_exito
aplicar_estilo_exito(lbl_helper, "✅ Validado")

# Limpiar
limpiar_estilo_helper(lbl_helper)
```

### KPI Card

```python
from gui.componentes import crear_kpi_card

crear_kpi_card(parent, row=0, col=0, icono="🔥", label="Calorías", valor="2,400 kcal")
```

---

## 🔄 Migración desde Sistema Legacy

### Mapeo de Colores

| Legacy | Aurora Fitness |
|--------|---------------|
| `#0D0D0D` (`COLOR_BG`) | `#0A0A0B` (`Colors.BG_PRIMARY`) |
| `#1A1A1A` (`COLOR_CARD`) | `#121214` (`Colors.BG_SECONDARY`) |
| `#9B4FB0` (`COLOR_PRIMARY`) | `#00897B` (`Colors.ACTION_PRIMARY`) |
| `#D4A84B` (`COLOR_SECONDARY`) | `#7CB342` (`Colors.ACTION_SECONDARY`) |
| `#F5F5F5` (`COLOR_TEXT`) | `#E8E8EC` (`Colors.TEXT_PRIMARY`) |

### Mapeo de API de Componentes

| Antes | Después |
|-------|---------|
| `crear_boton(..., estilo="primary")` | `crear_boton(..., variant="primary")` |
| `_crear_seccion(titulo, icono)` | `crear_seccion(parent, titulo, icono)` |

### Ejemplo de Migración

**Antes:**
```python
btn = ctk.CTkButton(
    parent,
    text="Procesar",
    fg_color="#9B4FB0",
    hover_color="#B565C6",
    font=("Segoe UI", 14, "bold")
)
```

**Después:**
```python
from gui.componentes import crear_boton

btn = crear_boton(parent, "Procesar", command=procesar, variant="primary")
```

---

## 🔧 Carga de Fuentes (PySide6)

Las fuentes Inter se registran automáticamente al iniciar la app mediante
`cargar_fuentes_personalizadas()` en `main.py`, usando `QFontDatabase.addApplicationFont()`.

No se requiere instalación del sistema — las fuentes son locales al proyecto.

---

## 🚨 Troubleshooting

### "ModuleNotFoundError: No module named 'gui.design_tokens'"

```bash
ls -la gui/design_tokens.py gui/__init__.py
# Si falta __init__.py:
touch gui/__init__.py
```

### "Inter no se aplica"

1. Verificar que `fonts/Inter/*.ttf` existan.
2. Confirmar que `cargar_fuentes_personalizadas()` se llama antes de crear ventanas.
3. Limpiar caché de Python:

```bash
find . -type d -name "__pycache__" -exec rm -r {} +
python main.py
```

### Colores no cambian

```bash
# Verificar tokens directamente:
python -c "from gui.design_tokens import Colors; print(Colors.ACTION_PRIMARY)"
# Debe imprimir: #00897B
```

---

## ✅ Tests de Verificación Rápida

```bash
# 1. Tokens accesibles
python -c "from gui.design_tokens import Colors, Typography, Spacing; print('OK')"

# 2. Componentes importan sin errores
python -c "from gui.componentes import crear_boton, crear_seccion; print('OK')"

# 3. Token ACTION_PRIMARY correcto
python -c "from gui.design_tokens import Colors; assert Colors.ACTION_PRIMARY == '#00897B', 'FAIL'; print('OK - #00897B')"
```

---

## 📦 Próximos Pasos

- [ ] Integrar Lucide Icons (reemplazar emojis en componentes)
- [ ] Migrar `ventana_admin.py`, `ventana_clientes.py`, `ventana_reportes.py` a tokens
- [ ] Implementar componentes avanzados (Tabs, Accordion)
- [ ] Crear suite de tests visuales automatizados
- [ ] Dark/Light mode toggle

---

## 🤝 Contribución

Al agregar nuevos componentes:

1. Usar **exclusivamente** tokens de `gui/design_tokens.py`
2. Documentar en este archivo con ejemplo de uso
3. Verificar contraste WCAG 2.1 AA (ratio ≥ 4.5:1 para texto normal)
4. No introducir colores `#HEX` hardcodeados fuera de `design_tokens.py`
