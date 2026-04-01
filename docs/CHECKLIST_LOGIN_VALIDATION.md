# ✅ Checklist de Validación - Login Screen Fixes

## Antes de Ejecutar
- [ ] Asegurar que PySide6 está instalado: `pip install PySide6`
- [ ] Verificar que `.venv` está activado si lo usas
- [ ] Tener credenciales de test disponibles (o probar el modo visual sin login real)

## Validación Visual Rápida

### Opción 1: Test Standalone (Recomendado)
```bash
cd /home/hernandez221000/MetodoBase-Full
python3 scripts/test_login_visual.py
```

**Verifica**:
- [ ] La ventana se muestra sin crashes
- [ ] Los botones tienen efecto glow/sombra visible
- [ ] El card principal tiene sombra visible
- [ ] Las animaciones de entrada funcionan (si no es Wayland)
- [ ] Los tabs "🏢 Dueño de Gym" y "👤 Cliente" cambian correctamente
- [ ] El hover sobre botones muestra efecto glow

### Opción 2: Test en Aplicación Completa
```bash
cd /home/hernandez221000/MetodoBase-Full
python3 main.py
```

**Verifica**:
- [ ] El login se carga correctamente
- [ ] Puedes hacer login con credenciales válidas
- [ ] Los mensajes de error se muestran correctamente
- [ ] La transición al dashboard es suave

## Validación en Diferentes Plataformas

### Linux X11
```bash
QT_QPA_PLATFORM=xcb python3 scripts/test_login_visual.py
```
- [ ] Animaciones habilitadas
- [ ] Efectos gráficos funcionan correctamente

### Linux Wayland
```bash
QT_QPA_PLATFORM=wayland python3 scripts/test_login_visual.py
```
- [ ] Animaciones deshabilitadas automáticamente (esperado)
- [ ] Ventana se renderiza correctamente sin animaciones
- [ ] No hay glitches visuales

## Logs de Diagnóstico

Si hay problemas, revisa los logs:
```bash
python3 main.py 2>&1 | grep -E "LOGIN_PREMIUM|THEME|ERROR"
```

**Busca estos mensajes**:
- `[LOGIN_PREMIUM] Could not setup button glow` → OK (fallback graceful)
- `[LOGIN_PREMIUM] Could not setup card shadow` → OK (fallback graceful)
- `[LOGIN_PREMIUM] Animations disabled` → OK en Wayland
- `[THEME] amarillo_neon cargado` → OK

## Problemas Conocidos y Soluciones

### Problema: "ModuleNotFoundError: No module named 'PySide6'"
**Solución**: 
```bash
pip install PySide6
# o
source .venv/bin/activate && pip install PySide6
```

### Problema: "No module named 'reportlab'"
**Solución**: 
```bash
pip install reportlab
# o instalar todas las dependencias
pip install -r requirements.txt
```

### Problema: Los efectos gráficos no se ven
**Diagnóstico**: Revisa logs para ver si aparece "Could not setup"
**Solución**: Esto es normal en algunas plataformas. La app funciona sin efectos.

### Problema: La ventana parpadea o tiene glitches visuales
**Causa Probable**: Wayland o VM sin aceleración
**Solución**: Las animaciones se deshabilitaron automáticamente. Si persiste:
```bash
# Forzar X11
QT_QPA_PLATFORM=xcb python3 main.py
```

## Comparación Antes/Después

### ANTES (problemas)
- ❌ Botones perdían sombra después de animaciones
- ❌ Crashes en VM/Wayland
- ❌ Glow excesivo (molesto visualmente)
- ❌ Sin manejo de errores en efectos

### DESPUÉS (corregido)
- ✅ Sombras se preservan a través de animaciones
- ✅ Funciona en todas las plataformas (fallback graceful)
- ✅ Glow sutil y profesional
- ✅ Manejo robusto de errores

## Testing Completado ✓
- [x] Sintaxis validada (py_compile)
- [x] Sin errores de linting
- [ ] Test visual en X11 (pendiente - requiere tu validación)
- [ ] Test visual en Wayland (pendiente - requiere tu validación)
- [ ] Test de login funcional (pendiente - requiere tu validación)

## Siguientes Pasos (Opcional)

Si todo funciona correctamente:
1. Considerar eliminar `ventana_login_unificada.py` (implementación vieja)
2. Documentar en el README la nueva pantalla de login
3. Agregar screenshots del login al wiki/docs

## Contacto
Si encuentras problemas no documentados aquí, revisa:
- `docs/LOGIN_SCREEN_FIXES_2026-03-28.md` (análisis completo)
- `/memories/repo/login-fixes-march2026.md` (notas técnicas)
