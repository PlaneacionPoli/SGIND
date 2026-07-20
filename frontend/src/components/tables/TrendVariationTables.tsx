export interface TrendVariationItem {
  indicador: string;
  linea: string;
  linea_color: string;
  variacion: number;
  positive: boolean;
}

function TrendTable({
  title,
  items,
  positive,
}: {
  title: string;
  items: TrendVariationItem[];
  positive: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h4 className="mb-3 text-sm font-semibold text-slate-700">{title}</h4>
      {items.length === 0 ? (
        <p className="text-sm text-slate-500">Sin variaciones para mostrar.</p>
      ) : (
        <table className="w-full text-base">
          <thead>
            <tr className="border-b border-slate-100 text-left text-sm text-slate-500">
              <th className="pb-2 pr-2">Indicador</th>
              <th className="pb-2 pr-2">Línea</th>
              <th className="pb-2 text-right">Variación</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={`${item.indicador}-${item.variacion}`} className="border-b border-slate-50">
                <td className="py-2 pr-2 font-medium text-slate-800">{item.indicador}</td>
                <td className="py-2 pr-2">
                  <span
                    className="rounded-full px-2 py-0.5 text-xs font-semibold text-white"
                    style={{ backgroundColor: item.linea_color }}
                  >
                    {item.linea}
                  </span>
                </td>
                <td
                  className={`py-2 text-right font-bold ${
                    positive ? "text-emerald-600" : "text-red-600"
                  }`}
                >
                  {item.variacion > 0 ? "+" : ""}
                  {Number.isFinite(item.variacion) ? item.variacion.toFixed(1) : "—"}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export function TrendVariationTables({
  mejoraron = [],
  enRiesgo = [],
  periodoComparacion = "",
}: {
  mejoraron?: TrendVariationItem[];
  enRiesgo?: TrendVariationItem[];
  periodoComparacion?: string;
}) {
  return (
    <div className="space-y-3">
      {periodoComparacion ? (
        <p className="text-xs text-slate-500" dangerouslySetInnerHTML={{ __html: periodoComparacion }} />
      ) : null}
      <div className="grid gap-4 lg:grid-cols-2">
        <TrendTable title="Indicadores que mejoraron" items={mejoraron} positive />
        <TrendTable title="Indicadores en riesgo" items={enRiesgo} positive={false} />
      </div>
    </div>
  );
}
