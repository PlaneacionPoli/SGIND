"use client";

import { useId } from "react";

interface PmSparklineProps {
  values: number[];
  width?: number;
  height?: number;
  color?: string;
  trend?: "Creciente" | "Decreciente" | "Estable" | "—";
}

const TREND_DOT: Record<string, string> = {
  Creciente: "#2F9E44",
  Decreciente: "#E03131",
  Estable: "#64748B",
  "—": "#94A3B8",
};

/** Mini-gráfico de área por fila — equivalente a st.column_config.LineChartColumn
 * del legacy, pero con relleno degradado del color del factor y un punto final
 * coloreado por tendencia, para leer forma Y dirección del cambio de un
 * vistazo (la versión anterior solo mostraba la forma de la línea). */
export function PmSparkline({ values, width = 96, height = 28, color = "#1A3A5C", trend }: PmSparklineProps) {
  const gradientId = `pm-spark-${useId().replace(/:/g, "")}`;

  if (!values || values.length < 2) {
    return <span className="text-xs text-slate-400">—</span>;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / (values.length - 1);
  const coords = values.map((v, i) => [i * step, height - ((v - min) / range) * height] as const);
  const points = coords.map(([x, y]) => `${x},${y}`).join(" ");
  const areaPoints = `0,${height} ${points} ${width},${height}`;
  const [lastX, lastY] = coords[coords.length - 1];
  const dotColor = trend ? TREND_DOT[trend] ?? color : color;

  return (
    <svg width={width} height={height} className="overflow-visible" aria-hidden="true">
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.35} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#${gradientId})`} stroke="none" />
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle cx={lastX} cy={lastY} r={2.5} fill={dotColor} />
    </svg>
  );
}
