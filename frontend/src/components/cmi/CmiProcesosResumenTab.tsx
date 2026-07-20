"use client";

import type { CMIProcesosVistaGlobal, CMIProcesoBar } from "@/lib/types";
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

function nivelKey(pct: number | null): string {
  if (pct == null) return "pendiente";
  if (pct >= 100) return "sobrecumplimiento";
  if (pct >= 95) return "cumplimiento";
  if (pct >= 80) return "alerta";
  return "peligro";
}
function nivelLabel(pct: number | null): string {
  if (pct == null) return "Sin dato";
  if (pct >= 100) return "Sobrecumplimiento";
  if (pct >= 95) return "Cumplimiento";
  if (pct >= 80) return "Alerta";
  return "Peligro";
}

export function CmiProcesosResumenTab({ vista, baseAnio }: CmiProcesosResumenTabProps) {
  const { kpis, banner, distribucion_nivel, proceso_bars, catalog_charts, variacion } = vista;

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
            <h3 className="text-xl font-bold sm:text-2xl">{banner.anio} · {banner.mes}</h3>
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
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <CmiMetricCard title="Cumplimiento promedio" value={fmtPct(kpis.promedio)} subtitle={`Corte ${vista.mes_nombre}`} icon="📈" color="#1D4ED8" />
        <CmiMetricCard title="En alerta" value={String(nAlerta)} subtitle="80% – 94%" icon="⚠️" color="#B45309" />
        <CmiMetricCard title="En peligro" value={String(nPeligro)} subtitle="Menor a 80%" icon="🚨" color="#B71C1C" />
        <CmiMetricCard title="Procesos activos" value={String(kpis.n_procesos)} subtitle={`${kpis.n_subprocesos} subprocesos · ${kpis.n_unidades} unidades`} icon="🏢" color="#1A3A5C" />
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
                  const key = nivelKey(d.cumplimiento);
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
                          {nivelLabel(d.cumplimiento)}
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

          {/* Variación */}
          {(variacion.mejoraron.length > 0 || variacion.empeoraron.length > 0) && (
            <div className="flex flex-col gap-3">
              <VarTable title="Mayor mejora" rows={variacion.mejoraron} positive />
              <VarTable title="Mayor riesgo" rows={variacion.empeoraron} positive={false} />
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
