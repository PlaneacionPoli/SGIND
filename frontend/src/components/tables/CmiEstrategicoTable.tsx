import type { ResumenLineaObjetivo } from "@/lib/types";

interface CmiEstrategicoTableProps {
  objetivos: ResumenLineaObjetivo[];
  color: string;
}

export function CmiEstrategicoTable({ objetivos, color }: CmiEstrategicoTableProps) {
  if (!objetivos.length) {
    return (
      <div className="flex h-32 items-center justify-center text-sm text-slate-500">
        Sin indicadores CMI registrados para esta línea.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {objetivos.map((obj) => (
        <div key={obj.objetivo} className="overflow-hidden rounded-lg border border-slate-200">
          <div className="px-3 py-2 text-xs font-bold uppercase tracking-wide text-white" style={{ backgroundColor: color }}>
            {obj.objetivo}
          </div>
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-[11px] uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2 font-semibold">Indicador</th>
                <th className="px-3 py-2 font-semibold">Meta</th>
                <th className="px-3 py-2 font-semibold">Ejecución</th>
                <th className="px-3 py-2 font-semibold">Cumplimiento</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {obj.indicadores.map((ind, idx) => (
                <tr key={`${obj.objetivo}-${idx}`}>
                  <td className="px-3 py-2 text-slate-700">{ind.indicador}</td>
                  <td className="px-3 py-2 text-slate-600">{ind.meta ?? "—"}</td>
                  <td className="px-3 py-2 text-slate-600">{ind.ejecucion ?? "—"}</td>
                  <td className="px-3 py-2">
                    <span
                      className="rounded px-2 py-0.5 text-[11px] font-bold text-white"
                      style={{ backgroundColor: ind.nivel_color }}
                    >
                      {ind.cumplimiento != null ? `${ind.cumplimiento.toFixed(1)}%` : "—"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
