interface PmSparklineProps {
  values: number[];
  width?: number;
  height?: number;
  color?: string;
}

/** Mini-gráfico de línea inline por fila — equivalente a
 * st.column_config.LineChartColumn en la pestaña Métricas del legacy. */
export function PmSparkline({ values, width = 96, height = 28, color = "#1A3A5C" }: PmSparklineProps) {
  if (!values || values.length < 2) {
    return <span className="text-xs text-slate-400">—</span>;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / (values.length - 1);
  const points = values.map((v, i) => `${i * step},${height - ((v - min) / range) * height}`).join(" ");

  return (
    <svg width={width} height={height} className="overflow-visible" aria-hidden="true">
      <polyline points={points} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
