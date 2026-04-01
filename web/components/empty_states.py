"""
web/components/empty_states.py — Empty state components for UI

Provides reusable empty state messages when no data exists.

Usage in templates:
    from web.components.empty_states import get_empty_state_html
    
    empty_html = get_empty_state_html("clientes")
"""
from typing import Literal

EmptyStateType = Literal["clientes", "planes", "suscriptores", "facturas", "reportes"]


def get_empty_state_html(state_type: EmptyStateType, custom_message: str = "") -> str:
    """
    Genera HTML para un empty state.
    
    Args:
        state_type: Tipo de empty state
        custom_message: Mensaje personalizado (opcional)
        
    Returns:
        HTML string del empty state
    """
    
    templates = {
        "clientes": {
            "icon": "👥",
            "title": "No hay clientes aún",
            "description": "Comienza agregando tu primer cliente para crear planes nutricionales personalizados.",
            "cta_text": "Agregar Cliente",
            "cta_action": "window.location.href='/clientes?action=new'",
        },
        "planes": {
            "icon": "📋",
            "title": "No hay planes generados",
            "description": "Crea tu primer plan nutricional basado en los objetivos de tus clientes.",
            "cta_text": "Generar Plan",
            "cta_action": "window.location.href='/generar-plan'",
        },
        "suscriptores": {
            "icon": "💳",
            "title": "Sin suscriptores activos",
            "description": "Tus clientes con suscripción mensual aparecerán aquí. Configura pagos recurrentes desde el perfil del cliente.",
            "cta_text": "Ver Clientes",
            "cta_action": "window.location.href='/clientes'",
        },
        "facturas": {
            "icon": "🧾",
            "title": "No hay facturas",
            "description": "Las facturas generadas aparecerán aquí. Activa la facturación en configuración.",
            "cta_text": "Ir a Configuración",
            "cta_action": "window.location.href='/configuracion'",
        },
        "reportes": {
            "icon": "📊",
            "title": "No hay datos suficientes",
            "description": "Los reportes se generan cuando tienes al menos un plan nutricional creado.",
            "cta_text": "Generar Plan",
            "cta_action": "window.location.href='/generar-plan'",
        },
    }
    
    template = templates.get(state_type, templates["clientes"])
    
    # Usar custom_message si se provee
    description = custom_message if custom_message else template["description"]
    
    html = f"""
    <div class="empty-state" style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        text-align: center;
        min-height: 400px;
    ">
        <div class="empty-state-icon" style="
            font-size: 72px;
            margin-bottom: 24px;
            opacity: 0.6;
        ">
            {template["icon"]}
        </div>
        <h3 class="empty-state-title" style="
            font-size: 24px;
            font-weight: 600;
            color: var(--text-primary, #ffffff);
            margin-bottom: 12px;
        ">
            {template["title"]}
        </h3>
        <p class="empty-state-description" style="
            font-size: 16px;
            color: var(--text-secondary, rgba(255, 255, 255, 0.7));
            max-width: 480px;
            line-height: 1.6;
            margin-bottom: 32px;
        ">
            {description}
        </p>
        <button 
            onclick="{template["cta_action"]}"
            class="btn-primary"
            style="
                padding: 12px 32px;
                font-size: 16px;
                font-weight: 500;
                border-radius: 8px;
                border: none;
                cursor: pointer;
                background: linear-gradient(135deg, #FFEB3B 0%, #FFD700 100%);
                color: #1a1a1a;
                transition: transform 0.2s, box-shadow 0.2s;
            "
            onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 24px rgba(255, 235, 59, 0.3)'"
            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'"
        >
            {template["cta_text"]}
        </button>
    </div>
    """
    
    return html


# ── Helper para usar en Jinja2 templates ──────────────────────────────────

def register_empty_state_filter(app):
    """
    Registra el filtro 'empty_state' en Jinja2.
    
    Usage en template:
        {{ "clientes" | empty_state }}
    
    Args:
        app: FastAPI app instance con Jinja2Templates
    """
    try:
        from fastapi.templating import Jinja2Templates
        
        if hasattr(app, 'state') and hasattr(app.state, 'templates'):
            templates: Jinja2Templates = app.state.templates
            templates.env.filters['empty_state'] = get_empty_state_html
    except Exception as e:
        print(f"Warning: Could not register empty_state filter: {e}")
