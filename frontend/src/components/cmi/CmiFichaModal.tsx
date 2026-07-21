"use client";

import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CMIFichaIndicador } from "@/lib/types";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";
import { fmtMeta, fmtEjecucion } from "@/lib/formatValor";
import { NIVEL_COLORS } from "@/components/cmi/cmiChartColors";

interface CmiFichaModalProps {
  ficha: CMIFichaIndicador | null;
  loading?: boolean;
  onClose: () => void;
  onDownloadPdf?: () => void;
  downloadingPdf?: boolean;
}

function tendenciaMeta(tendencia?: string): { icon: string; color: string } {
  if (tendencia === "Al alza") return { icon: "↑", color: "#43A047" };
  if (tendencia === "A la baja") return { icon: "↓", color: "#D32F2F" };
  return { icon: "→", color: "#64748B" };
}

export function CmiFichaModal({ ficha, loading, onClose, onDownloadPdf, downloadingPdf }: CmiFichaModalProps) {
  if (!ficha && !loading) return null;

  const cump = typeof ficha?.cumplimiento_pct === "number" ? ficha.cumplimiento_pct : 0;
  const nivel = ficha?.["Nivel de cumplimiento"] as string | undefined;
  const nivelColor = (nivel && NIVEL_COLORS[nivel]) || "#94A3B8";
  const capped = Math.min(cump, 130);
  const donutData =
    capped >= 100
      ? [{ name: "cumplido", value: 130 }]
      : [
          { name: "cumplido", value: capped },
          { name: "resto", value: 130 - capped },
        ];
  const donutColors = capped >= 100 ? [nivelColor] : [nivelColor, "#E5E7EB"];

  const historico = ficha?.historico ?? [];
  const sparkData = historico.slice(-8);
  const multiYearData = historico.slice(-12);
  const { icon: tendIcon, color: tendColor } = tendenciaMeta(ficha?.tendencia);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white shadow-xl">
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <h3 className="text-lg font-bold text-poli-navy">Ficha del indicador</h3>
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
            <div>
              <p className="text-xs text-slate-500">Código {ficha.Id}</p>
              <h4 className="text-xl font-bold text-slate-900">{ficha.Indicador}</h4>
              {ficha.Linea && (
                <span
                  className="mt-2 inline-block rounded-full px-3 py-1 text-xs font-bold"
                  style={{
                    color: ficha.linea_color ?? "#1A3A5C",
                    backgroundColor: `${ficha.linea_color ?? "#1A3A5C"}22`,
                    border: `1px solid ${ficha.linea_color ?? "#1A3A5C"}`,
                  }}
                >
                  {ficha.Linea}
                </span>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <Stat label="Meta" value={fmtMeta(ficha as Record<string, unknown>)} />
              <Stat label="Ejecución" value={fmtEjecucion(ficha as Record<string, unknown>)} />
              <Stat label="Cumplimiento" value={fmtPct(ficha.cumplimiento_pct as number | undefined)} />
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <NivelBadge nivel={ficha["Nivel de cumplimiento"] as string | undefined} />
              {ficha.tendencia && (
                <span
                  className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-bold"
                  style={{ color: tendColor, backgroundColor: `${tendColor}18`, border: `1px solid ${tendColor}40` }}
                >
                  {tendIcon} Tendencia: {ficha.tendencia}
                </span>
              )}
            </div>

            {typeof ficha.Descripcion === "string" && ficha.Descripcion && (
              <div>
                <p className="text-xs font-semibold text-slate-500">Descripción</p>
                <p className="text-sm text-slate-700">{ficha.Descripcion}</p>
              </div>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 p-3">
                <p className="mb-1 text-sm font-semibold text-slate-700">Cumplimiento</p>
                <div className="relative">
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart>
                      <Pie
                        data={donutData}
                        dataKey="value"
                        innerRadius="70%"
                        outerRadius="100%"
                        startAngle={90}
                        endAngle={-270}
                        stroke="none"
                        isAnimationActive={false}
                      >
                        {donutData.map((entry, idx) => (
                          <Cell key={entry.name} fill={donutColors[idx]} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-xl font-extrabold" style={{ color: nivelColor }}>
                      {fmtPct(cump, 0)}
                    </span>
                    <span className="text-[9px] font-bold uppercase tracking-wide text-slate-500">
                      Cumplimiento
                    </span>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 p-3">
                <p className="mb-1 text-sm font-semibold text-slate-700">Tendencia reciente</p>
                {sparkData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={sparkData}>
                      <Tooltip
                        formatter={((value: number) => [fmtPct(value), "% Cumplimiento"]) as never}
                        labelFormatter={(periodo) => `Periodo ${periodo}`}
                        contentStyle={{ fontSize: 11 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="cumplimiento"
                        stroke={tendColor}
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        isAnimationActive={false}
                        name="% Cumplimiento"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="flex h-[180px] items-center justify-center text-xs text-slate-400">
                    Sin datos suficientes
                  </p>
                )}
              </div>
            </div>

            {multiYearData.length > 0 && (
              <div>
                <p className="mb-2 text-sm font-semibold text-slate-700">Evolución histórica Meta / Ejecución / %</p>
                <ResponsiveContainer width="100%" height={260}>
                  <ComposedChart data={multiYearData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="periodo" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="val" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="pct" orientation="right" tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar yAxisId="val" dataKey="meta" name="Meta" fill="#F59E0B" opacity={0.65} />
                    <Bar yAxisId="val" dataKey="ejecucion" name="Ejecución" fill="#1A3A5C" opacity={0.85} />
                    <Line
                      yAxisId="pct"
                      type="monotone"
                      dataKey="cumplimiento"
                      name="% Cumplimiento"
                      stroke="#0EA5E9"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            )}

            <div className="rounded-xl border border-slate-200 p-4">
              <p className="mb-3 text-sm font-semibold text-slate-700">Ficha de Identidad</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <IdentityField label="Objetivo" value={ficha.Objetivo as string | undefined} />
                <IdentityField
                  label="Responsable"
                  value={ficha["Responsable del calculo"] as string | undefined}
                />
                <IdentityField label="Fuente de datos" value={(ficha["Fuente V1"] as string) || "Kawak"} />
                <IdentityField label="Periodicidad" value={ficha.Frecuencia as string | undefined} />
                <IdentityField
                  label="Fórmula de cálculo"
                  value={ficha.Formula as string | undefined}
                  monospace
                  fullWidth
                />
              </div>
            </div>

            {ficha.narrativa_ia && (
              <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4">
                <p className="mb-2 text-sm font-bold text-poli-navy">
                  Análisis IA {ficha.narrativa_ia.fuente === "claude" ? "" : "(heurístico)"}
                </p>
                <div
                  className="prose prose-sm max-w-none text-slate-700"
                  dangerouslySetInnerHTML={{ __html: ficha.narrativa_ia.texto_html }}
                />
                <p className="mt-2 text-[10px] text-slate-400">Fuente: {ficha.narrativa_ia.fuente}</p>
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
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-bold text-slate-900">{value}</p>
    </div>
  );
}

function IdentityField({
  label,
  value,
  monospace,
  fullWidth,
}: {
  label: string;
  value?: string;
  monospace?: boolean;
  fullWidth?: boolean;
}) {
  const display = value && !["nan", "None", ""].includes(value) ? value : "—";
  return (
    <div className={fullWidth ? "sm:col-span-2" : undefined}>
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p
        className={
          monospace
            ? "mt-1 whitespace-pre-wrap break-all font-mono text-xs text-slate-800"
            : "mt-1 text-sm text-slate-800"
        }
      >
        {display}
      </p>
    </div>
  );
}
