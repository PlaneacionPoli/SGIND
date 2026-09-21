"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchPlanIndicadorDetalle } from "@/lib/api";
import { PmFactorBadge } from "./PmFactorBadge";
import { parseFactorNum } from "./pmFactorTheme";

interface PmIndicadorSeleccion {
  factor: string;
  indicador: string;
}

interface PmIndicadorModalProps {
  seleccion: PmIndicadorSeleccion | null;
  onClose: () => void;
}

/** Modal de detalle de un indicador del Plan — paridad con
 * pages/plan_mejoramiento.py::_open_indicador_modal. */
export function PmIndicadorModal({ seleccion, onClose }: PmIndicadorModalProps) {
  const query = useQuery({
    queryKey: ["plan-indicador-detalle", seleccion?.factor, seleccion?.indicador],
    queryFn: () => fetchPlanIndicadorDetalle({ factor: seleccion!.factor, indicador: seleccion!.indicador }),
    enabled: !!seleccion,
  });

  if (!seleccion) return null;
  const d = query.data;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <h3 className="text-lg font-bold text-poli-navy">{seleccion.indicador}</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-slate-500 hover:bg-slate-100"
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>
        <div className="space-y-4 px-6 py-5 text-sm">
          {query.isLoading ? (
            <div className="h-40 animate-pulse rounded-lg bg-slate-100" />
          ) : !d ? (
            <p className="text-slate-500">No se encontró información del indicador.</p>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <PmFactorBadge factorNum={parseFactorNum(d.factor)} variant="full" />
                <span className="text-xs font-semibold text-slate-500">{d.factor}</span>
              </div>
              <div>
                <p className="font-semibold text-slate-700">Característica</p>
                <p className="text-slate-600">{d.caracteristica}</p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="font-semibold text-slate-700">Acción de mejora</p>
                  <p className="text-slate-600">{d.accion_mejora}</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-700">Tipo</p>
                  <p className="text-slate-600">{d.tipo}</p>
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="font-semibold text-slate-700">Estado / Aprobación</p>
                  <p className="text-slate-600">
                    {d.estado} / {d.estado_aprobacion}
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-slate-700">Responsable</p>
                  <p className="text-slate-600">{d.responsable}</p>
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="font-semibold text-slate-700">Fuente</p>
                  <p className="text-slate-600">{d.fuente}</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-700">Periodicidad</p>
                  <p className="text-slate-600">{d.periodicidad}</p>
                </div>
              </div>
              <div>
                <p className="font-semibold text-slate-700">Fórmula</p>
                <p className="text-slate-600">{d.formula}</p>
              </div>
              <div>
                <p className="font-semibold text-slate-700">Observación de desempeño</p>
                <p className="text-slate-600">{d.observacion}</p>
              </div>
              <div>
                <p className="mb-2 font-semibold text-slate-700">Meta y ejecución — 2025 y 2026</p>
                <div className="overflow-hidden rounded-lg border border-slate-200">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                      <tr>
                        <th className="px-3 py-2 text-left">Año</th>
                        <th className="px-3 py-2 text-right">Meta</th>
                        <th className="px-3 py-2 text-right">Ejecución</th>
                        <th className="px-3 py-2 text-right">% Cumplimiento</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 tabular-nums text-slate-700">
                      {d.cumplimiento.map((f) => (
                        <tr key={f.anio}>
                          <td className="px-3 py-2 font-semibold text-slate-800">{f.anio}</td>
                          <td className="px-3 py-2 text-right">{f.meta}</td>
                          <td className="px-3 py-2 text-right">{f.ejecucion}</td>
                          <td className="px-3 py-2 text-right font-semibold text-slate-800">{f.cump}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div>
                <p className="mb-2 font-semibold text-slate-700">Metas 2026 – 2030</p>
                <div className="overflow-hidden rounded-lg border border-slate-200">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                      <tr>
                        {d.metas_futuras.map((m) => (
                          <th key={m.anio} className="px-3 py-2 text-right">
                            {m.anio}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="tabular-nums text-slate-700">
                      <tr>
                        {d.metas_futuras.map((m) => (
                          <td key={m.anio} className="px-3 py-2 text-right">
                            {m.meta}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
