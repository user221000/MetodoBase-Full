# 📖 MANUAL DE USUARIO - MÉTODO BASE

**Versión del Manual:** 1.0  
**Versión del Software:** 1.0.0  
**Última Actualización:** Marzo 2026

---

## TABLA DE CONTENIDOS

1. [Introducción](#introducción)
2. [Primeros Pasos](#primeros-pasos)
3. [Interfaz Principal](#interfaz-principal)
4. [Generar Plan Nutricional](#generar-plan-nutricional)
5. [Panel de Administración](#panel-de-administración)
6. [Reportes y Estadísticas](#reportes-y-estadísticas)
7. [Configuración Avanzada](#configuración-avanzada)
8. [Preguntas Frecuentes](#preguntas-frecuentes)
9. [Glosario](#glosario)

---

## INTRODUCCIÓN

### ¿Qué es Método Base?

Método Base es un software profesional diseñado para gimnasios que permite generar planes nutricionales personalizados basados en ciencia nutricional moderna.

### Beneficios Clave

#### Para el Gimnasio
- ✅ Generación rápida de planes (3-5 minutos)
- ✅ Costo fijo mensual (sin costos variables)
- ✅ Diferenciación competitiva
- ✅ Valor agregado para clientes

#### Para el Cliente
- ✅ Plan personalizado a sus necesidades
- ✅ Variedad en alimentos (rotación inteligente)
- ✅ Fácil de seguir (cantidades en gramos y equivalencias)
- ✅ PDF profesional con branding del gym

### Metodología Científica

Método Base utiliza:

1. **Fórmula Katch-McArdle** para metabolismo basal (TMB)
2. **Factores de actividad validados** para gasto energético
3. **Distribución de macros según objetivo**:
   - Déficit: -20% calorías, alta proteína
   - Superávit: +15% calorías, para ganar masa
   - Mantenimiento: 0% calorías, balance

---

## PRIMEROS PASOS

### Instalación

#### Requisitos Previos
- Windows 10/11 (64-bit)
- 4 GB RAM mínimo
- 500 MB espacio en disco

#### Pasos de Instalación

1. **Descargar Instalador**
```
MetodoBaseSetup_v1.0.0.exe
```

2. **Ejecutar Instalador**
   - Doble clic en el archivo
   - Aceptar permisos de administrador
   - Seguir asistente

3. **Elegir Ubicación**
   - Default: `C:\Program Files\Método Base\`
   - Personalizable según necesidad

4. **Completar Instalación**
   - Esperar barra de progreso
   - Click en "Finalizar"

### Primera Ejecución

Al abrir por primera vez:

1. **Verificación de Licencia**
   - Sistema busca archivo `licencia.lic`
   - Si no existe, muestra error

2. **Instalar Licencia**
   - Copiar `licencia.lic` (proporcionado por soporte)
   - Pegar en: `C:\Program Files\Método Base\`
   - Reiniciar aplicación

3. **Splash Screen**
   - Logo de Método Base
   - Carga de componentes
   - Duración: 2-3 segundos

4. **Ventana Principal**
   - Formulario de cliente
   - Listo para usar

---

## INTERFAZ PRINCIPAL

### Descripción General

La interfaz principal consta de:

```
┌─────────────────────────────────────────┐
│         MÉTODO BASE                     │
│    Fitness Gym Real del Valle           │
│       Powered by C. H.                 │
├─────────────────────────────────────────┤
│  👤 DATOS DEL CLIENTE                  │
│  [Nombre: ________________]            │
│  [Teléfono: ___]  [Edad: __]          │
├─────────────────────────────────────────┤
│  ⚖ MEDIDAS CORPORALES                 │
│  [Peso: ___] [Estatura: ___]          │
│  [Grasa: ___]                          │
├─────────────────────────────────────────┤
│  🏋 PERFIL DE ENTRENAMIENTO            │
│  [Actividad: ▼]  [Objetivo: ▼]        │
├─────────────────────────────────────────┤
│     [ GENERAR PLAN Y PDF ]             │
├─────────────────────────────────────────┤
│  REGISTRO DE OPERACIONES               │
│  [12:34:56] Sistema listo...           │
└─────────────────────────────────────────┘
```

### Secciones

#### 1. Header (Superior)
- **Nombre Corto:** "Método Base"
- **Nombre Gym:** Personalizable
- **Tagline:** "Powered by..."

#### 2. Datos del Cliente
- **Nombre:** Campo obligatorio
- **Teléfono:** Opcional (recomendado para WhatsApp)
- **Edad:** Campo obligatorio (10-100 años)

#### 3. Medidas Corporales
- **Peso:** kg (20-155 kg)
- **Estatura:** cm (100-230 cm)
- **Grasa:** % (5-60%)

#### 4. Perfil de Entrenamiento
- **Actividad:** Sedentaria / Ligera / Moderada / Intensa / Muy Intensa
- **Objetivo:** Déficit / Superávit / Mantenimiento

#### 5. Botones de Acción
- **GENERAR PLAN Y PDF:** Botón principal
- **Enviar por WhatsApp:** Envía plan al cliente
- **Abrir carpeta de PDF:** Explorador de archivos

#### 6. Registro de Operaciones
- Log en tiempo real
- Timestamps
- Estados (OK/ERROR)

---

## GENERAR PLAN NUTRICIONAL

### Proceso Paso a Paso

#### Paso 1: Completar Formulario

**Datos Obligatorios:**
1. Nombre completo
2. Edad
3. Peso (kg)
4. Estatura (cm)
5. % Grasa corporal
6. Nivel de actividad
7. Objetivo

**Datos Opcionales:**
- Teléfono (recomendado)

#### Paso 2: Validación en Tiempo Real

Mientras escribes, el sistema valida:

- ✅ **Verde + ✓:** Campo válido
- ❌ **Rojo + ✗:** Campo inválido (mensaje de error)
- ⚪ **Gris:** Campo opcional vacío

**Ejemplo:**
```
Nombre:   Juan Pérez          ✓
Teléfono: 5213312345678       ✓
Edad:     25                  ✓
Peso:     80.5                ✓
Estatura: 175                 ✓
Grasa:    18                  ✓
```

#### Paso 3: Botón "GENERAR PLAN Y PDF"

- **Deshabilitado:** Si hay errores de validación
- **Habilitado (morado):** Cuando formulario es válido

Al hacer click:

```
[  5%] Validando datos…
[ 20%] Calculando metabolismo…
[ 45%] Construyendo plan alimenticio…
[ 65%] Mostrando vista previa…
[ 80%] Generando PDF…
[100%] ✓ Plan generado y PDF listo
```

#### Paso 4: Vista Previa del Plan

**Ventana Modal Muestra:**

```
╔═══════════════════════════════════════════╗
║  Plan para Juan Pérez                     ║
║  Objetivo: DÉFICIT | Kcal: 2000           ║
╠═══════════════════════════════════════════╣
║  🌅 DESAYUNO — 500 kcal                  ║
║    • Huevo: 150g (3 huevos)              ║
║    • Avena: 80g                          ║
║    • Banana: 100g (1 plátano)            ║
║    P: 30g | C: 55g | G: 12g             ║
╠═══════════════════════════════════════════╣
║  ☀️ ALMUERZO — 450 kcal                  ║
║    • Pechuga de Pollo: 120g              ║
║    • Arroz Blanco: 80g                   ║
║    • Brócoli: 100g                       ║
║    P: 35g | C: 40g | G: 8g              ║
╠═══════════════════════════════════════════╣
║  ...más comidas...                        ║
╠═══════════════════════════════════════════╣
║  [📄 Generar PDF]    [✏️ Modificar]       ║
╚═══════════════════════════════════════════╝
```

**Opciones:**
- **📄 Generar PDF:** Continúa y crea el PDF
- **✏️ Modificar:** Vuelve al formulario sin generar

#### Paso 5: PDF Generado

Si confirmas:

1. **PDF se Genera**
   - Ubicación: `planes/[NOMBRE]_[FECHA]_[HORA].pdf`
   - Se abre automáticamente

2. **Toast Notification**
   ```
   ✓ PDF generado exitosamente
   ```

3. **Botones se Habilitan**
   - "Enviar por WhatsApp"
   - "Abrir carpeta de PDF"

4. **Log Actualizado**
   ```
   [12:45:23] PLAN GENERADO — Juan Pérez | DÉFICIT |
              Kcal obj: 2000 | Kcal real: 1985 | Desv: 0.75%
   [12:45:23] PDF: planes/JuanPerez_2026-03-09_12-45-23.pdf
   ```

### Contenido del PDF

El PDF generado incluye:

#### Portada
- Logo del gym
- Nombre del cliente
- Fecha de generación
- Objetivo y calorías

#### Resumen del Cliente
- Datos antropométricos
- TMB y GET
- Distribución de macros

#### Plan Diario
- 4 comidas (desayuno, almuerzo, comida, cena)
- Cada comida con:
  - Alimentos y cantidades en gramos
  - Equivalencias (ej: "150g = 3 huevos")
  - Macros por comida
  - Calorías por comida

#### Tips Nutricionales
- Hidratación
- Timing de comidas
- Suplementación básica

#### Footer
- Contacto del gym
- Redes sociales
- Mensaje de motivación

---

## PANEL DE ADMINISTRACIÓN

### Acceso

**Atajo:** `Ctrl + Shift + A`

Solo personal autorizado debe conocer este atajo.

### Pestaña 1: 🎨 Branding

#### Información del Gimnasio
- **Nombre del Gym:** Aparece en PDFs y ventana principal
- **Nombre Corto:** Aparece en título de ventana
- **Tagline:** Subtítulo (ej: "Powered by...")

#### Información de Contacto
- **Teléfono:** Aparece en PDF footer
- **Email:** Para soporte a clientes
- **Dirección:** Ubicación del gym
- **WhatsApp:** Número con código de país (52...)

#### Colores Corporativos
- **Color Primario:** Morado por default (#9B4FB0)
- **Color Secundario:** Dorado por default (#D4A84B)

**Formato:** Hexadecimal (`#RRGGBB`)

**Botón:** 💾 Guardar Configuración

**Nota:** Requiere reiniciar app para ver cambios.

### Pestaña 2: 🔐 Licencia

Muestra:

#### Estado Actual
```
✅ Licencia válida (340 días restantes)
```
o
```
❌ Licencia expirada hace 15 días
```

#### Información Detallada
- 🏋️ **Gimnasio:** Fitness Gym Real del Valle
- 📅 **Fecha de emisión:** 2026-03-09
- ⏰ **Fecha de expiración:** 2027-03-09
- 🔑 **ID de instalación:** abc123...(oculto)

#### Botones
- **🔄 Renovar Licencia:** Muestra contacto de soporte
- **📞 Contactar Soporte:** Info de contacto

### Pestaña 3: 💾 Base de Datos

#### Estadísticas del Gimnasio

Grid de 4 KPIs:
```
┌──────────┬──────────┬──────────┬──────────┐
│    👥    │    📈    │   🍽️    │    ⚡    │
│   125    │    12    │    48    │  2,050   │
│  Total   │  Nuevos  │  Planes  │   Prom   │
│ Clientes │  (30d)   │  (30d)   │   Kcal   │
└──────────┴──────────┴──────────┴──────────┘
```

#### Gestión de Backups

**Información:**
- Backups automáticos cada 7 días
- Ubicación: `registros/backups/`

**Botones:**
- **📦 Crear Backup:** Backup manual inmediato
- **🗑️ Limpiar Antiguos:** Elimina backups >90 días

### Pestaña 4: 🔍 Búsqueda

#### Barra de Búsqueda
```
[🔍 Nombre, teléfono o ID del cliente...]  [Buscar]
```

#### Resultados

Muestra tarjetas de clientes:
```
╔═══════════════════════════════════════╗
║  Juan Pérez               5 planes   ║
║  📱 5213312345678 | 👤 30 años       ║
║  🎯 Déficit                          ║
╚═══════════════════════════════════════╝
```

---

## REPORTES Y ESTADÍSTICAS

### Acceso

Panel Admin > Base de Datos > "📊 Ver Reportes Completos"

### Dashboard

#### KPIs Principales (8 métricas)

**Fila 1:**
- 👥 **Total Clientes:** Activos actualmente
- 🆕 **Clientes Nuevos:** En período seleccionado
- 🍽️ **Planes Generados:** En período
- ⚡ **Promedio Kcal:** De todos los planes

**Fila 2:**
- 📉 **Déficit:** Planes con déficit calórico
- 📈 **Superávit:** Planes para ganancia
- ➡️ **Mantenimiento:** Planes neutros
- 📊 **Tasa Crecimiento:** % nuevos vs total

### Gráficas

#### Gráfica 1: Distribución de Objetivos (Pie Chart)
```
       Déficit
         45%
   ┌─────────┐
   │    ○    │  Superávit 30%
   └─────────┘
   Mantenimiento 25%
```

#### Gráfica 2: Top 10 Clientes (Barras Horizontales)
```
Juan Pérez   ██████████████  14
María García ███████████     11
Pedro López  █████████        9
...
```

### Top Clientes

Listado con medallas:
```
🥇 Juan Pérez ........................... 14 planes
🥈 María García ......................... 11 planes
🥉 Pedro López .......................... 9 planes
 4. Ana Martínez ......................... 7 planes
 5. Carlos Ruiz .......................... 6 planes
```

### Selector de Período

Dropdown con opciones:
- Últimos 7 días
- Últimos 30 días **(default)**
- Últimos 90 días
- Último año
- Todo el tiempo

### Exportar

**Botón:** 📤 Exportar

**Formatos:**
1. **Excel (.xlsx)** - 3 hojas:
   - Resumen: KPIs principales
   - Top Clientes: Listado completo
   - Objetivos: Distribución

2. **CSV (.csv)** - Solo resumen

**Ubicación:** Elige al guardar

---

## CONFIGURACIÓN AVANZADA

### Archivos de Configuración

#### 1. `config/branding.json`
```json
{
  "nombre_gym": "Tu Gym",
  "colores": {
    "primario": "#9B4FB0",
    "secundario": "#D4A84B"
  },
  "contacto": {
    "telefono": "33 1234 5678",
    "email": "contacto@tugym.mx"
  }
}
```
**Editar:** Panel Admin > Branding

#### 2. `licencia.lic`
```json
{
  "nombre_gym": "Fitness Gym",
  "fecha_expiracion": "2027-03-09",
  "clave": "abc123..."
}
```
**NO EDITAR MANUALMENTE** - Corrupta licencia

#### 3. `registros/clientes.db`

Base de datos SQLite.

**Backups:**
```
registros/backups/clientes_YYYYMMDD_HHMMSS.db
```

**Restaurar:**
1. Cerrar aplicación
2. Renombrar `clientes.db` a `clientes_old.db`
3. Copiar backup y renombrar a `clientes.db`
4. Abrir aplicación

### Carpetas Importantes
```
C:\Program Files\Método Base\
├── MetodoBase.exe          # Ejecutable principal
├── licencia.lic            # Archivo de licencia
├── config/
│   └── branding.json       # Personalización
├── registros/
│   ├── clientes.db         # Base de datos
│   ├── metodo_base.log     # Logs del sistema
│   └── backups/            # Backups automáticos
├── planes/                 # PDFs generados
│   └── [CLIENTE]/
│       └── plan_*.pdf
└── assets/                 # Recursos (logo, fonts)
```

### Logs del Sistema

**Ubicación:** `registros/metodo_base.log`

**Formato:**
```
[2026-03-09 12:34:56] [INFO] Cliente creado: Juan Pérez
[2026-03-09 12:35:01] [INFO] Plan generado exitosamente
[2026-03-09 12:35:02] [ERROR] Error generando PDF: Permiso denegado
```

**Niveles:**
- **INFO:** Operaciones normales
- **WARNING:** Advertencias (no crítico)
- **ERROR:** Errores (operación falló)

**Rotación:** Automática al llegar a 10 MB (5 backups)

---

## PREGUNTAS FRECUENTES

### General

**P: ¿Cuántos planes puedo generar?**  
R: Ilimitados. La licencia no tiene restricciones de uso.

**P: ¿Funciona sin internet?**  
R: Sí, completamente offline excepto WhatsApp (requiere conexión).

**P: ¿Puedo usar en múltiples computadoras?**  
R: Una licencia = Una instalación. Contacta para licencias adicionales.

### Técnico

**P: ¿Cómo restauro un backup?**  
R: Ver sección "Configuración Avanzada > Archivos de Configuración"

**P: ¿Qué hago si el PDF no se genera?**  
R:
1. Verificar permisos de escritura
2. Revisar logs en `registros/metodo_base.log`
3. Contactar soporte con logs

**P: ¿Puedo cambiar el logo del gym?**  
R: Sí, reemplaza `assets/logo_gym.png` con tu logo (formato PNG, 512x512px recomendado)

### Licenciamiento

**P: ¿Qué pasa cuando expira la licencia?**  
R: La aplicación deja de funcionar. Todos los datos se preservan. Renovando vuelve a funcionar.

**P: ¿Cómo renuevo mi licencia?**  
R: Contacta soporte 30 días antes. Te enviaremos nuevo archivo `licencia.lic`.

**P: ¿Puedo transferir mi licencia a otra computadora?**  
R: No directamente. Contacta soporte para transferencia.

---

## GLOSARIO

**TMB (Tasa Metabólica Basal):**  
Calorías que tu cuerpo quema en reposo absoluto.

**GET (Gasto Energético Total):**  
TMB × Factor de actividad = Calorías totales diarias.

**Macros (Macronutrientes):**  
Proteínas, carbohidratos y grasas.

**Déficit Calórico:**  
Comer menos calorías de las que gastas (para perder peso).

**Superávit Calórico:**  
Comer más calorías de las que gastas (para ganar peso/músculo).

**Rotación Inteligente:**  
Sistema que varía alimentos en cada plan para evitar monotonía.

**Katch-McArdle:**  
Fórmula científica para calcular TMB basada en masa magra.

**Backup:**  
Copia de seguridad de la base de datos.

**Licencia:**  
Archivo que autoriza el uso del software por 1 año.

---

## APÉNDICE A: ATAJOS DE TECLADO

| Atajo | Acción |
|-------|--------|
| Ctrl + Shift + A | Abrir Panel Admin |
| Esc | Cerrar ventanas modales |

---

## APÉNDICE B: CÓDIGOS DE ERROR

| Código | Descripción | Solución |
|--------|------------|----------|
| E001 | Licencia inválida | Verificar archivo licencia.lic |
| E002 | Base de datos corrupta | Restaurar desde backup |
| E003 | Error generando PDF | Verificar permisos |
| E004 | Sin espacio en disco | Liberar espacio |
| E005 | Archivo no encontrado | Reinstalar aplicación |

---

© 2026 Consultoría Hernández  
Manual de Usuario v1.0

**Soporte:**  
📱 +52 1 7441614117  
📧 Oscar_Autumn@outlook.com
