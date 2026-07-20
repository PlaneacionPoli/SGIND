"use client";

import dynamic from "next/dynamic";
import type { Layout } from "plotly.js";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export interface CumplimientoBarItem {
  label: string;
  value: number | null;
  color: string;
}

interface CmiCumplimientoHorizBarPlotlyProps {
  data: CumplimientoBarItem[];
  title?: string;
  emptyMessage?: string;
}

export function CmiCumplimientoHorizBarPlotly({
  data,
  title,
  emptyMessage = "Sin datos",
}: CmiCumplimientoHorizBarPlotlyProps) {
  if (!data.length) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-slate-500">{emptyMessage}</div>
    );
  }

  const sorted = [...data].sort((a, b) => (a.value ?? 0) - (b.value ?? 0));
  const labels = sorted.map((d) => (d.label.length > 36 ? `${d.label.slice(0, 34)}…` : d.label));

  const trace = {
    type: "bar" as const,
    orientation: "h" as const,
    y: labels,
    x: sorted.map((d) => d.value ?? 0),
    marker: { color: sorted.map((d) => d.color) },
    text: sorted.map((d) => (d.value != null ? `${d.value.toFixed(1)}%` : "—")),
    textposition: "outside" as const,
    hovertemplate: "<b>%{y}</b><br>Cumplimiento: %{x:.1f}%<extra></extra>",
  };

  const layout: Partial<Layout> = {
    title: title ? { text: title, font: { size: 12, color: "#334155" } } : undefined,
    margin: { l: 160, r: 48, t: title ? 36 : 16, b: 16 },
    height: Math.max(240, sorted.length * 34),
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    showlegend: false,
    xaxis: { range: [0, 120], ticksuffix: "%", gridcolor: "#E2E8F0" },
    yaxis: { automargin: true },
    font: { family: "inherit", size: 11 },
  };

  return (
    <Plot
      data={[trace]}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );
}
