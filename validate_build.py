"""
validate_build.py — Valida que el ejecutable generado funcione correctamente.

Uso:
    python validate_build.py                     # Valida dist/MetodoBase[.exe]
    python validate_build.py --exe dist/MyApp    # Ruta explícita
    python validate_build.py --url-only          # Solo verifica endpoints (si ya corre)
"""
import argparse
import platform
import subprocess
import sys
import time
from pathlib import Path

# Importar requests opcionalmente (puede no estar en el venv de build)
try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

BASE_DIR = Path(__file__).parent


# ── Utilidades ────────────────────────────────────────────────────────────────

def _ok(msg: str) -> None:
    print(f"  ✅ {msg}")

def _fail(msg: str) -> None:
    print(f"  ❌ {msg}")

def _warn(msg: str) -> None:
    print(f"  ⚠️  {msg}")

def _sep(title: str = "") -> None:
    width = 54
    line = "─" * width
    if title:
        pad = (width - len(title) - 2) // 2
        print("─" * pad + f" {title} " + "─" * (width - pad - len(title) - 2))
    else:
        print(line)


# ── Fase 1: Verificar archivos del build ──────────────────────────────────────

def check_build_output(exe: Path) -> bool:
    _sep("Verificando archivos generados")

    if not exe.exists():
        _fail(f"Ejecutable no encontrado: {exe}")
        print()
        print("  Asegúrate de haber ejecutado:")
        print("    python build.py --clean")
        return False

    size_mb = exe.stat().st_size / 1_048_576

    if exe.is_dir():
        # Modo onedir: contar archivos internos
        files = list(exe.rglob("*"))
        _ok(f"Directorio ejecutable: {exe}  ({len(files)} archivos, {size_mb:.0f} MB)")
    else:
        _ok(f"Ejecutable: {exe}  ({size_mb:.1f} MB)")
        if size_mb < 5:
            _warn("Tamaño muy pequeño — posible build incompleto")
        elif size_mb > 500:
            _warn("Tamaño muy grande (>500 MB) — revisar excludes en build_config.py")
        else:
            _ok(f"Tamaño razonable ({size_mb:.1f} MB)")

    return True


# ── Fase 2: Iniciar ejecutable y verificar servidor ───────────────────────────

