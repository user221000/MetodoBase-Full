#!/usr/bin/env python3
"""
scripts/rollback_migration.py — Rollback de migración de BD.

FASE 9 del plan de consolidación.

Permite revertir la migración en cualquier fase:
- Fase 1→0: Desactivar shadow writes
- Fase 2→1: Desactivar dual-write, volver a legacy-only
- Fase 3→2: SA primary → legacy primary 
- Fase 4→3: Reactivar legacy writes

Uso:
    # Ver estado actual
    python scripts/rollback_migration.py --status
    
    # Rollback a fase anterior
    python scripts/rollback_migration.py --to-phase 2
    
    # Rollback completo a legacy
    python scripts/rollback_migration.py --full-rollback
    
    # Backup antes de rollback
    python scripts/rollback_migration.py --backup --to-phase 2
"""
import argparse
import json
import logging
import os
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)


# ── Rollback Plan ───────────────────────────────────────────────────────────

@dataclass
class RollbackStep:
    """Paso individual de rollback."""
    description: str
    action: str
    reversible: bool = True


ROLLBACK_PLANS = {
    # Rollback desde fase 2 a fase 1
    (2, 1): [
        RollbackStep(
            description="Desactivar dual-write",
            action="set_flag:dual_write_enabled=false",
        ),
        RollbackStep(
            description="Verificar que legacy sigue funcionando",
            action="verify:legacy_operational",
        ),
    ],
    # Rollback desde fase 3 a fase 2
    (3, 2): [
        RollbackStep(
            description="Cambiar lectura primaria a legacy",
            action="set_flag:use_sa_for_read=false",
        ),
        RollbackStep(
            description="Cambiar escritura primaria a legacy",
            action="set_flag:sa_is_primary=false",
        ),
        RollbackStep(
            description="Verificar paridad de datos",
            action="verify:data_parity",
        ),
    ],
    # Rollback desde fase 4 a fase 3
    (4, 3): [
        RollbackStep(
            description="Reactivar legacy",
            action="set_flag:legacy_deprecated=false",
        ),
        RollbackStep(
            description="Activar shadow write a legacy",
            action="set_flag:shadow_write_legacy=true",
        ),
    ],
}


# ── Rollback Manager ────────────────────────────────────────────────────────

