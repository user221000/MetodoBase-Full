"""
src/repositories/cliente_repository.py — Repository para gestión de clientes.

Implementa Strangler Fig pattern:
- Lee de legacy o SA según feature flags
- Escribe a uno o ambos backends según fase
- Valida consistencia en dual-write
"""
import sqlite3
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.feature_flags import get_migration_flags, DBMigrationFlags
from .base import (
    BaseRepository,
    ClienteDTO,
    EntityNotFoundError,
    DuplicateEntityError,
    SyncError,
    SyncResult,
    get_sync_tracker,
)

logger = logging.getLogger(__name__)


class ClienteRepository(BaseRepository[ClienteDTO, str]):
    """
    Repository para clientes con soporte dual-BD.
    
    Fases de migración:
    1. LEGACY_PRIMARY: Lee de legacy, shadow write a SA
    2. DUAL_WRITE: Escribe a ambos, lee de legacy
    3. SA_PRIMARY: Lee de SA, shadow write a legacy
    4. SA_ONLY: Solo SA, legacy deprecated
    """
    
    def __init__(
        self,
        legacy_db_path: str = "clientes.db",
        flags: Optional[DBMigrationFlags] = None,
    ):
        self._legacy_db_path = legacy_db_path
        self._flags = flags or get_migration_flags()
        self._tracker = get_sync_tracker()
        
        # SQLAlchemy session será lazy-loaded
        self._sa_session = None
    
    # ── Propiedades ─────────────────────────────────────────────────────────
    
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
                logger.warning("SQLAlchemy no disponible, usando solo legacy")
                return None
        return self._sa_session
    
    @property
    def phase(self) -> int:
        """Fase actual de migración (1-4)."""
        return self._flags.current_phase()
    
    # ── CRUD Principal ──────────────────────────────────────────────────────
    
    def get_by_id(self, entity_id: str, gym_id: Optional[str] = None) -> Optional[ClienteDTO]:
        """
        Obtiene cliente por ID.
        
        Routing según fase:
        - Fase 1-2: Lee de legacy
        - Fase 3-4: Lee de SQLAlchemy
        """
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
    ) -> List[ClienteDTO]:
        """Lista clientes con paginación."""
        if self._flags.should_read_from_sa():
            return self._list_from_sa(gym_id, offset, limit, filters)
        else:
            return self._list_from_legacy(gym_id, offset, limit, filters)
    
    def save(self, entity: ClienteDTO) -> ClienteDTO:
        """
        Guarda cliente (create o update).
        
        Estrategia dual-write según fase:
        - Fase 1: Legacy only, shadow SA
        - Fase 2: Ambos (legacy primary)
        - Fase 3: Ambos (SA primary)
        - Fase 4: SA only
        """
        is_new = not self.exists(entity.id_cliente, entity.gym_id)
        
        # Determinar a dónde escribir
        write_legacy = self._flags.should_write_to_legacy()
        write_sa = self._flags.should_write_to_sa()
        
        result_legacy = None
        result_sa = None
        
        try:
            # Escribir a legacy si aplica
            if write_legacy:
                result_legacy = self._save_to_legacy(entity, is_new)
                self._tracker.record(SyncResult(
                    success=True,
                    source="repository",
                    target="legacy",
                    entity_type="cliente",
                    entity_id=entity.id_cliente,
                    operation="create" if is_new else "update",
                ))
            
            # Escribir a SA si aplica
            if write_sa:
                result_sa = self._save_to_sa(entity, is_new)
                self._tracker.record(SyncResult(
                    success=True,
                    source="repository",
                    target="sqlalchemy",
                    entity_type="cliente",
                    entity_id=entity.id_cliente,
                    operation="create" if is_new else "update",
                ))
            
            # Validar consistencia si dual-write
            if write_legacy and write_sa:
                self._validate_sync(entity.id_cliente, entity.gym_id)
            
            # Retornar según fuente primaria
            return result_sa if self._flags.should_read_from_sa() else result_legacy
            
        except Exception as e:
            logger.error("Error en save cliente %s: %s", entity.id_cliente, e)
            self._tracker.record(SyncResult(
                success=False,
                source="repository",
                target="dual",
                entity_type="cliente",
                entity_id=entity.id_cliente,
                operation="create" if is_new else "update",
                error=str(e),
            ))
            raise
    
    def delete(self, entity_id: str, gym_id: Optional[str] = None) -> bool:
        """Elimina cliente (soft delete)."""
        write_legacy = self._flags.should_write_to_legacy()
        write_sa = self._flags.should_write_to_sa()
        
        success = True
        
        if write_legacy:
            success = success and self._delete_from_legacy(entity_id, gym_id)
        
        if write_sa:
            success = success and self._delete_from_sa(entity_id, gym_id)
        
        return success
    
    def exists(self, entity_id: str, gym_id: Optional[str] = None) -> bool:
        """Verifica si cliente existe."""
        if self._flags.should_read_from_sa():
            return self._exists_in_sa(entity_id, gym_id)
        else:
            return self._exists_in_legacy(entity_id, gym_id)
    
    def count(
        self,
        gym_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Cuenta clientes."""
        if self._flags.should_read_from_sa():
            return self._count_in_sa(gym_id, filters)
        else:
            return self._count_in_legacy(gym_id, filters)
    
    # ── Métodos búsqueda adicionales ────────────────────────────────────────
    
    def search_by_name(
        self,
        name_pattern: str,
        gym_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[ClienteDTO]:
        """Busca clientes por nombre (LIKE)."""
        if self._flags.should_read_from_sa():
            return self._search_name_sa(name_pattern, gym_id, limit)
        else:
            return self._search_name_legacy(name_pattern, gym_id, limit)
    
    def get_recent(
        self,
        gym_id: Optional[str] = None,
        days: int = 30,
        limit: int = 50,
    ) -> List[ClienteDTO]:
        """Obtiene clientes registrados recientemente."""
        # Implementación simplificada - read from primary
        all_clients = self.get_all(gym_id=gym_id, limit=limit)
        return all_clients  # TODO: filtrar por fecha cuando exista
    
    # ── Implementación Legacy (sqlite3 raw) ─────────────────────────────────
    
    def _get_legacy_conn(self) -> sqlite3.Connection:
        """Obtiene conexión a BD legacy."""
        conn = sqlite3.connect(self._legacy_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_from_legacy(self, entity_id: str, gym_id: Optional[str]) -> Optional[ClienteDTO]:
        """Lee cliente de BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                cursor = conn.execute(
                    "SELECT * FROM clientes WHERE id_cliente = ?",
                    (entity_id,)
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_dto(dict(row))
                return None
        except Exception as e:
            logger.error("Error leyendo legacy cliente %s: %s", entity_id, e)
            return None
    
    def _list_from_legacy(
        self,
        gym_id: Optional[str],
        offset: int,
        limit: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[ClienteDTO]:
        """Lista clientes de BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                # Build query
                query = "SELECT * FROM clientes"
                params = []
                
                # Filters
                where_clauses = []
                if filters:
                    if filters.get("activo") is not None:
                        where_clauses.append("activo = ?")
                        params.append(1 if filters["activo"] else 0)
                    if filters.get("sexo"):
                        where_clauses.append("sexo = ?")
                        params.append(filters["sexo"])
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                
                query += f" ORDER BY nombre LIMIT {limit} OFFSET {offset}"
                
                cursor = conn.execute(query, params)
                return [self._row_to_dto(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error listando legacy clientes: %s", e)
            return []
    
    def _save_to_legacy(self, entity: ClienteDTO, is_new: bool) -> ClienteDTO:
        """Guarda cliente en BD legacy."""
        with self._get_legacy_conn() as conn:
            if is_new:
                conn.execute("""
                    INSERT INTO clientes (
                        id_cliente, nombre, telefono, email, edad, sexo,
                        peso_kg, estatura_cm, grasa_corporal_pct, masa_magra_kg,
                        nivel_actividad, objetivo, plantilla_tipo,
                        fecha_registro, ultimo_plan, total_planes_generados,
                        activo, notas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity.id_cliente, entity.nombre, entity.telefono, entity.email,
                    entity.edad, entity.sexo, entity.peso_kg, entity.estatura_cm,
                    entity.grasa_corporal_pct, entity.masa_magra_kg,
                    entity.nivel_actividad, entity.objetivo, entity.plantilla_tipo,
                    entity.fecha_registro or datetime.now(),
                    entity.ultimo_plan, entity.total_planes_generados,
                    1 if entity.activo else 0, entity.notas,
                ))
            else:
                conn.execute("""
                    UPDATE clientes SET
                        nombre = ?, telefono = ?, email = ?, edad = ?, sexo = ?,
                        peso_kg = ?, estatura_cm = ?, grasa_corporal_pct = ?,
                        masa_magra_kg = ?, nivel_actividad = ?, objetivo = ?,
                        plantilla_tipo = ?, ultimo_plan = ?,
                        total_planes_generados = ?, activo = ?, notas = ?
                    WHERE id_cliente = ?
                """, (
                    entity.nombre, entity.telefono, entity.email,
                    entity.edad, entity.sexo, entity.peso_kg, entity.estatura_cm,
                    entity.grasa_corporal_pct, entity.masa_magra_kg,
                    entity.nivel_actividad, entity.objetivo, entity.plantilla_tipo,
                    entity.ultimo_plan, entity.total_planes_generados,
                    1 if entity.activo else 0, entity.notas,
                    entity.id_cliente,
                ))
            conn.commit()
        return entity
    
    def _delete_from_legacy(self, entity_id: str, gym_id: Optional[str]) -> bool:
        """Soft delete en BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                conn.execute(
                    "UPDATE clientes SET activo = 0 WHERE id_cliente = ?",
                    (entity_id,)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error("Error eliminando legacy cliente %s: %s", entity_id, e)
            return False
    
    def _exists_in_legacy(self, entity_id: str, gym_id: Optional[str]) -> bool:
        """Verifica existencia en BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM clientes WHERE id_cliente = ?",
                    (entity_id,)
                )
                return cursor.fetchone() is not None
        except:
            return False
    
    def _count_in_legacy(self, gym_id: Optional[str], filters: Optional[Dict[str, Any]]) -> int:
        """Cuenta clientes en BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM clientes")
                return cursor.fetchone()[0]
        except:
            return 0
    
    def _search_name_legacy(self, pattern: str, gym_id: Optional[str], limit: int) -> List[ClienteDTO]:
        """Busca por nombre en BD legacy."""
        try:
            with self._get_legacy_conn() as conn:
                cursor = conn.execute(
                    "SELECT * FROM clientes WHERE nombre LIKE ? LIMIT ?",
                    (f"%{pattern}%", limit)
                )
                return [self._row_to_dto(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error buscando legacy clientes: %s", e)
            return []
    
    # ── Implementación SQLAlchemy ───────────────────────────────────────────
    
    def _get_from_sa(self, entity_id: str, gym_id: Optional[str]) -> Optional[ClienteDTO]:
        """Lee cliente de SQLAlchemy."""
        if self._sa is None:
            logger.warning("SQLAlchemy no disponible, fallback a legacy")
            return self._get_from_legacy(entity_id, gym_id)
        
        try:
            from web.database.models import Cliente
            
            query = self._sa.query(Cliente).filter(Cliente.id_cliente == entity_id)
            if gym_id:
                query = query.filter(Cliente.gym_id == gym_id)
            
            cliente = query.first()
            if cliente:
                return self._model_to_dto(cliente)
            return None
        except Exception as e:
            logger.error("Error leyendo SA cliente %s: %s", entity_id, e)
            return None
    
    def _list_from_sa(
        self,
        gym_id: Optional[str],
        offset: int,
        limit: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[ClienteDTO]:
        """Lista clientes de SQLAlchemy."""
        if self._sa is None:
            return self._list_from_legacy(gym_id, offset, limit, filters)
        
        try:
            from web.database.models import Cliente
            
            query = self._sa.query(Cliente)
            
            if gym_id:
                query = query.filter(Cliente.gym_id == gym_id)
            
            if filters:
                if filters.get("activo") is not None:
                    query = query.filter(Cliente.activo == filters["activo"])
                if filters.get("sexo"):
                    query = query.filter(Cliente.sexo == filters["sexo"])
            
            query = query.order_by(Cliente.nombre)
            query = query.offset(offset).limit(limit)
            
            return [self._model_to_dto(c) for c in query.all()]
        except Exception as e:
            logger.error("Error listando SA clientes: %s", e)
            return []
    
    def _save_to_sa(self, entity: ClienteDTO, is_new: bool) -> ClienteDTO:
        """Guarda cliente en SQLAlchemy."""
        if self._sa is None:
            raise RuntimeError("SQLAlchemy no disponible para escritura")
        
        try:
            from web.database.models import Cliente
            
            if is_new:
                cliente = Cliente(
                    id_cliente=entity.id_cliente,
                    gym_id=entity.gym_id,
                    nombre=entity.nombre,
                    telefono=entity.telefono,
                    email=entity.email,
                    edad=entity.edad,
                    sexo=entity.sexo,
                    peso_kg=entity.peso_kg,
                    estatura_cm=entity.estatura_cm,
                    grasa_corporal_pct=entity.grasa_corporal_pct,
                    masa_magra_kg=entity.masa_magra_kg,
                    nivel_actividad=entity.nivel_actividad,
                    objetivo=entity.objetivo,
                    plantilla_tipo=entity.plantilla_tipo,
                    activo=entity.activo,
                    notas=entity.notas,
                )
                self._sa.add(cliente)
            else:
                cliente = self._sa.query(Cliente).filter(
                    Cliente.id_cliente == entity.id_cliente
                ).first()
                
                if cliente:
                    cliente.nombre = entity.nombre
                    cliente.telefono = entity.telefono
                    cliente.email = entity.email
                    cliente.edad = entity.edad
                    cliente.sexo = entity.sexo
                    cliente.peso_kg = entity.peso_kg
                    cliente.estatura_cm = entity.estatura_cm
                    cliente.grasa_corporal_pct = entity.grasa_corporal_pct
                    cliente.masa_magra_kg = entity.masa_magra_kg
                    cliente.nivel_actividad = entity.nivel_actividad
                    cliente.objetivo = entity.objetivo
                    cliente.plantilla_tipo = entity.plantilla_tipo
                    cliente.activo = entity.activo
                    cliente.notas = entity.notas
            
            self._sa.commit()
            return entity
        except Exception as e:
            self._sa.rollback()
            raise
    
    def _delete_from_sa(self, entity_id: str, gym_id: Optional[str]) -> bool:
        """Soft delete en SQLAlchemy."""
        if self._sa is None:
            return True  # No-op si SA no disponible
        
        try:
            from web.database.models import Cliente
            
            query = self._sa.query(Cliente).filter(Cliente.id_cliente == entity_id)
            if gym_id:
                query = query.filter(Cliente.gym_id == gym_id)
            
            cliente = query.first()
            if cliente:
                cliente.activo = False
                self._sa.commit()
            return True
        except Exception as e:
            logger.error("Error eliminando SA cliente %s: %s", entity_id, e)
            self._sa.rollback()
            return False
    
    def _exists_in_sa(self, entity_id: str, gym_id: Optional[str]) -> bool:
        """Verifica existencia en SQLAlchemy."""
        if self._sa is None:
            return self._exists_in_legacy(entity_id, gym_id)
        
        try:
            from web.database.models import Cliente
            
            query = self._sa.query(Cliente.id_cliente).filter(
                Cliente.id_cliente == entity_id
            )
            if gym_id:
                query = query.filter(Cliente.gym_id == gym_id)
            
            return query.first() is not None
        except:
            return False
    
    def _count_in_sa(self, gym_id: Optional[str], filters: Optional[Dict[str, Any]]) -> int:
        """Cuenta clientes en SQLAlchemy."""
        if self._sa is None:
            return self._count_in_legacy(gym_id, filters)
        
        try:
            from web.database.models import Cliente
            
            query = self._sa.query(Cliente)
            if gym_id:
                query = query.filter(Cliente.gym_id == gym_id)
            return query.count()
        except:
            return 0
    
    def _search_name_sa(self, pattern: str, gym_id: Optional[str], limit: int) -> List[ClienteDTO]:
        """Busca por nombre en SQLAlchemy."""
        if self._sa is None:
            return self._search_name_legacy(pattern, gym_id, limit)
        
        try:
            from web.database.models import Cliente
            
            query = self._sa.query(Cliente).filter(
                Cliente.nombre.ilike(f"%{pattern}%")
            )
            if gym_id:
                query = query.filter(Cliente.gym_id == gym_id)
            
            return [self._model_to_dto(c) for c in query.limit(limit).all()]
        except Exception as e:
            logger.error("Error buscando SA clientes: %s", e)
            return []
    
    # ── Conversión y Validación ─────────────────────────────────────────────
    
    def _row_to_dto(self, row: Dict[str, Any]) -> ClienteDTO:
        """Convierte fila legacy a DTO."""
        return ClienteDTO(
            id_cliente=row.get("id_cliente", ""),
            nombre=row.get("nombre", ""),
            gym_id=row.get("gym_id"),  # Legacy puede no tener
            telefono=row.get("telefono"),
            email=row.get("email"),
            edad=row.get("edad"),
            sexo=row.get("sexo"),
            peso_kg=row.get("peso_kg"),
            estatura_cm=row.get("estatura_cm"),
            grasa_corporal_pct=row.get("grasa_corporal_pct"),
            masa_magra_kg=row.get("masa_magra_kg"),
            nivel_actividad=row.get("nivel_actividad"),
            objetivo=row.get("objetivo"),
            plantilla_tipo=row.get("plantilla_tipo", "general"),
            fecha_registro=row.get("fecha_registro"),
            ultimo_plan=row.get("ultimo_plan"),
            total_planes_generados=row.get("total_planes_generados", 0),
            activo=bool(row.get("activo", 1)),
            notas=row.get("notas"),
        )
    
    def _model_to_dto(self, model) -> ClienteDTO:
        """Convierte modelo SQLAlchemy a DTO."""
        return ClienteDTO(
            id_cliente=model.id_cliente,
            nombre=model.nombre,
            gym_id=model.gym_id,
            telefono=model.telefono,
            email=model.email,
            edad=model.edad,
            sexo=model.sexo,
            peso_kg=model.peso_kg,
            estatura_cm=model.estatura_cm,
            grasa_corporal_pct=model.grasa_corporal_pct,
            masa_magra_kg=model.masa_magra_kg,
            nivel_actividad=model.nivel_actividad,
            objetivo=model.objetivo,
            plantilla_tipo=getattr(model, 'plantilla_tipo', 'general'),
            fecha_registro=model.fecha_registro,
            ultimo_plan=getattr(model, 'ultimo_plan', None),
            total_planes_generados=getattr(model, 'total_planes_generados', 0),
            activo=getattr(model, 'activo', True),
            notas=model.notas,
        )
    
    def _validate_sync(self, entity_id: str, gym_id: Optional[str]) -> None:
        """
        Valida consistencia entre legacy y SA después de dual-write.
        
        Lanza SyncError si hay discrepancia crítica.
        """
        legacy = self._get_from_legacy(entity_id, gym_id)
        sa = self._get_from_sa(entity_id, gym_id)
        
        if legacy is None and sa is None:
            return  # Ambos no existen, ok
        
        if legacy is None or sa is None:
            self._tracker.record(SyncResult(
                success=False,
                source="legacy" if legacy else "sqlalchemy",
                target="sqlalchemy" if legacy else "legacy",
                entity_type="cliente",
                entity_id=entity_id,
                operation="validate",
                error="Entity exists in one BD but not the other",
            ))
            return  # Log pero no lanzar
        
        # Comparar campos críticos
        critical_match = (
            legacy.nombre == sa.nombre and
            legacy.peso_kg == sa.peso_kg and
            legacy.objetivo == sa.objetivo
        )
        
        if not critical_match:
            logger.warning(
                "Sync drift detected for cliente %s: legacy=%s vs sa=%s",
                entity_id, legacy.nombre, sa.nombre
            )
            self._tracker.record(SyncResult(
                success=False,
                source="legacy",
                target="sqlalchemy",
                entity_type="cliente",
                entity_id=entity_id,
                operation="validate",
                error="Critical field mismatch",
                details={
                    "legacy_nombre": legacy.nombre,
                    "sa_nombre": sa.nombre,
                },
            ))
    
    # ── Migration Utilities ─────────────────────────────────────────────────
    
    def migrate_to_sa(self, batch_size: int = 100, dry_run: bool = True) -> Dict[str, Any]:
        """
        Migra todos los clientes de legacy a SQLAlchemy.
        
        Args:
            batch_size: Tamaño de batch para commits
            dry_run: Si True, no hace cambios reales
        
        Returns:
            Estadísticas de migración
        """
        stats = {
            "total_legacy": 0,
            "migrated": 0,
            "already_exists": 0,
            "errors": 0,
            "dry_run": dry_run,
        }
        
        # Get all from legacy
        all_legacy = self._list_from_legacy(
            gym_id=None,
            offset=0,
            limit=100000,
            filters=None,
        )
        stats["total_legacy"] = len(all_legacy)
        
        for cliente in all_legacy:
            try:
                if self._exists_in_sa(cliente.id_cliente, cliente.gym_id):
                    stats["already_exists"] += 1
                    continue
                
                if not dry_run:
                    self._save_to_sa(cliente, is_new=True)
                
                stats["migrated"] += 1
                
            except Exception as e:
                logger.error("Error migrando cliente %s: %s", cliente.id_cliente, e)
                stats["errors"] += 1
        
        return stats
    
    def compare_databases(self, gym_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Compara estado entre legacy y SA para auditoría.
        
        Returns:
            Reporte de diferencias
        """
        legacy_clients = {c.id_cliente: c for c in self._list_from_legacy(gym_id, 0, 100000, None)}
        sa_clients = {c.id_cliente: c for c in self._list_from_sa(gym_id, 0, 100000, None)}
        
        only_legacy = set(legacy_clients.keys()) - set(sa_clients.keys())
        only_sa = set(sa_clients.keys()) - set(legacy_clients.keys())
        both = set(legacy_clients.keys()) & set(sa_clients.keys())
        
        mismatches = []
        for client_id in both:
            l = legacy_clients[client_id]
            s = sa_clients[client_id]
            if l.nombre != s.nombre or l.peso_kg != s.peso_kg:
                mismatches.append({
                    "id": client_id,
                    "legacy": {"nombre": l.nombre, "peso_kg": l.peso_kg},
                    "sa": {"nombre": s.nombre, "peso_kg": s.peso_kg},
                })
        
        return {
            "legacy_count": len(legacy_clients),
            "sa_count": len(sa_clients),
            "only_in_legacy": list(only_legacy),
            "only_in_sa": list(only_sa),
            "in_both": len(both),
            "mismatches": mismatches,
        }
