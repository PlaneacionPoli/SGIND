"use client";

import { getFactorColor } from "./pmFactorTheme";

interface PmFactorRingsProps {
  data: Array<{ factor: string; factorNum?: number | null; value: number }>;
  valueSuffix?: string;
  emptyMessage?: string;
  onFactorClick?: (factor: string) => void;
}

const SIZE = 84;
const STROKE = 8;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/** Anillos de progreso por Factor CNA — reemplaza la barra horizontal Plotly.
 * Cada anillo toma el color temático fijo de su factor (pmFactorTheme.ts),
 * la misma identidad visual que las insignias de factor en la tabla, y
 * comunica el estado relativo de un vistazo sin ejes ni leyenda. */
export function PmFactorRings({
  data,
  valueSuffix = "",
  emptyMessage = "Sin datos",
  onFactorClick,
}: PmFactorRingsProps) {
  if (!data.length) {
    return <div className="flex h-48 items-center justify-center text-sm text-slate-500">{emptyMessage}</div>;
  }

  const max = Math.max(...data.map((d) => d.value), 1);
  const sorted = [...data].sort((a, b) => b.value - a.value);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
      {sorted.map((d) => {
        const pct = valueSuffix === "%" ? Math.max(0, Math.min(100, d.value)) : (d.value / max) * 100;
        const color = getFactorColor(d.factorNum);
        const offset = CIRCUMFERENCE * (1 - pct / 100);
        const displayValue = valueSuffix === "%" ? Math.round(d.value * 10) / 10 : Math.round(d.value);

        return (
          <div
            key={d.factor}
            onClick={onFactorClick ? () => onFactorClick(d.factor) : undefined}
            className={`flex flex-col items-center gap-2 rounded-xl p-3 text-center transition-colors ${
              onFactorClick ? "cursor-pointer hover:bg-slate-50" : ""
            }`}
            title={d.factor}
          >
            <div className="relative" style={{ width: SIZE, height: SIZE }}>
              <svg width={SIZE} height={SIZE} className="-rotate-90">
                <circle cx={SIZE / 2} cy={SIZE / 2} r={RADIUS} fill="none" stroke="#E2E8F0" strokeWidth={STROKE} />
                <circle
                  cx={SIZE / 2}
                  cy={SIZE / 2}
                  r={RADIUS}
                  fill="none"
                  stroke={color}
                  strokeWidth={STROKE}
                  strokeLinecap="round"
                  strokeDasharray={CIRCUMFERENCE}
                  strokeDashoffset={offset}
                  style={{ transition: "stroke-dashoffset 0.4s ease" }}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-slate-800">
                {displayValue}
                {valueSuffix}
              </div>
            </div>
            <span className="line-clamp-2 text-[11px] font-medium leading-tight text-slate-600">{d.factor}</span>
          </div>
        );
      })}
    </div>
  );
}
