# Dual Database Consolidation Plan

**Author:** Audit Pipeline  
**Date:** 2026-03-28  
**Status:** Planning  

## Problem Statement

The application uses two separate SQLite databases for user/auth data:

1. **`web_usuarios.db`** — Raw SQLite3 via `web/auth.py`
   - Stores: `web_usuarios` table (auth: id, email, password_hash, nombre, apellido, tipo, fecha_registro, activo)
   - Also stores: `auth_tokens` table (session tokens)
   - Access: Direct `sqlite3.connect()` calls, no ORM

2. **`metodobase_web.db`** — SQLAlchemy ORM via `web/database/engine.py`
   - Stores: `Usuario` model (same fields + gym_id, role, subscription data)
   - Also stores: all business data (clientes, planes, gym_profiles, checkout_sessions, etc.)
   - Access: SQLAlchemy sessions, Alembic migrations

**Risk:** User data is dual-written to both databases and can desync. A user created via the registration flow goes into `web_usuarios.db` first, then gets synced to the SA `Usuario` table. If either write fails, the databases diverge.

## Current Architecture

```
Registration → web/auth.py (sqlite3) → web_usuarios.db
                     ↓ (dual write)
              web/database/repository.py (SA) → metodobase_web.db
                     
Login → web/auth.py → web_usuarios.db (password verify)
            ↓
       Token issued → auth_tokens in web_usuarios.db

API calls → web/auth_deps.py → validates token from web_usuarios.db
                 ↓
            read user from SA Usuario model (metodobase_web.db)
```

## Migration Phases

### Phase 1: Sync Verification (Non-breaking)

**Goal:** Detect desync between the two databases.

**Steps:**
1. Add a `/api/admin/db-sync-check` endpoint (admin-only) that:
   - Reads all users from `web_usuarios.db`
   - Reads all users from SA `Usuario` table
   - Reports mismatches (missing in either, field differences)
2. Add a startup check in `lifespan()` that logs warnings for any desync
3. Add a `scripts/verify_db_sync.py` CLI tool for manual audits

**Rollback:** Remove the endpoint and startup check.

### Phase 2: Migrate Auth to SQLAlchemy (Parallel Write)

**Goal:** Auth reads/writes go to SA, with fallback to legacy.

**Steps:**
1. Create `web/auth_sa.py` — same interface as `web/auth.py` but using SA models
2. Migrate `auth_tokens` table to SA model (add `AuthToken` to `web/database/models.py`)
3. Update `web/auth.py` functions to delegate to SA while keeping legacy as fallback:
   - `register_user()` → write to SA first, then legacy
   - `authenticate()` → read from SA first, fallback to legacy
   - `get_user_by_id()` → read from SA
4. Feature flag: `DB_MIGRATION_PHASE >= 2` enables SA-primary auth
5. Monitor for 2 weeks in production with dual-read logging

**Rollback:** Set `DB_MIGRATION_PHASE=1` to revert to legacy-primary.

### Phase 3: Remove Legacy Dependency

**Goal:** Eliminate `web_usuarios.db` entirely.

**Steps:**
1. Remove all `sqlite3` usage from `web/auth.py`
2. Remove `_conn()`, `_db_path()` functions
3. Update `init_auth()` to use SA engine exclusively
4. Remove `web_usuarios.db` creation logic
5. Add migration script: `scripts/migrate_legacy_users.py`
   - One-time import of any users only in legacy DB into SA
6. Remove the `web_usuarios.db` file from data directory
7. Update `init_auth()`, `register_user()`, `authenticate()`, `get_user_by_id()` to use only SA

**Rollback:** Restore `web/auth.py` from git, re-run sync to populate legacy DB.

## Timeline Estimate

| Phase | Duration | Risk |
|-------|----------|------|
| Phase 1 | 1 sprint | Low — read-only verification |
| Phase 2 | 2 sprints | Medium — auth is critical path |
| Phase 3 | 1 sprint | Low — after Phase 2 is stable |

## Success Criteria

- Zero user-facing auth failures during migration
- All users accessible via SA models
- `web_usuarios.db` file no longer needed
- Single source of truth for user data
- Alembic manages all schema changes

## Files Affected

| File | Phase | Change |
|------|-------|--------|
| `web/auth.py` | 2, 3 | Refactor to use SA |
| `web/database/models.py` | 2 | Add `AuthToken` model |
| `web/database/engine.py` | 2 | Ensure auth tables in SA |
| `web/auth_deps.py` | 2 | Update token validation |
| `config/feature_flags.py` | 2 | Already has `DB_MIGRATION_PHASE` |
| `scripts/verify_db_sync.py` | 1 | New file |
| `scripts/migrate_legacy_users.py` | 3 | New file |
