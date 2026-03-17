"""
MetodoBase API Server — entry point.

Uso:
    python api_server.py [--port PORT] [--host HOST] [--no-browser]

No modifica main.py ni la GUI PySide6 existente.
"""
import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path

# ── PyInstaller frozen detection ──────────────────────────────────────────────
# En modo frozen (ejecutable), sys._MEIPASS apunta al directorio extraído.
# En desarrollo, usamos el directorio del script.
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _ROOT = Path(sys._MEIPASS)
else:
    _ROOT = Path(__file__).resolve().parent

# Raíz del proyecto en sys.path (necesario en modo desarrollo y frozen)
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main() -> None:
    parser = argparse.ArgumentParser(description="MetodoBase API Server")
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("API_PORT", 8000)),
        help="Puerto del servidor (default: 8000)",
    )
    parser.add_argument(
        "--host", default=os.getenv("API_HOST", "127.0.0.1"),
        help="Host del servidor (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="No abrir el navegador automáticamente",
    )
    parser.add_argument(
        "--reload", action="store_true",
        help="Activar hot-reload (solo desarrollo)",
    )
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"

    print(f"\n{'='*52}")
    print(f"  MetodoBase API Server v2.0")
    print(f"  Dashboard : {url}")
    print(f"  API Docs  : {url}/docs")
    print(f"  Host      : {args.host}:{args.port}")
    print(f"{'='*52}\n")
    print("  Presiona Ctrl+C para detener el servidor\n")

    if not args.no_browser:
        def _open() -> None:
            import time
            time.sleep(1.8)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    import uvicorn
    from api.app import create_app

    if args.reload:
        # Modo reload: uvicorn maneja el relaunch, pasa la factory como string
        uvicorn.run(
            "api.app:create_app",
            host=args.host,
            port=args.port,
            log_level="info",
            reload=True,
            factory=True,
        )
    else:
        uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
