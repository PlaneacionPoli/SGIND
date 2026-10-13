"use client";

import dynamic from "next/dynamic";
import type { Data, Layout } from "plotly.js";
import { fmtValorSigno } from "@/lib/formatValor";
import type { FichaHistoricoPunto } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const fmtVar = (v: number | null | undefined) =>
  v == null ? "—" : `${v > 0 ? "▲ +" : v < 0 ? "▼ −" : "= "}${Math.abs(v).toFixed(1)} pp`;

const colorVar = (v: number | null | undefined) =>
  v == null || v === 0 ? "text-slate-500" : v > 0 ? "text-emerald-700" : "text-red-700";

/**
 * Evolución histórica COMPLETA del indicador (todos los años y cortes, sin depender del PDI):
 * barras Meta/Ejecución, línea de % de cumplimiento con la variación frente al corte anterior y
 * una tabla con los mismos valores. El eje X es categórico: los periodos "2026-05" NO deben
 * interpretarse como fechas.
 */
export function FichaHistoricoChart({ historico }: { historico: FichaHistoricoPunto[] }) {
  if (!historico.length) {
    return <p className="text-sm text-slate-500">Sin registros históricos para este indicador.</p>;
  }
  const x = historico.map((h) => h.etiqueta ?? h.periodo);
  const fmt = (v: number | null | undefined, h: FichaHistoricoPunto) =>
    v == null ? "—" : fmtValorSigno(v, h.signo, h.decimales);

  const data = [
    {
      type: "bar",
      name: "Meta",
      x,
      y: historico.map((h) => h.meta ?? null),
      marker: { color: "#F9A825" },
      customdata: historico.map((h) => fmt(h.meta, h)),
      hovertemplate: "<b>%{x}</b><br>Meta: %{customdata}<extra></extra>",
    },
    {
      type: "bar",
      name: "Ejecución",
      x,
      y: historico.map((h) => h.ejecucion ?? null),
      marker: { color: "#1A3A5C" },
      customdata: historico.map((h) => fmt(h.ejecucion, h)),
      hovertemplate: "<b>%{x}</b><br>Ejecución: %{customdata}<extra></extra>",
    },
    {
      type: "scatter",
      mode: "lines+markers+text",
      name: "% Cumplimiento",
      x,
      y: historico.map((h) => h.cumplimiento ?? null),
      yaxis: "y2",
      line: { color: "#2E7D32", width: 2 },
      marker: { size: 7, color: "#2E7D32" },
      text: historico.map((h) =>
        h.variacion_cumplimiento_pp == null
          ? ""
          : `${h.variacion_cumplimiento_pp > 0 ? "+" : h.variacion_cumplimiento_pp < 0 ? "−" : ""}${Math.abs(h.variacion_cumplimiento_pp).toFixed(1)}`,
      ),
      textposition: "top center",
      textfont: { size: 9, color: "#2E7D32" },
      customdata: historico.map((h) => fmtVar(h.variacion_cumplimiento_pp)),
      hovertemplate:
        "<b>%{x}</b><br>Cumplimiento: %{y:.1f}%<br>Variación vs corte anterior: %{customdata}<extra></extra>",
    },
  ] as Data[];

  const layout = {
    margin: { l: 56, r: 56, t: 10, b: 56 },
    height: 320,
    barmode: "group",
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    legend: { orientation: "h", y: 1.18 },
    yaxis: { title: { text: "Valor" }, gridcolor: "#E2E8F0" },
    yaxis2: { overlaying: "y", side: "right", ticksuffix: "%", title: { text: "% Cumplimiento" } },
    xaxis: { type: "category", tickangle: -45, gridcolor: "#E2E8F0" },
    font: { family: "inherit", size: 10 },
  } as Partial<Layout>;

  return (
    <div className="space-y-3">
      <Plot
        data={data}
        layout={layout}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%" }}
        useResizeHandler
      />
      <p className="text-[11px] text-slate-500">
        Los números sobre la línea verde son la variación del % de cumplimiento (puntos porcentuales) frente al
        corte anterior.
      </p>
      <div className="max-h-56 overflow-auto rounded-lg border border-slate-200">
        <table className="min-w-full text-xs">
          <thead className="sticky top-0 bg-slate-100 text-slate-600">
            <tr>
              <th className="px-2 py-1.5 text-left">Periodo</th>
              <th className="px-2 py-1.5 text-right">Meta</th>
              <th className="px-2 py-1.5 text-right">Ejecución</th>
              <th className="px-2 py-1.5 text-right">% Cumpl.</th>
              <th className="px-2 py-1.5 text-right">Variación</th>
            </tr>
          </thead>
          <tbody>
            {[...historico].reverse().map((h) => (
              <tr key={h.periodo} className="border-t border-slate-100">
                <td className="px-2 py-1.5 text-slate-700">{h.etiqueta ?? h.periodo}</td>
                <td className="px-2 py-1.5 text-right">{fmt(h.meta, h)}</td>
                <td className="px-2 py-1.5 text-right">{fmt(h.ejecucion, h)}</td>
                <td className="px-2 py-1.5 text-right font-semibold">
                  {h.cumplimiento == null ? "—" : `${h.cumplimiento.toFixed(1)}%`}
                </td>
                <td className={`px-2 py-1.5 text-right font-semibold ${colorVar(h.variacion_cumplimiento_pp)}`}>
                  {fmtVar(h.variacion_cumplimiento_pp)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
