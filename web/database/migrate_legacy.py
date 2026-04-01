"""
web/database/migrate_legacy.py — Migra datos de SQLite legacy a SA multi-tenant.

Ejecutar una sola vez:
    python -m web.database.migrate_legacy [--gym-id UUID]

Sin --gym-id, asigna todos los clientes al primer gym user encontrado.
"""
import argparse
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

from web.database.engine import init_db, get_engine
from web.database.models import Base, Cliente, PlanGenerado, Usuario
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _parse_dt(val):
    """Parse a datetime string from legacy SQLite, or return None."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(val, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _find_legacy_db(name: str) -> Path:
    from web.constants import CARPETA_REGISTROS
    p = Path(CARPETA_REGISTROS) / name
    if p.exists():
        return p
    raise FileNotFoundError(f"Legacy DB not found: {p}")


def _find_gym_id(engine) -> str:
    """Busca el primer usuario tipo gym en web_usuarios.db legacy."""
    try:
        db_path = _find_legacy_db("web_usuarios.db")
    except FileNotFoundError:
        raise SystemExit("No web_usuarios.db found. Create a gym user first via /registro.")
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id FROM web_usuarios WHERE tipo='gym' ORDER BY rowid LIMIT 1"
        ).fetchone()
        if not row:
            raise SystemExit("No gym user found in web_usuarios.db")
        return row["id"]


def migrate(gym_id: str) -> dict:
    init_db()
    engine = get_engine()

    legacy_path = _find_legacy_db("clientes.db")
    legacy = sqlite3.connect(str(legacy_path))
    legacy.row_factory = sqlite3.Row

    stats = {"usuarios_migrated": 0, "usuarios_skipped": 0,
             "clientes_migrated": 0, "clientes_skipped": 0,
             "planes_migrated": 0, "planes_skipped": 0}

    with Session(engine) as session:
        with session.no_autoflush:
            # Migrate usuarios first (FK target for clientes.gym_id)
            try:
                users_path = _find_legacy_db("web_usuarios.db")
                users_conn = sqlite3.connect(str(users_path))
                users_conn.row_factory = sqlite3.Row
                user_rows = users_conn.execute("SELECT * FROM web_usuarios").fetchall()
                for ur in user_rows:
                    existing = session.query(Usuario).filter(
                        Usuario.id == ur["id"]
                    ).first()
                    if existing:
                        stats["usuarios_skipped"] += 1
                        continue
                    u = Usuario(
                        id=ur["id"],
                        email=ur["email"],
                        password_hash=ur["password_hash"],
                        nombre=ur["nombre"],
                        apellido=ur["apellido"] or "",
                        tipo=ur["tipo"],
                        activo=bool(ur["activo"]) if ur["activo"] is not None else True,
                        fecha_registro=_parse_dt(ur["fecha_registro"]),
                    )
                    session.add(u)
                    stats["usuarios_migrated"] += 1
                session.flush()
                users_conn.close()
            except FileNotFoundError:
                pass  # No users DB — will fail on FK if gym_id doesn't exist

            # Migrate clientes
            rows = legacy.execute("SELECT * FROM clientes").fetchall()
            for row in rows:
                existing = session.query(Cliente).filter(
                    Cliente.id_cliente == row["id_cliente"]
                ).first()
                if existing:
                    stats["clientes_skipped"] += 1
                    continue

                c = Cliente(
                    id_cliente=row["id_cliente"],
                    gym_id=gym_id,
                    nombre=row["nombre"] or "Sin nombre",
                    telefono=row["telefono"],
                    email=row["email"],
                    edad=row["edad"],
                    sexo=row["sexo"],
                    peso_kg=row["peso_kg"],
                    estatura_cm=row["estatura_cm"],
                    grasa_corporal_pct=row["grasa_corporal_pct"],
                    masa_magra_kg=row["masa_magra_kg"],
                    nivel_actividad=row["nivel_actividad"],
                    objetivo=row["objetivo"],
                    fecha_registro=_parse_dt(row["fecha_registro"]),
                    ultimo_plan=_parse_dt(row["ultimo_plan"]),
                    total_planes_generados=row["total_planes_generados"] or 0,
                    activo=bool(row["activo"]) if row["activo"] is not None else True,
                    notas=row["notas"],
                    plantilla_tipo=row["plantilla_tipo"] or "general",
                )
                session.add(c)
                stats["clientes_migrated"] += 1

            session.flush()

            # Migrate planes
            plan_rows = legacy.execute("SELECT * FROM planes_generados").fetchall()
            for pr in plan_rows:
                # Check if plan already migrated (by id_cliente + fecha)
                fecha_parsed = _parse_dt(pr["fecha_generacion"])
                existing = session.query(PlanGenerado).filter(
                    PlanGenerado.id_cliente == pr["id_cliente"],
                    PlanGenerado.fecha_generacion == fecha_parsed,
                ).first()
                if existing:
                    stats["planes_skipped"] += 1
                    continue

                p = PlanGenerado(
                    id_cliente=pr["id_cliente"],
                    gym_id=gym_id,
                    fecha_generacion=fecha_parsed,
                    tmb=pr["tmb"],
                    get_total=pr["get_total"],
                    kcal_objetivo=pr["kcal_objetivo"],
                    kcal_real=pr["kcal_real"],
                    proteina_g=pr["proteina_g"],
                    carbs_g=pr["carbs_g"],
                    grasa_g=pr["grasa_g"],
                    objetivo=pr["objetivo"],
                    nivel_actividad=pr["nivel_actividad"],
                    ruta_pdf=pr["ruta_pdf"],
                    peso_en_momento=pr["peso_en_momento"],
                    grasa_en_momento=pr["grasa_en_momento"],
                    desviacion_maxima_pct=pr["desviacion_maxima_pct"],
                    plantilla_tipo=pr["plantilla_tipo"] or "general",
                    tipo_plan=pr["tipo_plan"] or "menu_fijo",
                )
                session.add(p)
                stats["planes_migrated"] += 1

            session.commit()

    legacy.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Migrate legacy SQLite → SA multi-tenant")
    parser.add_argument("--gym-id", help="UUID del gym owner. Auto-detect if omitted.")
    args = parser.parse_args()

    init_db()
    gym_id = args.gym_id or _find_gym_id(get_engine())
    logger.info("Migrating legacy data → gym_id: %s", gym_id)

    stats = migrate(gym_id)
    logger.info("Migration complete:")
    logger.info("   Usuarios migrated:  %d", stats['usuarios_migrated'])
    logger.info("   Usuarios skipped:   %d", stats['usuarios_skipped'])
    logger.info("   Clientes migrated:  %d", stats['clientes_migrated'])
    logger.info("   Clientes skipped:   %d", stats['clientes_skipped'])
    logger.info("   Planes migrated:    %d", stats['planes_migrated'])
    logger.info("   Planes skipped:     %d", stats['planes_skipped'])


if __name__ == "__main__":
    main()
