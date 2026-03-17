/**
 * plan.js — Generador de Plan Nutricional.
 *
 * Lee el id_cliente de la URL (/generar-plan/{id}), carga datos del cliente,
 * y orquesta la generación del plan nutricional vía POST /api/generar-plan.
 */

const planState = {
  clienteId: null,
  cliente: null,
  resultado: null,
  planNumero: 1,
};

/* ── Leer ID del cliente desde la URL ────────────────────────────────────── */
function getClienteIdFromURL() {
  const parts = window.location.pathname.split('/');
  return parts[parts.length - 1] || null;
}

/* ── Cargar datos del cliente ────────────────────────────────────────────── */
async function cargarCliente(id) {
  try {
    const data = await API.getCliente(id);
    planState.cliente = data;
    renderClienteCard(data);

    // Obtener historial de planes para número de rotación
    const historial = await API.get(`/clientes/${id}`);
    planState.planNumero = (data.total_planes_generados || 0) + 1;

    document.getElementById('section-config').style.display = 'block';
  } catch (err) {
    showToast(`Error cargando cliente: ${err.message}`, 'error');
    document.getElementById('section-error').style.display = 'flex';
  }
}

/* ── Render: card del cliente ────────────────────────────────────────────── */
function renderClienteCard(c) {
  const grasa = c.grasa_corporal_pct ? `${c.grasa_corporal_pct}%` : '—';
  const imc = c.peso_kg && c.estatura_cm
    ? (c.peso_kg / Math.pow(c.estatura_cm / 100, 2)).toFixed(1)
    : '—';

  const card = document.getElementById('cliente-card');
  if (!card) return;

  card.innerHTML = `
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.25rem;">
      <div style="width:3rem;height:3rem;border-radius:9999px;background:#004E89;
                  display:flex;align-items:center;justify-content:center;
                  color:white;font-size:1.25rem;font-weight:700;flex-shrink:0;">
        ${(c.nombre || '?').charAt(0).toUpperCase()}
      </div>
      <div>
        <h3 style="font-family:'Poppins',sans-serif;font-weight:700;font-size:1.1rem;
                    color:#111827;">${c.nombre || '—'}</h3>
        <p style="font-size:0.8125rem;color:#6B7280;">${c.edad ? c.edad + ' años' : ''} · ${c.telefono || c.email || c.id_cliente}</p>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1rem;">
      ${metricItem('Peso', c.peso_kg ? c.peso_kg + ' kg' : '—')}
      ${metricItem('Estatura', c.estatura_cm ? c.estatura_cm + ' cm' : '—')}
      ${metricItem('% Grasa', grasa)}
      ${metricItem('IMC', imc)}
      ${metricItem('Actividad', fmt.nivel(c.nivel_actividad))}
      ${metricItem('Objetivo', fmt.objetivo(c.objetivo))}
    </div>
    <div style="padding-top:0.75rem;border-top:1px solid #F3F4F6;display:flex;align-items:center;gap:0.75rem;">
      ${c.objetivo ? `<span class="badge badge-${c.objetivo}">${fmt.objetivo(c.objetivo)}</span>` : ''}
      <span style="font-size:0.75rem;color:#9CA3AF;">Plan #${planState.planNumero} en rotación</span>
    </div>
  `;
}

function metricItem(label, value) {
  return `
    <div style="background:#F9FAFB;border-radius:0.5rem;padding:0.625rem;">
      <p style="font-size:0.7rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;
                letter-spacing:0.05em;">${label}</p>
      <p style="font-weight:700;color:#111827;font-size:0.9rem;margin-top:0.125rem;">${value}</p>
    </div>
  `;
}

/* ── Generar plan ────────────────────────────────────────────────────────── */
async function generarPlan() {
  const btnGenerar = document.getElementById('btn-generar');
  if (btnGenerar) btnGenerar.disabled = true;

  // Mostrar sección de loading
  document.getElementById('section-config').style.display = 'none';
  document.getElementById('section-loading').style.display = 'flex';
  document.getElementById('section-resultado').style.display = 'none';

  try {
    const resp = await API.generarPlan(planState.clienteId, planState.planNumero);
    planState.resultado = resp;
    renderResultado(resp);
    showToast('¡Plan nutricional generado exitosamente!', 'success');
  } catch (err) {
    document.getElementById('section-config').style.display = 'block';
    if (btnGenerar) btnGenerar.disabled = false;
    showToast(`Error: ${err.message}`, 'error');
  } finally {
    document.getElementById('section-loading').style.display = 'none';
  }
}

