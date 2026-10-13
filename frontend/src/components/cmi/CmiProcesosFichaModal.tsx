"use client";

import type { CMIProcesosFichaIndicador } from "@/lib/types";
import { fmtPct, NivelBadge, SobreejecucionBadge } from "@/components/cmi/nivelUtils";
import { fmtMeta, fmtEjecucion } from "@/lib/formatValor";
import { FichaHistoricoChart } from "@/components/cmi/FichaHistoricoChart";

interface CmiProcesosFichaModalProps {
  ficha: CMIProcesosFichaIndicador | null;
  loading?: boolean;
  onClose: () => void;
  onDownloadPdf?: () => void;
  downloadingPdf?: boolean;
}

export function CmiProcesosFichaModal({
  ficha,
  loading,
  onClose,
  onDownloadPdf,
  downloadingPdf,
}: CmiProcesosFichaModalProps) {
  if (!ficha && !loading) return null;

  const tipoColor = ficha?.tipo_proceso_color ?? "#1A3A5C";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white shadow-xl">
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <h3 className="text-lg font-bold text-poli-navy">
            {ficha ? `${ficha.Id} — ${ficha.Indicador}` : "Ficha — CMI por Procesos"}
          </h3>
          <div className="flex items-center gap-3">
            {onDownloadPdf && ficha && (
              <button
                type="button"
                onClick={onDownloadPdf}
                disabled={downloadingPdf}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
              >
                {downloadingPdf ? "Generando…" : "Descargar PDF"}
              </button>
            )}
            <button type="button" onClick={onClose} className="text-slate-500 hover:text-slate-800">
              ✕
            </button>
          </div>
        </div>

        {loading ? (
          <p className="p-6 text-sm text-slate-500">Cargando ficha...</p>
        ) : ficha ? (
          <div className="space-y-5 p-6">

            {typeof ficha.Descripcion === "string" && ficha.Descripcion && (
              <div>
                <p className="text-xs font-semibold text-slate-500">Descripción</p>
                <p className="text-sm text-slate-700">{ficha.Descripcion}</p>
              </div>
            )}

            {(ficha.linea_estrategica || ficha.objetivo_estrategico) && (
              <div className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-blue-700">
                  Línea estratégica y objetivo (PDI seleccionado)
                </p>
                <p className="text-sm font-semibold text-slate-800">{ficha.linea_estrategica ?? "—"}</p>
                {ficha.objetivo_estrategico && (
                  <p className="text-xs text-slate-600">{ficha.objetivo_estrategico}</p>
                )}
                {ficha.meta_estrategica && (
                  <p className="text-xs italic text-slate-500">Meta: {ficha.meta_estrategica}</p>
                )}
              </div>
            )}

            <div>
              <p className="mb-2 text-sm font-semibold text-slate-700">
                Evolución histórica (todos los periodos disponibles)
              </p>
              <FichaHistoricoChart historico={ficha.historico ?? []} />
            </div>

            {ficha.narrativa_ia && (
              <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4">
                <p className="mb-2 text-sm font-bold text-poli-navy">
                  Análisis IA {ficha.narrativa_ia.fuente === "heuristica" ? "(heurístico)" : ""}
                </p>
                <div
                  className="prose prose-sm max-w-none text-slate-700"
                  dangerouslySetInnerHTML={{ __html: ficha.narrativa_ia.texto_html }}
                />
                <p className="mt-2 text-[10px] text-slate-400">Fuente: {ficha.narrativa_ia.fuente}</p>
              </div>
            )}

            <div>
              <div className="flex flex-wrap gap-2">
                {ficha.tipo_proceso && (
                  <span
                    className="inline-block rounded-full px-3 py-1 text-xs font-bold"
                    style={{
                      color: tipoColor,
                      backgroundColor: `${tipoColor}22`,
                      border: `1px solid ${tipoColor}`,
                    }}
                  >
                    {ficha.tipo_proceso}
                  </span>
                )}
                {ficha.tendencia && (
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                    Tendencia: {ficha.tendencia}
                  </span>
                )}
              </div>
              <p className="mt-2 text-sm text-slate-600">
                {ficha.proceso_padre}
                {ficha.subproceso_final ? ` · ${ficha.subproceso_final}` : ""}
                {ficha.unidad ? ` · ${ficha.unidad}` : ""}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <Stat label="Meta" value={fmtMeta(ficha as Record<string, unknown>)} />
              <Stat label="Ejecución" value={fmtEjecucion(ficha as Record<string, unknown>)} />
              <Stat label="Cumplimiento" value={fmtPct(ficha.cumplimiento_pct as number | undefined)} />
            </div>

            <div className="flex flex-wrap gap-2">
              <NivelBadge nivel={ficha["Nivel de cumplimiento"] as string | undefined} />
<SobreejecucionBadge nivel={ficha["Nivel sobreejecucion"] as string | undefined} />
              {ficha.tendencia && (
                <span className="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                  {ficha.tendencia === "Al alza" ? "↑" : ficha.tendencia === "A la baja" ? "↓" : "→"}{" "}
                  {ficha.tendencia}
                </span>
              )}
            </div>

            {(ficha.formula_calculo || ficha.responsable || ficha.fuente_datos || ficha.periodicidad) && (
              <div>
                <p className="mb-2 text-sm font-semibold text-slate-700">Ficha de Identidad</p>
                <dl className="grid gap-3 sm:grid-cols-2">
                  {ficha.responsable && (
                    <div>
                      <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                        Responsable
                      </dt>
                      <dd className="text-sm text-slate-700">{ficha.responsable}</dd>
                    </div>
                  )}
                  {ficha.fuente_datos && (
                    <div>
                      <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                        Fuente de datos
                      </dt>
                      <dd className="text-sm text-slate-700">{ficha.fuente_datos}</dd>
                    </div>
                  )}
                  {ficha.formula_calculo && (
                    <div className="sm:col-span-2">
                      <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                        Fórmula de cálculo
                      </dt>
                      <dd className="text-sm text-slate-700">{ficha.formula_calculo}</dd>
                    </div>
                  )}
                  {ficha.periodicidad && (
                    <div>
                      <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                        Periodicidad
                      </dt>
                      <dd className="text-sm text-slate-700">{ficha.periodicidad}</dd>
                    </div>
                  )}
                </dl>
              </div>
            )}

            {ficha.asociaciones_pdi && ficha.asociaciones_pdi.length > 0 && (
              <div>
                <p className="mb-2 text-sm font-semibold text-slate-700">Línea estratégica por PDI (todas las asociaciones del indicador)</p>
                <ul className="space-y-2">
                  {ficha.asociaciones_pdi.map((a, i) => (
                    <li key={`${a.version_id}-${i}`} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{a.pdi}</p>
                      <p className="text-sm font-semibold text-slate-800">{a.linea ?? "—"}</p>
                      {a.objetivo && <p className="text-xs text-slate-600">{a.objetivo}</p>}
                      {a.meta && <p className="text-xs italic text-slate-500">Meta: {a.meta}</p>}
                    </li>
                  ))}
                </ul>
              </div>
            )}

          </div>
        ) : null}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-bold text-slate-900">{value}</p>
    </div>
  );
}
