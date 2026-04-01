"""enable_rls_policies_multi_tenant

Revision ID: c4f8e9d2a3b1
Revises: 936af15af980
Create Date: 2026-03-24 10:30:00.000000

Row Level Security (RLS) policies para aislamiento multi-tenant en PostgreSQL.
Estas políticas garantizan que cada gym solo puede ver sus propios datos.

NOTA: Solo aplica para PostgreSQL. SQLite no soporta RLS.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'c4f8e9d2a3b1'
down_revision: Union[str, Sequence[str], None] = '936af15af980'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def is_postgres() -> bool:
    """Check if we're running on PostgreSQL."""
    bind = op.get_bind()
    return bind.dialect.name == 'postgresql'


def upgrade() -> None:
    """Enable RLS policies for multi-tenant isolation."""
    if not is_postgres():
        # SQLite no soporta RLS - skip silently
        return
    
    conn = op.get_bind()
    
    # ── Habilitar RLS en tablas con gym_id ────────────────────────────────────
    
    # Tabla: clientes
    conn.execute(text("ALTER TABLE clientes ENABLE ROW LEVEL SECURITY"))
    conn.execute(text("ALTER TABLE clientes FORCE ROW LEVEL SECURITY"))
    conn.execute(text("""
        CREATE POLICY tenant_isolation_clientes ON clientes
        FOR ALL
        USING (gym_id = current_setting('app.current_tenant', TRUE))
        WITH CHECK (gym_id = current_setting('app.current_tenant', TRUE))
    """))
    
    # Tabla: planes_generados
    conn.execute(text("ALTER TABLE planes_generados ENABLE ROW LEVEL SECURITY"))
    conn.execute(text("ALTER TABLE planes_generados FORCE ROW LEVEL SECURITY"))
    conn.execute(text("""
        CREATE POLICY tenant_isolation_planes ON planes_generados
        FOR ALL
        USING (gym_id = current_setting('app.current_tenant', TRUE))
        WITH CHECK (gym_id = current_setting('app.current_tenant', TRUE))
    """))
    
    # Tabla: subscriptions (si existe)
    try:
        conn.execute(text("ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE subscriptions FORCE ROW LEVEL SECURITY"))
        conn.execute(text("""
            CREATE POLICY tenant_isolation_subscriptions ON subscriptions
            FOR ALL
            USING (gym_id = current_setting('app.current_tenant', TRUE))
            WITH CHECK (gym_id = current_setting('app.current_tenant', TRUE))
        """))
    except Exception:
        pass  # tabla puede no existir en todas las instalaciones
    
    # Tabla: payments (si existe)
    try:
        conn.execute(text("ALTER TABLE payments ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE payments FORCE ROW LEVEL SECURITY"))
        conn.execute(text("""
            CREATE POLICY tenant_isolation_payments ON payments
            FOR ALL
            USING (gym_id = current_setting('app.current_tenant', TRUE))
            WITH CHECK (gym_id = current_setting('app.current_tenant', TRUE))
        """))
    except Exception:
        pass
    
    # ── Crear función helper para set tenant ──────────────────────────────────
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION set_tenant(tenant_id TEXT)
        RETURNS VOID AS $$
        BEGIN
            PERFORM set_config('app.current_tenant', tenant_id, FALSE);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER
    """))
    
    # ── Crear rol de aplicación si no existe ──────────────────────────────────
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'metodobase_app') THEN
                CREATE ROLE metodobase_app;
            END IF;
        END
        $$
    """))
    
    # Otorgar permisos al rol de aplicación
    for table in ['clientes', 'planes_generados', 'usuarios', 'refresh_tokens']:
        try:
            conn.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO metodobase_app"))
        except Exception:
            pass


def downgrade() -> None:
    """Remove RLS policies."""
    if not is_postgres():
        return
    
    conn = op.get_bind()
    
    # Eliminar políticas
    for table, policy in [
        ('clientes', 'tenant_isolation_clientes'),
        ('planes_generados', 'tenant_isolation_planes'),
        ('subscriptions', 'tenant_isolation_subscriptions'),
        ('payments', 'tenant_isolation_payments'),
    ]:
        try:
            conn.execute(text(f"DROP POLICY IF EXISTS {policy} ON {table}"))
            conn.execute(text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))
        except Exception:
            pass
    
    # Eliminar función helper
    try:
        conn.execute(text("DROP FUNCTION IF EXISTS set_tenant(TEXT)"))
    except Exception:
        pass
