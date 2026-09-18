"use client";

import dynamic from "next/dynamic";
import type { Data, Layout } from "plotly.js";
import { getFactorColor } from "./pmFactorTheme";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface PmFactorBarChartProps {
  data: Array<{ factor: string; factorNum?: number | null; value: number }>;
  valueSuffix?: string;
  emptyMessage?: string;
  onFactorClick?: (factor: string) => void;
}

/** Barras horizontales por Factor CNA — usado tanto en la pestaña Indicadores
 * (conteo/cumplimiento por factor) como en Métricas (chart_metricas_por_factor,
 * clic en una barra filtra la tabla por ese factor). Cada barra toma el color
 * temático fijo de su factor (ver pmFactorTheme.ts), no un color plano único —
 * la misma identidad visual que las insignias de factor en la tabla. */
export function PmFactorBarChart({
  data,
  valueSuffix = "",
  emptyMessage = "Sin datos",
  onFactorClick,
}: PmFactorBarChartProps) {
  if (!data.length) {
    return <div className="flex h-48 items-center justify-center text-sm text-slate-500">{emptyMessage}</div>;
  }

  const sorted = [...data].sort((a, b) => a.value - b.value);
  const labels = sorted.map((d) => (d.factor.length > 40 ? `${d.factor.slice(0, 38)}…` : d.factor));

  const trace: Data = {
    type: "bar",
    orientation: "h",
    y: labels,
    x: sorted.map((d) => d.value),
    marker: { color: sorted.map((d) => getFactorColor(d.factorNum)) },
    text: sorted.map((d) => `${d.value}${valueSuffix}`),
    textposition: "auto",
    hovertemplate: `%{y}: %{x}${valueSuffix}<extra></extra>`,
  };

  const layout: Partial<Layout> = {
    margin: { l: 8, r: 24, t: 8, b: 24 },
    height: Math.max(220, sorted.length * 34),
    xaxis: { showgrid: true, zeroline: false },
    yaxis: { automargin: true },
  };

  return (
    <Plot
      data={[trace]}
      layout={layout}
      config={{
        displayModeBar: true,
        modeBarButtonsToRemove: [
          "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d",
          "autoScale2d", "resetScale2d", "hoverClosestCartesian", "hoverCompareCartesian", "toggleSpikelines",
        ],
        displaylogo: false,
        responsive: true,
      }}
      style={{ width: "100%" }}
      onClick={
        onFactorClick
          ? (event) => {
              const idx = event.points?.[0]?.pointIndex;
              if (idx != null) onFactorClick(sorted[idx].factor);
            }
          : undefined
      }
    />
  );
}
