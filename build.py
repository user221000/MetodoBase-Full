"""
build.py — Script automatizado de empaquetado para MetodoBase.

Uso:
    python build.py                  # Testea y crea ejecutable
    python build.py --clean          # Limpia builds previos primero
    python build.py --no-tests       # Salta tests (no recomendado)
    python build.py --clean --test   # Limpia, construye y prueba el exe
    python build.py --zip            # Crea .zip de distribución final

El script asume que el entorno virtual está activo.
"""
import argparse
import logging
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent


# ── Utilidades ────────────────────────────────────────────────────────────────

def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    logger.info("$ %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=False)
    if check and result.returncode != 0:
        logger.error("Comando falló (código %d)", result.returncode)
        sys.exit(result.returncode)
    return result


def _separator(title: str = "") -> None:
    width = 60
    if title:
        pad = (width - len(title) - 2) // 2
        logger.info("─" * pad + f" {title} " + "─" * pad)
    else:
        logger.info("─" * width)


# ── Paso 1: Limpiar ──────────────────────────────────────────────────────────

def clean_build_dirs() -> None:
    _separator("Limpiando builds anteriores")
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for d in dirs_to_clean:
        p = BASE_DIR / d
        if p.exists():
            logger.info("Eliminando %s/", d)
            shutil.rmtree(p)

    for spec in BASE_DIR.glob("*.spec"):
        logger.info("Eliminando %s", spec.name)
        spec.unlink()

    logger.info("✅ Limpieza completada")


# ── Paso 2: Verificar dependencias ──────────────────────────────────────────

def check_dependencies() -> None:
    _separator("Verificando dependencias")
    try:
        import PyInstaller  # noqa: F401
        logger.info("✅ PyInstaller disponible")
    except ImportError:
        logger.error("PyInstaller no está instalado. Ejecuta:")
        logger.error("  pip install pyinstaller>=6.0.0")
        sys.exit(1)

    try:
        import fastapi, uvicorn, reportlab  # noqa: F401
        logger.info("✅ FastAPI, Uvicorn y ReportLab disponibles")
    except ImportError as e:
        logger.error("Dependencia faltante: %s", e)
        logger.error("Instala con: pip install -r requirements.txt -r requirements_api.txt")
        sys.exit(1)


# ── Paso 3: Ejecutar tests ────────────────────────────────────────────────────

def run_tests() -> None:
    _separator("Ejecutando tests")
    result = _run(
        [sys.executable, "-m", "pytest", "tests/test_api.py", "-v", "--tb=short"],
        check=False,
    )
    if result.returncode != 0:
        logger.error("❌ Tests fallaron. Abortando build.")
        logger.error("Para forzar el build sin tests: python build.py --no-tests")
        sys.exit(1)
    logger.info("✅ Tests pasaron")


# ── Paso 4: Crear ejecutable ─────────────────────────────────────────────────

def build_executable() -> Path:
    _separator("Generando ejecutable con PyInstaller")
    from build_config import PYINSTALLER_CONFIG

    is_windows = platform.system() == "Windows"
    sep = ";" if is_windows else ":"

    cmd = [sys.executable, "-m", "PyInstaller"]
    cmd += ["--name", PYINSTALLER_CONFIG["name"]]

    if PYINSTALLER_CONFIG.get("onefile"):
        cmd.append("--onefile")

    if PYINSTALLER_CONFIG.get("windowed"):
        cmd.append("--windowed")

    icon_path = PYINSTALLER_CONFIG.get("icon", "")
    if icon_path and Path(icon_path).exists():
        cmd += ["--icon", icon_path]
    else:
        logger.warning("Icono no encontrado en %s — se usará icono por defecto", icon_path)

    for src, dest in PYINSTALLER_CONFIG.get("add_data", []):
        if Path(src).exists():
            cmd += ["--add-data", f"{src}{sep}{dest}"]
        else:
            logger.warning("add_data origen no existe: %s", src)

    for imp in PYINSTALLER_CONFIG.get("hidden_imports", []):
        cmd += ["--hidden-import", imp]

    for exc in PYINSTALLER_CONFIG.get("excludes", []):
        cmd += ["--exclude-module", exc]

    # No preguntar confirmaciones
    cmd.append("--noconfirm")

    cmd.append(PYINSTALLER_CONFIG["entry_point"])

    _run(cmd)

    ext = ".exe" if is_windows else ""
    exe = BASE_DIR / "dist" / f"{PYINSTALLER_CONFIG['name']}{ext}"
    if not exe.exists():
        logger.error("Ejecutable no encontrado en %s", exe)
        sys.exit(1)

    size_mb = exe.stat().st_size / 1_048_576
    logger.info("✅ Ejecutable creado: %s (%.1f MB)", exe, size_mb)
    return exe


# ── Paso 5: Probar ejecutable ─────────────────────────────────────────────────

def test_executable(exe: Path) -> None:
    _separator("Probando ejecutable")
    if not exe.exists():
        logger.error("No se encontró el ejecutable: %s", exe)
        return

    # Prueba básica: iniciar con --help o con timeout corto
    result = subprocess.run(
        [str(exe), "--help"],
        capture_output=True,
        timeout=15,
    )
    if result.returncode == 0:
        logger.info("✅ Ejecutable responde a --help")
    else:
        logger.warning(
            "⚠️  El ejecutable no responde a --help (puede ser normal si no implementa ese flag)"
        )
        logger.info("Salida: %s", result.stdout.decode(errors="replace")[:200])


# ── Paso 6: Crear paquete de distribución ────────────────────────────────────

def create_distribution_zip(exe: Path) -> Path:
    _separator("Creando paquete de distribución")
    from build_config import APP_NAME, APP_VERSION

    dist_dir = BASE_DIR / "dist"
    zip_name = f"{APP_NAME}_v{APP_VERSION}.zip"
    zip_path = dist_dir / zip_name

    folder = f"{APP_NAME}_v{APP_VERSION}/"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # En modo onedir, exe es el directorio dist/MetodoBase/
        # En modo onefile, exe es el binario dist/MetodoBase[.exe]
        if exe.is_dir():
            # Incluir todo el contenido del directorio (binario + _internal)
            for file in exe.rglob("*"):
                if file.is_file():
                    arcname = folder + str(file.relative_to(exe.parent))
                    zf.write(file, arcname)
            logger.info("  + %s/ (%d archivos)", exe.name,
                        sum(1 for f in exe.rglob("*") if f.is_file()))
        else:
            zf.write(exe, folder + exe.name)
            logger.info("  + %s", exe.name)

        # Archivos de documentación y configuración
        extras = [
            (BASE_DIR / ".env.example",           "config.env.example"),
            (BASE_DIR / "README_DISTRIBUCION.md",  "LEEME.md"),
            (BASE_DIR / "LICENSE",                 "Licencia.txt"),
            (BASE_DIR / "metodobase_iniciar.bat",  "metodobase_iniciar.bat"),
        ]
        for src, name in extras:
            if Path(src).exists():
                zf.write(src, folder + name)
                logger.info("  + %s", name)
            else:
                logger.warning("  - %s (no encontrado, omitido)", name)

    size_mb = zip_path.stat().st_size / 1_048_576
    logger.info("✅ Paquete creado: %s (%.1f MB)", zip_path.name, size_mb)
    return zip_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Build script para MetodoBase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--clean",    action="store_true", help="Limpia builds anteriores")
    parser.add_argument("--no-tests", action="store_true", help="Omite los tests pre-build")
    parser.add_argument("--test",     action="store_true", help="Prueba el ejecutable al final")
    parser.add_argument("--zip",      action="store_true", help="Genera .zip de distribución")
    args = parser.parse_args()

    _separator("MetodoBase — Build Script")
    logger.info("Sistema: %s | Python: %s", platform.system(), sys.version.split()[0])

    if args.clean:
        clean_build_dirs()

    check_dependencies()

    if not args.no_tests:
        run_tests()
    else:
        logger.warning("⚠️  Tests omitidos (--no-tests)")

    exe = build_executable()

    if args.test:
        test_executable(exe)

    if args.zip:
        create_distribution_zip(exe)

    _separator("Completado")
    logger.info("✅ Ejecutable listo: %s", exe)
    logger.info("")
    logger.info("Próximos pasos:")
    logger.info("  1. Prueba el ejecutable manualmente en una PC limpia")
    logger.info("  2. Crea un instalador con Inno Setup usando setup_installer.iss")
    logger.info("  3. Distribuye la carpeta dist/ o el .zip generado")


if __name__ == "__main__":
    main()
