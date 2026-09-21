"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Legend,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchPlanMetricaDetalle } from "@/lib/api";
import { PmFactorBadge } from "./PmFactorBadge";
import { getFactorColor, parseFactorNum } from "./pmFactorTheme";
import { fmtValor, fmtVariacion, lineaTendencia, variacionClass } from "./pmVariacion";

interface PmMetricaSeleccion {
  factor: string;
  indicador: string;
  subindicador: string | null;
}

interface PmMetricaModalProps {
  seleccion: PmMetricaSeleccion | null;
  onClose: () => void;
}

const TENDENCIA_BADGE: Record<string, string> = {
  Creciente: "bg-emerald-50 text-emerald-700",
  Decreciente: "bg-rose-50 text-rose-700",
  Estable: "bg-slate-100 text-slate-600",
  "—": "bg-slate-50 text-slate-400",
};

function Ficha({
  label,
  children,
  className = "text-poli-navy",
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <div className={`mt-1 text-lg font-bold ${className}`}>{children}</div>
    </div>
  );
}

/** Modal de detalle de una métrica — paridad con
 * pages/plan_mejoramiento.py::_open_metrica_modal (resultado vs. meta por año).
 * Para un consolidado (indicador con desglose) muestra el total/promedio año a
 * año, más el desglose por categoría en el orden del archivo. */
