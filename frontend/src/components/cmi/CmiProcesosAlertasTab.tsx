"use client";

import { useMemo, useState } from "react";
import type { CMIAlertaCritica, Indicator } from "@/lib/types";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";
import { fmtMeta, fmtEjecucion } from "@/lib/formatValor";

interface CmiProcesosAlertasTabProps {
  peligro: number;
  alerta: number;
  items: Indicator[];
  alertasCriticas: CMIAlertaCritica[];
  onOpenFicha?: (id: string) => void;
}

export function CmiProcesosAlertasTab({
  peligro,
  alerta,
  items,
  alertasCriticas,
  onOpenFicha,
}: CmiProcesosAlertasTabProps) {
  const [severidad, setSeveridad] = useState("Todos");
  const [proceso, setProceso] = useState("Todos");

  const procesos = useMemo(() => {
    const set = new Set(
      items
        .map((i) => (i as Record<string, unknown>).Proceso_padre as string | undefined)
        .filter(Boolean) as string[]
    );
    return ["Todos", ...Array.from(set).sort()];
  }, [items]);

  const filtered = useMemo(() => {
    return items.filter((ind) => {
      const nivel = ind["Nivel de cumplimiento"] as string | undefined;
      const proc = (ind as Record<string, unknown>).Proceso_padre as string | undefined;
      if (severidad !== "Todos" && nivel !== severidad) return false;
      if (proceso !== "Todos" && proc !== proceso) return false;
      return true;
    });
  }, [items, severidad, proceso]);

  return (
    <div className="space-y-8">
      {alertasCriticas.length > 0 && (
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-800">Alertas críticas (vista global)</h3>
            <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-bold text-red-800">
              {alertasCriticas.length} en peligro &lt;80%
            </span>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {alertasCriticas.map((a) => (
              <div
                key={a.id || a.indicador}
                className="rounded-xl border border-red-200 bg-gradient-to-br from-red-50 to-white p-4 shadow-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    {onOpenFicha && a.id ? (
                      <button
                        type="button"
                        onClick={() => onOpenFicha(a.id)}
                        className="text-left font-bold text-red-900 hover:underline"
                      >
                        {a.indicador}
                      </button>
                    ) : (
                      <p className="font-bold text-red-900">{a.indicador}</p>
                    )}
                    <p className="mt-1 text-xs text-slate-600">{a.proceso}</p>
                    <span
                      className="mt-1 inline-block rounded px-2 py-0.5 text-[10px] font-bold text-white"
                      style={{ backgroundColor: a.tipo_color }}
                    >
                      {a.tipo_proceso}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-extrabold text-red-700">{fmtPct(a.cumplimiento)}</p>
                    {a.brecha_pp != null && (
                      <p className="text-xs text-red-600">Brecha: {a.brecha_pp} pp</p>
                    )}
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-700">{a.diagnostico}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 className="mb-4 text-lg font-semibold text-slate-800">Centro de alertas (filtros aplicados)</h3>
        <p className="mb-4 text-xs text-slate-500">
          Respeta unidad, proceso, subproceso, clasificación y frecuencia del panel superior.
        </p>

        {items.length === 0 ? (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-8 text-center">
            <p className="text-lg font-semibold text-emerald-800">¡Excelente!</p>
            <p className="mt-1 text-sm text-emerald-700">No hay alertas en el corte filtrado.</p>
          </div>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg p-5 text-center" style={{ backgroundColor: "#FFCDD2" }}>
                <p className="text-3xl font-bold" style={{ color: "#C62828" }}>
                  {peligro}
                </p>
                <p className="text-sm font-bold" style={{ color: "#C62828" }}>
                  Peligro (&lt; 80%)
                </p>
              </div>
              <div className="rounded-lg p-5 text-center" style={{ backgroundColor: "#FEF3D0" }}>
                <p className="text-3xl font-bold" style={{ color: "#F9A825" }}>
                  {alerta}
                </p>
                <p className="text-sm font-bold" style={{ color: "#F9A825" }}>
                  Alerta (80% – 99%)
                </p>
              </div>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <label className="flex flex-col gap-1 text-sm">
                <span className="font-medium text-slate-600">Severidad</span>
                <select
                  value={severidad}
                  onChange={(e) => setSeveridad(e.target.value)}
                  className="rounded-lg border border-slate-200 px-3 py-2"
                >
                  {["Todos", "Peligro", "Alerta"].map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1 text-sm">
                <span className="font-medium text-slate-600">Proceso</span>
                <select
                  value={proceso}
                  onChange={(e) => setProceso(e.target.value)}
                  className="rounded-lg border border-slate-200 px-3 py-2"
                >
                  {procesos.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Indicador</th>
                    <th className="px-4 py-3">Proceso</th>
                    <th className="px-4 py-3 text-right">Meta</th>
                    <th className="px-4 py-3 text-right">Ejecución</th>
                    <th className="px-4 py-3 text-right">Cumpl.</th>
                    <th className="px-4 py-3">Nivel</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((ind) => {
                    const id = String(ind.Id ?? "");
                    const proc = (ind as Record<string, unknown>).Proceso_padre as string | undefined;
                    return (
                      <tr key={id || String(ind.Indicador)} className="hover:bg-slate-50">
                        <td className="px-4 py-3">
                          {onOpenFicha && id ? (
                            <button
                              type="button"
                              onClick={() => onOpenFicha(id)}
                              className="font-medium text-poli-blue hover:underline"
                            >
                              {ind.Indicador}
                            </button>
                          ) : (
                            <span className="font-medium text-slate-800">{ind.Indicador}</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-slate-600">{proc ?? "—"}</td>
                        <td className="px-4 py-3 text-right">{fmtMeta(ind as Record<string, unknown>)}</td>
                        <td className="px-4 py-3 text-right">{fmtEjecucion(ind as Record<string, unknown>)}</td>
                        <td className="px-4 py-3 text-right font-semibold">
                          {fmtPct(ind.cumplimiento_pct as number)}
                        </td>
                        <td className="px-4 py-3">
                          <NivelBadge nivel={ind["Nivel de cumplimiento"] as string} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
