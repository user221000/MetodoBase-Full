/**
 * MetodoBase Web — Cliente API
 * Funciones para consumir los endpoints REST del backend.
 */

const MetodoBaseAPI = (() => {
    const BASE = '';  // Misma origin

    async function _request(path, options = {}) {
        const res = await fetch(BASE + path, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options,
        });

        if (!res.ok) {
            let detalle = `HTTP ${res.status}`;
            try {
                const err = await res.json();
                detalle = err.detail
                    ? (typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail))
                    : detalle;
            } catch (_) {}
            throw new Error(detalle);
        }

        // 204 No Content
        if (res.status === 204) return null;
        return res.json();
    }

    return {
        // ---- Estadísticas ----
        obtenerEstadisticas() {
            return _request('/api/estadisticas');
        },

        // ---- Clientes ----
        listarClientes({ buscar = '', solo_activos = true, pagina = 1, por_pagina = 20 } = {}) {
            const params = new URLSearchParams();
            if (buscar)       params.set('buscar', buscar);
            if (!solo_activos) params.set('solo_activos', 'false');
            params.set('pagina', pagina);
            params.set('por_pagina', por_pagina);
            return _request(`/api/clientes?${params}`);
        },

        obtenerCliente(id) {
            return _request(`/api/clientes/${encodeURIComponent(id)}`);
        },

        crearCliente(datos) {
            return _request('/api/clientes', {
                method: 'POST',
                body: JSON.stringify(datos),
            });
        },

        actualizarCliente(id, datos) {
            return _request(`/api/clientes/${encodeURIComponent(id)}`, {
                method: 'PUT',
                body: JSON.stringify(datos),
            });
        },

        // ---- Planes ----
        generarPlan(datos) {
            return _request('/api/generar-plan', {
                method: 'POST',
                body: JSON.stringify(datos),
            });
        },

        obtenerPlanesCliente(id) {
            return _request(`/api/planes/${encodeURIComponent(id)}`);
        },
    };
})();
