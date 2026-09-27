import type { ResumenLineaObjetivo } from "@/lib/types";

interface CmiEstrategicoTableProps {
  objetivos: ResumenLineaObjetivo[];
  color: string;
}

// Réplica del bloque CMI Estratégico del proyecto de referencia: título
// "CMI Estratégico" y cada objetivo en una barra sólida del color de la
// línea, tabla con Meta/Ejecución alineados a la derecha y Cumplimiento
// centrado en texto de color (no badge de fondo).
export function CmiEstrategicoTable({ objetivos, color }: CmiEstrategicoTableProps) {
  return (
    <div>
      <div
        className="mb-3 rounded px-3 py-2 text-center text-sm font-black uppercase tracking-wide text-white"
        style={{ backgroundColor: color }}
      >
        CMI Estratégico
      </div>

      {!objetivos.length ? (
        <div className="flex h-24 items-center justify-center text-sm text-slate-500">
          Sin indicadores CMI disponibles.
        </div>
      ) : (
        <div className={`grid gap-3.5 ${objetivos.length === 1 ? "grid-cols-1" : "sm:grid-cols-2"}`}>
          {objetivos.map((obj) => (
            <div key={obj.objetivo}>
              <div
                className="mb-2.5 rounded px-3 py-2 text-center text-sm font-extrabold uppercase text-white"
                style={{ backgroundColor: color }}
              >
                {obj.objetivo}
              </div>
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="h-8 border-b-2 border-slate-200 bg-slate-100">
                    <th className="px-2.5 py-2 text-left font-bold text-slate-700">Indicador</th>
                    <th className="px-2.5 py-2 text-right font-bold text-slate-700">Meta</th>
                    <th className="px-2.5 py-2 text-right font-bold text-slate-700">Ejecución</th>
                    <th className="px-2.5 py-2 text-center font-bold text-slate-700">Cumplimiento</th>
                  </tr>
                </thead>
                <tbody>
                  {obj.indicadores.map((ind, idx) => (
                    <tr key={`${obj.objetivo}-${idx}`} className="h-9 border-b border-slate-100">
                      <td className="px-2.5 py-2 text-slate-700">{ind.indicador}</td>
                      <td className="px-2.5 py-2 text-right text-slate-600">{ind.meta ?? "—"}</td>
                      <td className="px-2.5 py-2 text-right text-slate-600">{ind.ejecucion ?? "—"}</td>
                      <td
                        className="px-2.5 py-2 text-center font-bold"
                        style={{ color: ind.nivel_color }}
                      >
                        {ind.cumplimiento != null ? `${Math.round(ind.cumplimiento)}%` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
