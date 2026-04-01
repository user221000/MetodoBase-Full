"""
web.routes — Web-specific API routes with multi-tenant isolation.

Available routers:
- auth: Authentication endpoints (login, registro, refresh, logout, me)
- clientes: CRUD de clientes (filtrado por gym_id)
- planes: Generación y gestión de planes nutricionales
- stats: Estadísticas y métricas del gym
- billing: Stripe payments y webhooks
- gym_profile: Perfil del gimnasio (branding, etc.)
- team: Gestión de equipos RBAC (invitar, roles, etc.)
- pages: HTML page routes (template rendering)
"""
from . import auth, clientes, planes, stats, billing, gym_profile, team, pages

__all__ = ["auth", "clientes", "planes", "stats", "billing", "gym_profile", "team", "pages"]
