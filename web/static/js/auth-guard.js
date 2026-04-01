/**
 * auth-guard.js — Redirects unauthenticated users to login.
 * Skips redirect when already on auth pages to prevent loops.
 */
(function() {
  var path = window.location.pathname;
  var authPages = ['/', '/login-gym', '/login-usuario', '/registro'];
  if (authPages.some(function(p) { return path === p; })) return;
  var token = localStorage.getItem('mb_token');
  if (!token) {
    window.location.replace('/');
  }
})();
