"""
Migration: Add RBAC fields to usuarios table

This migration adds the following columns to support Role-Based Access Control:
- role: UserRole enum (owner, admin, nutriologo, viewer)
- team_gym_id: FK to owner's usuarios.id for team members
- invited_by: FK to inviter's usuarios.id
- invitation_token: Secure token for accepting invitations
- invitation_expires: When the invitation expires
- invitation_role: Role that will be assigned when invitation is accepted

Run manually:
    python scripts/migrate_rbac.py

Or via alembic (if configured):
    alembic upgrade head
"""
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from web.database.engine import get_engine


def migrate_up():
    """Add RBAC columns to usuarios table."""
    engine = get_engine()
    
    columns_to_add = [
        ('role', 'VARCHAR(20) DEFAULT "viewer"'),
        ('team_gym_id', 'VARCHAR(36)'),
        ('invited_by', 'INTEGER'),
        ('invitation_token', 'VARCHAR(64)'),
        ('invitation_expires', 'DATETIME'),
        ('invitation_role', 'VARCHAR(20)'),
    ]
    
    with engine.connect() as conn:
        for col_name, col_def in columns_to_add:
            try:
                conn.execute(text(f'ALTER TABLE usuarios ADD COLUMN {col_name} {col_def}'))
                print(f'✓ Added column: {col_name}')
            except Exception as e:
                if 'duplicate column' in str(e).lower():
                    print(f'· Column already exists: {col_name}')
                else:
                    print(f'! Error adding {col_name}: {e}')
        
        conn.commit()
    
    # Update existing users with appropriate roles
    with engine.connect() as conn:
        # Gym owners get OWNER role
        result = conn.execute(text("UPDATE usuarios SET role = 'owner' WHERE tipo = 'gym' AND (role IS NULL OR role = '')"))
        print(f'✓ Updated {result.rowcount} gym users to role=owner')
        
        # System admins get OWNER role too (for now)
        result = conn.execute(text("UPDATE usuarios SET role = 'owner' WHERE tipo = 'admin' AND (role IS NULL OR role = '')"))
        print(f'✓ Updated {result.rowcount} admin users to role=owner')
        
        # Regular users default to VIEWER
        result = conn.execute(text("UPDATE usuarios SET role = 'viewer' WHERE tipo = 'usuario' AND (role IS NULL OR role = '')"))
        print(f'✓ Updated {result.rowcount} regular users to role=viewer')
        
        conn.commit()
    
    # Create indices for performance
    indices = [
        ('ix_usuarios_team_gym', 'usuarios', 'team_gym_id'),
        ('ix_usuarios_invitation', 'usuarios', 'invitation_token'),
    ]
    
    with engine.connect() as conn:
        for idx_name, table, column in indices:
            try:
                conn.execute(text(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})'))
                print(f'✓ Created index: {idx_name}')
            except Exception as e:
                print(f'· Index {idx_name}: {e}')
        
        conn.commit()
    
    print('\n✅ RBAC migration completed successfully!')


def migrate_down():
    """Remove RBAC columns (destructive!)."""
    engine = get_engine()
    
    # SQLite doesn't support DROP COLUMN easily, would need to recreate table
    print('⚠️  SQLite does not easily support DROP COLUMN.')
    print('   To rollback, you would need to:')
    print('   1. Create new table without RBAC columns')
    print('   2. Copy data')
    print('   3. Drop old table')
    print('   4. Rename new table')
    print('')
    print('   This migration does NOT auto-rollback for safety.')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='RBAC Migration for MetodoBase')
    parser.add_argument('--down', action='store_true', help='Rollback migration')
    args = parser.parse_args()
    
    if args.down:
        migrate_down()
    else:
        migrate_up()
