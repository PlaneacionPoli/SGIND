"use client";

import { useQuery } from "@tanstack/react-query";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchPlanMetricaDetalle } from "@/lib/api";
import { PmFactorBadge } from "./PmFactorBadge";
import { getFactorColor, parseFactorNum } from "./pmFactorTheme";

interface PmMetricaSeleccion {
  factor: string;
  indicador: string;
  subindicador: string | null;
}

interface PmMetricaModalProps {
  seleccion: PmMetricaSeleccion | null;
  onClose: () => void;
}

function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
}

/** Modal de detalle de una métrica — paridad con
 * pages/plan_mejoramiento.py::_open_metrica_modal (resultado vs. meta por año). */
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
  const chartData = (d?.serie ?? []).map((p) => ({ anio: p.anio, Resultado: p.ejecucion, Meta: p.meta }));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <div>
            <h3 className="text-lg font-bold text-poli-navy">{seleccion.indicador}</h3>
            {seleccion.subindicador && seleccion.subindicador !== seleccion.indicador ? (
              <p className="text-xs text-slate-500">{seleccion.subindicador}</p>
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
        <div className="space-y-4 px-6 py-5 text-sm">
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
              {chartData.length ? (
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="anio" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="Resultado"
                        stroke={getFactorColor(parseFactorNum(d.factor))}
                        strokeWidth={2.5}
                        dot={{ r: 3 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="Meta"
                        stroke="#B45309"
                        strokeWidth={1.5}
                        strokeDasharray="4 4"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-slate-500">Sin serie histórica registrada.</p>
              )}
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="font-semibold text-slate-700">Proceso</p>
                  <p className="text-slate-600">{d.proceso}</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-700">Sentido / Periodicidad</p>
                  <p className="text-slate-600">
                    {d.sentido} · {d.periodicidad}
                  </p>
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="font-semibold text-slate-700">Variación último año</p>
                  <p className="text-slate-600">{fmtPct(d.variacion_ultima_pct)} respecto al año anterior</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-700">Variación promedio anual</p>
                  <p className="text-slate-600">{fmtPct(d.variacion_promedio_pct)} promedio interanual</p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
