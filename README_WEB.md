# 🌐 MetodoBase Web — Guía de Ejecución

Aplicación web moderna para gestión nutricional de gyms. Corre en `http://localhost:8000` y **no afecta** la app desktop PySide6 existente.

## 📋 Requisitos

- Python 3.10+
- Las dependencias de `requirements.txt`

## 🚀 Instalación y Ejecución

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Iniciar el servidor web

Desde el directorio raíz del proyecto:

```bash
python -m web.main_web
```

O con uvicorn directamente:

```bash
uvicorn web.main_web:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Abrir en el navegador

- **Dashboard:** http://localhost:8000
- **Clientes:** http://localhost:8000/clientes
- **Generar Plan:** http://localhost:8000/generar-plan
- **API Docs:** http://localhost:8000/docs

## 🏗️ Estructura

```
web/
├── main_web.py              # FastAPI entry point (puerto 8000)
├── test_api.py              # Tests de la API con pytest
├── api/
│   ├── __init__.py
│   ├── routes.py            # Endpoints REST
│   ├── schemas.py           # Modelos Pydantic
│   └── dependencies.py      # Inyección de BD
├── static/
│   ├── css/styles.css       # Estilos personalizados
│   ├── js/
│   │   ├── main.js          # JavaScript principal
│   │   ├── api.js           # Cliente API REST
│   │   └── components.js    # Toasts y utilidades
│   └── assets/logo.png
└── templates/
    ├── base.html            # Layout base con Tailwind CSS
    ├── dashboard.html       # Dashboard con KPIs
    ├── clientes.html        # Gestión de clientes
    └── generar-plan.html    # Formulario 3 pasos
```

## 🔌 Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/estadisticas` | KPIs del dashboard |
| `GET` | `/api/clientes` | Listar clientes (búsqueda + paginación) |
| `GET` | `/api/clientes/{id}` | Detalle de cliente |
| `POST` | `/api/clientes` | Crear cliente |
| `PUT` | `/api/clientes/{id}` | Actualizar cliente |
| `POST` | `/api/generar-plan` | Generar plan nutricional + PDF |
| `GET` | `/api/planes/{id}` | Historial de planes de un cliente |
| `GET` | `/api/descargar-pdf/{nombre}` | Descargar PDF de un plan |
| `GET` | `/health` | Health check |

## 🧪 Ejecutar Tests

```bash
pytest web/test_api.py -v
```

## 🎨 Diseño

- **Framework CSS:** Tailwind CSS (CDN)
- **Color primario:** `#FF6B35` (Naranja energético)
- **Color secundario:** `#004E89` (Azul gimnasio)
- **JavaScript:** Vanilla JS (sin frameworks)
- **Responsivo:** Desktop-first, compatible mobile

## 📊 Base de Datos

Usa el mismo SQLite que la app desktop (en `APP_DATA_DIR/registros/clientes.db`). No modifica ni duplica la estructura existente.

## ⚠️ Notas

- **No modifica** `core/`, `src/`, `gui/` (excepto un bug fix de SQL en `src/gestor_bd.py`)
- Comparte la misma base de datos que la app desktop
- CORS habilitado para desarrollo local (`allow_origins=["*"]`)
- **Para producción:** restringir `allow_origins` a dominio específico
