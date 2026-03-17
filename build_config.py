"""
build_config.py — Configuración de empaquetado para MetodoBase.

Importado por build.py y referenciado en el .spec de PyInstaller.
"""
from pathlib import Path

# ── Directorios base ──────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
SRC_DIR        = BASE_DIR / "src"
CORE_DIR       = BASE_DIR / "core"
STATIC_DIR     = BASE_DIR / "static"
ASSETS_DIR     = BASE_DIR / "assets"
FONTS_DIR      = BASE_DIR / "fonts"
CONFIG_DIR     = BASE_DIR / "config"

# ── Metadatos de la aplicación ────────────────────────────────────────────────
APP_NAME       = "MetodoBase"
APP_VERSION    = "2.0.0"
APP_AUTHOR     = "Consultoría Hernández"
APP_ICON       = str(ASSETS_DIR / "logo.ico")   # .ico para Windows

# ── Datos a empaquetar dentro del ejecutable ──────────────────────────────────
# Formato: (origen, destino_dentro_del_paquete)
# En Windows PyInstaller usa ';' como separador, en Linux/Mac usa ':'
ADD_DATA = [
    (str(STATIC_DIR),          "static"),
    (str(ASSETS_DIR),          "assets"),
    (str(FONTS_DIR),           "fonts"),
    (str(CONFIG_DIR),          "config"),
    (str(BASE_DIR / "api"),    "api"),
    (str(BASE_DIR / "src"),    "src"),
    (str(BASE_DIR / "core"),   "core"),
    (str(BASE_DIR / "utils"),  "utils"),
]

# ── Hidden imports requeridos por uvicorn / FastAPI / legacy ──────────────────
HIDDEN_IMPORTS = [
    # Uvicorn internals (necesarios en onefile)
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    # Auth
    "passlib.handlers.bcrypt",
    "passlib.handlers.pbkdf2",
    # Crypto
    "cryptography.hazmat.backends.openssl",
    "cryptography.hazmat.primitives.ciphers.algorithms",
    # ReportLab (a veces no se detecta automáticamente)
    "reportlab.graphics.barcode.code128",
    "reportlab.graphics.barcode.code39",
    # Pillow
    "PIL._tkinter_finder",
    # SQLite
    "sqlite3",
]

# ── Módulos a excluir (reducen tamaño del ejecutable) ─────────────────────────
EXCLUDES = [
    "tkinter",          # UI antigua — reemplazada por FastAPI/web
    "matplotlib",       # Solo usado en GUI PySide6, no en API server
    "pandas",           # Solo en exportador_multi.py (import lazy, no ruta API)
    "openpyxl",         # Ídem
    "numpy",
    "PySide6",          # GUI desktop — no incluir en bundle web
    "test",
    "unittest",
    "doctest",
    "pydoc",
    "xmlrpc",
]

# ── Configuración de PyInstaller ──────────────────────────────────────────────
PYINSTALLER_CONFIG = {
    "name":           APP_NAME,
    "icon":           APP_ICON,

    # onefile=False → directorio dist/MetodoBase/ (compatible con Inno Setup)
    # Usa --onefile sólo para distribución ZIP sin instalador
    "onefile":        False,
    "windowed":       True,     # Sin consola visible en producción (--noconsole)
    "add_data":       ADD_DATA,
    "hidden_imports": HIDDEN_IMPORTS,
    "excludes":       EXCLUDES,
    "entry_point":    "api_server.py",
}

# ── Configuración de runtime ──────────────────────────────────────────────────
RUNTIME_CONFIG = {
    "host":      "127.0.0.1",
    "port":      8000,
    "log_level": "info",
    "reload":    False,
}
