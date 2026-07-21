"use client";

import type { CMIProcesosVistaGlobal } from "@/lib/types";
import { CmiCatalogChartsPlotly } from "@/components/cmi/CmiCatalogChartsPlotly";
import { CmiDonutNivelPlotly } from "@/components/cmi/CmiDonutNivelPlotly";
import { CmiMetricCard } from "@/components/cmi/CmiMetricCard";
import { fmtNum, fmtPct } from "@/components/cmi/nivelUtils";

interface CmiProcesosResumenTabProps {
  vista: CMIProcesosVistaGlobal;
  baseAnio: number;
}

const NIVEL_COLOR: Record<string, string> = {
  sobrecumplimiento: "#1D4ED8",
  cumplimiento: "#166534",
  alerta: "#B45309",
  peligro: "#B71C1C",
};
const NIVEL_BG: Record<string, string> = {
  sobrecumplimiento: "#EFF6FF",
  cumplimiento: "#F0FDF4",
  alerta: "#FFFBEB",
  peligro: "#FFF1F2",
};

// Fallback solo si el backend no envía "nivel" (ya clasificado por indicador
// respetando regímenes especiales, ej. Plan Anual alerta<95%/tope 100%).
function nivelKeyFallback(pct: number | null): string {
  if (pct == null) return "pendiente";
  if (pct >= 105) return "sobrecumplimiento";
  if (pct >= 100) return "cumplimiento";
  if (pct >= 80) return "alerta";
  return "peligro";
}

function nivelKey(d: { nivel?: string | null; cumplimiento: number | null }): string {
  if (d.nivel) return d.nivel.toLowerCase();
  return nivelKeyFallback(d.cumplimiento);
}
function nivelLabel(d: { nivel?: string | null; cumplimiento: number | null }): string {
  if (d.nivel) return d.nivel;
  const key = nivelKeyFallback(d.cumplimiento);
  if (key === "pendiente") return "Sin dato";
  return key.charAt(0).toUpperCase() + key.slice(1);
}

