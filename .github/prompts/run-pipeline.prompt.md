---
description: "Ejecuta el pipeline completo de cambios: Arquitecto → Product → Engineer → QA → Engineer (fixes). Usa: /run-pipeline [descripción del cambio]. Ejemplo: /run-pipeline optimizar dashboard para gimnasios reales."
---

# Pipeline de Cambios — Ejecución Completa

**Objetivo:** {{input}}

Ejecuta las 5 fases del pipeline EN ORDEN. No saltes fases. No suavices cambios. Prioriza coherencia global.

---

## Fase 1 — Arquitecto

Invoca al agente `Arquitecto - MetodoBase` con:

> Analiza el proyecto completo en el contexto de: {{input}}.
> Detecta problemas estructurales, deuda técnica y conflictos.
> Genera: (1) lista de problemas, (2) plan de refactor, (3) qué NO tocar.
> Revisa @workspace completo: api/, core/, src/, ui_desktop/, web/, config/, design_system/.

**Output requerido:** Problemas + Plan + Restricciones

---

## Fase 2 — Product

Invoca al agente `Product & Ideación - MetodoBase` con:

> Con base en el análisis del Arquitecto (pásale el output de Fase 1):
> Optimiza para conversión y uso real en gimnasios.
> Genera: (1) cambios UI concretos, (2) features vendibles que un gym pagaría.
> NO proponer cosas bonitas inútiles. Solo valor real.

**Output requerido:** Cambios UI + Features vendibles priorizadas

---

## Fase 3 — Engineer (primera pasada)

Invoca al agente `Implementador - MetodoBase` con:

> Implementa exactamente lo especificado en Fase 1 + Fase 2.
> Elimina cualquier código legacy que interfiera.
> Tienes PERMISO de romper cosas que necesitan romperse para avanzar.
> Prioriza consistencia sobre compatibilidad con código viejo.
> Revisa @workspace para contexto completo antes de tocar archivos.

**Output requerido:** Código implementado + archivos modificados + legacy eliminado

---

## Fase 4 — QA

Invoca al agente `QA & Auditor - MetodoBase` con:

> Valida TODO lo que el Engineer implementó.
> Corre pytest. Encuentra bugs, inconsistencias y partes no implementadas.
> Si detectas errores críticos, genera INSTRUCCIONES OBLIGATORIAS para el Engineer con prioridad, archivo, línea y acción exacta.

**Output requerido:** Resultados pytest + Bugs + Instrucciones obligatorias para Engineer (si aplica)

---

## Fase 5 — Engineer (fixes finales)

**Solo si Fase 4 reportó errores críticos o altos.**

Invoca al agente `Implementador - MetodoBase` con:

> Aplica estos fixes obligatorios del QA: [pegar instrucciones de Fase 4].
> Cada fix debe verificarse ejecutando el test indicado.
> NO omitas ningún fix marcado como crítico.

**Output requerido:** Fixes aplicados + Tests pasando

---

## Reglas del pipeline

1. NO ignorar fases — todas son obligatorias
2. NO suavizar cambios — si algo debe romperse, se rompe
3. Priorizar coherencia global sobre parches locales
4. Si el Arquitecto dice NO tocar X → el Engineer NO toca X
5. Cada fase recibe el output COMPLETO de la fase anterior
6. Después de Fase 5, reportar resumen final al usuario
