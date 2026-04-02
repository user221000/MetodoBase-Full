/**
 * auth-guard.js — Auth + interface isolation guard.
 * - Unauthenticated users → /
 * - tipo='usuario' on gym-only pages → /mi-plan
 * - tipo='gym' on user-only pages → /dashboard
 * Uses window.location.replace() to prevent back-button loops.
 */
(function() {
  var path = window.location.pathname;
  var authPages = ['/', '/login-gym', '/login-usuario', '/registro'];
  if (authPages.some(function(p) { return path === p; })) return;

  var token = localStorage.getItem('mb_token');
  if (!token) {
    window.location.replace('/');
    return;
  }

  var tipo = localStorage.getItem('mb_tipo');

  var gymPages = ['/dashboard', '/clientes', '/planes', '/suscripciones', '/configuracion', '/generar-plan'];
  var userPages = ['/mi-plan', '/mi-perfil', '/mi-historial', '/mi-suscripcion'];

  if (tipo === 'usuario' && gymPages.some(function(p) { return path === p || path.startsWith(p + '/'); })) {
    window.location.replace('/mi-plan');
    return;
  }

  if (tipo === 'gym' && userPages.some(function(p) { return path === p || path.startsWith(p + '/'); })) {
    window.location.replace('/dashboard');
    return;
  }
})();
