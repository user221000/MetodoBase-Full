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
VERSION = "1.0.0"

# Datos a incluir (archivos y carpetas)
DATAS = [
    (str(BASE_DIR / "assets"), "assets"),
    (str(BASE_DIR / "fonts"), "fonts"),
    (str(BASE_DIR / "config"), "config"),
]

# Paquetes ocultos (que PyInstaller no detecta automáticamente)
HIDDEN_IMPORTS = [
    "customtkinter",
    "PIL._tkinter_finder",
    "reportlab",
    "reportlab.pdfbase",
    "reportlab.pdfbase.ttfonts",
    "reportlab.lib",
    "reportlab.lib.pagesizes",
    "reportlab.platypus",
    "pandas",
    "openpyxl",
    "xlsxwriter",
    "matplotlib",
    "matplotlib.backends.backend_tkagg",
    "numpy",
    "dotenv",
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
