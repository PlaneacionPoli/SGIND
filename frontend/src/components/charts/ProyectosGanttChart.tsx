"use client";

import dynamic from "next/dynamic";
import type { Layout } from "plotly.js";
import type Plotly from "plotly.js";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export interface ProyectoGanttItem {
  id: string;
  nombre: string;
  linea: string;
  linea_color: string;
  anio_inicio: number;
  anio_fin: number;
  duracion_anios: number;
  anios_activos: number[];
  cumplimiento: number;
  estado: string;
}

export interface ProyectosGanttData {
  anio_min: number;
  anio_max: number;
  items: ProyectoGanttItem[];
}

function formatYearRange(inicio: number, fin: number): string {
  return inicio === fin ? String(inicio) : `${inicio}–${fin}`;
}

function truncateLabel(text: string, max = 42): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

interface ProyectosGanttChartProps {
  data: ProyectosGanttData;
}

export function ProyectosGanttChart({ data }: ProyectosGanttChartProps) {
  const items = data.items ?? [];
  if (!items.length) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-slate-500">
        Sin datos de cronograma para mostrar.
      </div>
    );
  }

  const labels = items.map((item) => truncateLabel(item.nombre));
  const durations = items.map((item) => item.anio_fin - item.anio_inicio + 1);
  const bases = items.map((item) => item.anio_inicio - 0.5);
  const colors = items.map((item) => item.linea_color);
  const barText = items.map((item) => formatYearRange(item.anio_inicio, item.anio_fin));

  const trace = {
    type: "bar" as const,
    orientation: "h" as const,
    y: labels,
    x: durations,
    base: bases,
    marker: {
      color: colors,
      line: { color: "#FFFFFF", width: 1 },
    },
    text: barText,
    textposition: "inside" as const,
    insidetextanchor: "middle" as const,
    textfont: { family: "Inter, sans-serif", size: 10, color: "#FFFFFF" },
    hovertemplate:
      "<b>%{customdata[0]}</b><br>" +
      "Línea: %{customdata[1]}<br>" +
      "Vigencia: %{customdata[2]}<br>" +
      "Años activos: %{customdata[3]}<br>" +
      "Cumplimiento: %{customdata[4]:.1f}% · %{customdata[5]}<extra></extra>",
    customdata: items.map((item) => {
      const vigencia = formatYearRange(item.anio_inicio, item.anio_fin);
      const duracionLabel = item.duracion_anios === 1 ? "1 año" : `${item.duracion_anios} años`;
      return [
        item.nombre,
        item.linea,
        `${vigencia} (${duracionLabel})`,
        item.anios_activos.join(", "),
        item.cumplimiento,
        item.estado,
      ];
    }),
  };

  const height = Math.max(420, items.length * 30 + 120);
  const { anio_min, anio_max } = data;

  const layout: Partial<Layout> = {
    margin: { t: 24, l: 220, r: 24, b: 48 },
    height,
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    xaxis: {
      title: { text: "Horizonte PDI (años)", font: { size: 12, color: "#475569" } },
      range: [anio_min - 0.6, anio_max + 0.6],
      tickmode: "linear",
      dtick: 1,
      tickvals: Array.from({ length: anio_max - anio_min + 1 }, (_, i) => anio_min + i),
      gridcolor: "#E2E8F0",
      zeroline: false,
    },
    yaxis: {
      automargin: true,
      tickfont: { size: 10, color: "#334155" },
    },
    bargap: 0.25,
    showlegend: false,
  };

  return (
    <div className="w-full">
      <Plot
        data={[trace as Plotly.Data]}
        layout={layout}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: `${height}px` }}
        useResizeHandler
      />
    </div>
  );
}