class RollbackManager:
    """Gestiona operaciones de rollback."""
    
    def __init__(self, backup_dir: str = ".rollback_backups"):
        self._backup_dir = Path(backup_dir)
        self._backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_current_phase(self) -> int:
        """Obtiene fase actual de migración."""
        try:
            from config.feature_flags import get_migration_flags
            return get_migration_flags().current_phase()
        except:
            return 1  # Default a legacy
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado actual del sistema."""
        try:
            from config.feature_flags import get_migration_flags
            flags = get_migration_flags()
            
            return {
                "current_phase": flags.current_phase(),
                "flags": {
                    "use_sa_for_read": flags.use_sa_for_read,
                    "dual_write_enabled": flags.dual_write_enabled,
                    "sa_is_primary": flags.sa_is_primary,
                    "legacy_deprecated": flags.legacy_deprecated,
                    "shadow_write_legacy": flags.shadow_write_legacy,
                },
                "can_rollback_to": self._get_rollback_options(),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_rollback_options(self) -> list:
        """Obtiene fases a las que se puede hacer rollback."""
        current = self.get_current_phase()
        options = []
        for phase in range(current - 1, 0, -1):
            options.append(phase)
        return options
    
    def backup_databases(self) -> Dict[str, str]:
        """Crea backup de todas las BDs."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backups = {}
        
        # Legacy DB
        legacy_path = Path("clientes.db")
        if legacy_path.exists():
            backup_path = self._backup_dir / f"clientes_{timestamp}.db"
            shutil.copy2(legacy_path, backup_path)
            backups["legacy"] = str(backup_path)
            logger.info("Backup legacy: %s", backup_path)
        
        # SA DB (SQLite)
        from config.constantes import CARPETA_REGISTROS
        sa_path = Path(CARPETA_REGISTROS) / "metodobase_web.db"
        if sa_path.exists():
            backup_path = self._backup_dir / f"metodobase_web_{timestamp}.db"
            shutil.copy2(sa_path, backup_path)
            backups["sqlalchemy"] = str(backup_path)
            logger.info("Backup SA: %s", backup_path)
        
        # Guardar metadata
        meta_path = self._backup_dir / f"backup_meta_{timestamp}.json"
        with open(meta_path, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "phase": self.get_current_phase(),
                "backups": backups,
            }, f, indent=2)
        
        return backups
    
    def restore_from_backup(self, timestamp: str) -> bool:
        """Restaura BDs desde un backup."""
        meta_path = self._backup_dir / f"backup_meta_{timestamp}.json"
        
        if not meta_path.exists():
            logger.error("Backup metadata no encontrado: %s", meta_path)
            return False
        
        with open(meta_path) as f:
            meta = json.load(f)
        
        for db_type, backup_path in meta.get("backups", {}).items():
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error("Backup file no encontrado: %s", backup_file)
                continue
            
            if db_type == "legacy":
                target = Path("clientes.db")
            else:
                from config.constantes import CARPETA_REGISTROS
                target = Path(CARPETA_REGISTROS) / "metodobase_web.db"
            
            shutil.copy2(backup_file, target)
            logger.info("Restaurado %s → %s", backup_file, target)
        
        return True
    
    def list_backups(self) -> list:
        """Lista backups disponibles."""
        backups = []
        for meta_file in self._backup_dir.glob("backup_meta_*.json"):
            with open(meta_file) as f:
                meta = json.load(f)
                backups.append({
                    "timestamp": meta["timestamp"],
                    "phase": meta["phase"],
                    "files": list(meta.get("backups", {}).keys()),
                })
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
    
    def rollback_to_phase(self, target_phase: int, dry_run: bool = True) -> Dict[str, Any]:
        """
        Ejecuta rollback a una fase específica.
        
        Args:
            target_phase: Fase destino (1-3)
            dry_run: Si True, solo muestra pasos sin ejecutar
        
        Returns:
            Resultado del rollback
        """
        current_phase = self.get_current_phase()
        
        if target_phase >= current_phase:
            return {
                "success": False,
                "error": f"No se puede hacer rollback de fase {current_phase} a {target_phase}",
            }
        
        result = {
            "from_phase": current_phase,
            "to_phase": target_phase,
            "dry_run": dry_run,
            "steps": [],
        }
        
        # Ejecutar rollback fase por fase
        for from_phase in range(current_phase, target_phase, -1):
            to_phase = from_phase - 1
            steps = ROLLBACK_PLANS.get((from_phase, to_phase), [])
            
            for step in steps:
                step_result = {
                    "description": step.description,
                    "action": step.action,
                    "executed": False,
                    "success": False,
                }
                
                if not dry_run:
                    try:
                        self._execute_step(step)
                        step_result["executed"] = True
                        step_result["success"] = True
                    except Exception as e:
                        step_result["error"] = str(e)
                        logger.error("Rollback step failed: %s", e)
                        result["steps"].append(step_result)
                        result["success"] = False
                        return result
                
                result["steps"].append(step_result)
        
        result["success"] = True
        return result
    
    def _execute_step(self, step: RollbackStep):
        """Ejecuta un paso de rollback."""
        action = step.action
        
        if action.startswith("set_flag:"):
            # Parsear y establecer flag
            flag_spec = action.split(":", 1)[1]
            flag_name, value_str = flag_spec.split("=")
            value = value_str.lower() == "true"
            
            from config.feature_flags import get_migration_flags
            flags = get_migration_flags()
            setattr(flags, flag_name, value)
            logger.info("Flag %s = %s", flag_name, value)
            
        elif action.startswith("verify:"):
            # Ejecutar verificación
            verify_type = action.split(":", 1)[1]
            self._run_verification(verify_type)
    
    def _run_verification(self, verify_type: str):
        """Ejecuta una verificación."""
        if verify_type == "legacy_operational":
            # Verificar que legacy funciona
            conn = sqlite3.connect("clientes.db")
            count = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
            conn.close()
            logger.info("Legacy operational: %d clientes", count)
            
        elif verify_type == "data_parity":
            # Verificar paridad
            from scripts.validate_migration import MigrationValidator
            validator = MigrationValidator()
            result = validator.validate_data_parity(sample_size=50)
            if not result.passed:
                raise Exception(f"Parity check failed: {result.errors}")
            logger.info("Data parity verified")
    
    def full_rollback(self, dry_run: bool = True) -> Dict[str, Any]:
        """Rollback completo a fase 1 (legacy only)."""
        current = self.get_current_phase()
        
        if current == 1:
            return {"success": True, "message": "Ya está en fase 1"}
        
        # Backup primero
        if not dry_run:
            self.backup_databases()
        
        return self.rollback_to_phase(1, dry_run=dry_run)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Rollback de migración de BD"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Mostrar estado actual"
    )
    parser.add_argument(
        "--to-phase",
        type=int,
        help="Fase destino del rollback (1-3)"
    )
    parser.add_argument(
        "--full-rollback",
        action="store_true",
        help="Rollback completo a fase 1 (legacy)"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Crear backup antes de rollback"
    )
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="Listar backups disponibles"
    )
    parser.add_argument(
        "--restore",
        help="Restaurar desde backup (timestamp)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo mostrar pasos sin ejecutar"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Ejecutar rollback (requerido para cambios reales)"
    )
    
    args = parser.parse_args()
    
    manager = RollbackManager()
    
    if args.status:
        status = manager.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.list_backups:
        backups = manager.list_backups()
        print("Backups disponibles:")
        for b in backups:
            print(f"  {b['timestamp']} - Fase {b['phase']} - {b['files']}")
        return
    
    if args.restore:
        if not args.execute:
            print("Usa --execute para restaurar realmente")
            return
        success = manager.restore_from_backup(args.restore)
        print("Restauración:", "OK" if success else "FAILED")
        return
    
    if args.backup:
        backups = manager.backup_databases()
        print("Backups creados:", backups)
    
    dry_run = not args.execute
    
    if args.full_rollback:
        result = manager.full_rollback(dry_run=dry_run)
        print(json.dumps(result, indent=2))
        
    elif args.to_phase:
        result = manager.rollback_to_phase(args.to_phase, dry_run=dry_run)
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
