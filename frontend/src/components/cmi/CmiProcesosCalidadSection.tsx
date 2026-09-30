"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import type { Data, Layout } from "plotly.js";
import { Info, SlidersHorizontal, Radar, AlertTriangle, CheckCircle2, ChevronRight, ChevronDown } from "lucide-react";
import type { CMICalidadDashboard } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface CmiProcesosCalidadSectionProps {
  calidad: CMICalidadDashboard;
}

const PRIORIDAD_STYLE = {
  Alta: { bg: "#fef2f2", border: "#dc2626", text: "#b91c1c", sub: "#991b1b", strong: "#7f1d1d" },
  Media: { bg: "#fffbeb", border: "#d97706", text: "#b45309", sub: "#92400e", strong: "#78350f" },
  Baja: { bg: "#ecfdf5", border: "#059669", text: "#047857", sub: "#065f46", strong: "#064e3b" },
} as const;

const ALERTA_STYLE = {
  critica: { bg: "#fff7ed", border: "#ea580c", text: "#c2410c", sub: "#7c2d12" },
  fortaleza: { bg: "#f0fdf4", border: "#16a34a", text: "#15803d", sub: "#166534" },
} as const;

function scoreColor(score: number): { bg: string; fg: string } {
  if (score >= 90) return { bg: "#dcfce7", fg: "#15803d" };
  if (score >= 70) return { bg: "#fef3c7", fg: "#b45309" };
  return { bg: "#fee2e2", fg: "#b91c1c" };
}

