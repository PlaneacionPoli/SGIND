"use client";

import type { CMIVistaRapidaLinea } from "@/lib/types";
import { fmtPct } from "@/components/cmi/nivelUtils";

const DOT_COLORS = {
  sobrecumplimiento: "#1D4ED8",
  cumplimiento: "#166534",
  alerta: "#B45309",
  riesgo: "#B71C1C",
  pendiente: "#475569",
};

interface CmiVistaRapidaCardsProps {
  lineas: CMIVistaRapidaLinea[];
  onVerLinea?: (lineaKey: string) => void;
}

export function CmiVistaRapidaCards({ lineas, onVerLinea }: CmiVistaRapidaCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {lineas.map((linea) => (
        <div
          key={linea.linea_key}
          className="overflow-hidden rounded-2xl border border-[#E6ECF5] bg-[#F8FAFF] shadow-[0_2px_8px_rgba(26,58,92,0.08)] transition hover:-translate-y-0.5 hover:border-[#D0DDF0] hover:shadow-[0_6px_16px_rgba(26,58,92,0.14)]"
        >
          <div
            className="flex items-center justify-between gap-2 px-4 py-3"
            style={{ backgroundColor: linea.color }}
          >
            <span className="truncate text-sm font-bold text-white">
              {linea.linea_display ?? linea.linea.replace(/_/g, " ")}
            </span>
            <span
              className="shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-bold"
              style={{
                backgroundColor: linea.estado_bg ?? "#FFFFFF",
                color: linea.estado_text ?? "#1A3A5C",
                borderColor: `${linea.estado_color ?? linea.color}33`,
              }}
            >
              {linea.estado_label ?? linea.estado}
            </span>
          </div>

          <div className="space-y-4 p-4">
            <div className="grid grid-cols-[1.2fr_0.8fr_0.8fr] gap-2">
              <div
                className="rounded-xl border px-3 py-3 text-center"
                style={{
                  backgroundColor: linea.estado_bg ?? "#F8FAFF",
                  borderColor: "#DFE8DF",
                }}
              >
                <p
                  className="text-2xl font-extrabold leading-none sm:text-3xl"
                  style={{ color: linea.estado_color ?? linea.color }}
                >
                  {linea.estado_icon ?? ""} {fmtPct(linea.cumplimiento)}
                </p>
                <p className="mt-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Cumplimiento
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white px-2 py-3 text-center">
                <p className="text-xl font-extrabold text-slate-900">{linea.total_indicadores}</p>
                <p className="mt-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Indicadores
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white px-2 py-3 text-center">
                <p className="text-xl font-extrabold text-slate-900">{linea.n_objetivos}</p>
                <p className="mt-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Objetivos
                </p>
              </div>
            </div>

            <div>
              <div className="mb-1.5 flex justify-between text-[10px] font-semibold text-slate-500">
                <span>Progreso</span>
                <span>{linea.progress_meta_label ?? "Meta 100%"}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-md bg-[#E1E7F0]">
                <div
                  className="h-full rounded-md transition-all"
                  style={{
                    width: `${linea.progress_width ?? Math.min(100, linea.cumplimiento)}%`,
                    backgroundColor: linea.estado_color ?? linea.color,
                  }}
                />
              </div>
              <DistribucionBar
                total={linea.total_indicadores}
                sobrecumplimiento={linea.n_sobrecumplimiento}
                cumplimiento={linea.n_cumplimiento}
                alerta={linea.n_alerta}
                riesgo={linea.n_riesgo}
              />
              <div className="mt-2 grid grid-cols-2 gap-1 text-[11px] font-semibold text-[#3D4E66]">
                <LegendDot color={DOT_COLORS.sobrecumplimiento} label={`${linea.n_sobrecumplimiento} Sobrecump.`} />
                <LegendDot color={DOT_COLORS.cumplimiento} label={`${linea.n_cumplimiento} Cumpl.`} />
                <LegendDot color={DOT_COLORS.alerta} label={`${linea.n_alerta} Alerta`} />
                <LegendDot color={DOT_COLORS.riesgo} label={`${linea.n_riesgo} Riesgo`} />
              </div>
            </div>

            {onVerLinea && (
              <button
                type="button"
                onClick={() => onVerLinea(linea.linea_key)}
                className="w-full rounded-lg border border-dashed border-[#D9E2EF] bg-[#EEF4FD] px-3 py-2.5 text-xs font-semibold text-[#1A3A5C] transition hover:border-[#BFD4EE] hover:bg-[#E4EEFB]"
              >
                Ver análisis detallado →
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

function DistribucionBar({
  total,
  sobrecumplimiento,
  cumplimiento,
  alerta,
  riesgo,
}: {
  total: number;
  sobrecumplimiento: number;
  cumplimiento: number;
  alerta: number;
  riesgo: number;
}) {
  const pendiente = Math.max(0, total - sobrecumplimiento - cumplimiento - alerta - riesgo);
  const segments = [
    { count: sobrecumplimiento, color: DOT_COLORS.sobrecumplimiento },
    { count: cumplimiento, color: DOT_COLORS.cumplimiento },
    { count: alerta, color: DOT_COLORS.alerta },
    { count: riesgo, color: DOT_COLORS.riesgo },
    { count: pendiente, color: DOT_COLORS.pendiente },
  ].filter((s) => s.count > 0);

  const sum = segments.reduce((a, s) => a + s.count, 0) || 1;

  return (
    <div className="mt-2 flex h-1.5 gap-0.5 overflow-hidden rounded-sm">
      {segments.map((seg, i) => (
        <div
          key={i}
          className="h-full rounded-sm"
          style={{ width: `${(seg.count / sum) * 100}%`, backgroundColor: seg.color }}
          title={`${seg.count} indicadores`}
        />
      ))}
    </div>
  );
}
