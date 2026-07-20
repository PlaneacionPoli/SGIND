# Fase 5 — Frontend Next.js

**Estado:** En progreso  
**Fecha:** 2026-06-13

## Páginas conectadas a API

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

- [ ] Modal CRUD OM
- [ ] shadcn/ui design system
- [ ] Páginas secundarias (PDI, diagnóstico, etc.)
- [ ] Componentes IA en frontend
- [ ] Lighthouse > 90

## Verificación

```bash
cd sgind-v2/frontend && npm run build
# Abrir http://localhost:3000 → Dev login → Resumen General
```
