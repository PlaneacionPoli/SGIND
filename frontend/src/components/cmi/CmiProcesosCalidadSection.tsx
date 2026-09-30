"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import type { Data, Layout } from "plotly.js";
import type { CMICalidadDashboard } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface CmiProcesosCalidadSectionProps {
  calidad: CMICalidadDashboard;
}

const PRIORIDAD_STYLE = {
  Alta: { bg: "#fde0e0", border: "#e63535", text: "#7a0000" },
  Media: { bg: "#fff3cd", border: "#e6a800", text: "#7a5000" },
  Baja: { bg: "#dbeeff", border: "#1a6fdb", text: "#003d8f" },
} as const;

export function CmiProcesosCalidadSection({ calidad }: CmiProcesosCalidadSectionProps) {
  const [subprocesoOpen, setSubprocesoOpen] = useState(false);
  const [detalleOpen, setDetalleOpen] = useState(false);

  const recomendaciones = useMemo(() => {
    const dims = [...calidad.alertas_dim].sort((a, b) => a.score - b.score);
    return dims.slice(0, 3).map((d) => {
      const prioridad = d.score < 70 ? "Alta" : d.score < 90 ? "Media" : "Baja";
      const afectados = calidad.registros
        .filter((r) => (r.criterios[d.dimension] ?? "").toUpperCase().includes("NO"))
        .map((r) => r.tematica)
        .filter((v, i, arr) => v && arr.indexOf(v) === i)
        .slice(0, 5);
      return { dimension: d.dimension, score: d.score, prioridad, afectados };
    });
  }, [calidad.alertas_dim, calidad.registros]);

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

  return (
    <section className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-2">
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
            <h4 className="mb-2 text-sm font-bold text-slate-800">Dimensiones de calidad</h4>
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

      {recomendaciones.length > 0 && (
        <div>
          <h4 className="mb-3 text-sm font-bold text-slate-800">Recomendaciones priorizadas</h4>
          <div className="grid gap-3 sm:grid-cols-3">
            {recomendaciones.map((r) => {
              const style = PRIORIDAD_STYLE[r.prioridad as keyof typeof PRIORIDAD_STYLE];
              return (
                <div
                  key={r.dimension}
                  className="rounded-xl border-2 p-4"
                  style={{ backgroundColor: style.bg, borderColor: style.border }}
                >
                  <p className="text-xs font-bold" style={{ color: style.text }}>
                    Prioridad {r.prioridad} · {r.dimension} ({r.score}%)
                  </p>
                  {r.afectados.length > 0 ? (
                    <ul className="mt-2 space-y-1 text-xs text-slate-700">
                      {r.afectados.map((a) => (
                        <li key={a}>• {a}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-xs text-slate-500">Sin indicadores puntuales identificados.</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
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

      {calidad.registros.length > 0 && (
        <details open={detalleOpen} onToggle={(e) => setDetalleOpen(e.currentTarget.open)}>
          <summary className="cursor-pointer text-sm font-bold text-slate-800">
            Detalle por indicador ({calidad.registros.length})
          </summary>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Temática</th>
                  <th className="px-4 py-3">Proceso</th>
                  <th className="px-4 py-3">Subproceso</th>
                  {dims.map((d) => (
                    <th key={d} className="px-3 py-3 text-center">
                      {d}
                    </th>
                  ))}
                  <th className="px-4 py-3 text-right">% Calidad</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {calidad.registros.map((r, i) => (
                  <tr key={`${r.tematica}-${i}`}>
                    <td className="px-4 py-3 font-medium">{r.tematica}</td>
                    <td className="px-4 py-3 text-slate-600">{r.proceso}</td>
                    <td className="px-4 py-3 text-slate-600">{r.subproceso}</td>
                    {dims.map((d) => {
                      const v = (r.criterios[d] ?? "").toUpperCase();
                      const ok = v.includes("NO") ? false : v.length > 0;
                      return (
                        <td key={d} className="px-3 py-3 text-center">
                          {v ? (ok ? "✅" : "⚠️") : "—"}
                        </td>
                      );
                    })}
                    <td className="px-4 py-3 text-right font-semibold">
                      {r.pct_calidad != null ? `${r.pct_calidad}%` : "—"}
                    </td>
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
