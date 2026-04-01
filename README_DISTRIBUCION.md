# 📦 Distribución de Método Base v2.0

## Contenido del paquete

```
MetodoBase_v2.0/
├── MetodoBase.exe          ← Ejecutable principal (doble clic para iniciar)
├── LEEME.md                ← Este archivo
├── config.env.example      ← Plantilla de configuración (renombrar a .env)
└── Licencia.txt            ← Términos de uso
```

---

## Requisitos del sistema

| Requisito         | Mínimo          | Recomendado     |
|-------------------|-----------------|-----------------|
| Sistema operativo | Windows 10 x64  | Windows 11 x64  |
| RAM               | 4 GB            | 8 GB            |
| Espacio en disco  | 300 MB libres   | 1 GB libres     |
| Procesador        | Intel i3 / Ryzen 3 | Intel i5 / Ryzen 5 |
| Navegador         | Chrome 90+ / Edge 90+ | Chrome actualizado |

> **Linux:** También funciona en Ubuntu 22.04+ ejecutando `./MetodoBase` desde terminal.

---

## Instalación para usuarios finales (Windows)

### Paso 1 — Descomprimir

1. Haz clic derecho en `MetodoBase_v2.0.zip`
2. Selecciona **"Extraer todo..."**
3. Elige la carpeta de destino, por ejemplo:  
   `C:\Program Files\MetodoBase\`

### Paso 2 — Primer uso

1. Abre la carpeta `MetodoBase_v2.0/`
2. Doble clic en **`MetodoBase.exe`**
3. Si aparece el aviso de Windows Defender → [ver sección Solución de problemas](#firewall)
4. Se abrirá una ventana de consola y **automáticamente** se abrirá el navegador en  
   `http://localhost:8000`

### Paso 3 — Configuración inicial (opcional)

Si quieres personalizar el nombre del gym, logo o colores:
1. Copia `config.env.example` → `.env` en la misma carpeta que el ejecutable
2. Edita `.env` con tu editor de texto (Bloc de notas, Notepad++, etc.)
3. Reinicia la aplicación

---

## Uso diario

```
1. Ejecutar MetodoBase.exe
2. El navegador se abre automáticamente
3. Al terminar de trabajar → cerrar la ventana de consola (o Ctrl+C)
```

> Los datos se guardan en `C:\Users\TU_USUARIO\.metodobase\` y **no se borran** al actualizar.

---

## Actualización

1. Descarga la nueva versión
2. Reemplaza `MetodoBase.exe` con el nuevo archivo
3. Tus datos y configuración se mantienen intactos

---

## Solución de problemas{#firewall}

### "Windows protegió tu PC"

Aparece porque la app no tiene certificado de Microsoft ($300+/año).  
Es normal en software de distribución directa.

**Solución:**
1. Click en **"Más información"** (texto azul)
2. Click en **"Ejecutar de todas formas"**

Solo necesitas hacerlo una vez por versión.

---

### "El puerto 8000 ya está en uso"

Otro programa usa el mismo puerto.

**Opciones:**
- Cierra y vuelve a abrir `MetodoBase.exe`
- O edita `.env` y cambia `PORT=8000` por `PORT=8080`

---

### La ventana se cierra inmediatamente

Ejecuta desde consola para ver el error:
1. Abre **PowerShell** (Win+X → Windows PowerShell)
2. Navega a la carpeta: `cd "C:\Program Files\MetodoBase"`
3. Ejecuta: `.\MetodoBase.exe`
4. Copia el mensaje de error y compártelo con soporte

---

### El navegador no se abre solo

Abre manualmente: **[http://localhost:8000](http://localhost:8000)**

---

### "Error de base de datos"

Verifica que tienes permisos de escritura en tu perfil:
- Ejecuta `MetodoBase.exe` como Administrador (clic derecho → Ejecutar como administrador)
- Si persiste, contacta soporte

---

## Datos y privacidad

- Todos los datos se guardan **localmente** en tu PC
- Directorio de datos: `C:\Users\TU_USUARIO\.metodobase\`
- No se envía información a ningún servidor externo
- Los PDFs se guardan en `C:\Users\TU_USUARIO\.metodobase\planes\`

---

## Desinstalación

1. Elimina la carpeta de instalación (`C:\Program Files\MetodoBase\`)
2. **Opcional:** Elimina también los datos del usuario:  
   `C:\Users\TU_USUARIO\.metodobase\`  
   ⚠️ Esto borra todos los clientes, planes y PDFs guardados

---

## Soporte

| Canal           | Contacto                                                    |
|-----------------|-------------------------------------------------------------|
| Email           | soporte@metodobase.mx                                       |
| WhatsApp        | [+52 744 161 4117](https://wa.me/5217441614117)             |
| Horario soporte | Lunes a Viernes, 9:00 – 18:00 (hora Ciudad de México)       |

---

## Para el instalador (Desarrolladores)

Para crear un instalador `.exe` con Inno Setup:

```bash
# Desde el repositorio, con Inno Setup instalado:
iscc setup_installer.iss
```

El resultado se genera en `Output/setup_metodobase.exe`.

---

## Notas de versión — v2.0.0

- ✅ Nueva interfaz web moderna (Tailwind CSS + FastAPI)
- ✅ Dashboard con KPIs en tiempo real
- ✅ Wizard de registro de cliente en 3 pasos
- ✅ Generación de planes nutricionales con Katch-McArdle
- ✅ PDFs profesionales con branding del gym
- ✅ Rotación inteligente de alimentos
- ✅ Compatible con Windows 10/11 y Ubuntu 22.04+
- 🔧 Interfaz PySide6 legacy disponible en `main.py` (modo avanzado)

---

## Firma de código

### Windows — Certificado EV con signtool.exe

```powershell
# Requisitos: certificado EV en token USB (SafeNet) + Windows SDK
# 1. Firmar el ejecutable principal
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 ^
  /a "dist\MetodoBase\MetodoBase.exe"

# 2. Firmar el instalador generado por Inno Setup
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 ^
  /a "Output\MetodoBaseSetup_v2.0.0.exe"

# 3. Verificar firma
signtool verify /pa "dist\MetodoBase\MetodoBase.exe"
```

### macOS — Notarización con Apple

```bash
# Requisitos: Xcode CLI tools, Developer ID Application certificate
# 1. Firmar el .app bundle
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: CONSULTORIA HERNANDEZ" \
  dist/MetodoBase.app

# 2. Crear .dmg
create-dmg \
  --volname "Método Base" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "MetodoBase.app" 150 190 \
  --app-drop-link 450 185 \
  "Output/MetodoBase_v2.0.0.dmg" \
  "dist/MetodoBase.app"

# 3. Notarizar
xcrun notarytool submit Output/MetodoBase_v2.0.0.dmg \
  --apple-id "developer@consultoriahernandez.mx" \
  --team-id "XXXXXXXXXX" \
  --password "@keychain:AC_PASSWORD" \
  --wait

# 4. Grapar el ticket
xcrun stapler staple Output/MetodoBase_v2.0.0.dmg
```

---

*Método Base v2.0.0 — Generado el 16/03/2026 — Consultoría Hernández*
