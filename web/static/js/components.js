/**
 * MetodoBase Web — Componentes reutilizables
 * Toast notifications y utilidades de UI.
 */

// ============================================================================
// TOAST NOTIFICATIONS
// ============================================================================

/**
 * Muestra una notificación toast.
 * @param {string} mensaje  - Texto a mostrar
 * @param {'success'|'error'|'info'} tipo - Tipo de toast
 * @param {number} duracion - Milisegundos antes de desaparecer (default 3500)
 */
function mostrarToast(mensaje, tipo = 'info', duracion = 3500) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const iconos = { success: '✅', error: '❌', info: 'ℹ️' };

    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo} fade-in`;
    toast.innerHTML = `
        <span class="text-base flex-shrink-0">${iconos[tipo] || 'ℹ️'}</span>
        <span>${mensaje}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, duracion);
}

// ============================================================================
// MODAL GENÉRICO
// ============================================================================

/**
 * Abre un modal por su ID.
 * @param {string} modalId
 */
function abrirModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }
}

/**
 * Cierra un modal por su ID.
 * @param {string} modalId
 */
function cerrarModalPorId(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }
}

// ============================================================================
// ESTADO DE CARGA EN BOTONES
// ============================================================================

/**
 * Activa el estado de carga en un botón.
 * @param {HTMLElement} btn
 */
function setBtnLoading(btn) {
    btn.disabled = true;
    btn._originalText = btn.innerHTML;
    btn.classList.add('btn-loading');
}

/**
 * Desactiva el estado de carga en un botón.
 * @param {HTMLElement} btn
 */
function setBtnReady(btn) {
    btn.disabled = false;
    btn.classList.remove('btn-loading');
    if (btn._originalText) btn.innerHTML = btn._originalText;
}

// ============================================================================
// FORMATO DE FECHAS
// ============================================================================

/**
 * Formatea una fecha ISO a formato legible en español.
 * @param {string} isoStr
 * @returns {string}
 */
function formatearFecha(isoStr) {
    if (!isoStr) return '—';
    try {
        return new Date(isoStr).toLocaleDateString('es-MX', {
            year: 'numeric', month: 'short', day: 'numeric',
        });
    } catch (_) {
        return isoStr;
    }
}

// Exportar para uso global en las páginas
window.mostrarToast      = mostrarToast;
window.abrirModal        = abrirModal;
window.cerrarModalPorId  = cerrarModalPorId;
window.setBtnLoading     = setBtnLoading;
window.setBtnReady       = setBtnReady;
window.formatearFecha    = formatearFecha;
