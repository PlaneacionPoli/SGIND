"use client";

import dynamic from "next/dynamic";
import type { Layout } from "plotly.js";
import type Plotly from "plotly.js";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export interface SunburstPlotlyData {
  ids?: string[];
  labels: string[];
  parents: string[];
  values: number[];
  colors: string[];
  text: string[];
  customdata?: Array<[number] | number[]>;
}

interface SunburstPlotlyChartProps {
  data: SunburstPlotlyData;
}

export function SunburstPlotlyChart({ data }: SunburstPlotlyChartProps) {
  if (!data.labels?.length) {
    return (
      <div className="flex h-80 items-center justify-center text-sm text-slate-500">
        Sin datos para el gráfico
      </div>
    );
  }

  const trace = {
    type: "sunburst" as const,
    ids: data.ids ?? data.labels,
    labels: data.labels,
    parents: data.parents,
    values: data.values,
    branchvalues: "remainder" as const,
    marker: {
      colors: data.colors,
      line: { color: "#FFFFFF", width: 1 },
    },
    customdata: data.customdata,
    text: data.text,
    textinfo: "text" as const,
    texttemplate: "%{text}",
    insidetextorientation: "auto" as const,
    textposition: "auto" as const,
    textfont: { family: "Inter, sans-serif", size: 11, color: "#062A4F" },
    insidetextfont: { family: "Inter, sans-serif", size: 11, color: "#062A4F" },
    hovertemplate: "<b>%{label}</b><br>Promedio cumplimiento: %{customdata[0]:.1f}%<extra></extra>",
    domain: { x: [0, 1] as [number, number], y: [0, 1] as [number, number] },
    maxdepth: 2,
    sort: false,
    separation: 0,
    uniformtext: { minsize: 5, mode: "show" as const },
  };

  const layout: Partial<Layout> = {
    margin: { t: 10, l: 10, r: 10, b: 10 },
    height: 780,
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    showlegend: false,
  };

  return (
    <div className="w-full">
      <Plot
        data={[trace as Plotly.Data]}
        layout={layout}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: "780px" }}
        useResizeHandler
      />
    </div>
  );
}
