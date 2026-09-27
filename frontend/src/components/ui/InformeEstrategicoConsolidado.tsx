interface InformeEstrategicoConsolidadoProps {
  data?: {
    resumen_ejecutivo: string;
    logros: string;
    retos_priorizados: string;
  } | null;
}

/** Resumen ejecutivo cualitativo + balance estratégico (logros vs. retos
 * priorizados PDI 2026-2030) — solo vista Consolidado, Cierre PDI 2022-2025.
 * Texto de autoría directa (ver backend/scripts/generar_narrativa_estrategica.py),
 * no generado en el navegador. */
export function InformeEstrategicoConsolidado({ data }: InformeEstrategicoConsolidadoProps) {
  if (!data) return null;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-poli-blue">
          Informe Estratégico — Resumen Ejecutivo
        </p>
        <p className="text-sm leading-relaxed text-slate-700">{data.resumen_ejecutivo}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-emerald-700">
            Logros transformacionales
          </p>
          <p className="text-sm leading-relaxed text-emerald-950">{data.logros}</p>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-amber-700">
            Retos priorizados — PDI 2026-2030
          </p>
          <p className="text-sm leading-relaxed text-amber-950">{data.retos_priorizados}</p>
        </div>
      </div>
    </div>
  );
}
