/**
 * clientes.js — Wizard 3 pasos para crear un nuevo cliente.
 *
 * Paso 1: Datos personales (nombre, teléfono, email, edad, sexo)
 * Paso 2: Antropometría (peso, estatura, % grasa)
 * Paso 3: Objetivos (nivel actividad, objetivo, notas)
 *
 * Validación: doble capa — HTML5 + JS antes de cada avance.
 * Submit: POST /api/clientes → redirección a /generar-plan/{id}
 */

const wizardState = {
  currentStep: 1,
  totalSteps: 3,
  data: {},
};

/* ── Navegación del wizard ───────────────────────────────────────────────── */
function goToStep(n) {
  // Validar el paso actual antes de avanzar
  if (n > wizardState.currentStep) {
    if (!validarPasoActual()) return;
  }

  // Ocultar el paso actual
  const current = document.getElementById(`step-${wizardState.currentStep}`);
  if (current) current.style.display = 'none';

  // Mostrar el nuevo paso
  wizardState.currentStep = n;
  const next = document.getElementById(`step-${n}`);
  if (next) next.style.display = 'block';

  actualizarIndicadores();
  actualizarBotones();
}

function siguientePaso() {
  if (wizardState.currentStep < wizardState.totalSteps) {
    goToStep(wizardState.currentStep + 1);
  }
}

function pasoAnterior() {
  if (wizardState.currentStep > 1) {
    goToStep(wizardState.currentStep - 1);
  }
}

function actualizarIndicadores() {
  for (let i = 1; i <= wizardState.totalSteps; i++) {
    const circle = document.getElementById(`circle-${i}`);
    const label  = document.getElementById(`label-${i}`);
    if (!circle) continue;

    if (i < wizardState.currentStep) {
      circle.className = 'step-indicator done';
      circle.textContent = '✓';
    } else if (i === wizardState.currentStep) {
      circle.className = 'step-indicator active';
      circle.textContent = i;
    } else {
      circle.className = 'step-indicator pending';
      circle.textContent = i;
    }

    if (label) {
      label.style.fontWeight = i === wizardState.currentStep ? '700' : '400';
      label.style.color = i === wizardState.currentStep ? '#004E89' : '#9CA3AF';
    }

    // Línea conectora
    const line = document.getElementById(`line-${i}`);
    if (line) {
      line.style.background = i < wizardState.currentStep ? '#10B981' : '#E5E7EB';
    }
  }
}

function actualizarBotones() {
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const btnSubmit = document.getElementById('btn-submit');

  if (btnPrev) btnPrev.style.display = wizardState.currentStep === 1 ? 'none' : 'inline-flex';
  if (btnNext) btnNext.style.display = wizardState.currentStep === wizardState.totalSteps ? 'none' : 'inline-flex';
  if (btnSubmit) btnSubmit.style.display = wizardState.currentStep === wizardState.totalSteps ? 'inline-flex' : 'none';
}

/* ── Validación por paso ─────────────────────────────────────────────────── */
function validarPasoActual() {
  const step = wizardState.currentStep;
  let ok = true;

  // Limpiar errores previos
  document.querySelectorAll(`#step-${step} .field-error`).forEach(el => el.classList.remove('visible'));
  document.querySelectorAll(`#step-${step} .input-field`).forEach(el => el.classList.remove('error'));

  function showError(fieldId, msg) {
    const field = document.getElementById(fieldId);
    const errEl = document.getElementById(`${fieldId}-error`);
    if (field) field.classList.add('error');
    if (errEl) { errEl.textContent = msg; errEl.classList.add('visible'); }
    ok = false;
  }

  if (step === 1) {
    const nombre = document.getElementById('nombre')?.value.trim() || '';
    if (nombre.length < 2) showError('nombre', 'El nombre debe tener al menos 2 caracteres');

    const edad = parseInt(document.getElementById('edad')?.value || '');
    if (isNaN(edad) || edad < 15 || edad > 80)
      showError('edad', 'Edad debe estar entre 15 y 80 años');

    const tel = document.getElementById('telefono')?.value.replace(/\D/g, '') || '';
    if (tel && tel.length !== 10)
      showError('telefono', 'El teléfono debe tener 10 dígitos');

    const email = document.getElementById('email')?.value.trim() || '';
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      showError('email', 'Correo electrónico inválido');
  }

  if (step === 2) {
    const peso = parseFloat(document.getElementById('peso_kg')?.value || '');
    if (isNaN(peso) || peso < 40 || peso > 200)
      showError('peso_kg', 'Peso debe estar entre 40 y 200 kg');

    const estatura = parseFloat(document.getElementById('estatura_cm')?.value || '');
    if (isNaN(estatura) || estatura < 140 || estatura > 220)
      showError('estatura_cm', 'Estatura debe estar entre 140 y 220 cm');

    const grasa = document.getElementById('grasa_corporal_pct')?.value;
    if (grasa !== '' && grasa != null) {
      const g = parseFloat(grasa);
      if (!isNaN(g) && (g < 5 || g > 60))
        showError('grasa_corporal_pct', '% grasa debe estar entre 5 y 60');
    }
  }

  if (step === 3) {
    const nivel = document.getElementById('nivel_actividad')?.value || '';
    if (!['nula','leve','moderada','intensa'].includes(nivel))
      showError('nivel_actividad', 'Selecciona un nivel de actividad');

    const objetivo = document.getElementById('objetivo')?.value || '';
    if (!['deficit','mantenimiento','superavit'].includes(objetivo))
      showError('objetivo', 'Selecciona un objetivo');
  }

  return ok;
}

