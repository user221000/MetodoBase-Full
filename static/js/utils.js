/**
 * utils.js — Helpers compartidos entre todas las páginas de MetodoBase.
 *
 * Expone globalmente:
 *   API        — fetch helpers con manejo de errores centralizado
 *   showToast  — notificaciones flotantes
 *   setLoading — overlay de carga global
 *   fmt        — formateadores de texto/números
 */

/* ── API ─────────────────────────────────────────────────────────────────── */
const API = {
  baseURL: '/api',

  async request(method, endpoint, body = null) {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body !== null) {
      options.body = JSON.stringify(body);
    }

    let resp;
    try {
      resp = await fetch(`${this.baseURL}${endpoint}`, options);
    } catch (networkErr) {
      throw new Error('Sin conexión con el servidor. ¿Está corriendo api_server.py?');
    }

    if (!resp.ok) {
      let detail = `Error ${resp.status}`;
      try {
        const json = await resp.json();
        detail = json.detail || json.message || detail;
        // Pydantic validation errors (HTTP 422) come as list
        if (Array.isArray(json.detail)) {
          detail = json.detail.map(e => e.msg || e.message || JSON.stringify(e)).join('; ');
        }
      } catch (_) { /* ignore */ }
      throw new Error(detail);
    }

    return resp.json();
  },

  get:    (ep)       => API.request('GET',    ep),
  post:   (ep, body) => API.request('POST',   ep, body),
  put:    (ep, body) => API.request('PUT',    ep, body),
  delete: (ep)       => API.request('DELETE', ep),

  // Shortcuts
  getClientes:       (q = '', limite = 100) => API.get(`/clientes?q=${encodeURIComponent(q)}&limite=${limite}`),
  getCliente:        (id)                   => API.get(`/clientes/${id}`),
  crearCliente:      (data)                 => API.post('/clientes', data),
  actualizarCliente: (id, data)             => API.put(`/clientes/${id}`, data),
  getEstadisticas:   ()                     => API.get('/estadisticas'),
  generarPlan:       (id, num = 1)          => API.post('/generar-plan', { id_cliente: id, plan_numero: num }),
  descargarPdfUrl:   (id)                   => `${API.baseURL}/descargar-pdf/${id}`,
};

/* ── Toast ───────────────────────────────────────────────────────────────── */
function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText =
      'position:fixed;top:1rem;right:1rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem;';
    document.body.appendChild(container);
  }

  const icons = {
    success: '✓',
    error:   '✕',
    info:    'ℹ',
    warning: '⚠',
  };

  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span style="font-size:1rem">${icons[type] || '•'}</span><span>${message}</span>`;
  container.appendChild(el);

  setTimeout(() => {
    el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    el.style.opacity = '0';
    el.style.transform = 'translateX(100%)';
    setTimeout(() => el.remove(), 300);
  }, duration);
}

/* ── Loading overlay ─────────────────────────────────────────────────────── */
function setLoading(show, message = 'Cargando...') {
  let overlay = document.getElementById('loading-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.style.cssText =
      'position:fixed;inset:0;background:rgba(0,0,0,0.45);display:flex;' +
      'align-items:center;justify-content:center;z-index:8888;';
    overlay.innerHTML = `
      <div style="background:white;padding:2rem;border-radius:1rem;
                  display:flex;flex-direction:column;align-items:center;gap:1rem;min-width:200px;">
        <div class="spinner"></div>
        <p id="loading-msg" style="font-size:0.875rem;color:#4B5563;font-weight:500;">${message}</p>
      </div>`;
    document.body.appendChild(overlay);
  }
  const msg = overlay.querySelector('#loading-msg');
  if (msg) msg.textContent = message;
  overlay.style.display = show ? 'flex' : 'none';
}

/* ── Formateadores ───────────────────────────────────────────────────────── */
const fmt = {
  number(n, decimals = 0) {
    if (n == null) return '—';
    return Number(n).toLocaleString('es-MX', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  },

  date(dateStr) {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleDateString('es-MX', {
        year: 'numeric', month: 'short', day: 'numeric',
      });
    } catch (_) { return dateStr; }
  },

  relativeDate(dateStr) {
    if (!dateStr) return 'Sin actividad';
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return 'Hoy';
    if (days === 1) return 'Ayer';
    if (days < 7) return `Hace ${days} días`;
    if (days < 30) return `Hace ${Math.floor(days / 7)} sem.`;
    return fmt.date(dateStr);
  },

  objetivo(val) {
    const map = { deficit: 'Déficit', mantenimiento: 'Mantenimiento', superavit: 'Superávit' };
    return map[val] || (val ? val.charAt(0).toUpperCase() + val.slice(1) : '—');
  },

  nivel(val) {
    const map = { nula: 'Sedentario', leve: 'Leve', moderada: 'Moderada', intensa: 'Intensa' };
    return map[val] || (val || '—');
  },

  badgeObjetivo(val) {
    const cls = { deficit: 'badge-deficit', mantenimiento: 'badge-mantenimiento', superavit: 'badge-superavit' };
    return `<span class="badge ${cls[val] || ''}">${fmt.objetivo(val)}</span>`;
  },

  macroPercent(gramos, kcalTotal, calsPerGram) {
    if (!kcalTotal) return 0;
    return Math.round((gramos * calsPerGram / kcalTotal) * 100);
  },
};

/* ── Navegación del sidebar (marca enlace activo) ────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    const isActive =
      (href === '/' && path === '/') ||
      (href !== '/' && path.startsWith(href));
    link.classList.toggle('active', isActive);
  });
});
