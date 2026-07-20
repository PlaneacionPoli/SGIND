export interface ProyectoDetalleRow {
  linea: string;
  id: string;
  nombre: string;
  cumplimiento: number;
  estado: string;
  nivel: string;
}

export interface RetoDetalleRow {
  linea: string;
  cumplimiento: number;
  nivel: string;
}

interface DetailTablesProps {
  vista: string;
  rows?: ProyectoDetalleRow[] | RetoDetalleRow[];
}

function groupByLinea<T extends { linea: string }>(rows: T[]): Map<string, T[]> {
  const map = new Map<string, T[]>();
  for (const row of rows) {
    const key = row.linea || "Sin línea";
    const list = map.get(key) ?? [];
    list.push(row);
    map.set(key, list);
  }
  return map;
}

export function DetailTables({ vista, rows }: DetailTablesProps) {
  if (!rows?.length) return null;

  if (vista === "proyectos") {
    const proyectos = rows as ProyectoDetalleRow[];
    const grouped = groupByLinea(proyectos);
    return (
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-800">Detalle por línea estratégica</h3>
        {Array.from(grouped.entries()).map(([linea, items]) => (
          <div key={linea} className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700">
              {linea}
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-base">
                <thead>
                  <tr className="border-b border-slate-100 text-left text-sm uppercase tracking-wide text-slate-500">
                    <th className="px-4 py-2">ID</th>
                    <th className="px-4 py-2">Proyecto</th>
                    <th className="px-4 py-2">Cumplimiento</th>
                    <th className="px-4 py-2">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id} className="border-b border-slate-50 last:border-0">
                      <td className="px-4 py-2 font-mono text-sm text-slate-600">{item.id}</td>
                      <td className="px-4 py-2 text-slate-800">{item.nombre}</td>
                      <td className="px-4 py-2 font-semibold text-slate-700">{item.cumplimiento}%</td>
                      <td className="px-4 py-2">
                        <span
                          className="rounded-full px-2 py-0.5 text-xs font-medium"
                          style={{
                            backgroundColor:
                              item.estado === "Cerrado"
                                ? "#DCFCE7"
                                : item.estado === "En ejecución"
                                  ? "#FEF3C7"
                                  : "#F1F5F9",
                            color:
                              item.estado === "Cerrado"
                                ? "#166534"
                                : item.estado === "En ejecución"
                                  ? "#92400E"
                                  : "#475569",
                          }}
                        >
                          {item.estado}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (vista === "retos") {
    const retos = rows as RetoDetalleRow[];
    return (
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700">
          Cumplimiento por línea estratégica
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-base">
            <thead>
              <tr className="border-b border-slate-100 text-left text-sm uppercase tracking-wide text-slate-500">
                <th className="px-4 py-2">Línea</th>
                <th className="px-4 py-2">Cumplimiento</th>
                <th className="px-4 py-2">Nivel</th>
              </tr>
            </thead>
            <tbody>
              {retos.map((item) => (
                <tr key={item.linea} className="border-b border-slate-50 last:border-0">
                  <td className="px-4 py-2 text-slate-800">{item.linea}</td>
                  <td className="px-4 py-2 font-semibold text-slate-700">{item.cumplimiento}%</td>
                  <td className="px-4 py-2 text-slate-600">{item.nivel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return null;
}