export function PmMetricaModal({ seleccion, onClose }: PmMetricaModalProps) {
  const query = useQuery({
    queryKey: ["plan-metrica-detalle", seleccion?.factor, seleccion?.indicador, seleccion?.subindicador],
    queryFn: () =>
      fetchPlanMetricaDetalle({
        factor: seleccion!.factor,
        indicador: seleccion!.indicador,
        subindicador: seleccion?.subindicador ?? undefined,
      }),
    enabled: !!seleccion,
  });

  if (!seleccion) return null;
  const d = query.data;
  const color = getFactorColor(parseFactorNum(d?.factor ?? seleccion.factor));
  const fmtNum = (v: number | null | undefined) => fmtValor(v, d?.signo ?? null, d?.decimales ?? null);
  const serie = d?.serie ?? [];
  const ajuste = lineaTendencia(serie.map((p) => p.ejecucion));
  const chartData = serie.map((p, i) => ({
    anio: p.anio,
    Resultado: p.ejecucion,
    Meta: p.meta,
    Variacion: p.variacion_pct ?? null,
    Tendencia: ajuste[i] == null ? null : Math.round(ajuste[i]! * 100) / 100,
  }));
  const hayTendencia = chartData.some((p) => p.Tendencia != null);
  const hayMeta = chartData.some((p) => p.Meta != null);
  const desglose = d?.desglose ?? [];
  const anios = Array.from(new Set(desglose.flatMap((c) => c.serie.map((p) => p.anio)))).sort();
  const periodoFicha =
    d?.anio_inicio != null && d.anio_fin != null
      ? d.anio_inicio === d.anio_fin
        ? String(d.anio_inicio)
        : `${d.anio_inicio} – ${d.anio_fin}`
      : (d?.periodo_texto ?? "—");
  const etiquetaResultado = d?.consolidado && d.agregacion ? d.agregacion : "Resultado";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <div>
            <h3 className="text-lg font-bold text-poli-navy">{seleccion.indicador}</h3>
            {seleccion.subindicador && seleccion.subindicador !== seleccion.indicador ? (
              <p className="text-xs text-slate-500">{seleccion.subindicador}</p>
            ) : d?.consolidado ? (
              <p className="text-xs text-slate-500">
                Consolidado · {desglose.length} categorías
                {d.agregacion ? ` · ${d.agregacion.toLowerCase()} por año` : ""}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-slate-500 hover:bg-slate-100"
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>
        <div className="space-y-5 px-6 py-5 text-sm">
          {query.isLoading ? (
            <div className="h-64 animate-pulse rounded-lg bg-slate-100" />
          ) : !d ? (
            <p className="text-slate-500">No se encontró información de la métrica.</p>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <PmFactorBadge factorNum={parseFactorNum(d.factor)} variant="full" />
                <span className="text-xs font-semibold text-slate-500">{d.factor}</span>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <Ficha label="Periodo">
                  <span className="text-base">{periodoFicha}</span>
                </Ficha>
                <Ficha label={`${etiquetaResultado}${d.ultimo_anio ? ` ${d.ultimo_anio}` : ""}`}>
                  {d.valor_fmt}
                </Ficha>
                <Ficha label="Variación último año" className={variacionClass(d.variacion_ultima_pct)}>
                  {fmtVariacion(d.variacion_ultima_pct)}
                </Ficha>
                <Ficha label="Variación promedio anual" className={variacionClass(d.variacion_promedio_pct)}>
                  {fmtVariacion(d.variacion_promedio_pct)}
                </Ficha>
                <Ficha label="Tendencia">
                  <span
                    className={`rounded-full px-2 py-0.5 text-sm font-semibold ${
                      TENDENCIA_BADGE[d.tendencia] ?? TENDENCIA_BADGE["—"]
                    }`}
                  >
                    {d.tendencia}
                  </span>
                </Ficha>
              </div>

              {chartData.length ? (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 22, right: 24, left: 4, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="anio" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} domain={[0, "auto"]} tickFormatter={(v: number) => fmtNum(v)} />
                      <Tooltip formatter={(v: unknown) => (typeof v === "number" ? fmtNum(v) : String(v ?? "—"))} />
                      <Legend verticalAlign="bottom" height={24} iconType="plainline" wrapperStyle={{ fontSize: 11 }} />
                      <Line
                        type="monotone"
                        dataKey="Resultado"
                        stroke={color}
                        strokeWidth={2.5}
                        dot={{ r: 3 }}
                        connectNulls
                      >
                        <LabelList
                          dataKey="Resultado"
                          position="top"
                          fontSize={11}
                          fontWeight={600}
                          fill="#334155"
                          formatter={(v: unknown) => (typeof v === "number" ? fmtNum(v) : "")}
                        />
                      </Line>
                      {hayTendencia ? (
                        <Line
                          type="linear"
                          dataKey="Tendencia"
                          name="Tendencia (lineal)"
                          stroke="#7C3AED"
                          strokeWidth={2}
                          strokeDasharray="6 4"
                          dot={false}
                          activeDot={false}
                          connectNulls
                        />
                      ) : null}
                      {hayMeta ? (
                        <Line
                          type="monotone"
                          dataKey="Meta"
                          stroke="#B45309"
                          strokeWidth={1.5}
                          strokeDasharray="4 4"
                          dot={false}
                        />
                      ) : null}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-slate-500">Sin serie histórica registrada.</p>
              )}

              {chartData.length ? (
                <div className="overflow-x-auto rounded-xl border border-slate-200">
                  <table className="min-w-full text-right text-xs tabular-nums">
                    <thead className="bg-slate-50 font-semibold text-slate-500">
                      <tr>
                        <th className="px-3 py-2 text-left">Año</th>
                        {chartData.map((p) => (
                          <th key={p.anio} className="px-3 py-2">
                            {p.anio}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="text-slate-700">
                      <tr className="border-t border-slate-100">
                        <td className="px-3 py-2 text-left font-semibold">{etiquetaResultado}</td>
                        {chartData.map((p) => (
                          <td key={p.anio} className="px-3 py-2 font-semibold">
                            {fmtNum(p.Resultado)}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-t border-slate-100">
                        <td className="px-3 py-2 text-left font-semibold">Variación</td>
                        {chartData.map((p) => (
                          <td key={p.anio} className={`px-3 py-2 font-medium ${variacionClass(p.Variacion)}`}>
                            {fmtVariacion(p.Variacion)}
                          </td>
                        ))}
                      </tr>
                      {hayMeta ? (
                        <tr className="border-t border-slate-100">
                          <td className="px-3 py-2 text-left font-semibold">Meta</td>
                          {chartData.map((p) => (
                            <td key={p.anio} className="px-3 py-2">
                              {fmtNum(p.Meta)}
                            </td>
                          ))}
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              ) : null}

              {desglose.length ? (
                <div>
                  <p className="mb-2 font-semibold text-slate-700">Desglose por categoría</p>
                  <div className="overflow-x-auto rounded-xl border border-slate-200">
                    <table className="min-w-full text-right text-xs tabular-nums">
                      <thead className="bg-slate-50 font-semibold text-slate-500">
                        <tr>
                          <th className="px-3 py-2 text-left">Categoría</th>
                          {anios.map((a) => (
                            <th key={a} className="px-3 py-2">
                              {a}
                            </th>
                          ))}
                          <th className="px-3 py-2 text-left">Tendencia</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {desglose.map((c, i) => (
                          <tr key={`${c.subindicador}|${i}`}>
                            <td className="whitespace-normal px-3 py-2 text-left font-medium">
                              {c.subindicador ?? "—"}
                            </td>
                            {anios.map((a) => (
                              <td key={a} className="px-3 py-2">
                                {fmtNum(c.serie.find((p) => p.anio === a)?.ejecucion)}
                              </td>
                            ))}
                            <td className="px-3 py-2 text-left">
                              <span
                                className={`rounded-full px-2 py-0.5 font-semibold ${
                                  TENDENCIA_BADGE[c.tendencia] ?? TENDENCIA_BADGE["—"]
                                }`}
                              >
                                {c.tendencia}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : null}

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="font-semibold text-slate-700">Fuente</p>
                  <p className="text-slate-600">{d.fuente}</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-700">Periodicidad</p>
                  <p className="text-slate-600">{d.periodicidad}</p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
