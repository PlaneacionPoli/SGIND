export interface YoYRow {
  linea: string;
  anio_actual: number;
  cumplimiento_actual: number | null;
  cumplimiento_anterior: number | null;
  variacion_pp: number | null;
  en_riesgo: number;
}

interface YoYTableProps {
  rows: YoYRow[];
}

export function YoYTable({ rows }: YoYTableProps) {
  if (!rows.length) {
    return (
      <p className="text-sm text-slate-500">Sin datos de variación interanual para el periodo.</p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-slate-600">Línea</th>
            <th className="px-4 py-2 text-right font-medium text-slate-600">Año ant.</th>
            <th className="px-4 py-2 text-right font-medium text-slate-600">Año act.</th>
            <th className="px-4 py-2 text-right font-medium text-slate-600">Variación</th>
            <th className="px-4 py-2 text-right font-medium text-slate-600">En riesgo</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row) => (
            <tr key={row.linea}>
              <td className="px-4 py-2 font-medium text-slate-800">{row.linea}</td>
              <td className="px-4 py-2 text-right text-slate-600">
                {row.cumplimiento_anterior != null ? `${row.cumplimiento_anterior}%` : "—"}
              </td>
              <td className="px-4 py-2 text-right text-slate-800">
                {row.cumplimiento_actual != null ? `${row.cumplimiento_actual}%` : "—"}
              </td>
              <td
                className={`px-4 py-2 text-right font-medium ${
                  row.variacion_pp == null
                    ? "text-slate-400"
                    : row.variacion_pp >= 0
                      ? "text-emerald-600"
                      : "text-red-600"
                }`}
              >
                {row.variacion_pp != null ? `${row.variacion_pp > 0 ? "+" : ""}${row.variacion_pp} pp` : "—"}
              </td>
              <td className="px-4 py-2 text-right text-amber-600">{row.en_riesgo}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
