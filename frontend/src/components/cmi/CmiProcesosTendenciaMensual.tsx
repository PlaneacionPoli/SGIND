"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { colorCumplimiento } from "@/components/cmi/cmiChartColors";
import { fmtPct } from "@/components/cmi/nivelUtils";
import { fetchCMIProcesosTendencia } from "@/lib/api";
import type { CMITendenciaMensualResponse } from "@/lib/types";
import { useAuthReady } from "@/stores/auth-store";

interface Props {
  /** Si se indica, la tendencia es de ese proceso (y el detalle baja a sus subprocesos). */
  proceso?: string;
  subproceso?: string;
  titulo?: string;
}

const W = 640;
const H = 210;
const PAD_X = 40;
const PAD_T = 22;
const PAD_B = 46;

function Grafica({
  data,
  seleccionado,
  onSelect,
}: {
  data: CMITendenciaMensualResponse;
  seleccionado: number;
  onSelect: (mes: number) => void;
}) {
  const cerrados = data.serie.filter((p) => p.cerrado && p.cumplimiento != null);
  const vals = [...cerrados.map((p) => p.cumplimiento as number), 100, 80];
  const lo = Math.floor(Math.min(...vals) / 10) * 10 - 5;
  const hi = Math.ceil(Math.max(...vals) / 10) * 10 + 5;
  const x = (mes: number) => PAD_X + ((mes - 1) * (W - PAD_X * 2)) / 11;
  const y = (v: number) => H - PAD_B - ((v - lo) / (hi - lo)) * (H - PAD_B - PAD_T);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Cumplimiento mensual del año en curso">
      {[80, 100].map((ref) => (
        <g key={ref}>
          <line
            x1={PAD_X}
            x2={W - PAD_X}
            y1={y(ref)}
            y2={y(ref)}
            stroke={ref === 100 ? "#94A3B8" : "#FBBF24"}
            strokeDasharray="4 4"
          />
          <text x={W - PAD_X + 4} y={y(ref) + 3} fontSize={10} fill="#64748B">
            {ref}%
          </text>
        </g>
      ))}
      {cerrados.slice(1).map((p, k) => (
        <line
          key={p.mes}
          x1={x(cerrados[k].mes)}
          y1={y(cerrados[k].cumplimiento as number)}
          x2={x(p.mes)}
          y2={y(p.cumplimiento as number)}
          stroke="#1A3A5C"
          strokeWidth={2.5}
        />
      ))}
      {data.serie.map((p) => (
        <g
          key={p.mes}
          onClick={() => p.cerrado && p.cumplimiento != null && onSelect(p.mes)}
          className={p.cerrado ? "cursor-pointer" : undefined}
        >
          <title>
            {p.cerrado
              ? `${p.nombre}: ${p.cumplimiento != null ? p.cumplimiento.toFixed(1) + "%" : "sin dato"} · ${p.n_indicadores} indicadores con corte (${p.n_reportes_mes} reportaron en el mes)`
              : `${p.nombre}: mes aún no cerrado`}
          </title>
          {p.cerrado && p.cumplimiento != null && (
            <>
              <circle
                cx={x(p.mes)}
                cy={y(p.cumplimiento)}
                r={p.mes === seleccionado ? 7 : 4.5}
                fill={colorCumplimiento(p.cumplimiento)}
                stroke={p.mes === seleccionado ? "#0F172A" : "#fff"}
                strokeWidth={2}
              />
              <text
                x={x(p.mes)}
                y={y(p.cumplimiento) - 11}
                textAnchor="middle"
                fontSize={10}
                fontWeight={700}
                fill="#0F172A"
              >
                {p.cumplimiento.toFixed(1)}
              </text>
            </>
          )}
          <text x={x(p.mes)} y={H - 26} textAnchor="middle" fontSize={11} fill={p.cerrado ? "#334155" : "#CBD5E1"}>
            {p.nombre.slice(0, 3)}
          </text>
          <text x={x(p.mes)} y={H - 12} textAnchor="middle" fontSize={9} fill="#94A3B8">
            {p.cerrado && p.n_indicadores ? `n=${p.n_indicadores}` : ""}
          </text>
        </g>
      ))}
    </svg>
  );
}