export function CmiProcesosCalidadSection({ calidad }: CmiProcesosCalidadSectionProps) {
  const [subprocesoOpen, setSubprocesoOpen] = useState(false);
  const [indicadoresOpen, setIndicadoresOpen] = useState(true);

  if (!calidad.disponible) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        {calidad.mensaje ?? "Mapa de calidad no disponible."}
      </div>
    );
  }

  const score = calidad.score_global ?? 0;
  const gaugeColor = score >= 90 ? "#22c55e" : score >= 70 ? "#f59e0b" : "#ef4444";
  const dims = Object.keys(calidad.dim_scores);
  const dimsBajoMeta = dims.filter((d) => calidad.dim_scores[d] < 90);
  const dimDebil = dims.length
    ? dims.reduce((min, d) => (calidad.dim_scores[d] < calidad.dim_scores[min] ? d : min), dims[0])
    : null;

  const alertCount = calidad.alertas.length + calidad.recomendaciones.length;
  const procesoUnico = calidad.por_proceso.length === 1 ? calidad.por_proceso[0] : null;

  return (
    <section className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <div className="mb-1 flex items-center justify-between">
              <h4 className="text-sm font-bold text-slate-800">Score global</h4>
              <Info className="h-[18px] w-[18px] text-slate-400" />
            </div>
            <Plot
              data={[
                {
                  type: "indicator",
                  mode: "gauge+number",
                  value: score,
                  number: { suffix: "%", font: { size: 32 } },
                  gauge: {
                    axis: { range: [0, 100] },
                    bar: { color: gaugeColor },
                    steps: [
                      { range: [0, 70], color: "#fde0e0" },
                      { range: [70, 90], color: "#fff3cd" },
                      { range: [90, 100], color: "#d1f5e0" },
                    ],
                  },
                } as unknown as Data,
              ]}
              layout={{ margin: { l: 24, r: 24, t: 10, b: 10 }, height: 200 } as Partial<Layout>}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%" }}
              useResizeHandler
            />
          </div>
          <div className="grid grid-cols-3 divide-x divide-slate-100 border-t border-slate-100 pt-3 text-center">
            <MiniKpi label="Registros" value={String(calidad.kpis.total_registros)} />
            <MiniKpi label="Subprocesos" value={String(calidad.kpis.total_subprocesos)} />
            <MiniKpi label="Promedio" value={calidad.kpis.promedio != null ? `${calidad.kpis.promedio}%` : "—"} />
          </div>
        </div>

        {dims.length > 0 && (
          <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div>
              <div className="mb-4 flex items-center justify-between">
                <h4 className="text-sm font-bold text-slate-800">Dimensiones de calidad</h4>
                <SlidersHorizontal className="h-[18px] w-[18px] text-slate-400" />
              </div>
              <div className="space-y-4">
                {dims.map((dim) => {
                  const value = calidad.dim_scores[dim];
                  const color = calidad.dim_colors[dim] ?? "#1A3A5C";
                  return (
                    <div key={dim}>
                      <div className="mb-1.5 flex items-center justify-between text-sm">
                        <span className="text-slate-800">{dim}</span>
                        <span className="font-bold" style={{ color }}>
                          {value.toFixed(0)}%
                        </span>
                      </div>
                      <div className="h-2.5 rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{ width: `${Math.max(0, Math.min(100, value))}%`, backgroundColor: color }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-500">
              <span>Estándar meta mínimo: 90%</span>
              {dimsBajoMeta.length > 0 ? (
                <span className="inline-flex items-center gap-1 font-semibold text-amber-600">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  {dimsBajoMeta.length} dimensión{dimsBajoMeta.length > 1 ? "es" : ""} bajo meta
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Todas sobre meta
                </span>
              )}
            </div>
          </div>
        )}

        {dims.length > 0 && (
          <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div>
              <div className="mb-1 flex items-center justify-between">
                <h4 className="text-sm font-bold text-slate-800">Análisis por dimensión</h4>
                <Radar className="h-[18px] w-[18px] text-slate-400" />
              </div>
              <Plot
                data={[
                  {
                    type: "scatterpolar",
                    r: [...dims.map((d) => calidad.dim_scores[d]), calidad.dim_scores[dims[0]]],
                    theta: [...dims, dims[0]],
                    fill: "toself",
                    fillcolor: "rgba(26,58,92,0.15)",
                    line: { color: "#1A3A5C" },
                  },
                ]}
                layout={
                  {
                    margin: { l: 40, r: 40, t: 20, b: 20 },
                    height: 200,
                    polar: { radialaxis: { range: [0, 100], ticksuffix: "%" } },
                    showlegend: false,
                  } as Partial<Layout>
                }
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: "100%" }}
                useResizeHandler
              />
            </div>
            {dimDebil && (
              <p className="mt-2 border-t border-slate-100 pt-3 text-center text-xs text-slate-500">
                Brecha principal focalizada en: <span className="font-semibold text-slate-700">{dimDebil}</span>
              </p>
            )}
          </div>
        )}
      </div>

      {alertCount > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
            <h4 className="text-sm font-bold text-slate-800">
              Alertas <span className="font-normal text-slate-500">• Recomendaciones priorizadas</span>
            </h4>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {calidad.alertas.map((a) => {
              const style = ALERTA_STYLE[a.tipo];
              return (
                <div
                  key={a.titulo}
                  className="flex flex-col justify-between rounded-xl border border-slate-200 border-l-4 p-3.5"
                  style={{ backgroundColor: style.bg, borderLeftColor: style.border }}
                >
                  <div>
                    <p className="mb-1 flex items-center gap-1.5 text-sm font-bold" style={{ color: style.text }}>
                      {a.tipo === "critica" ? (
                        <AlertTriangle className="h-4 w-4" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4" />
                      )}
                      {a.titulo}
                    </p>
                    {a.detalle && (
                      <p className="text-xs font-semibold" style={{ color: style.sub }}>
                        {a.detalle}
                      </p>
                    )}
                    {a.indicadores.length > 0 && (
                      <p className="mt-1 text-xs italic" style={{ color: style.sub }}>
                        {a.indicadores.join(", ")}
                        {a.indicadores_extra > 0 ? ` +${a.indicadores_extra}` : ""}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
            {calidad.recomendaciones.map((r) => {
              const style = PRIORIDAD_STYLE[r.prioridad];
              return (
                <div
                  key={r.titulo}
                  className="flex flex-col justify-between rounded-xl border border-slate-200 border-l-4 p-3.5"
                  style={{ backgroundColor: style.bg, borderLeftColor: style.border }}
                >
                  <div>
                    <p className="mb-1 text-sm font-bold" style={{ color: style.text }}>
                      {r.prioridad}: {r.titulo}
                    </p>
                    {r.items.map((item, i) => (
                      <p
                        key={i}
                        className="mt-1 text-xs"
                        style={{ color: i === 0 ? style.sub : style.strong, fontWeight: i > 0 ? 600 : 400 }}
                      >
                        {item}
                      </p>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {calidad.detalle_indicadores.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <button
            type="button"
            onClick={() => setIndicadoresOpen((o) => !o)}
            className="flex w-full items-center justify-between gap-2 border-b border-slate-100 px-5 py-3.5 text-left"
          >
            <span className="flex items-center gap-2">
              {indicadoresOpen ? (
                <ChevronDown className="h-5 w-5 text-poli-navy" />
              ) : (
                <ChevronRight className="h-5 w-5 text-slate-400" />
              )}
              <span className="text-sm font-bold text-slate-800">
                Detalle por indicador ({calidad.detalle_indicadores.length})
              </span>
            </span>
            <span className="text-xs text-slate-500">
              Mostrando {calidad.detalle_indicadores.length} de {calidad.detalle_indicadores.length} registros
            </span>
          </button>
          {indicadoresOpen && (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    <th className="px-4 py-2.5">Indicador</th>
                    {dims.map((d) => (
                      <th key={d} className="px-3 py-2.5 text-center">
                        {d}
                      </th>
                    ))}
                    <th className="px-4 py-2.5 text-right">Score total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {calidad.detalle_indicadores.map((row, i) => (
                    <tr key={`${row.indicador}-${i}`} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-medium text-slate-800">{row.indicador}</td>
                      {dims.map((d) => {
                        const v = row.dimensiones[d];
                        if (v == null) {
                          return (
                            <td key={d} className="px-3 py-3 text-center text-slate-400">
                              —
                            </td>
                          );
                        }
                        const { bg, fg } = scoreColor(v);
                        return (
                          <td key={d} className="px-3 py-3 text-center">
                            <span
                              className="inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold"
                              style={{ backgroundColor: bg, color: fg }}
                            >
                              {v.toFixed(0)}%
                            </span>
                          </td>
                        );
                      })}
                      <td className="px-4 py-3 text-right font-bold">
                        {row.score_total == null ? (
                          "—"
                        ) : (
                          <span style={{ color: scoreColor(row.score_total).fg }}>{row.score_total.toFixed(0)}%</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {procesoUnico && (
            <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 bg-slate-50/60 p-4">
              <div>
                <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-500">Proceso</span>
                <span className="text-sm font-semibold text-slate-800">{procesoUnico.Proceso}</span>
              </div>
              <div className="flex items-center gap-6">
                <FooterStat label="% Calidad" value={`${procesoUnico.pct_calidad}%`} color="text-poli-navy" />
                <FooterStat label="Cumple" value={String(procesoUnico.cumple)} color="text-emerald-600" />
                <FooterStat label="Parcial" value={String(procesoUnico.parcial)} color="text-amber-600" />
                <FooterStat label="No cumple" value={String(procesoUnico.no_cumple)} color="text-red-600" />
              </div>
            </div>
          )}
        </div>
      )}

      {!procesoUnico && calidad.por_proceso.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <th className="px-4 py-3">Proceso</th>
                <th className="px-4 py-3 text-right">% Calidad</th>
                <th className="px-4 py-3 text-right">Cumple</th>
                <th className="px-4 py-3 text-right">Parcial</th>
                <th className="px-4 py-3 text-right">No cumple</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {calidad.por_proceso.map((p) => (
                <tr key={p.Proceso} className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 font-medium text-slate-800">{p.Proceso}</td>
                  <td className="px-4 py-3 text-right font-semibold text-poli-navy">{p.pct_calidad}%</td>
                  <td className="px-4 py-3 text-right font-semibold text-emerald-600">{p.cumple}</td>
                  <td className="px-4 py-3 text-right font-semibold text-amber-600">{p.parcial}</td>
                  <td className="px-4 py-3 text-right font-semibold text-red-600">{p.no_cumple}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {calidad.por_subproceso.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <button
            type="button"
            onClick={() => setSubprocesoOpen((o) => !o)}
            className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left"
          >
            <span className="flex items-center gap-2">
              {subprocesoOpen ? (
                <ChevronDown className="h-5 w-5 text-poli-navy" />
              ) : (
                <ChevronRight className="h-5 w-5 text-slate-400" />
              )}
              <span className="text-sm font-bold text-slate-800">
                Detalle por subproceso ({calidad.por_subproceso.length})
              </span>
            </span>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              {subprocesoOpen ? "Contraer" : "Expandir"}
            </span>
          </button>
          {subprocesoOpen && (
            <div className="overflow-x-auto border-t border-slate-100">
              <table className="w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    <th className="px-4 py-3">Proceso</th>
                    <th className="px-4 py-3">Subproceso</th>
                    <th className="px-4 py-3 text-right">Registros</th>
                    <th className="px-4 py-3 text-right">% Calidad</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {calidad.por_subproceso.map((p, i) => (
                    <tr key={`${p.Proceso}-${p.Subproceso}-${i}`} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 text-slate-800">{p.Proceso}</td>
                      <td className="px-4 py-3 text-slate-600">{p.Subproceso}</td>
                      <td className="px-4 py-3 text-right">{p.registros}</td>
                      <td className="px-4 py-3 text-right font-semibold text-poli-navy">{p.pct_calidad}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function MiniKpi({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-lg font-bold text-poli-navy">{value}</p>
      <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">{label}</p>
    </div>
  );
}

function FooterStat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="text-right">
      <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
      <span className={`text-sm font-bold ${color}`}>{value}</span>
    </div>
  );
}
