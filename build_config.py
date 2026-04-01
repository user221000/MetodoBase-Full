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
from config.constantes import VERSION
APP_NAME       = "MetodoBase"
APP_VERSION    = VERSION
APP_AUTHOR     = "MetodoBase"  # Generic vendor name
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
    (str(BASE_DIR / "utils"),         "utils"),
    (str(BASE_DIR / "ui_desktop"),    "ui_desktop"),
    (str(BASE_DIR / "design_system"), "design_system"),
]

# ── Hidden imports requeridos por el build desktop ────────────────────────────
HIDDEN_IMPORTS = [
    # PySide6 (GUI desktop)
    "PySide6.QtWidgets",
    "PySide6.QtCore",
    "PySide6.QtGui",
    # App internals
    "core.branding",
    "core.licencia",
    "ui_desktop.pyside.theme_manager",
    "ui_desktop.pyside.flow_controller",
    "ui_desktop.pyside.gym_app_window",
    # Auth
    "passlib.handlers.bcrypt",
    "passlib.handlers.pbkdf2",
    # Crypto
    "cryptography.hazmat.backends.openssl",
    "cryptography.hazmat.primitives.ciphers.algorithms",
    # ReportLab (a veces no se detecta automáticamente)
    "reportlab.graphics.barcode.code128",
    "reportlab.graphics.barcode.code39",
    # SQLite
    "sqlite3",
]

# ── Módulos a excluir (reducen tamaño del ejecutable) ─────────────────────────
EXCLUDES = [
    "tkinter",          # UI antigua — no se usa
    "customtkinter",    # Legacy — no se usa
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
    "entry_point":    "main.py",
}

# ── Configuración de runtime ──────────────────────────────────────────────────
RUNTIME_CONFIG = {
    "host":      "127.0.0.1",
    "port":      8000,
    "log_level": "info",
    "reload":    False,
}

# ── Ofuscación de core/licencia.py con PyArmor (pre-PyInstaller) ──────────────
#
# Pasos para ofuscar antes del build (idempotente):
#
#   1. pip install pyarmor
#   2. pyarmor gen --output dist_obf core/licencia.py
#   3. cp dist_obf/licencia.py core/licencia.py   (reemplazar fuente)
#   4. Ejecutar PyInstaller normalmente (build.py o MetodoBase.spec)
#
# Script idempotente (ejecutar desde la raíz del proyecto):
#
#   import shutil, subprocess, sys
#   from pathlib import Path
#   ORIG = Path("core/licencia.py")
#   BACKUP = Path("core/licencia.py.orig")
#   OBFDIR = Path("dist_obf")
#   if not BACKUP.exists():
#       shutil.copy2(ORIG, BACKUP)
#   subprocess.check_call([sys.executable, "-m", "pyarmor", "gen",
#                          "--output", str(OBFDIR), str(ORIG)])
#   shutil.copy2(OBFDIR / "licencia.py", ORIG)
#   print("✅ core/licencia.py ofuscado — backup en core/licencia.py.orig")
#
# Para restaurar: cp core/licencia.py.orig core/licencia.py
OFUSCAR_LICENCIA = False  # Cambiar a True para activar en CI
