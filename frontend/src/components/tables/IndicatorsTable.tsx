import type { Indicator } from "@/lib/types";

const BADGE: Record<string, string> = {
  Peligro: "bg-red-100 text-red-800",
  Alerta: "bg-amber-100 text-amber-800",
  Cumplimiento: "bg-green-100 text-green-800",
  Sobrecumplimiento: "bg-blue-100 text-blue-800",
};

function formatPct(value?: number) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${Math.round(value * 1000) / 10}%`;
}

interface IndicatorsTableProps {
  items: Indicator[];
  total?: number;
}

export function IndicatorsTable({ items, total }: IndicatorsTableProps) {
  if (!items.length) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
        No hay indicadores para los filtros seleccionados.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      {total != null && (
        <div className="border-b border-slate-100 px-4 py-2 text-xs text-slate-500">
          Mostrando {items.length} de {total} indicadores
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-base">
          <thead className="bg-slate-50 text-sm uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Indicador</th>
              <th className="px-4 py-3">Proceso</th>
              <th className="px-4 py-3">Categoría</th>
              <th className="px-4 py-3 text-right">Cumplimiento</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((row, idx) => (
              <tr key={`${row.Id}-${idx}`} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-sm text-slate-600">{row.Id}</td>
                <td className="max-w-xs truncate px-4 py-3 text-slate-800" title={row.Indicador}>
                  {row.Indicador ?? "—"}
                </td>
                <td className="px-4 py-3 text-slate-600">{row.Proceso ?? "—"}</td>
                <td className="px-4 py-3">
                  {row.Categoria ? (
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        BADGE[row.Categoria] ?? "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {row.Categoria}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-4 py-3 text-right font-medium text-slate-800">
                  {formatPct(row.Cumplimiento_norm)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
