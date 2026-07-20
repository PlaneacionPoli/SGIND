# UAT — Registro de Bugs y Feedback

**Fase:** 11 — Validación con Usuarios  
**Sistema:** SGIND v2 (Next.js 14 + FastAPI + PostgreSQL)

---

## Clasificación de Severidad

| Nivel | Etiqueta | Criterio | Acción requerida |
|-------|----------|----------|-----------------|
| 1 | 🔴 **BLOQUEANTE** | Impide usar el módulo completamente. Dato incorrecto. | Corregir antes de aprobar UAT |
| 2 | 🟠 **MAYOR** | Función importante no funciona pero hay workaround. | Corregir antes de go-live |
| 3 | 🟡 **MENOR** | Problema estético o de usabilidad. No afecta datos. | Corregir si hay tiempo, o en sprint post-UAT |
| 4 | 🔵 **MEJORA** | Funcionalidad nueva sugerida por usuario. | Backlog futuro |

> **Hito F11:** Cero bugs 🔴 BLOQUEANTE antes de aprobar la fase.

---

## Template de Registro

```
### BUG-XXX: [Título breve]

- **Severidad:** 🔴 BLOQUEANTE | 🟠 MAYOR | 🟡 MENOR | 🔵 MEJORA
- **Módulo:** [Ej: Resumen General]
- **URL:** [Ej: /resumen-general]
- **Reportado por:** [Nombre / Rol]
- **Fecha:** YYYY-MM-DD
- **Ronda UAT:** 1 / 2

**Descripción:**
[Qué ocurre]

**Pasos para reproducir:**
1.
2.
3.

**Comportamiento esperado:**
[Lo que debería pasar]

**Comportamiento actual:**
[Lo que pasa realmente]

**Evidencia:** [Screenshot / video / log]

**Estado:** Abierto | En revisión | Corregido | Verificado | Cerrado
**Asignado a:** 
**Corregido en commit:** 
```

---

## Bugs Registrados

<!-- Agregar un bloque por bug. Ordenar por severidad. -->

### BUG-001: [Ejemplo — eliminar antes de usar]

- **Severidad:** 🟡 MENOR
- **Módulo:** Resumen General
- **URL:** /resumen-general
- **Reportado por:** UAT Coordinador
- **Fecha:** 2026-06-19
- **Ronda UAT:** 1

**Descripción:**
[Placeholder — este es un ejemplo de cómo registrar un bug]

**Pasos para reproducir:**
1. Ingresar al sistema
2. Ir a Resumen General
3. Observar ...

**Comportamiento esperado:**
...

**Comportamiento actual:**
...

**Estado:** Cerrado (ejemplo)  
**Asignado a:** —  
**Corregido en commit:** —

---

## Resumen de Estado

| ID | Módulo | Severidad | Título | Estado | Asignado |
|----|--------|-----------|--------|--------|---------|
| BUG-001 | Ejemplo | 🟡 MENOR | Placeholder | Cerrado | — |

---

## Historial de Correcciones por Ronda

### Ronda 1 → Ronda 2

| Bug | Corregido | Verificado por |
|-----|-----------|----------------|
| | | |

### Ronda 2 → Aprobación Final

| Bug | Corregido | Verificado por |
|-----|-----------|----------------|
| | | |

---

## Métricas UAT

| Métrica | Ronda 1 | Ronda 2 | Final |
|---------|---------|---------|-------|
| Bugs BLOQUEANTE abiertos | | | 0 ✅ |
| Bugs MAYOR abiertos | | | |
| Bugs MENOR abiertos | | | |
| Mejoras registradas | | | |
| Total cerrados | | | |