/**
 * Cumplimiento de los 12 meses del año en curso. El filtro de mes es exclusivo de esta visual:
 * limita el corte al último mes cerrado y detalla el cumplimiento por proceso (o subproceso).
 */
export function CmiProcesosTendenciaMensual({ proceso, subproceso, titulo }: Props) {
  const { isAuthenticated } = useAuthReady();
  const [mes, setMes] = useState<number | undefined>(undefined);
  useEffect(() => setMes(undefined), [proceso, subproceso]);

  const q = useQuery({
    queryKey: ["cmi-procesos-tendencia", proceso, subproceso, mes],
    queryFn: () => fetchCMIProcesosTendencia({ proceso, subproceso, mes }),
    enabled: isAuthenticated,
    placeholderData: (prev) => prev,
  });
  const data = q.data;

  if (q.isLoading) return <div className="h-64 animate-pulse rounded-2xl bg-slate-200" />;
  if (!data || data.serie.length === 0 || data.ultimo_mes_cerrado === 0) {
    return (
      <p className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500">
        Aún no hay cortes mensuales cerrados del año en curso.
      </p>
    );
  }

  const sel = data.mes_seleccionado;
  const cierre = data.serie.find((p) => p.mes === sel);
  const maxN = Math.max(...data.detalle.map((d) => d.cumplimiento ?? 0), 100);
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h4 className="text-sm font-bold text-slate-800">{titulo ?? `Cumplimiento mensual ${data.anio}`}</h4>
          <p className="text-xs text-slate-500">
            Cada mes toma el último reporte de cada indicador hasta ese mes (Cierre, Promedio o Acumulado).
          </p>
        </div>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Corte (hasta el último mes cerrado)
          </span>
          <select
            value={sel}
            onChange={(e) => setMes(Number(e.target.value))}
            className="rounded-lg border border-slate-200 px-3 py-1.5"
          >
            {data.serie
              .filter((p) => p.cerrado)
              .map((p) => (
                <option key={p.mes} value={p.mes}>
                  {p.nombre}
                </option>
              ))}
          </select>
        </label>
      </div>

      <div className="grid gap-5 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <Grafica data={data} seleccionado={sel} onSelect={setMes} />
          <p className="mt-1 text-[11px] text-slate-500">
            n = indicadores con corte a ese mes. Los semestrales entran en junio, por eso el universo crece. Los
            meses posteriores al último cerrado no se muestran.
          </p>
        </div>
        <div className="lg:col-span-2">
          <p className="mb-2 text-xs font-semibold text-slate-700">
            {data.agrupado_por === "subproceso" ? "Por subproceso" : "Por proceso"} · corte{" "}
            {data.mes_seleccionado_nombre}
            {cierre?.cumplimiento != null && (
              <span className="ml-1 font-normal text-slate-500">(global {fmtPct(cierre.cumplimiento)})</span>
            )}
          </p>
          <ul className="max-h-60 space-y-1.5 overflow-y-auto pr-1">
            {data.detalle.map((d) => (
              <li key={d.nombre} className="text-[11px]">
                <div className="flex justify-between gap-2">
                  <span className="truncate text-slate-700" title={d.nombre}>
                    {d.nombre}
                  </span>
                  <span className="shrink-0 font-bold" style={{ color: colorCumplimiento(d.cumplimiento) }}>
                    {fmtPct(d.cumplimiento)}
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(((d.cumplimiento ?? 0) / maxN) * 100, 100)}%`,
                      backgroundColor: colorCumplimiento(d.cumplimiento),
                    }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
