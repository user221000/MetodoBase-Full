/**
 * MetodoBase Web — JavaScript principal
 * Inicialización global y utilidades compartidas.
 */

// ============================================================================
// RESALTAR LINK ACTIVO EN NAVBAR
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    document.querySelectorAll('nav a.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === path || (href !== '/' && path.startsWith(href))) {
            link.classList.add('bg-white/20');
        }
    });
});
