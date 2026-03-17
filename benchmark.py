"""
benchmark.py — Medición de performance de MetodoBase API.

Requiere que el servidor esté corriendo en localhost:8000.
Uso:
    # En terminal 1:
    python api_server.py

    # En terminal 2:
    python benchmark.py
    python benchmark.py --host 127.0.0.1 --port 8000 --n 5
    python benchmark.py --plan   # incluye benchmark de generación de plan (lento)

Métricas reportadas:
    - Tiempo promedio, desviación estándar, mínimo, máximo
    - Percentil 95 (P95)
    - Requests por segundo (RPS)
"""
from __future__ import annotations

import argparse
import statistics
import time
from typing import Callable

try:
    import requests
except ImportError:
    print("requests no instalado. Ejecuta: pip install requests")
    raise

# ── Configuración ─────────────────────────────────────────────────────────────

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
TIMEOUT = 30  # segundos

# ── Colores ANSI (opcionales, funcionan en Linux/Mac) ────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def _color_tiempo(t: float) -> str:
    """Coloriza el tiempo según umbrales de performance."""
    if t < 0.5:
        return f"{GREEN}{t:.3f}s{RESET}"
    elif t < 2.0:
        return f"{YELLOW}{t:.3f}s{RESET}"
    else:
        return f"{RED}{t:.3f}s{RESET}"


# ── Motor de benchmark ────────────────────────────────────────────────────────

def _bench(
    label: str,
    fn: Callable[[], requests.Response],
    n: int = 10,
    expect_status: int = 200,
) -> dict:
    """
    Ejecuta `fn` n veces y mide el tiempo de respuesta.

    Returns:
        dict con métricas: avg, std, min, max, p95, rps, errors
    """
    times: list[float] = []
    errors = 0

    for i in range(n):
        t0 = time.perf_counter()
        try:
            resp = fn()
            elapsed = time.perf_counter() - t0
            if resp.status_code == expect_status:
                times.append(elapsed)
            else:
                errors += 1
                print(f"  [{label}] Iter {i+1}: HTTP {resp.status_code}")
        except requests.exceptions.ConnectionError:
            errors += 1
            print(f"  [{label}] Iter {i+1}: ConnectionError — ¿está corriendo el servidor?")
        except Exception as exc:
            errors += 1
            print(f"  [{label}] Iter {i+1}: Error — {exc}")

    if not times:
        return {
            "label": label, "n": n, "errors": errors,
            "avg": 0, "std": 0, "min": 0, "max": 0, "p95": 0, "rps": 0,
        }

    avg = statistics.mean(times)
    std = statistics.stdev(times) if len(times) > 1 else 0
    p95 = sorted(times)[int(len(times) * 0.95)]
    rps = 1.0 / avg if avg > 0 else 0

    return {
        "label": label,
        "n": n,
        "errors": errors,
        "avg": avg,
        "std": std,
        "min": min(times),
        "max": max(times),
        "p95": p95,
        "rps": rps,
    }


def _print_result(r: dict) -> None:
    """Imprime una fila de resultado formateada."""
    status = f"{RED}[{r['errors']} errores]{RESET}" if r["errors"] else f"{GREEN}OK{RESET}"
    print(
        f"  {BOLD}{r['label']:<40}{RESET}"
        f"  avg={_color_tiempo(r['avg'])}"
        f"  p95={_color_tiempo(r['p95'])}"
        f"  min={r['min']:.3f}s"
        f"  max={r['max']:.3f}s"
        f"  rps={CYAN}{r['rps']:.1f}{RESET}"
        f"  {status}"
    )


