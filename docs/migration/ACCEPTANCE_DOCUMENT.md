# Acta de Aceptación — SGIND v2

**Sistema:** Sistema de Indicadores Estratégicos, CMI y Planeación Institucional (SGIND v2)  
**Versión evaluada:** v2.0.0  
**Tecnología:** Next.js 14 + FastAPI + PostgreSQL  
**Fecha de inicio UAT:** ___________  
**Fecha de aprobación:** ___________

---

## 1. Alcance de la Evaluación

El presente documento certifica que el sistema **SGIND v2** fue evaluado por los usuarios clave de la institución en las siguientes dimensiones:

| Módulo | Evaluado | Aprobado |
|--------|----------|---------|
| Acceso y Autenticación (Azure AD) | ☐ | ☐ |
| Resumen General | ☐ | ☐ |
| CMI Estratégico | ☐ | ☐ |
| CMI Procesos | ☐ | ☐ |
| Gestión OM | ☐ | ☐ |
| Plan de Mejoramiento | ☐ | ☐ |
| Seguimiento Operativo | ☐ | ☐ |
| Informe por Procesos | ☐ | ☐ |
| Diagnóstico del Sistema | ☐ | ☐ |

---

## 2. Criterios de Aceptación Cumplidos

### 2.1 Funcionalidad

- [ ] Todos los módulos del sistema renderizan datos correctamente
- [ ] Las operaciones CRUD de Gestión OM funcionan sin errores
- [ ] Las exportaciones PDF/Excel generan archivos con datos correctos
- [ ] La autenticación con Azure AD institucional es funcional

### 2.2 Exactitud de Datos

- [ ] Los indicadores muestran valores idénticos al sistema Streamlit legacy (tolerancia ±0.01%)
- [ ] Los porcentajes de cumplimiento son correctos para todos los módulos
- [ ] La semaforización (colores) corresponde a los umbrales definidos

### 2.3 Usabilidad

- [ ] Los tiempos de carga son aceptables (< 8 segundos por página)
- [ ] La navegación es intuitiva para el perfil de usuario objetivo
- [ ] Los mensajes de error son claros y comprensibles

### 2.4 Calidad Técnica

- [ ] Cero bugs bloqueantes al momento de la aprobación
- [ ] Paridad numérica verificada con script `uat_verify.py`
- [ ] Tests E2E pasan en el ambiente de staging

---

## 3. Rondas de Validación

### Ronda 1

| Fecha | Módulos evaluados | Participantes | Bugs encontrados | Resultado |
|-------|------------------|--------------|-----------------|-----------|
| | | | | Aprobado / Observaciones |

### Ronda 2

| Fecha | Módulos evaluados | Participantes | Bugs encontrados | Resultado |
|-------|------------------|--------------|-----------------|-----------|
| | | | | Aprobado / Observaciones |

---

## 4. Bugs Identificados y Estado Final

> Referencia completa: [UAT_BUGS.md](UAT_BUGS.md)

| ID | Severidad | Descripción | Estado al cierre |
|----|-----------|-------------|-----------------|
| | | | |

**Total bugs bloqueantes al cierre:** **0** ✅  
**Total bugs mayores al cierre:** ___  
**Total mejoras registradas para backlog:** ___

---

## 5. Observaciones Generales

> Comentarios, sugerencias y observaciones relevantes de los usuarios validadores:

___________________________________________________________________________  
___________________________________________________________________________  
___________________________________________________________________________

---

## 6. Decisión de Aceptación

☐ **APROBADO** — El sistema SGIND v2 cumple con los criterios de aceptación definidos y está autorizado para avanzar al cutover (Fase 12).

☐ **APROBADO CON CONDICIONES** — El sistema está aprobado sujeto a la corrección de los siguientes puntos antes del go-live:

1. ___________
2. ___________

☐ **RECHAZADO** — El sistema no cumple los criterios de aceptación. Requiere una ronda adicional de correcciones y re-evaluación.

---

## 7. Firmas de Aprobación

| Rol | Nombre | Firma | Fecha |
|-----|--------|-------|-------|
| Coordinador UAT | | | |
| Director de Planeación | | | |
| Analista de Planeación | | | |
| Responsable TI / Desarrollo | | | |
| Director(a) / Decano(a) (opcional) | | | |

---

## 8. Próximos Pasos (post-aprobación)

Una vez firmado este documento, se procede con:

1. **Fase 12 — Cutover**: Definir ventana de mantenimiento y redirigir URL principal a SGIND v2
2. **Comunicación**: Notificar a todos los usuarios el cambio de sistema
3. **Monitoreo**: 48 horas de observación activa post-cutover
4. **Legacy**: Streamlit pasa a modo read-only por mínimo 30 días

---

*Documento generado como parte de la Fase 11 — UAT del proyecto SGIND v2*  
*Referencia: `sgind-v2/docs/migration/ROADMAP.md`*
