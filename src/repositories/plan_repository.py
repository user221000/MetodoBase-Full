"""
src/repositories/plan_repository.py — Repository para planes generados.

Mismo patrón Strangler Fig que ClienteRepository.
"""
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.feature_flags import get_migration_flags, DBMigrationFlags
from .base import (
    BaseRepository,
    PlanDTO,
    EntityNotFoundError,
    SyncResult,
    get_sync_tracker,
)

logger = logging.getLogger(__name__)


class PlanRepository(BaseRepository[PlanDTO, int]):
    """
    Repository para planes generados con soporte dual-BD.
    """
    
    def __init__(
        self,
        legacy_db_path: str = "clientes.db",
        flags: Optional[DBMigrationFlags] = None,
    ):
        self._legacy_db_path = legacy_db_path
        self._flags = flags or get_migration_flags()
        self._tracker = get_sync_tracker()
        self._sa_session = None
    
    @property
    def _sa(self):
        """Lazy load SQLAlchemy session."""
        if self._sa_session is None:
            try:
                from web.database.engine import _SessionLocal, init_db
                if _SessionLocal is None:
                    init_db()
                from web.database.engine import _SessionLocal
                self._sa_session = _SessionLocal()
            except ImportError:
                logger.warning("SQLAlchemy no disponible")
                return None
        return self._sa_session
    
    # ── CRUD Principal ──────────────────────────────────────────────────────
    
    def get_by_id(self, entity_id: int, gym_id: Optional[str] = None) -> Optional[PlanDTO]:
        """Obtiene plan por ID."""
        if self._flags.should_read_from_sa():
            return self._get_from_sa(entity_id, gym_id)
        else:
            return self._get_from_legacy(entity_id, gym_id)
    
    def get_all(
        self,
        gym_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[PlanDTO]:
        """Lista planes con paginación."""
        if self._flags.should_read_from_sa():
            return self._list_from_sa(gym_id, offset, limit, filters)
        else:
            return self._list_from_legacy(gym_id, offset, limit, filters)
    
    def save(self, entity: PlanDTO) -> PlanDTO:
        """Guarda plan (create o update)."""
        is_new = entity.id is None or not self.exists(entity.id, entity.gym_id)
        
        write_legacy = self._flags.should_write_to_legacy()
        write_sa = self._flags.should_write_to_sa()
        
        result = None
        
        try:
            if write_legacy:
                result = self._save_to_legacy(entity, is_new)
                self._tracker.record(SyncResult(
                    success=True,
                    source="repository",
                    target="legacy",
                    entity_type="plan",
                    entity_id=str(entity.id or "new"),
                    operation="create" if is_new else "update",
                ))
            
            if write_sa:
                result = self._save_to_sa(entity, is_new)
                self._tracker.record(SyncResult(
                    success=True,
                    source="repository",
                    target="sqlalchemy",
                    entity_type="plan",
                    entity_id=str(result.id),
                    operation="create" if is_new else "update",
                ))
            
            return result
            
        except Exception as e:
            logger.error("Error en save plan: %s", e)
            self._tracker.record(SyncResult(
                success=False,
                source="repository",
                target="dual",
                entity_type="plan",
                entity_id=str(entity.id or "new"),
                operation="create" if is_new else "update",
                error=str(e),
            ))
            raise
    
    def delete(self, entity_id: int, gym_id: Optional[str] = None) -> bool:
        """Elimina plan."""
        write_legacy = self._flags.should_write_to_legacy()
        write_sa = self._flags.should_write_to_sa()
        
        success = True
        
        if write_legacy:
            success = success and self._delete_from_legacy(entity_id, gym_id)
        
        if write_sa:
            success = success and self._delete_from_sa(entity_id, gym_id)
        
        return success
    
    def exists(self, entity_id: int, gym_id: Optional[str] = None) -> bool:
        """Verifica si plan existe."""
        if self._flags.should_read_from_sa():
            return self._exists_in_sa(entity_id, gym_id)
        else:
            return self._exists_in_legacy(entity_id, gym_id)
    
    def count(
        self,
        gym_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Cuenta planes."""
        if self._flags.should_read_from_sa():
            return self._count_in_sa(gym_id, filters)
        else:
            return self._count_in_legacy(gym_id, filters)
    
    # ── Métodos búsqueda adicionales ────────────────────────────────────────
    
    def get_by_cliente(
        self,
        id_cliente: str,
        gym_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[PlanDTO]:
        """Obtiene planes de un cliente."""
        filters = {"id_cliente": id_cliente}
        return self.get_all(gym_id=gym_id, limit=limit, filters=filters)
    
    def get_recent(
        self,
        gym_id: Optional[str] = None,
        days: int = 30,
        limit: int = 100,
    ) -> List[PlanDTO]:
        """Obtiene planes generados recientemente."""
        # Para legacy, no hay filtro por fecha fácil
        return self.get_all(gym_id=gym_id, limit=limit)
    
    # ── Implementación Legacy ───────────────────────────────────────────────
    
    def _get_legacy_conn(self) -> sqlite3.Connection:
        """Obtiene conexión a BD legacy."""
        conn = sqlite3.connect(self._legacy_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_from_legacy(self, entity_id: int, gym_id: Optional[str]) -> Optional[PlanDTO]:
        """Lee plan de BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                cursor = conn.execute(
                    "SELECT * FROM planes_generados WHERE id = ?",
                    (entity_id,)
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_dto(dict(row))
                return None
        except Exception as e:
            logger.error("Error leyendo legacy plan %s: %s", entity_id, e)
            return None
    
    def _list_from_legacy(
        self,
        gym_id: Optional[str],
        offset: int,
        limit: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[PlanDTO]:
        """Lista planes de BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                query = "SELECT * FROM planes_generados"
                params = []
                where_clauses = []
                
                if filters:
                    if filters.get("id_cliente"):
                        where_clauses.append("id_cliente = ?")
                        params.append(filters["id_cliente"])
                    if filters.get("objetivo"):
                        where_clauses.append("objetivo = ?")
                        params.append(filters["objetivo"])
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                
                query += f" ORDER BY fecha_generacion DESC LIMIT {limit} OFFSET {offset}"
                
                cursor = conn.execute(query, params)
                return [self._row_to_dto(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error listando legacy planes: %s", e)
            return []
    
    def _save_to_legacy(self, entity: PlanDTO, is_new: bool) -> PlanDTO:
        """Guarda plan en BD legacy."""
        with self._get_legacy_conn() as conn:
            if is_new:
                cursor = conn.execute("""
                    INSERT INTO planes_generados (
                        id_cliente, fecha_generacion, tmb, get_total,
                        kcal_objetivo, kcal_real, proteina_g, carbs_g, grasa_g,
                        objetivo, nivel_actividad, plantilla_tipo, tipo_plan,
                        ruta_pdf, desviacion_maxima_pct,
                        peso_en_momento, grasa_en_momento
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity.id_cliente,
                    entity.fecha_generacion or datetime.now(),
                    entity.tmb, entity.get_total,
                    entity.kcal_objetivo, entity.kcal_real,
                    entity.proteina_g, entity.carbs_g, entity.grasa_g,
                    entity.objetivo, entity.nivel_actividad,
                    entity.plantilla_tipo, entity.tipo_plan,
                    entity.ruta_pdf, entity.desviacion_maxima_pct,
                    entity.peso_en_momento, entity.grasa_en_momento,
                ))
                entity.id = cursor.lastrowid
            else:
                conn.execute("""
                    UPDATE planes_generados SET
                        tmb = ?, get_total = ?,
                        kcal_objetivo = ?, kcal_real = ?,
                        proteina_g = ?, carbs_g = ?, grasa_g = ?,
                        objetivo = ?, nivel_actividad = ?,
                        plantilla_tipo = ?, tipo_plan = ?,
                        ruta_pdf = ?, desviacion_maxima_pct = ?,
                        peso_en_momento = ?, grasa_en_momento = ?
                    WHERE id = ?
                """, (
                    entity.tmb, entity.get_total,
                    entity.kcal_objetivo, entity.kcal_real,
                    entity.proteina_g, entity.carbs_g, entity.grasa_g,
                    entity.objetivo, entity.nivel_actividad,
                    entity.plantilla_tipo, entity.tipo_plan,
                    entity.ruta_pdf, entity.desviacion_maxima_pct,
                    entity.peso_en_momento, entity.grasa_en_momento,
                    entity.id,
                ))
            conn.commit()
        return entity
    
    def _delete_from_legacy(self, entity_id: int, gym_id: Optional[str]) -> bool:
        """Delete en BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                conn.execute("DELETE FROM planes_generados WHERE id = ?", (entity_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error("Error eliminando legacy plan %s: %s", entity_id, e)
            return False
    
    def _exists_in_legacy(self, entity_id: int, gym_id: Optional[str]) -> bool:
        """Verifica existencia en BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM planes_generados WHERE id = ?",
                    (entity_id,)
                )
                return cursor.fetchone() is not None
        except:
            return False
    
    def _count_in_legacy(self, gym_id: Optional[str], filters: Optional[Dict[str, Any]]) -> int:
        """Cuenta planes en BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM planes_generados")
                return cursor.fetchone()[0]
        except:
            return 0
    
    # ── Implementación SQLAlchemy ───────────────────────────────────────────
    
    def _get_from_sa(self, entity_id: int, gym_id: Optional[str]) -> Optional[PlanDTO]:
        """Lee plan de SQLAlchemy."""
        if self._sa is None:
            return self._get_from_legacy(entity_id, gym_id)
        
        try:
            from web.database.models import PlanGenerado
            
            query = self._sa.query(PlanGenerado).filter(PlanGenerado.id == entity_id)
            if gym_id:
                query = query.filter(PlanGenerado.gym_id == gym_id)
            
            plan = query.first()
            if plan:
                return self._model_to_dto(plan)
            return None
        except Exception as e:
            logger.error("Error leyendo SA plan %s: %s", entity_id, e)
            return None
    
    def _list_from_sa(
        self,
        gym_id: Optional[str],
        offset: int,
        limit: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[PlanDTO]:
        """Lista planes de SQLAlchemy."""
        if self._sa is None:
            return self._list_from_legacy(gym_id, offset, limit, filters)
        
        try:
            from web.database.models import PlanGenerado
            
            query = self._sa.query(PlanGenerado)
            
            if gym_id:
                query = query.filter(PlanGenerado.gym_id == gym_id)
            
            if filters:
                if filters.get("id_cliente"):
                    query = query.filter(PlanGenerado.id_cliente == filters["id_cliente"])
                if filters.get("objetivo"):
                    query = query.filter(PlanGenerado.objetivo == filters["objetivo"])
            
            query = query.order_by(PlanGenerado.fecha_generacion.desc())
            query = query.offset(offset).limit(limit)
            
            return [self._model_to_dto(p) for p in query.all()]
        except Exception as e:
            logger.error("Error listando SA planes: %s", e)
            return []
    
    def _save_to_sa(self, entity: PlanDTO, is_new: bool) -> PlanDTO:
        """Guarda plan en SQLAlchemy."""
        if self._sa is None:
            raise RuntimeError("SQLAlchemy no disponible")
        
        try:
            from web.database.models import PlanGenerado
            
            if is_new:
                plan = PlanGenerado(
                    id_cliente=entity.id_cliente,
                    gym_id=entity.gym_id,
                    fecha_generacion=entity.fecha_generacion or datetime.now(timezone.utc),
                    tmb=entity.tmb,
                    get_total=entity.get_total,
                    kcal_objetivo=entity.kcal_objetivo,
                    kcal_real=entity.kcal_real,
                    proteina_g=entity.proteina_g,
                    carbs_g=entity.carbs_g,
                    grasa_g=entity.grasa_g,
                    objetivo=entity.objetivo,
                    nivel_actividad=entity.nivel_actividad,
                    plantilla_tipo=entity.plantilla_tipo,
                    tipo_plan=entity.tipo_plan,
                    ruta_pdf=entity.ruta_pdf,
                    desviacion_maxima_pct=entity.desviacion_maxima_pct,
                    peso_en_momento=entity.peso_en_momento,
                    grasa_en_momento=entity.grasa_en_momento,
                )
                self._sa.add(plan)
                self._sa.flush()
                entity.id = plan.id
            else:
                plan = self._sa.query(PlanGenerado).filter(
                    PlanGenerado.id == entity.id
                ).first()
                
                if plan:
                    plan.tmb = entity.tmb
                    plan.get_total = entity.get_total
                    plan.kcal_objetivo = entity.kcal_objetivo
                    plan.kcal_real = entity.kcal_real
                    plan.proteina_g = entity.proteina_g
                    plan.carbs_g = entity.carbs_g
                    plan.grasa_g = entity.grasa_g
                    plan.objetivo = entity.objetivo
                    plan.ruta_pdf = entity.ruta_pdf
            
            self._sa.commit()
            return entity
        except Exception as e:
            self._sa.rollback()
            raise
    
    def _delete_from_sa(self, entity_id: int, gym_id: Optional[str]) -> bool:
        """Delete en SQLAlchemy."""
        if self._sa is None:
            return True
        
        try:
            from web.database.models import PlanGenerado
            
            query = self._sa.query(PlanGenerado).filter(PlanGenerado.id == entity_id)
            if gym_id:
                query = query.filter(PlanGenerado.gym_id == gym_id)
            
            plan = query.first()
            if plan:
                self._sa.delete(plan)
                self._sa.commit()
            return True
        except Exception as e:
            logger.error("Error eliminando SA plan %s: %s", entity_id, e)
            self._sa.rollback()
            return False
    
    def _exists_in_sa(self, entity_id: int, gym_id: Optional[str]) -> bool:
        """Verifica existencia en SQLAlchemy."""
        if self._sa is None:
            return self._exists_in_legacy(entity_id, gym_id)
        
        try:
            from web.database.models import PlanGenerado
            
            query = self._sa.query(PlanGenerado.id).filter(PlanGenerado.id == entity_id)
            if gym_id:
                query = query.filter(PlanGenerado.gym_id == gym_id)
            return query.first() is not None
        except:
            return False
    
    def _count_in_sa(self, gym_id: Optional[str], filters: Optional[Dict[str, Any]]) -> int:
        """Cuenta planes en SQLAlchemy."""
        if self._sa is None:
            return self._count_in_legacy(gym_id, filters)
        
        try:
            from web.database.models import PlanGenerado
            
            query = self._sa.query(PlanGenerado)
            if gym_id:
                query = query.filter(PlanGenerado.gym_id == gym_id)
            return query.count()
        except:
            return 0
    
    # ── Conversión ──────────────────────────────────────────────────────────
    
    def _row_to_dto(self, row: Dict[str, Any]) -> PlanDTO:
        """Convierte fila legacy a DTO."""
        return PlanDTO(
            id=row.get("id"),
            id_cliente=row.get("id_cliente", ""),
            gym_id=row.get("gym_id"),
            fecha_generacion=row.get("fecha_generacion"),
            tmb=row.get("tmb"),
            get_total=row.get("get_total"),
            kcal_objetivo=row.get("kcal_objetivo"),
            kcal_real=row.get("kcal_real"),
            proteina_g=row.get("proteina_g"),
            carbs_g=row.get("carbs_g"),
            grasa_g=row.get("grasa_g"),
            objetivo=row.get("objetivo"),
            nivel_actividad=row.get("nivel_actividad"),
            plantilla_tipo=row.get("plantilla_tipo", "general"),
            tipo_plan=row.get("tipo_plan", "menu_fijo"),
            ruta_pdf=row.get("ruta_pdf"),
            desviacion_maxima_pct=row.get("desviacion_maxima_pct"),
            peso_en_momento=row.get("peso_en_momento"),
            grasa_en_momento=row.get("grasa_en_momento"),
        )
    
    def _model_to_dto(self, model) -> PlanDTO:
        """Convierte modelo SQLAlchemy a DTO."""
        return PlanDTO(
            id=model.id,
            id_cliente=model.id_cliente,
            gym_id=model.gym_id,
            fecha_generacion=model.fecha_generacion,
            tmb=model.tmb,
            get_total=model.get_total,
            kcal_objetivo=model.kcal_objetivo,
            kcal_real=model.kcal_real,
            proteina_g=model.proteina_g,
            carbs_g=model.carbs_g,
            grasa_g=model.grasa_g,
            objetivo=model.objetivo,
            nivel_actividad=model.nivel_actividad,
            plantilla_tipo=getattr(model, 'plantilla_tipo', 'general'),
            tipo_plan=getattr(model, 'tipo_plan', 'menu_fijo'),
            ruta_pdf=model.ruta_pdf,
            desviacion_maxima_pct=model.desviacion_maxima_pct,
            peso_en_momento=getattr(model, 'peso_en_momento', None),
            grasa_en_momento=getattr(model, 'grasa_en_momento', None),
        )
    
    # ── Migration Utilities ─────────────────────────────────────────────────
    
    def migrate_to_sa(self, batch_size: int = 100, dry_run: bool = True) -> Dict[str, Any]:
        """
        Migra todos los planes de legacy a SQLAlchemy.
        """
        stats = {
            "total_legacy": 0,
            "migrated": 0,
            "errors": 0,
            "dry_run": dry_run,
        }
        
        all_legacy = self._list_from_legacy(
            gym_id=None,
            offset=0,
            limit=100000,
            filters=None,
        )
        stats["total_legacy"] = len(all_legacy)
        
        for plan in all_legacy:
            try:
                if not dry_run:
                    plan.id = None  # Force new insert
                    self._save_to_sa(plan, is_new=True)
                stats["migrated"] += 1
            except Exception as e:
                logger.error("Error migrando plan %s: %s", plan.id, e)
                stats["errors"] += 1
        
        return stats
