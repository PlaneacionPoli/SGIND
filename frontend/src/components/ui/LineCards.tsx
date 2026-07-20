import type { CMILinea } from "@/lib/types";

interface LineCardsProps {
  lineas: CMILinea[];
}

const LINE_COLORS = [
  "border-l-red-500",
  "border-l-blue-500",
  "border-l-emerald-500",
  "border-l-amber-500",
  "border-l-violet-500",
  "border-l-cyan-500",
];

export function LineCards({ lineas }: LineCardsProps) {
  if (!lineas.length) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
        Sin datos de líneas estratégicas para el periodo seleccionado.
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {lineas.map((linea, idx) => (
        <div
          key={linea.linea}
          className={`rounded-xl border border-slate-200 border-l-4 bg-white p-4 shadow-sm ${LINE_COLORS[idx % LINE_COLORS.length]}`}
        >
          <h4 className="font-semibold text-poli-navy">{linea.linea}</h4>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center text-sm">
            <div>
              <p className="text-xs text-slate-500">Indicadores</p>
              <p className="font-bold text-slate-800">{linea.total_indicadores}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Cumplimiento</p>
              <p className="font-bold text-slate-800">
                {linea.cumplimiento_promedio != null ? `${linea.cumplimiento_promedio}%` : "—"}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">En riesgo</p>
              <p className="font-bold text-amber-600">{linea.en_riesgo}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
