"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SemaphoreItem } from "@/lib/types";

const COLORS: Record<string, string> = {
  Peligro: "#ef4444",
  Alerta: "#f59e0b",
  Cumplimiento: "#22c55e",
  Sobrecumplimiento: "#3b82f6",
};

interface SemaphoreChartProps {
  data: SemaphoreItem[];
}

export function SemaphoreChart({ data }: SemaphoreChartProps) {
  if (!data.length) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-400">
        Sin datos de semáforo
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="categoria" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Bar dataKey="count" name="Indicadores" radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.categoria} fill={COLORS[entry.categoria] ?? "#94a3b8"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