export function CmiProcesosResumenTab({ vista, baseAnio }: CmiProcesosResumenTabProps) {
  const { kpis, banner, distribucion_nivel, proceso_bars, catalog_charts, variacion_procesos, brecha_ambiental } = vista;
  const mejoraronProcesos = (variacion_procesos?.mejoraron ?? []).map((r) => ({
    indicador: r.name,
    variacion: r.change,
  }));
  const empeoraronProcesos = (variacion_procesos?.empeoraron ?? []).map((r) => ({
    indicador: r.name,
    variacion: r.change,
  }));

  const conteo = kpis.conteo_estados ?? {};
  const nAlerta = conteo["Alerta"] ?? 0;
  const nPeligro = conteo["Peligro"] ?? 0;

  const sorted = [...proceso_bars].sort((a, b) => (b.cumplimiento ?? 0) - (a.cumplimiento ?? 0));
  const maxPct = Math.max(...sorted.map((d) => Math.max(d.cumplimiento ?? 0, d.cumplimiento_anterior ?? 0)), 100);

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="rounded-2xl bg-gradient-to-br from-[#173a63] to-[#2d5a8a] p-5 text-white shadow-lg sm:p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-white/60">CMI por Procesos</p>
            <h3 className="text-xl font-bold sm:text-2xl">
              {banner.pct_saludable != null
                ? `${fmtNum(banner.pct_saludable)}% de los indicadores opera en niveles saludables`
                : `${banner.anio} · ${banner.mes}`}
            </h3>
            <p className="mt-0.5 text-xs text-white/60">{banner.anio} · {banner.mes}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Chip label="Subprocesos = 1" />
            <Chip label="Validado Kawak" />
          </div>
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <BannerStat label="Cumplimiento global" value={fmtPct(banner.cumplimiento_global)} large />
          <BannerStat
            label={`vs ${banner.base_anio}`}
            value={banner.variacion_pp != null ? `${banner.variacion_pp > 0 ? "+" : ""}${fmtNum(banner.variacion_pp)} pp` : "—"}
          />
          <BannerStat label="Indicadores" value={String(banner.total_indicadores)} />
          <BannerStat label="En riesgo" value={String(banner.en_riesgo)} />
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <CmiMetricCard title="Indicadores activos" value={String(kpis.total)} subtitle={`Proceso: Todos · ${kpis.n_procesos} procesos · ${kpis.n_subprocesos} subprocesos`} icon="📌" color="#1D4ED8" />
        <CmiMetricCard title="Cumplimiento promedio" value={fmtPct(kpis.promedio)} subtitle={`Corte ${vista.mes_nombre}`} icon="✔️" color="#047857" />
        <CmiMetricCard title="En alerta" value={String(nAlerta)} subtitle="80% – 99%" icon="⚠️" color="#B45309" />
        <CmiMetricCard title="En peligro" value={String(nPeligro)} subtitle="Menor a 80%" icon="🚨" color="#B71C1C" />
        <CmiMetricCard title="Procesos activos" value={String(kpis.n_procesos)} subtitle={`${kpis.n_unidades} unidades organizacionales`} icon="🏢" color="#1A3A5C" />
        <CmiMetricCard title="Subprocesos activos" value={String(kpis.n_subprocesos)} subtitle="Subprocesos válidos según filtro CMI por Procesos" icon="🧩" color="#B45309" />
      </div>

      {/* Gráficas de catálogo */}
      <CmiCatalogChartsPlotly periodicidad={catalog_charts.periodicidad} tipoIndicador={catalog_charts.tipo_indicador} />

      {/* Tabla ranking + panel lateral */}
      <div className="grid gap-5 xl:grid-cols-3">
        {/* Tabla de procesos — ocupa 2/3 */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm xl:col-span-2">
          <div className="flex items-center justify-between gap-2 border-b border-slate-100 px-5 py-3">
            <h4 className="text-sm font-bold text-slate-800">
              Ranking de procesos por cumplimiento
              {baseAnio ? <span className="ml-1 font-normal text-slate-500">(vs {baseAnio})</span> : null}
            </h4>
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-semibold text-slate-500">
              {sorted.length} procesos
            </span>
          </div>

          <div className="max-h-[520px] overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 z-10 bg-slate-50">
                <tr className="border-b border-slate-200 text-[10px] font-bold uppercase tracking-wide text-slate-500">
                  <th className="w-8 px-4 py-2 text-center">#</th>
                  <th className="px-3 py-2 text-left">Proceso</th>
                  <th className="w-24 px-3 py-2 text-left">Nivel</th>
                  <th className="w-32 px-3 py-2 text-left">Progreso</th>
                  <th className="w-16 px-3 py-2 text-right">%</th>
                  {baseAnio && <th className="w-16 px-3 py-2 text-right">Δ {baseAnio}</th>}
                  <th className="w-12 px-4 py-2 text-right">Ind.</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((d, i) => {
                  const key = nivelKey(d);
                  const color = NIVEL_COLOR[key] ?? "#94A3B8";
                  const bg = NIVEL_BG[key] ?? "#F8FAFC";
                  const delta = d.cumplimiento != null && d.cumplimiento_anterior != null
                    ? d.cumplimiento - d.cumplimiento_anterior : null;
                  const barW = d.cumplimiento != null ? Math.min((d.cumplimiento / maxPct) * 100, 100) : 0;
                  const prevW = d.cumplimiento_anterior != null ? Math.min((d.cumplimiento_anterior / maxPct) * 100, 100) : 0;

                  return (
                    <tr
                      key={d.proceso}
                      className="border-b border-slate-100 transition-colors hover:bg-slate-50"
                    >
                      {/* Rank */}
                      <td className="px-4 py-2.5 text-center">
                        <span
                          className="inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold text-white"
                          style={{ backgroundColor: color }}
                        >
                          {i + 1}
                        </span>
                      </td>

                      {/* Nombre */}
                      <td className="px-3 py-2.5">
                        <span className="font-semibold text-slate-800" title={d.proceso}>
                          {d.proceso.length > 32 ? `${d.proceso.slice(0, 31)}…` : d.proceso}
                        </span>
                      </td>

                      {/* Nivel badge */}
                      <td className="px-3 py-2.5">
                        <span
                          className="inline-block rounded-full px-2 py-0.5 text-[10px] font-bold"
                          style={{ backgroundColor: bg, color }}
                        >
                          {nivelLabel(d)}
                        </span>
                      </td>

                      {/* Mini barra */}
                      <td className="px-3 py-2.5">
                        <div className="relative h-2.5 overflow-hidden rounded-full bg-slate-100">
                          {prevW > 0 && (
                            <div
                              className="absolute left-0 top-0 h-full rounded-full opacity-25"
                              style={{ width: `${prevW}%`, backgroundColor: color }}
                            />
                          )}
                          <div
                            className="absolute left-0 top-0 h-full rounded-full"
                            style={{ width: `${barW}%`, backgroundColor: color }}
                          />
                          {/* línea 100% */}
                          <div
                            className="absolute top-0 h-full w-px bg-slate-400/50"
                            style={{ left: `${(100 / maxPct) * 100}%` }}
                          />
                        </div>
                      </td>

                      {/* % actual */}
                      <td className="px-3 py-2.5 text-right">
                        <span className="font-extrabold" style={{ color }}>
                          {d.cumplimiento != null ? `${d.cumplimiento.toFixed(1)}%` : "—"}
                        </span>
                      </td>

                      {/* Delta */}
                      {baseAnio && (
                        <td className="px-3 py-2.5 text-right">
                          {delta != null ? (
                            <span
                              className="font-bold"
                              style={{ color: delta >= 0 ? "#166534" : "#B71C1C" }}
                            >
                              {delta >= 0 ? "▲" : "▼"} {Math.abs(delta).toFixed(1)}
                            </span>
                          ) : (
                            <span className="text-slate-300">—</span>
                          )}
                        </td>
                      )}

                      {/* N indicadores */}
                      <td className="px-4 py-2.5 text-right text-slate-400">
                        {d.n_indicadores}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Panel lateral — 1/3 */}
        <div className="flex flex-col gap-4">
          {/* Donut */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <h4 className="mb-3 text-sm font-bold text-slate-800">Distribución por nivel</h4>
            <CmiDonutNivelPlotly data={distribucion_nivel} total={kpis.total} />
          </div>

          {/* Brecha ambiental crítica (paridad con insight de Streamlit) */}
          {brecha_ambiental && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 shadow-sm">
              <div className="mb-1 flex items-center gap-1.5">
                <span className="text-sm">🌱</span>
                <h4 className="text-xs font-bold text-emerald-800">Brecha ambiental crítica</h4>
              </div>
              <p className="text-[11px] leading-snug text-emerald-900/80">{brecha_ambiental.texto}</p>
            </div>
          )}

          {/* Variación por proceso (paridad: comparación vs año base, no a nivel de indicador) */}
          {(mejoraronProcesos.length > 0 || empeoraronProcesos.length > 0) && (
            <div className="flex flex-col gap-3">
              <VarTable title="Procesos con mayor mejora" rows={mejoraronProcesos} positive />
              <VarTable title="Procesos en mayor riesgo" rows={empeoraronProcesos} positive={false} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Chip({ label }: { label: string }) {
  return <span className="rounded-full bg-white/15 px-2.5 py-1 text-[10px] font-semibold text-white/90">{label}</span>;
}

function BannerStat({ label, value, large }: { label: string; value: string; large?: boolean }) {
  return (
    <div className="rounded-xl bg-white/10 px-3 py-2.5">
      <p className="text-[10px] font-bold uppercase tracking-wider text-white/55">{label}</p>
      <p className={`mt-0.5 font-bold ${large ? "text-2xl" : "text-lg"}`}>{value}</p>
    </div>
  );
}

function VarTable({ title, rows, positive }: { title: string; rows: Array<{ indicador: string; variacion: number }>; positive: boolean }) {
  if (!rows.length) return null;
  const accent = positive ? "#166534" : "#B71C1C";
  const bg = positive ? "#F0FDF4" : "#FFF1F2";
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <div className="mb-2 flex items-center gap-1.5 rounded-lg px-2 py-1" style={{ backgroundColor: bg }}>
        <span className="text-xs font-bold" style={{ color: accent }}>{positive ? "▲" : "▼"}</span>
        <h4 className="text-xs font-bold" style={{ color: accent }}>{title}</h4>
      </div>
      <ul className="space-y-1.5">
        {rows.slice(0, 5).map((r) => (
          <li key={r.indicador} className="flex items-start justify-between gap-2">
            <span className="truncate text-[11px] leading-tight text-slate-600" title={r.indicador}>{r.indicador}</span>
            <span className="shrink-0 text-[11px] font-extrabold" style={{ color: accent }}>
              {r.variacion > 0 ? "+" : ""}{fmtNum(r.variacion)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
