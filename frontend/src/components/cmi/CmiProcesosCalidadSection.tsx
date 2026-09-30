"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import type { Data, Layout } from "plotly.js";
import type { CMICalidadDashboard } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface CmiProcesosCalidadSectionProps {
  calidad: CMICalidadDashboard;
}

const PRIORIDAD_STYLE = {
  Alta: { bg: "#ffebee", border: "#ef5350", text: "#b71c1c" },
  Media: { bg: "#fff8e1", border: "#ffa726", text: "#e65100" },
  Baja: { bg: "#e8f5e9", border: "#66bb6a", text: "#1b5e20" },
} as const;

const ALERTA_STYLE = {
  critica: { bg: "#fff8e1", border: "#ffa726", text: "#e65100", sub: "#78350f" },
  fortaleza: { bg: "#e8f5e9", border: "#66bb6a", text: "#1b5e20", sub: "#1b5e20" },
} as const;

function scoreColor(score: number): { bg: string; fg: string } {
  if (score >= 90) return { bg: "#e8f5e9", fg: "#1b5e20" };
  if (score >= 70) return { bg: "#fff8e1", fg: "#e65100" };
  return { bg: "#ffebee", fg: "#b71c1c" };
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

  const alertCount = calidad.alertas.length + calidad.recomendaciones.length;

  return (
    <section className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h4 className="mb-2 text-sm font-bold text-slate-800">Score global</h4>
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
            layout={{ margin: { l: 24, r: 24, t: 10, b: 10 }, height: 220 } as Partial<Layout>}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: "100%" }}
            useResizeHandler
          />
          <div className="mt-2 grid grid-cols-3 gap-2 text-center">
            <MiniKpi label="Registros" value={String(calidad.kpis.total_registros)} />
            <MiniKpi label="Subprocesos" value={String(calidad.kpis.total_subprocesos)} />
            <MiniKpi label="Promedio" value={calidad.kpis.promedio != null ? `${calidad.kpis.promedio}%` : "—"} />
          </div>
        </div>

        {dims.length > 0 && (
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h4 className="mb-3 text-sm font-bold text-slate-800">Dimensiones de calidad</h4>
            <div className="space-y-3">
              {dims.map((dim) => {
                const value = calidad.dim_scores[dim];
                const color = calidad.dim_colors[dim] ?? "#1A3A5C";
                return (
                  <div key={dim}>
                    <div className="mb-1 flex items-center justify-between text-xs font-semibold text-slate-600">
                      <span>{dim}</span>
                      <span style={{ color }}>{value.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-200">
                      <div
                        className="h-2 rounded-full"
                        style={{ width: `${Math.max(0, Math.min(100, value))}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {dims.length > 0 && (
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h4 className="mb-2 text-sm font-bold text-slate-800">Análisis por dimensión</h4>
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
                  height: 220,
                  polar: { radialaxis: { range: [0, 100], ticksuffix: "%" } },
                  showlegend: false,
                } as Partial<Layout>
              }
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%" }}
              useResizeHandler
            />
          </div>
        )}
      </div>

      {alertCount > 0 && (
        <div>
          <h4 className="mb-3 text-sm font-bold text-slate-800">
            ⚠️ Alertas &nbsp;&nbsp;&nbsp; 💡 Recomendaciones priorizadas
          </h4>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {calidad.alertas.map((a) => {
              const style = ALERTA_STYLE[a.tipo];
              return (
                <div
                  key={a.titulo}
                  className="rounded-lg border-l-4 p-3"
                  style={{ backgroundColor: style.bg, borderLeftColor: style.border }}
                >
                  <p className="text-xs font-bold" style={{ color: style.text }}>
                    {a.tipo === "critica" ? "⏱ " : "✓ "}
                    {a.titulo}
                  </p>
                  <p className="mt-1 text-[11px]" style={{ color: style.sub }}>
                    {a.detalle}
                  </p>
                  {a.indicadores.length > 0 && (
                    <p className="mt-1 text-[11px] italic" style={{ color: style.sub }}>
                      {a.indicadores.join(", ")}
                      {a.indicadores_extra > 0 ? ` +${a.indicadores_extra}` : ""}
                    </p>
                  )}
                </div>
              );
            })}
            {calidad.recomendaciones.map((r) => {
              const style = PRIORIDAD_STYLE[r.prioridad];
              return (
                <div
                  key={r.titulo}
                  className="rounded-lg border-l-4 p-3"
                  style={{ backgroundColor: style.bg, borderLeftColor: style.border }}
                >
                  <p className="text-xs font-bold" style={{ color: style.text }}>
                    {r.prioridad}: {r.titulo}
                  </p>
                  <ul className="mt-1 space-y-0.5 text-[11px] text-slate-700">
                    {r.items.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {calidad.detalle_indicadores.length > 0 && (
        <details open={indicadoresOpen} onToggle={(e) => setIndicadoresOpen(e.currentTarget.open)}>
          <summary className="cursor-pointer text-sm font-bold text-slate-800">
            Detalle por indicador ({calidad.detalle_indicadores.length})
          </summary>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Indicador</th>
                  {dims.map((d) => (
                    <th key={d} className="px-3 py-3 text-center">
                      {d}
                    </th>
                  ))}
                  <th className="px-4 py-3 text-center">Score total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {calidad.detalle_indicadores.map((row, i) => (
                  <tr key={`${row.indicador}-${i}`}>
                    <td className="px-4 py-3 font-medium">{row.indicador}</td>
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
                            className="rounded-full px-2 py-0.5 text-xs font-semibold"
                            style={{ backgroundColor: bg, color: fg }}
                          >
                            {v.toFixed(0)}%
                          </span>
                        </td>
                      );
                    })}
                    <td className="px-4 py-3 text-center font-bold">
                      {row.score_total == null ? (
                        "—"
                      ) : (
                        <span style={{ color: scoreColor(row.score_total).fg }}>
                          {row.score_total.toFixed(0)}%
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}

      {calidad.por_proceso.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Proceso</th>
                <th className="px-4 py-3 text-right">% Calidad</th>
                <th className="px-4 py-3 text-right">Cumple</th>
                <th className="px-4 py-3 text-right">Parcial</th>
                <th className="px-4 py-3 text-right">No cumple</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {calidad.por_proceso.map((p) => (
                <tr key={p.Proceso}>
                  <td className="px-4 py-3 font-medium">{p.Proceso}</td>
                  <td className="px-4 py-3 text-right font-semibold">{p.pct_calidad}%</td>
                  <td className="px-4 py-3 text-right text-emerald-700">{p.cumple}</td>
                  <td className="px-4 py-3 text-right text-amber-700">{p.parcial}</td>
                  <td className="px-4 py-3 text-right text-red-700">{p.no_cumple}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {calidad.por_subproceso.length > 0 && (
        <details open={subprocesoOpen} onToggle={(e) => setSubprocesoOpen(e.currentTarget.open)}>
          <summary className="cursor-pointer text-sm font-bold text-slate-800">
            Detalle por subproceso ({calidad.por_subproceso.length})
          </summary>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Proceso</th>
                  <th className="px-4 py-3">Subproceso</th>
                  <th className="px-4 py-3 text-right">Registros</th>
                  <th className="px-4 py-3 text-right">% Calidad</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {calidad.por_subproceso.map((p, i) => (
                  <tr key={`${p.Proceso}-${p.Subproceso}-${i}`}>
                    <td className="px-4 py-3">{p.Proceso}</td>
                    <td className="px-4 py-3 text-slate-600">{p.Subproceso}</td>
                    <td className="px-4 py-3 text-right">{p.registros}</td>
                    <td className="px-4 py-3 text-right font-semibold">{p.pct_calidad}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
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