def _separator(title: str = "") -> None:
    width = 70
    if title:
        pad = max(0, (width - len(title) - 2) // 2)
        print(f"\n{'─'*pad} {BOLD}{title}{RESET} {'─'*pad}")
    else:
        print("─" * width)


# ── Benchmarks específicos ────────────────────────────────────────────────────

def bench_dashboard(base_url: str, n: int) -> dict:
    return _bench("GET /", lambda: requests.get(f"{base_url}/", timeout=TIMEOUT), n)


def bench_estadisticas(base_url: str, n: int) -> dict:
    return _bench(
        "GET /api/estadisticas",
        lambda: requests.get(f"{base_url}/api/estadisticas", timeout=TIMEOUT),
        n,
    )


def bench_listar_clientes(base_url: str, n: int) -> dict:
    return _bench(
        "GET /api/clientes",
        lambda: requests.get(f"{base_url}/api/clientes", timeout=TIMEOUT),
        n,
    )


def bench_buscar_clientes(base_url: str, n: int) -> dict:
    return _bench(
        "GET /api/clientes?q=test",
        lambda: requests.get(f"{base_url}/api/clientes?q=test", timeout=TIMEOUT),
        n,
    )


def bench_crear_cliente(base_url: str, n: int) -> list[str]:
    """Crea n clientes y mide el tiempo. Devuelve los IDs creados para limpieza posterior."""
    ids: list[str] = []
    payload = {
        "nombre": "Benchmark User",
        "edad": 30,
        "peso_kg": 75.0,
        "estatura_cm": 172.0,
        "grasa_corporal_pct": 18.0,
        "nivel_actividad": "moderada",
        "objetivo": "mantenimiento",
    }

    times: list[float] = []
    for i in range(n):
        p = {**payload, "nombre": f"Benchmark User {i:03d}"}
        t0 = time.perf_counter()
        resp = requests.post(f"{base_url}/api/clientes", json=p, timeout=TIMEOUT)
        times.append(time.perf_counter() - t0)
        if resp.status_code == 201:
            ids.append(resp.json().get("id_cliente", ""))

    avg = statistics.mean(times)
    std = statistics.stdev(times) if len(times) > 1 else 0
    p95 = sorted(times)[int(len(times) * 0.95)]
    r = {
        "label": "POST /api/clientes",
        "n": n, "errors": n - len(ids),
        "avg": avg, "std": std, "min": min(times), "max": max(times),
        "p95": p95, "rps": 1.0 / avg if avg else 0,
    }
    _print_result(r)
    return ids


def bench_generar_plan(base_url: str, n: int = 3) -> None:
    """Crea un cliente, genera n planes, reporta tiempos."""
    payload_c = {
        "nombre": "Benchmark Plan",
        "edad": 28,
        "peso_kg": 78.0,
        "estatura_cm": 174.0,
        "grasa_corporal_pct": 20.0,
        "nivel_actividad": "moderada",
        "objetivo": "deficit",
    }
    resp_c = requests.post(f"{base_url}/api/clientes", json=payload_c, timeout=15)
    if resp_c.status_code != 201:
        print(f"  {RED}No se pudo crear cliente para benchmark de plan{RESET}")
        return

    id_c = resp_c.json()["id_cliente"]
    times: list[float] = []
    pdfs: list[str] = []

    for i in range(1, n + 1):
        t0 = time.perf_counter()
        resp_p = requests.post(
            f"{base_url}/api/generar-plan",
            json={"id_cliente": id_c, "plan_numero": i},
            timeout=60,
        )
        elapsed = time.perf_counter() - t0
        if resp_p.status_code == 200:
            times.append(elapsed)
            pdfs.append(resp_p.json().get("ruta_pdf", ""))
            print(f"  Plan {i}/{n}: {_color_tiempo(elapsed)} — PDF: {len(resp_p.content)} bytes")
        else:
            print(f"  Plan {i}/{n}: {RED}Error HTTP {resp_p.status_code}{RESET}")

    if times:
        avg = statistics.mean(times)
        std = statistics.stdev(times) if len(times) > 1 else 0
        print(f"\n  {BOLD}Resumen generación de plan:{RESET}")
        print(f"    Promedio : {_color_tiempo(avg)}")
        print(f"    Std Dev  : {std:.3f}s")
        print(f"    Min      : {min(times):.3f}s")
        print(f"    Max      : {max(times):.3f}s")
        target = 5.0
        status = f"{GREEN}✅ < {target}s{RESET}" if avg < target else f"{RED}❌ > {target}s{RESET}"
        print(f"    Target   : {target}s → {status}")

    # Cleanup
    from pathlib import Path
    requests.delete(f"{base_url}/api/clientes/{id_c}", timeout=TIMEOUT)
    for ruta in pdfs:
        p = Path(ruta)
        if p.exists():
            p.unlink(missing_ok=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark de MetodoBase API")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host del servidor")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Puerto")
    parser.add_argument("--n", type=int, default=10, help="Repeticiones por endpoint")
    parser.add_argument("--plan", action="store_true", help="Incluye benchmark de plan (lento)")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    n = args.n

    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"  {BOLD}MetodoBase API — Benchmark de Performance{RESET}")
    print(f"  Servidor : {CYAN}{base_url}{RESET}")
    print(f"  Muestras : {n} por endpoint")
    print(f"{'='*70}{RESET}")

    # Verificar que el servidor responde
    try:
        requests.get(f"{base_url}/api/estadisticas", timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"\n{RED}❌ No se puede conectar a {base_url}{RESET}")
        print("  Inicia el servidor con: python api_server.py")
        return

    _separator("Endpoints de solo lectura")
    results = []
    results.append(bench_dashboard(base_url, n))
    results.append(bench_estadisticas(base_url, n))
    results.append(bench_listar_clientes(base_url, n))
    results.append(bench_buscar_clientes(base_url, n))

    for r in results:
        _print_result(r)

    _separator("Creación de clientes")
    ids_creados = bench_crear_cliente(base_url, n)

    if args.plan:
        _separator(f"Generación de plan nutricional (n=3)")
        bench_generar_plan(base_url, n=3)

    # Limpiar clientes de benchmark
    for id_c in ids_creados:
        if id_c:
            requests.delete(f"{base_url}/api/clientes/{id_c}", timeout=TIMEOUT)

    _separator("Resumen de targets")
    targets = [
        ("Dashboard (GET /)", 2.0),
        ("Estadísticas (GET /api/estadisticas)", 1.0),
        ("Listar clientes", 1.0),
        ("Crear cliente", 1.0),
    ]
    for r, (label, target) in zip(results, targets):
        status = f"{GREEN}✅{RESET}" if r["avg"] < target else f"{RED}❌{RESET}"
        print(f"  {status} {label:<45} avg={r['avg']:.3f}s (target <{target}s)")

    print(f"\n{BOLD}{'='*70}{RESET}\n")


if __name__ == "__main__":
    main()
