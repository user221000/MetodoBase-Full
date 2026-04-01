/**
 * buttons.js — Unified button behavior with event delegation
 * MetodoBase v4.0 — Clean architecture pattern
 * 
 * Centraliza todos los event handlers de botones usando delegation
 * para eliminar onclick inline y mejorar separación de concerns.
 */

(function() {
  'use strict';

  // ── Event Handlers ───────────────────────────────────────────────────────
  const handlers = {
    /**
     * Acción: Cerrar sesión
     * Limpia localStorage y redirige a home
     */
    'logout': function(event, button) {
      const token = localStorage.getItem('mb_token');
      
      // Intentar logout en servidor (fire and forget, keepalive para que no se aborte al navegar)
      if (token) {
        fetch('/api/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + token },
          keepalive: true
        }).catch(() => {}); // Ignorar errores, siempre limpiamos local
      }
      
      // Limpiar localStorage
      localStorage.removeItem('mb_token');
      localStorage.removeItem('mb_refresh_token');
      localStorage.removeItem('mb_tipo');
      localStorage.removeItem('mb_nombre');
      localStorage.removeItem('mb_email');
      
      // Redirigir a home
      window.location.href = '/login-gym';
    },

    /**
     * Acción: Cerrar insight card
     * Oculta el card de insights/tips
     */
    'close-insight': function(event, button) {
      const card = button.closest('.insight-card');
      if (card) {
        card.style.display = 'none';
        
        // Opcional: guardar preferencia en localStorage
        localStorage.setItem('mb_insight_dismissed', 'true');
      }
    },

    /**
     * Acción: Toggle password visibility
     * Alterna entre mostrar/ocultar contraseña
     */
    'toggle-password': function(event, button) {
      const inputGroup = button.closest('.input-group') || button.closest('div[style*="position"]')?.parentElement;
      if (!inputGroup) return;
      
      const input = inputGroup.querySelector('input[type="password"], input[type="text"]');
      if (!input) return;
      
      // Toggle type
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      
      // Update icon: use SVG for eye open/closed — preserve existing SVG structure
      const svg = button.querySelector('svg');
      if (svg) {
        // Clear existing paths and set appropriate eye icon
        if (isPassword) {
          // Eye-off icon (password now visible)
          svg.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"/>';
        } else {
          // Eye-open icon (password now hidden)
          svg.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>';
        }
      }
      button.setAttribute('aria-label', isPassword ? 'Ocultar contraseña' : 'Mostrar contraseña');
    },

    /**
     * Acción: Set tipo de usuario (gym/usuario)
     * Para formulario de registro
     */
    'set-tipo': function(event, button) {
      const tipo = button.dataset.tipo;
      if (!tipo) {
        console.warn('[buttons] set-tipo: missing data-tipo attribute');
        return;
      }
      
      // Actualizar campo hidden
      const hiddenInput = document.getElementById('field-tipo') || document.querySelector('input[name="tipo"]');
      if (hiddenInput) {
        hiddenInput.value = tipo;
      }
      
      // Actualizar UI: marcar botón activo
      const allTipoBtns = document.querySelectorAll('[data-action="set-tipo"]');
      allTipoBtns.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
    }
  };

  // ── Central Click Handler (Event Delegation) ─────────────────────────────
  document.addEventListener('DOMContentLoaded', function() {
    // Delegación en body para capturar todos los clicks
    document.body.addEventListener('click', function(event) {
      const button = event.target.closest('[data-action]');
      if (!button) return;

      const action = button.dataset.action;
      
      // Ejecutar handler si existe
      if (handlers[action]) {
        event.preventDefault(); // Prevenir default solo si hay handler
        handlers[action](event, button);
      } else {
        console.warn(`[buttons] No handler defined for action: "${action}"`);
      }
    });

    // Log de inicialización (solo dev)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      console.log('[buttons] Event delegation initialized. Available actions:', Object.keys(handlers));
    }
  });

  // ── Función helper: cerrarSesion (backward compatibility) ────────────────
  // Mantener función global para código legacy que la llame directamente
  window.cerrarSesion = function() {
    handlers.logout(null, null);
  };

  // ── Función helper: togglePassword (backward compatibility) ─────────────
  window.togglePassword = function() {
    // Buscar el botón que debería tener data-action="toggle-password"
    const activeInput = document.activeElement;
    const inputGroup = activeInput?.closest('.input-group');
    const btn = inputGroup?.querySelector('[data-action="toggle-password"]');
    
    if (btn) {
      handlers['toggle-password'](null, btn);
    } else {
      console.warn('[buttons] togglePassword: could not find button with data-action="toggle-password"');
    }
  };

  // ── Función helper: setTipo (backward compatibility) ─────────────────────
  window.setTipo = function(tipo) {
    const btn = document.querySelector(`[data-action="set-tipo"][data-tipo="${tipo}"]`);
    if (btn) {
      handlers['set-tipo'](null, btn);
    } else {
      console.warn(`[buttons] setTipo: could not find button with data-tipo="${tipo}"`);
    }
  };

})();
