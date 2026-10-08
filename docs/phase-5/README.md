# Fase 5 — Frontend Next.js

**Estado:** Completada (salvo eliminar OM en UI)  
**Actualizado:** 2026-10-08 — ver `docs/migration/ROADMAP.md` Fase 5 para el detalle verificado contra código.

## Páginas conectadas a API (listado inicial 2026-06; el vigente está en ROADMAP.md)

| Página | Ruta | Endpoints |
|--------|------|-----------|
| Resumen General | `/resumen-general` | KPIs, semáforo, tendencia, indicadores |
| CMI Estratégico | `/cmi-estrategico` | `/cmi/estrategico`, `/cmi/alertas` |
| CMI Procesos | `/cmi-procesos` | `/cmi/procesos` |
| Gestión OM | `/gestion-om` | `/om` |

## Componentes reutilizables

- `components/ui/KPICard.tsx`
- `components/ui/FilterBar.tsx`
- `components/charts/SemaphoreChart.tsx`
- `components/charts/TrendChart.tsx`
- `components/tables/IndicatorsTable.tsx`

## Cliente API

- `src/lib/api.ts` — Axios + React Query
- `src/lib/types.ts` — tipos TypeScript

## Autenticación

- Botón **Dev login** en header (solo `NODE_ENV=development`)
- `POST /api/v1/auth/dev-token` crea usuario en BD y devuelve JWT
- Token persistido en Zustand (`sgind-auth`)

## Pendiente

- [x] Eliminar OM en UI (solo `administrador`)
- [ ] Lint ESLint sin warnings
- [ ] Componentes IA en frontend (el informe usa narrativa IA vía backend)
- [ ] Lighthouse > 90

## Verificación

```bash
cd frontend && npm run build
# Abrir http://localhost:3000 → Dev login → Resumen General
```
