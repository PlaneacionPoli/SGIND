"use client";

import { NIVEL_STYLES } from "@/components/cmi/nivelUtils";

const ORDEN = ["Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento"] as const;

/**
 * Cómo se reparte el semáforo de los indicadores en cada año (cierre anual; el año en curso es
 * parcial). Barras apiladas al 100 % para comparar la mezcla aunque cambie el número de indicadores.
 */
export function CmiProcesosMixNiveles({
  mix,
  anioParcial,
}: {
  mix: Record<string, Record<string, number>>;
  anioParcial: number | null;
}) {
  const anios = Object.keys(mix).sort();
  if (anios.length === 0) return null;
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h4 className="text-sm font-bold text-slate-800">Evolución del semáforo por año</h4>
      <p className="mb-3 text-xs text-slate-500">
        % de indicadores por nivel de cumplimiento en el cierre de cada año
        {anioParcial ? ` (${anioParcial} es parcial: último reporte de cada indicador)` : ""}.
      </p>
      <div className="space-y-2">
        {anios.map((a) => {
          const total = ORDEN.reduce((acc, n) => acc + (mix[a][n] ?? 0), 0) || 1;
          return (
            <div key={a} className="flex items-center gap-3">
              <span className="w-24 shrink-0 text-xs font-semibold text-slate-700">
                {a}
                {Number(a) === anioParcial ? " parcial" : ""}
              </span>
              <div className="flex h-6 flex-1 overflow-hidden rounded-md bg-slate-100">
                {ORDEN.map((n) => {
                  const v = mix[a][n] ?? 0;
                  if (!v) return null;
                  const pct = (v / total) * 100;
                  return (
                    <div
                      key={n}
                      title={`${n}: ${v} indicadores (${pct.toFixed(0)}%)`}
                      className="flex items-center justify-center text-[10px] font-bold text-white"
                      style={{ width: `${pct}%`, backgroundColor: NIVEL_STYLES[n].text }}
                    >
                      {pct >= 8 ? `${pct.toFixed(0)}%` : ""}
                    </div>
                  );
                })}
              </div>
              <span className="w-10 shrink-0 text-right text-[11px] text-slate-400">{total}</span>
            </div>
          );
        })}
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-[11px] text-slate-600">
        {ORDEN.map((n) => (
          <span key={n} className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: NIVEL_STYLES[n].text }} />
            {n}
          </span>
        ))}
      </div>
    </section>
  );
}
