"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import type { OMPlanAccionActividad } from "@/lib/types";

interface Props {
  numeroOm: string;
  cargando: boolean;
  actividades: OMPlanAccionActividad[] | undefined;
  onCerrar: () => void;
}

export function PlanAccionModal({ numeroOm, cargando, actividades, onCerrar }: Props) {
  useEffect(() => {
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && onCerrar();
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [onCerrar]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4" onClick={onCerrar}>
      <div role="dialog" aria-modal="true" aria-label={`Plan de acción de la OM ${numeroOm}`} className="max-h-[80vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-3 flex items-center justify-between">
          <h4 className="text-base font-bold text-slate-900">Plan de acción — OM {numeroOm}</h4>
          <button type="button" aria-label="Cerrar" onClick={onCerrar} className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100">
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>
        {cargando ? (
          <div className="h-24 animate-pulse rounded-lg bg-slate-200" />
        ) : !actividades?.length ? (
          <p className="text-sm text-slate-500">OM {numeroOm} sin actividades asociadas.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-3 py-2">Acción</th>
                  <th className="px-3 py-2">Responsable</th>
                  <th className="px-3 py-2">Avance</th>
                  <th className="px-3 py-2">Estado (Plan)</th>
                  <th className="px-3 py-2">Estado (OM)</th>
                </tr>
              </thead>
              <tbody>
                {actividades.map((act, idx) => (
                  <tr key={act.id_accion || idx} className="border-t border-slate-200">
                    <td className="px-3 py-2">{act.accion || "—"}</td>
                    <td className="px-3 py-2">{act.responsable || "—"}</td>
                    <td className="px-3 py-2">{act.avance || "—"}</td>
                    <td className="px-3 py-2">{act.estado_plan || "—"}</td>
                    <td className="px-3 py-2">{act.estado_om || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
