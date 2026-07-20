"use client";

import dynamic from "next/dynamic";
import type { Layout } from "plotly.js";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export interface CmiBarLineaItem {
  linea: string;
  cumplimiento: number;
  color: string;
}

interface CmiBarLineasPlotlyProps {
  data: CmiBarLineaItem[];
}

export function CmiBarLineasPlotly({ data }: CmiBarLineasPlotlyProps) {
  if (!data.length) {
    return (
      <div className="flex h-72 items-center justify-center text-sm text-slate-500">
        Sin datos por línea
      </div>
    );
  }

  const sorted = [...data].sort((a, b) => a.cumplimiento - b.cumplimiento);
  const maxX = Math.max(120, ...sorted.map((d) => d.cumplimiento * 1.1));
  const labels = sorted.map((d) =>
    d.linea.length > 28 ? `${d.linea.slice(0, 26)}…` : d.linea.replace(/_/g, " ")
  );
  const textLabels = sorted.map((d) => `${d.cumplimiento.toFixed(1)}%`);

  const trace = {
    type: "bar" as const,
    orientation: "h" as const,
    y: labels,
    x: sorted.map((d) => d.cumplimiento),
    text: textLabels,
    textposition: "outside" as const,
    textfont: { size: 11, color: "#374151" },
    marker: {
      color: sorted.map((d) => d.color),
      line: { color: "rgba(0,0,0,0)", width: 0 },
    },
    hovertemplate: "<b>%{y}</b><br>Cumplimiento: %{x:.1f}%<extra></extra>",
  };

  const layout: Partial<Layout> = {
    margin: { l: 140, r: 48, t: 24, b: 20 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    showlegend: false,
    xaxis: {
      range: [0, maxX],
      gridcolor: "#E5E7EB",
      ticksuffix: "%",
      tickfont: { size: 11, color: "#6B7280" },
    },
    yaxis: {
      tickfont: { size: 11, color: "#374151" },
      automargin: true,
    },
    shapes: [
      {
        type: "line",
        x0: 100,
        x1: 100,
        y0: -0.5,
        y1: sorted.length - 0.5,
        line: { color: "#6B7280", width: 2, dash: "dash" },
      },
    ],
    annotations: [
      {
        x: 100,
        y: 1.04,
        xref: "x",
        yref: "paper",
        text: "Meta 100%",
        showarrow: false,
        font: { size: 10, color: "#6B7280" },
      },
    ],
  };

  return (
    <Plot
      data={[trace]}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: Math.max(280, sorted.length * 42) }}
      useResizeHandler
    />
  );
}
