"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export interface FactorNivelStackedItem {
  factor: string;
  niveles: Array<{ nivel: string; cantidad: number; color: string }>;
  color: string;
}

interface PmFactorNivelStackedChartProps {
  data: FactorNivelStackedItem[];
}

export function PmFactorNivelStackedChart({ data }: PmFactorNivelStackedChartProps) {
  if (!data.length) {
    return (
      <div className="flex h-72 items-center justify-center text-sm text-slate-500">
        Sin datos para el gráfico de factor y nivel
      </div>
    );
  }

  const nivelColors = new Map<string, string>();
  const chartData = data.map((item) => {
    const row: Record<string, string | number> = { factor: item.factor };
    for (const n of item.niveles) {
      row[n.nivel] = n.cantidad;
      if (!nivelColors.has(n.nivel)) nivelColors.set(n.nivel, n.color);
    }
    return row;
  });
  const niveles = Array.from(nivelColors.keys());

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="factor"
          tick={{ fontSize: 10 }}
          angle={-30}
          textAnchor="end"
          interval={0}
          height={70}
        />
        <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {niveles.map((nivel) => (
          <Bar key={nivel} dataKey={nivel} name={nivel} stackId="nivel" fill={nivelColors.get(nivel)} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
