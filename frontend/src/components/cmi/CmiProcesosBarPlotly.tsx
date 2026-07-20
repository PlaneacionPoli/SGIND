"use client";

import type { CMIProcesoBar } from "@/lib/types";

// Paleta por nivel de cumplimiento
const NIVEL_COLOR = {
  sobrecumplimiento: "#1D4ED8",
  cumplimiento: "#166534",
  alerta: "#B45309",
  peligro: "#B71C1C",
  sin_dato: "#94A3B8",
};

function nivelColor(pct: number | null): string {
  if (pct == null) return NIVEL_COLOR.sin_dato;
  if (pct >= 100) return NIVEL_COLOR.sobrecumplimiento;
  if (pct >= 95) return NIVEL_COLOR.cumplimiento;
  if (pct >= 80) return NIVEL_COLOR.alerta;
  return NIVEL_COLOR.peligro;
}

function nivelBg(pct: number | null): string {
  if (pct == null) return "#F1F5F9";
  if (pct >= 100) return "#EFF6FF";
  if (pct >= 95) return "#F0FDF4";
  if (pct >= 80) return "#FFFBEB";
  return "#FFF1F2";
}

interface CmiProcesosBarPlotlyProps {
  data: CMIProcesoBar[];
  baseAnio?: number;
  maxHeight?: number;
  compact?: boolean;
  limit?: number;
}

export function CmiProcesosBarPlotly({
  data,
  baseAnio,
  compact = false,
  limit,
}: CmiProcesosBarPlotlyProps) {
  if (!data.length) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-slate-500">
        Sin datos por proceso
      </div>
    );
  }

  const sorted = [...data]
    .sort((a, b) => (b.cumplimiento ?? 0) - (a.cumplimiento ?? 0))
    .slice(0, limit ?? data.length);

  const maxPct = Math.max(...sorted.map((d) => Math.max(d.cumplimiento ?? 0, d.cumplimiento_anterior ?? 0)), 100);
  const scale = (v: number) => Math.min((v / maxPct) * 100, 100);

  const maxNameLen = compact ? 28 : 38;

  return (
    <div className="w-full space-y-1.5">
      {/* Leyenda */}
      <div className="mb-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] font-semibold text-slate-500">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-[#1D4ED8]" /> Sobrecumplimiento ≥100%
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-[#166534]" /> Cumplimiento 95–99%
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-[#B45309]" /> Alerta 80–94%
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-[#B71C1C]" /> Peligro &lt;80%
        </span>
      </div>

      {sorted.map((d) => {
        const pct = d.cumplimiento;
        const prev = d.cumplimiento_anterior;
        const color = nivelColor(pct);
        const bg = nivelBg(pct);
        const delta = pct != null && prev != null ? pct - prev : null;
        const name = d.proceso.length > maxNameLen ? `${d.proceso.slice(0, maxNameLen - 1)}…` : d.proceso;

        return (
          <div
            key={d.proceso}
            className="rounded-lg px-3 py-2"
            style={{ backgroundColor: bg }}
            title={`${d.proceso}: ${pct != null ? pct.toFixed(1) + "%" : "—"}${prev != null ? ` · ${baseAnio}: ${prev.toFixed(1)}%` : ""}`}
          >
            {/* Fila superior: nombre + valor + delta */}
            <div className="mb-1 flex items-center justify-between gap-2">
              <span
                className={`truncate font-semibold text-slate-800 ${compact ? "text-[11px]" : "text-xs"}`}
                title={d.proceso}
              >
                {name}
              </span>
              <div className="flex shrink-0 items-center gap-2">
                {delta != null && (
                  <span
                    className="text-[10px] font-bold"
                    style={{ color: delta >= 0 ? "#166534" : "#B71C1C" }}
                  >
                    {delta >= 0 ? "▲" : "▼"} {Math.abs(delta).toFixed(1)}pp
                  </span>
                )}
                <span
                  className="min-w-[48px] text-right text-xs font-extrabold"
                  style={{ color }}
                >
                  {pct != null ? `${pct.toFixed(1)}%` : "—"}
                </span>
              </div>
            </div>

            {/* Barra actual */}
            <div className="relative h-2 overflow-hidden rounded-full bg-slate-200">
              {/* Barra año anterior (fondo semitransparente) */}
              {prev != null && (
                <div
                  className="absolute left-0 top-0 h-full rounded-full opacity-30"
                  style={{ width: `${scale(prev)}%`, backgroundColor: color }}
                />
              )}
              {/* Barra actual */}
              {pct != null && (
                <div
                  className="absolute left-0 top-0 h-full rounded-full transition-all duration-500"
                  style={{ width: `${scale(pct)}%`, backgroundColor: color }}
                />
              )}
              {/* Línea de meta 100% */}
              <div
                className="absolute top-0 h-full w-px bg-slate-400 opacity-60"
                style={{ left: `${scale(100)}%` }}
              />
            </div>

            {/* Referencia año anterior */}
            {prev != null && baseAnio && (
              <p className="mt-0.5 text-[9px] text-slate-400">
                {baseAnio}: {prev.toFixed(1)}%
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
