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
    <div className="space-y-5">
      {objetivos.map((obj) => (
        <div key={obj.objetivo} className="overflow-hidden rounded-lg border border-slate-200">
          <div
            className="px-4 py-2.5 text-sm font-bold uppercase tracking-wide text-white"
            style={{ backgroundColor: color }}
          >
            {obj.objetivo}
          </div>
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3 font-bold">Indicador</th>
                <th className="px-4 py-3 font-bold">Meta</th>
                <th className="px-4 py-3 font-bold">Ejecución</th>
                <th className="px-4 py-3 font-bold">Cumplimiento</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {obj.indicadores.map((ind, idx) => (
                <tr key={`${obj.objetivo}-${idx}`} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-700">{ind.indicador}</td>
                  <td className="px-4 py-3 text-slate-600">{ind.meta ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-600">{ind.ejecucion ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-block rounded px-2.5 py-1 text-sm font-bold text-white"
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
