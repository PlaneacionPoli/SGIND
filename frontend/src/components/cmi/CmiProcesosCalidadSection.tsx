"use client";

import type { CMICalidadDashboard } from "@/lib/types";

interface CmiProcesosCalidadSectionProps {
  calidad: CMICalidadDashboard;
}

export function CmiProcesosCalidadSection({ calidad }: CmiProcesosCalidadSectionProps) {
  if (!calidad.disponible) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        {calidad.mensaje ?? "Mapa de calidad no disponible."}
      </div>
    );
  }

  const score = calidad.score_global ?? 0;
  const scoreColor = score >= 90 ? "text-emerald-700" : score >= 70 ? "text-amber-700" : "text-red-700";
  const scoreBg = score >= 90 ? "bg-emerald-50" : score >= 70 ? "bg-amber-50" : "bg-red-50";

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h3 className="text-lg font-semibold text-slate-800">Evaluación de calidad de datos</h3>
        <div className={`rounded-full px-4 py-2 text-sm font-bold ${scoreBg} ${scoreColor}`}>
          Score global: {score}%
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <KpiCard label="Registros" value={String(calidad.kpis.total_registros)} />
        <KpiCard label="Subprocesos" value={String(calidad.kpis.total_subprocesos)} />
        <KpiCard label="Promedio" value={calidad.kpis.promedio != null ? `${calidad.kpis.promedio}%` : "—"} />
      </div>

      {Object.keys(calidad.dim_scores).length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h4 className="mb-4 text-sm font-bold text-slate-800">Dimensiones de calidad</h4>
          <div className="space-y-3">
            {Object.entries(calidad.dim_scores).map(([dim, val]) => {
              const color = calidad.dim_colors[dim] ?? "#1A3A5C";
              return (
                <div key={dim}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="font-medium text-slate-700">{dim}</span>
                    <span className="font-bold" style={{ color }}>
                      {val}%
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${Math.min(100, val)}%`, backgroundColor: color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {calidad.alertas_dim.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-4">
          <h4 className="mb-2 text-sm font-bold text-amber-900">Dimensiones por debajo del 90%</h4>
          <ul className="space-y-1 text-sm text-amber-800">
            {calidad.alertas_dim.map((a) => (
              <li key={a.dimension}>
                {a.dimension}: {a.score}%
              </li>
            ))}
          </ul>
        </div>
      )}

      {calidad.por_proceso.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Proceso</th>
                <th className="px-4 py-3 text-right">% Calidad</th>
                <th className="px-4 py-3 text-right">Cumple</th>
                <th className="px-4 py-3 text-right">Parcial</th>
                <th className="px-4 py-3 text-right">No cumple</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {calidad.por_proceso.map((p) => (
                <tr key={p.Proceso}>
                  <td className="px-4 py-3 font-medium">{p.Proceso}</td>
                  <td className="px-4 py-3 text-right font-semibold">{p.pct_calidad}%</td>
                  <td className="px-4 py-3 text-right text-emerald-700">{p.cumple}</td>
                  <td className="px-4 py-3 text-right text-amber-700">{p.parcial}</td>
                  <td className="px-4 py-3 text-right text-red-700">{p.no_cumple}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-center shadow-sm">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-poli-navy">{value}</p>
    </div>
  );
}