/* ── Recolección de datos del formulario ─────────────────────────────────── */
function recolectarDatos() {
  const get = id => document.getElementById(id)?.value.trim() || null;
  const getNum = id => {
    const v = document.getElementById(id)?.value;
    return v !== '' && v != null ? parseFloat(v) : null;
  };
  const getForcedNum = id => {
    const v = document.getElementById(id)?.value;
    return v !== '' && v != null ? parseFloat(v) : undefined;
  };

  return {
    nombre:             get('nombre'),
    telefono:           get('telefono') || null,
    email:              get('email') || null,
    edad:               parseInt(document.getElementById('edad')?.value),
    sexo:               get('sexo') || null,
    peso_kg:            getNum('peso_kg'),
    estatura_cm:        getNum('estatura_cm'),
    grasa_corporal_pct: getNum('grasa_corporal_pct') || null,
    nivel_actividad:    get('nivel_actividad'),
    objetivo:           get('objetivo'),
    notas:              get('notas') || null,
  };
}

/* ── Submit ──────────────────────────────────────────────────────────────── */
async function submitForm() {
  if (!validarPasoActual()) return;

  const btnSubmit = document.getElementById('btn-submit');
  if (btnSubmit) {
    btnSubmit.disabled = true;
    btnSubmit.textContent = 'Guardando...';
  }

  setLoading(true, 'Creando cliente y calculando macros...');

  try {
    const data = recolectarDatos();
    const resp = await API.crearCliente(data);

    showToast(`¡Cliente '${data.nombre}' creado correctamente!`, 'success', 2500);
    setLoading(false);

    // Pequeña pausa para que el usuario vea el toast, luego redirige
    setTimeout(() => {
      window.location.href = `/generar-plan/${resp.id_cliente}`;
    }, 1200);

  } catch (err) {
    setLoading(false);
    showToast(`Error: ${err.message}`, 'error');
    if (btnSubmit) {
      btnSubmit.disabled = false;
      btnSubmit.textContent = 'Crear Cliente y Generar Plan';
    }
  }
}

/* ── Inicialización ──────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Mostrar solo el primer paso
  for (let i = 2; i <= wizardState.totalSteps; i++) {
    const el = document.getElementById(`step-${i}`);
    if (el) el.style.display = 'none';
  }

  actualizarIndicadores();
  actualizarBotones();

  // Btn listeners
  document.getElementById('btn-next')?.addEventListener('click', siguientePaso);
  document.getElementById('btn-prev')?.addEventListener('click', pasoAnterior);
  document.getElementById('btn-submit')?.addEventListener('click', submitForm);

  // Permitir navegar con Enter entre campos de texto en los inputs
  document.querySelectorAll('.input-field').forEach(input => {
    input.addEventListener('input', () => {
      input.classList.remove('error');
      const errEl = document.getElementById(`${input.id}-error`);
      if (errEl) errEl.classList.remove('visible');
    });
  });
});
