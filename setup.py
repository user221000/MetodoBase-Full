"""
Script de empaquetado para distribución a gimnasios.

Crea ejecutable standalone con PyInstaller:
- Todas las dependencias incluidas
- Assets empaquetados
- Icono personalizado
- Carpeta dist/ con todos los archivos

Uso:
    python setup.py build
"""

import sys
from pathlib import Path

try:
    import PyInstaller.__main__
except ImportError:
    print("ERROR: PyInstaller no instalado.")
    print("Ejecuta: pip install pyinstaller")
    sys.exit(1)

# Obtener directorio actual
BASE_DIR = Path(__file__).parent

# Configuración
APP_NAME = "MetodoBase"
MAIN_SCRIPT = "main.py"
ICON_FILE = "assets/icon.ico"
try:
    from config.constantes import VERSION
except ImportError:
    VERSION = "2.0.0"

# Datos a incluir (archivos y carpetas)
DATAS = [
    (str(BASE_DIR / "assets"), "assets"),
    (str(BASE_DIR / "fonts"), "fonts"),
    (str(BASE_DIR / "config"), "config"),
    (str(BASE_DIR / "src"), "src"),
    (str(BASE_DIR / "core"), "core"),
    (str(BASE_DIR / "utils"), "utils"),
    (str(BASE_DIR / "ui_desktop"), "ui_desktop"),
    (str(BASE_DIR / "design_system"), "design_system"),
]

# Paquetes ocultos (que PyInstaller no detecta automáticamente)
HIDDEN_IMPORTS = [
    "PySide6.QtWidgets",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "core.branding",
    "core.licencia",
    "ui_desktop.pyside.theme_manager",
    "ui_desktop.pyside.flow_controller",
    "ui_desktop.pyside.gym_app_window",
    "passlib.handlers.bcrypt",
    "passlib.handlers.pbkdf2",
    "cryptography.hazmat.backends.openssl",
    "cryptography.hazmat.primitives.ciphers.algorithms",
    "reportlab",
    "reportlab.pdfbase",
    "reportlab.pdfbase.ttfonts",
    "reportlab.lib",
    "reportlab.lib.pagesizes",
    "reportlab.platypus",
    "reportlab.graphics.barcode.code128",
    "reportlab.graphics.barcode.code39",
    "sqlite3",
]

# Construir argumentos para PyInstaller
pyinstaller_args = [
    str(BASE_DIR / MAIN_SCRIPT),
    "--name", APP_NAME,
    "--windowed",
    "--clean",
    "--noconfirm",
]

# Icono (solo si existe)
icon_path = BASE_DIR / ICON_FILE
if icon_path.exists():
    pyinstaller_args.extend(["--icon", str(icon_path)])

# Agregar datos
for src, dst in DATAS:
    if Path(src).exists():
        pyinstaller_args.extend(["--add-data", f"{src};{dst}"])

# Agregar imports ocultos
for imp in HIDDEN_IMPORTS:
    pyinstaller_args.extend(["--hidden-import", imp])

# Excluir módulos legacy
for exc in ["tkinter", "customtkinter"]:
    pyinstaller_args.extend(["--exclude-module", exc])

if __name__ == "__main__":
    print("=" * 60)
    print(f"EMPAQUETANDO {APP_NAME} v{VERSION}")
    print("=" * 60)
    print()

    PyInstaller.__main__.run(pyinstaller_args)

    print()
    print("=" * 60)
    print("✅ EMPAQUETADO COMPLETADO")
    print("=" * 60)
    print()
    print(f"📁 Ejecutable generado en: dist/{APP_NAME}/")
    print()
    print("📋 Próximos pasos:")
    print(f"1. Prueba el ejecutable: dist\\{APP_NAME}\\{APP_NAME}.exe")
    print("2. Crea el instalador con Inno Setup (ver setup_installer.iss)")
    print("3. Distribuye el instalador a los gimnasios")
    print()