/* ── Render: resultados del plan ─────────────────────────────────────────── */
function renderResultado(resp) {
  const macros = resp.macros || {};
  const plan   = resp.plan   || {};

  document.getElementById('section-resultado').style.display = 'block';

  // ── Macro summary
  const kcalObj  = macros.kcal_objetivo || 0;
  const kcalReal = macros.kcal_real     || 0;
  const prot     = macros.proteina_g    || 0;
  const carbs    = macros.carbs_g       || 0;
  const grasa    = macros.grasa_g       || 0;

  const pPct = fmt.macroPercent(prot, kcalReal, 4);
  const cPct = fmt.macroPercent(carbs, kcalReal, 4);
  const gPct = fmt.macroPercent(grasa, kcalReal, 9);

  const macroEl = document.getElementById('macros-summary');
  if (macroEl) macroEl.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.5rem;">
      ${macroCard('TMB', fmt.number(macros.tmb, 0), 'kcal', '#004E89')}
      ${macroCard('GET Total', fmt.number(macros.get_total, 0), 'kcal', '#FF6B35')}
      ${macroCard('Objetivo', fmt.number(kcalObj, 0), 'kcal', '#10B981')}
    </div>
    <div style="background:#F9FAFB;border-radius:0.75rem;padding:1.25rem;">
      <p style="font-size:0.8125rem;font-weight:600;color:#374151;margin-bottom:1rem;">
        Distribución de Macronutrientes
        <span style="font-weight:400;color:#9CA3AF;margin-left:0.5rem;">
          ${fmt.number(kcalReal, 0)} kcal reales
        </span>
      </p>
      ${macroBar('Proteína', prot, 'g', pPct, '#004E89')}
      ${macroBar('Carbohidratos', carbs, 'g', cPct, '#FF6B35')}
      ${macroBar('Grasas', grasa, 'g', gPct, '#10B981')}
    </div>
  `;

  // ── Desglose por comidas
  const comidasEl = document.getElementById('comidas-detail');
  if (comidasEl) {
    const comidas = ['desayuno', 'almuerzo', 'comida', 'cena'];
    const nombres = { desayuno: 'Desayuno', almuerzo: 'Almuerzo', comida: 'Comida', cena: 'Cena' };
    const iconos  = { desayuno: '🌅', almuerzo: '🥗', comida: '🍽️', cena: '🌙' };

    comidasEl.innerHTML = comidas.filter(c => plan[c]).map(c => {
      const comida = plan[c];
      const kcalR = comida.kcal_real || 0;
      const kcalO = comida.kcal_objetivo || 0;
      const desv = kcalO ? Math.abs(((kcalR - kcalO) / kcalO) * 100).toFixed(1) : 0;

      const alimentos = Object.entries(comida.alimentos || {})
        .sort(([, a], [, b]) => b - a)
        .map(([nombre, gramos]) =>
          `<div style="display:flex;justify-content:space-between;padding:0.25rem 0;
                       font-size:0.8125rem;border-bottom:1px solid #F3F4F6;">
             <span style="color:#374151;">${nombre.replace(/_/g, ' ')}</span>
             <span style="color:#6B7280;font-variant-numeric:tabular-nums;">${gramos} g</span>
           </div>`
        ).join('');

      return `
        <div class="card" style="padding:1.25rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
            <h4 style="font-family:'Poppins',sans-serif;font-weight:600;color:#111827;">
              ${iconos[c]} ${nombres[c]}
            </h4>
            <div style="text-align:right;">
              <span style="font-size:1rem;font-weight:700;color:#111827;">
                ${fmt.number(kcalR, 0)} kcal
              </span>
              <span style="font-size:0.75rem;color:#9CA3AF;margin-left:0.375rem;">
                (${desv}% desv.)
              </span>
            </div>
          </div>
          ${alimentos || '<p style="font-size:0.8125rem;color:#9CA3AF;">Sin alimentos registrados</p>'}
        </div>
      `;
    }).join('');
  }

  // ── Botón descarga PDF
  const btnPdf = document.getElementById('btn-download-pdf');
  if (btnPdf) {
    btnPdf.href = API.descargarPdfUrl(planState.clienteId);
    btnPdf.style.display = 'inline-flex';
  }

  // ── Botón "Generar otro"
  const btnOtro = document.getElementById('btn-generar-otro');
  if (btnOtro) btnOtro.style.display = 'inline-flex';
}

function macroCard(label, value, unit, color) {
  return `
    <div style="background:white;border-radius:0.625rem;padding:1rem;
                border-left:4px solid ${color};box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <p style="font-size:0.75rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;
                letter-spacing:0.05em;">${label}</p>
      <p style="font-size:1.5rem;font-weight:700;color:#111827;font-variant-numeric:tabular-nums;">
        ${value}<span style="font-size:0.875rem;color:#9CA3AF;margin-left:0.25rem;">${unit}</span>
      </p>
    </div>
  `;
}

function macroBar(label, value, unit, pct, color) {
  return `
    <div style="margin-bottom:0.875rem;">
      <div style="display:flex;justify-content:space-between;margin-bottom:0.375rem;">
        <span style="font-size:0.8125rem;font-weight:600;color:#374151;">${label}</span>
        <span style="font-size:0.8125rem;color:#6B7280;font-variant-numeric:tabular-nums;">
          ${fmt.number(value, 1)} ${unit}
          <span style="color:#9CA3AF;margin-left:0.25rem;">(${pct}%)</span>
        </span>
      </div>
      <div style="background:#E5E7EB;border-radius:9999px;height:6px;overflow:hidden;">
        <div class="macro-bar-fill" style="background:${color};width:${Math.min(pct,100)}%;"></div>
      </div>
    </div>
  `;
}

/* ── "Generar otro plan" ─────────────────────────────────────────────────── */
function generarOtro() {
  planState.planNumero += 1;
  document.getElementById('section-resultado').style.display = 'none';
  document.getElementById('section-config').style.display = 'block';

  const btnGenerar = document.getElementById('btn-generar');
  if (btnGenerar) {
    btnGenerar.disabled = false;
    btnGenerar.textContent = `Generar Plan #${planState.planNumero}`;
  }
}

/* ── Inicialización ──────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  planState.clienteId = getClienteIdFromURL();

  if (!planState.clienteId) {
    showToast('ID de cliente no encontrado en la URL', 'error');
    document.getElementById('section-error').style.display = 'flex';
    return;
  }

  document.getElementById('section-loading-cliente').style.display = 'flex';
  await cargarCliente(planState.clienteId);
  document.getElementById('section-loading-cliente').style.display = 'none';

  // Botón generar
  document.getElementById('btn-generar')?.addEventListener('click', generarPlan);

  // Botón generar otro
  document.getElementById('btn-generar-otro')?.addEventListener('click', generarOtro);
});
