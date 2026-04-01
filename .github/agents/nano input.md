nano input.txt


Prepara el sistema completo para una demo real en video hoy (grabación para redes sociales), asegurando que TODO funcione sin errores visibles.

Contexto:

* SaaS para gimnasios (gestión de clientes + planes + PDFs)
* Stack: React + Node + JWT auth
* El sistema ya funciona pero necesita validación final para demo pública

Objetivo:
Dejar el sistema en estado "demo-ready" (sin fallos visibles), no perfecto a nivel enterprise.

---

## Requisitos críticos (bloqueantes para grabar)

1. Flujo completo funcional:

* Login
* Crear cliente
* Crear plan
* Generar y descargar PDF
* Logout

Nada de esto puede fallar durante la demo.

---

2. UI/UX para demo:

* No mostrar errores técnicos (JSON, stack traces)
* Mensajes claros y simples
* Estados de carga (aunque sean básicos)
* Transiciones limpias (sin glitches visuales)

---

3. Autenticación:

* Token estable durante toda la demo
* No expiraciones inesperadas
* Manejo silencioso de errores

---

4. Backend:

* Endpoints críticos funcionando (especialmente PDF)
* Sin errores 500
* Logs limpios

---

5. Datos de prueba:

* Crear 2–3 clientes de ejemplo
* Tener planes ya listos
* Evitar estados vacíos en UI

---

6. Performance:

* Evitar cargas lentas visibles
* Si algo tarda, simular loading elegante

---

7. Deploy listo para demo:

* Variables de entorno correctas
* URLs reales (no localhost si grabas en web)
* Sistema accesible desde navegador limpio (incógnito)

---

## Output requerido:

* Checklist exacto de cosas a validar antes de grabar
* Lista de riesgos que pueden arruinar la demo
* Ajustes rápidos (quick fixes) para hoy (no overengineering)
* Script sugerido de flujo para grabar el video paso a paso

---

## Restricciones:

* No proponer mejoras complejas
* No cambiar arquitectura
* Todo debe poder hacerse en menos de 3–4 horas
* Enfocado en que la demo salga perfecta, no en perfección técnica

---

Sé directo, práctico y enfocado en ejecución inmediata.


