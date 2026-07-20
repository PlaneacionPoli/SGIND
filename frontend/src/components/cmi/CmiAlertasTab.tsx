"use client";

import { useMemo, useState } from "react";
import type { Indicator } from "@/lib/types";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";
import { fmtMeta, fmtEjecucion } from "@/lib/formatValor";

interface CmiAlertasTabProps {
  peligro: number;
  alerta: number;
  items: Indicator[];
  onOpenFicha?: (id: string) => void;
}

export function CmiAlertasTab({ peligro, alerta, items, onOpenFicha }: CmiAlertasTabProps) {
  const [severidad, setSeveridad] = useState("Todos");
  const [linea, setLinea] = useState("Todas");

  const lineas = useMemo(() => {
    const set = new Set(items.map((i) => i.Linea).filter(Boolean) as string[]);
    return ["Todas", ...Array.from(set).sort()];
  }, [items]);

  const filtered = useMemo(() => {
    return items.filter((ind) => {
      const nivel = ind["Nivel de cumplimiento"] as string | undefined;
      if (severidad !== "Todos" && nivel !== severidad) return false;
      if (linea !== "Todas" && ind.Linea !== linea) return false;
      return true;
    });
  }, [items, severidad, linea]);

  if (!items.length) {
    return (
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-8 text-center">
        <p className="text-lg font-semibold text-emerald-800">¡Excelente!</p>
        <p className="mt-1 text-sm text-emerald-700">
          No hay alertas activas (Peligro o Alerta) en este periodo.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-slate-800">Centro de Alertas y Notificaciones</h3>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg bg-red-100 p-5 text-center shadow-sm">
          <p className="text-3xl font-bold text-red-800">{peligro}</p>
          <p className="text-sm font-bold text-red-700">En Peligro Crítico (&lt; 80%)</p>
        </div>
        <div className="rounded-lg bg-amber-100 p-5 text-center shadow-sm">
          <p className="text-3xl font-bold text-amber-800">{alerta}</p>
          <p className="text-sm font-bold text-amber-700">En Alerta (80% – 99%)</p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-600">Filtrar por Nivel</span>
          <select
            value={severidad}
            onChange={(e) => setSeveridad(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="Todos">Todos</option>
            <option value="Peligro">Peligro</option>
            <option value="Alerta">Alerta</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-600">Filtrar por Línea</span>
          <select
            value={linea}
            onChange={(e) => setLinea(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2"
          >
            {lineas.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </label>
      </div>

      <h4 className="text-sm font-semibold text-slate-700">Matriz de Alertas</h4>

      {filtered.length === 0 ? (
        <p className="text-sm text-slate-500">No hay alertas que coincidan con los filtros.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-100">
              <tr>
                <th className="px-3 py-2">Indicador</th>
                <th className="px-3 py-2">Línea</th>
                <th className="px-3 py-2">Meta</th>
                <th className="px-3 py-2">Ejecución</th>
                <th className="px-3 py-2">%</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((ind) => (
                <tr key={ind.Id ?? ind.Indicador} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-medium">{ind.Indicador}</td>
                  <td className="px-3 py-2">{ind.Linea}</td>
                  <td className="px-3 py-2">{fmtMeta(ind as Record<string, unknown>)}</td>
                  <td className="px-3 py-2">{fmtEjecucion(ind as Record<string, unknown>)}</td>
                  <td className="px-3 py-2 font-semibold">{fmtPct(ind.cumplimiento_pct as number | undefined)}</td>
                  <td className="px-3 py-2">
                    <NivelBadge nivel={ind["Nivel de cumplimiento"] as string | undefined} />
                  </td>
                  <td className="px-3 py-2">
                    {ind.Id && onOpenFicha && (
                      <button
                        type="button"
                        onClick={() => onOpenFicha(String(ind.Id))}
                        className="rounded bg-poli-navy px-2 py-1 text-xs font-semibold text-white"
                      >
                        Ver ficha
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
