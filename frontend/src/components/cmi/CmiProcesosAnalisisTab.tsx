"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import type { Layout } from "plotly.js";
import type { CMIProcesoComparativa, CMIProcesosDashboardResponse } from "@/lib/types";
import { CmiProcesosCalidadSection } from "@/components/cmi/CmiProcesosCalidadSection";
import { paletteColor } from "@/components/cmi/cmiChartColors";
import { fmtPct } from "@/components/cmi/nivelUtils";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface CmiProcesosAnalisisTabProps {
  data: CMIProcesosDashboardResponse;
  comparativa?: CMIProcesoComparativa[];
}

const PROPUESTA_STYLES = [
  { key: "plan_mejoramiento", label: "Plan de mejoramiento", bg: "#fef3c7", border: "#92400e" },
  { key: "pdi", label: "PDI 2026-2030", bg: "#dbeafe", border: "#1e40af" },
  { key: "sga", label: "SGA", bg: "#ede9fe", border: "#4c1d95" },
  { key: "retos", label: "Retos", bg: "#ecfccb", border: "#365314" },
] as const;

export function CmiProcesosAnalisisTab({ data, comparativa = [] }: CmiProcesosAnalisisTabProps) {
  const { analisis_avanzado, calidad, meta, anio, mes_nombre } = data;
  const av = analisis_avanzado ?? {};
  const propuesta = av.propuesta_accion;
  const historico = useMemo(() => av.historico_indicadores ?? [], [av.historico_indicadores]);

  const [histId, setHistId] = useState(historico[0]?.id ?? "");

  const histChart = useMemo(() => {
    const item = historico.find((h) => h.id === histId);
    return item?.puntos ?? [];
  }, [historico, histId]);

  return (
    <div className="space-y-10">
      <p className="text-sm text-slate-600">
        Propuesta y variación usan filtros del panel · Histórico usa catálogo global ({anio}).
        Base comparativa: {meta.base_anio}
        {meta.base_mes ? ` (mes ${meta.base_mes})` : ""} · Corte filtrado: {mes_nombre}.
      </p>

      {propuesta && (
        <section>
          <h3 className="mb-4 text-lg font-semibold text-slate-800">Propuesta de acción</h3>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {PROPUESTA_STYLES.map((s) => (
              <div
                key={s.key}
                className="min-h-[120px] rounded-xl border-2 p-4"
                style={{ backgroundColor: s.bg, borderColor: s.border }}
              >
                <p className="text-xs font-bold" style={{ color: s.border }}>
                  {s.label}
                </p>
                <p className="mt-2 text-sm leading-snug text-slate-800">
                  {propuesta[s.key as keyof typeof propuesta] as string}
                </p>
              </div>
            ))}
          </div>
          {propuesta.top_criticos?.length > 0 && (
            <div className="mt-4 rounded-xl border border-red-200 bg-red-50/50 p-4">
              <h4 className="mb-2 text-sm font-bold text-red-900">Top indicadores críticos</h4>
              <ul className="space-y-1 text-sm text-slate-800">
                {propuesta.top_criticos.map((t) => (
                  <li key={t.indicador}>
                    <strong>{t.indicador}</strong> ({t.proceso}) — {fmtPct(t.cumplimiento)}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {av.insights && (
        <section className="grid gap-4 lg:grid-cols-2">
          <InsightCard icon="🏆" title="Mayor mejora" text={av.insights.mejora_proceso} accent="#43A047" />
          <InsightCard icon="⚡" title="Mayor riesgo" text={av.insights.riesgo_proceso} accent="#D32F2F" />
        </section>
      )}

      <section className="grid gap-6 lg:grid-cols-2">
        <VariationTable title="Procesos con mayor mejora" rows={av.variacion_procesos?.mejoraron ?? []} positive />
        <VariationTable title="Procesos en mayor riesgo" rows={av.variacion_procesos?.empeoraron ?? []} positive={false} />
      </section>

      {comparativa.length > 0 && (
        <section>
          <h3 className="mb-3 text-lg font-semibold text-slate-800">Comparativa de procesos (vista global)</h3>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3 text-left">Proceso</th>
                  <th className="px-4 py-3 text-right">Actual</th>
                  <th className="px-4 py-3 text-right">{meta.base_anio}</th>
                  <th className="px-4 py-3 text-right">Variación</th>
                </tr>
              </thead>
              <tbody>
                {comparativa.slice(0, 10).map((r) => (
                  <tr key={r.proceso} className="border-t border-slate-100">
                    <td className="px-4 py-3 font-medium">{r.proceso}</td>
                    <td className="px-4 py-3 text-right font-semibold" style={{ color: r.color }}>
                      {fmtPct(r.cumplimiento)}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">{fmtPct(r.cumplimiento_anterior)}</td>
                    <td
                      className={`px-4 py-3 text-right font-bold ${
                        (r.variacion ?? 0) >= 0 ? "text-emerald-700" : "text-red-700"
                      }`}
                    >
                      {r.variacion != null ? `${r.variacion > 0 ? "+" : ""}${r.variacion} pp` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {historico.length > 0 && (
        <section>
          <h3 className="mb-3 text-lg font-semibold text-slate-800">Evolución histórica del indicador</h3>
          <label className="mb-3 flex flex-col gap-1 text-sm">
            <span className="font-medium text-slate-600">Indicador</span>
            <select
              value={histId}
              onChange={(e) => setHistId(e.target.value)}
              className="max-w-xl rounded-lg border border-slate-200 px-3 py-2"
            >
              {historico.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.indicador}
                </option>
              ))}
            </select>
          </label>
          {histChart.length > 0 && (
            <Plot
              data={[
                {
                  type: "scatter",
                  mode: "lines+markers",
                  x: histChart.map((p) => p.periodo),
                  y: histChart.map((p) => p.cumplimiento),
                  line: { color: "#1A3A5C", width: 2 },
                  marker: {
                    size: 8,
                    color: histChart.map((_, i) => paletteColor(i)),
                  },
                  hovertemplate: "<b>%{x}</b><br>Cumplimiento: %{y:.1f}%<extra></extra>",
                },
              ]}
              layout={
                {
                  margin: { l: 48, r: 24, t: 16, b: 48 },
                  height: 300,
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                  yaxis: { range: [0, 120], ticksuffix: "%", gridcolor: "#E2E8F0" },
                  xaxis: { gridcolor: "#E2E8F0" },
                  shapes: [
                    { type: "line", x0: 0, x1: 1, xref: "paper", y0: 100, y1: 100, line: { color: "#2E7D32", dash: "dot" } },
                    { type: "line", x0: 0, x1: 1, xref: "paper", y0: 80, y1: 80, line: { color: "#F9A825", dash: "dot" } },
                  ],
                  font: { family: "inherit", size: 11 },
                } as Partial<Layout>
              }
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%" }}
              useResizeHandler
            />
          )}
        </section>
      )}

      <details className="rounded-xl border border-slate-200 bg-white p-4">
        <summary className="cursor-pointer text-sm font-bold text-slate-800">
          Evaluación de calidad de datos (Monitoreo de Información)
        </summary>
        <div className="mt-4">
          <CmiProcesosCalidadSection calidad={calidad} />
        </div>
      </details>
    </div>
  );
}

function InsightCard({
  icon,
  title,
  text,
  accent,
}: {
  icon: string;
  title: string;
  text: string;
  accent: string;
}) {
  return (
    <div
      className="rounded-xl border-l-[5px] bg-white p-5 shadow-[0_2px_8px_rgba(26,58,92,0.06)]"
      style={{ borderLeftColor: accent }}
    >
      <p className="text-2xl">{icon}</p>
      <p className="mt-2 font-bold text-slate-900">{title}</p>
      <p className="mt-1 text-sm text-slate-600">{text}</p>
    </div>
  );
}

function VariationTable({
  title,
  rows,
  positive,
}: {
  title: string;
  rows: Array<{ name: string; change: number }>;
  positive: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.06)]">
      <h4 className="mb-4 text-sm font-bold text-slate-800">{title}</h4>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-500">Sin datos comparativos.</p>
      ) : (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-xs uppercase text-slate-500">
              <th className="py-2 text-left">Proceso</th>
              <th className="py-2 text-right">Variación</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.name} className="border-t border-slate-100">
                <td className="py-2 text-slate-800">{r.name}</td>
                <td
                  className={`py-2 text-right font-bold ${positive ? "text-emerald-700" : "text-red-700"}`}
                >
                  {r.change > 0 ? "+" : ""}
                  {r.change.toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