def test_server(exe: Path, port: int = 8000, timeout: int = 25) -> bool:
    _sep("Iniciando ejecutable y verificando servidor")

    if not HAS_REQUESTS:
        _warn("'requests' no instalado — salteando verificación HTTP")
        _warn("  pip install requests  para habilitar esta prueba")
        return True

    # Determinar ejecutable real (onedir tiene subcarpeta)
    if exe.is_dir():
        is_windows = platform.system() == "Windows"
        real_exe = exe / (exe.name + (".exe" if is_windows else ""))
    else:
        real_exe = exe

    if not real_exe.exists():
        _fail(f"Binario no encontrado: {real_exe}")
        return False

    print(f"  🚀 Iniciando {real_exe.name} ...")
    proc = subprocess.Popen(
        [str(real_exe), "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{port}"

    # Esperar a que el servidor levante
    started = False
    for i in range(timeout):
        time.sleep(1)
        try:
            r = _requests.get(base_url, timeout=2)
            if r.status_code < 500:
                started = True
                break
        except _requests.exceptions.ConnectionError:
            pass
        print(f"  ⏳ Esperando servidor... {i+1}/{timeout}s", end="\r")

    print()

    if not started:
        _fail(f"Servidor no respondió en {timeout}s en {base_url}")
        proc.terminate()
        proc.wait(timeout=5)
        stderr_output = proc.stderr.read(2000).decode(errors="replace")
        if stderr_output:
            print("  --- stderr ---")
            print(stderr_output[:1000])
        return False

    _ok(f"Servidor responde en {base_url}")

    # ── Pruebas de endpoints ─────────────────────────────────────────────────
    all_pass = True

    endpoints = [
        ("GET", "/",                  [200],        "Dashboard principal"),
        ("GET", "/api/stats",         [200, 404],   "API estadísticas"),
        ("GET", "/api/clientes",      [200, 404],   "API clientes"),
        ("GET", "/docs",              [200],        "Swagger UI"),
        ("GET", "/static/css/custom.css", [200, 404], "Archivos estáticos"),
    ]

    for method, path, ok_codes, label in endpoints:
        try:
            r = _requests.request(method, base_url + path, timeout=5)
            if r.status_code in ok_codes:
                _ok(f"{label:35s}  [{r.status_code}]")
            else:
                _fail(f"{label:35s}  [{r.status_code}]")
                all_pass = False
        except Exception as exc:
            _fail(f"{label:35s}  ERROR: {exc}")
            all_pass = False

    # Parar el proceso
    print()
    print("  🛑 Deteniendo servidor...")
    proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()

    return all_pass


# ── Fase 3: Resumen ───────────────────────────────────────────────────────────

def print_summary(exe: Path, success: bool) -> None:
    _sep("Resumen")
    if success:
        print()
        print("  🎉 VALIDACIÓN COMPLETADA EXITOSAMENTE")
        print()
        print("  Próximos pasos:")
        print("    1. Testea el ejecutable manualmente en una PC limpia")
        print("    2. En Windows: compila el instalador con Inno Setup:")
        print("       iscc setup_installer.iss")
        print(f"    3. Distribuye {exe.parent / 'MetodoBase_v2.0.zip'}")
    else:
        print()
        print("  ❌ LA VALIDACIÓN FALLÓ — revisa los errores arriba")
        print()
        print("  Sugerencias:")
        print("    • Rebuild con: python build.py --clean --no-tests")
        print("    • Para ver errores detallados: python build.py --no-console")
        print("    • Revisa logs en ~/.metodobase/logs/ (o %APPDATA%\\MetodoBase\\logs)")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Valida el ejecutable de MetodoBase")
    parser.add_argument("--exe",      default=None,  help="Ruta al ejecutable/directorio")
    parser.add_argument("--port",     type=int, default=8000, help="Puerto del servidor")
    parser.add_argument("--timeout",  type=int, default=25,   help="Segundos de espera")
    parser.add_argument("--url-only", action="store_true", help="Solo verificar endpoints (sin lanzar proceso)")
    args = parser.parse_args()

    is_windows = platform.system() == "Windows"
    ext = ".exe" if is_windows else ""

    if args.exe:
        exe = Path(args.exe)
    else:
        exe = BASE_DIR / "dist" / f"MetodoBase{ext}"
        # Fallback: directorio (onedir mode)
        if not exe.exists():
            exe_dir = BASE_DIR / "dist" / "MetodoBase"
            if exe_dir.is_dir():
                exe = exe_dir

    _sep("MetodoBase — Validación de Build")
    print(f"  Sistema: {platform.system()} {platform.machine()}")
    print(f"  Ejecutable: {exe}")
    print()

    success = True

    if not args.url_only:
        success = check_build_output(exe) and success
        if success:
            print()
            success = test_server(exe, port=args.port, timeout=args.timeout) and success
    else:
        if not HAS_REQUESTS:
            _fail("Instala requests: pip install requests")
            sys.exit(1)
        print(f"  Verificando {args.port} sin lanzar proceso...")
        base = f"http://127.0.0.1:{args.port}"
        for _, path, codes, label in [
            ("GET", "/", [200], "Dashboard"),
            ("GET", "/docs", [200], "Swagger"),
        ]:
            try:
                r = _requests.get(base + path, timeout=3)
                if r.status_code in codes:
                    _ok(f"{label}: {r.status_code}")
                else:
                    _fail(f"{label}: {r.status_code}")
                    success = False
            except Exception as e:
                _fail(f"{label}: {e}")
                success = False

    print_summary(exe, success)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
