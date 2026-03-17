/**
 * dashboard.js — Lógica del Dashboard Principal.
 *
 * Carga en paralelo: estadísticas (KPIs) + lista de clientes.
 * Renderiza cards de KPI, tabla de clientes y buscador en tiempo real.
 */

const state = {
  clientes: [],
  stats: {},
  filtro: '',
};

/* ── Inicialización ──────────────────────────────────────────────────────── */
async function init() {
  setLoading(true, 'Cargando dashboard...');
  try {
    const [clientesResp, statsResp] = await Promise.all([
      API.getClientes(),
      API.getEstadisticas(),
    ]);
    state.clientes = clientesResp.clientes || [];
    state.stats = statsResp || {};
    renderKPIs(state.stats);
    renderTabla(state.clientes);
  } catch (err) {
    showToast(err.message, 'error');
    renderKPIs({});
    renderTabla([]);
  } finally {
    setLoading(false);
  }
}

/* ── KPI Cards ───────────────────────────────────────────────────────────── */
function renderKPIs(stats) {
  const total        = stats.total_clientes     ?? state.clientes.length;
  const nuevos       = stats.clientes_nuevos    ?? 0;
  const planes       = stats.planes_periodo     ?? 0;
  const kcal         = stats.promedio_kcal      ?? 0;
  const retencion    = stats.tasa_retencion     ?? 0;

  const kpis = [
    {
      label: 'Clientes Activos',
      value: fmt.number(total),
      sub: `+${nuevos} este mes`,
      subColor: 'text-green-600',
      icon: `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
      iconBg: 'bg-blue-50 text-blue-600',
    },
    {
      label: 'Planes Generados',
      value: fmt.number(planes),
      sub: 'últimos 30 días',
      subColor: 'text-gray-400',
      icon: `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
      iconBg: 'bg-orange-50 text-orange-500',
    },
    {
      label: 'Promedio Kcal',
      value: kcal ? fmt.number(kcal, 0) + ' kcal' : '—',
      sub: 'objetivo promedio',
      subColor: 'text-gray-400',
      icon: `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
      iconBg: 'bg-green-50 text-green-600',
    },
    {
      label: 'Retención',
      value: retencion ? retencion + '%' : '—',
      sub: 'clientes activos / total',
      subColor: retencion >= 60 ? 'text-green-600' : 'text-orange-500',
      icon: `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>`,
      iconBg: 'bg-purple-50 text-purple-600',
    },
  ];

  const container = document.getElementById('kpi-cards');
  if (!container) return;
  container.innerHTML = kpis.map(k => `
    <div class="kpi-card">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;">
        <div>
          <p style="font-size:0.8125rem;font-weight:600;color:#6B7280;">${k.label}</p>
          <p style="font-size:1.875rem;font-weight:700;color:#111827;margin-top:0.375rem;
                     font-variant-numeric:tabular-nums;">${k.value}</p>
          <p style="font-size:0.75rem;margin-top:0.25rem;" class="${k.subColor}">${k.sub}</p>
        </div>
        <div class="${k.iconBg}" style="padding:0.625rem;border-radius:0.625rem;">${k.icon}</div>
      </div>
    </div>
  `).join('');
}

/* ── Tabla de clientes ──────────────────────────────────────────────────── */
function renderTabla(clientes) {
  const tbody = document.getElementById('tabla-body');
  if (!tbody) return;

  const empty = document.getElementById('tabla-empty');

  if (!clientes || clientes.length === 0) {
    tbody.innerHTML = '';
    if (empty) empty.style.display = 'flex';
    return;
  }
  if (empty) empty.style.display = 'none';

  tbody.innerHTML = clientes.map(c => `
    <tr>
      <td>
        <div style="font-weight:600;color:#111827;">${c.nombre || '—'}</div>
        <div style="font-size:0.75rem;color:#6B7280;">${c.telefono || c.email || c.id_cliente}</div>
      </td>
      <td style="color:#6B7280;">${c.edad ? c.edad + ' años' : '—'}</td>
      <td>${fmt.badgeObjetivo(c.objetivo)}</td>
      <td style="color:#6B7280;">${fmt.nivel(c.nivel_actividad)}</td>
      <td style="font-variant-numeric:tabular-nums;color:#6B7280;">${c.total_planes_generados ?? 0}</td>
      <td style="color:#6B7280;">${fmt.relativeDate(c.ultimo_plan)}</td>
      <td>
        <div style="display:flex;gap:0.5rem;">
          <a href="/generar-plan/${c.id_cliente}"
             style="font-size:0.8125rem;font-weight:600;color:#FF6B35;text-decoration:none;
                    padding:0.3rem 0.75rem;border:1.5px solid #FF6B35;border-radius:0.375rem;
                    transition:all 0.15s ease;"
             onmouseover="this.style.background='#FF6B35';this.style.color='white'"
             onmouseout="this.style.background='';this.style.color='#FF6B35'">
            Generar Plan
          </a>
          <button onclick="eliminarCliente('${c.id_cliente}','${(c.nombre||'').replace(/'/g,"\\'")}'); event.stopPropagation();"
                  style="font-size:0.8125rem;color:#9CA3AF;border:none;background:none;
                         cursor:pointer;padding:0.3rem 0.5rem;border-radius:0.375rem;transition:color 0.15s;"
                  onmouseover="this.style.color='#EF4444'"
                  onmouseout="this.style.color='#9CA3AF'"
                  title="Desactivar cliente">
            ✕
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

/* ── Buscador ────────────────────────────────────────────────────────────── */
function aplicarFiltro(q) {
  state.filtro = q.toLowerCase();
  const filtrados = state.clientes.filter(c => {
    const hay = [c.nombre, c.telefono, c.email, c.id_cliente]
      .filter(Boolean).join(' ').toLowerCase();
    return hay.includes(state.filtro);
  });
  renderTabla(filtrados);
}

let _searchDebounce;
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('search-input');
  if (input) {
    input.addEventListener('input', e => {
      clearTimeout(_searchDebounce);
      _searchDebounce = setTimeout(() => aplicarFiltro(e.target.value), 300);
    });
  }
});

/* ── Eliminar (soft delete) ──────────────────────────────────────────────── */
async function eliminarCliente(id, nombre) {
  if (!confirm(`¿Desactivar a "${nombre}"?\n\nSus datos y planes se conservan,\nsolo dejará de aparecer en la lista.`)) return;
  try {
    await API.delete(`/clientes/${id}`);
    showToast(`"${nombre}" desactivado`, 'success');
    state.clientes = state.clientes.filter(c => c.id_cliente !== id);
    renderTabla(state.clientes);
    // Actualizar el KPI de total
    state.stats.total_clientes = (state.stats.total_clientes || 1) - 1;
    renderKPIs(state.stats);
  } catch (err) {
    showToast(`Error al desactivar: ${err.message}`, 'error');
  }
}

/* ── Arranque ────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', init);
