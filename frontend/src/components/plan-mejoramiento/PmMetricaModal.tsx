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
  grupo?: string | null;
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
    queryKey: [
      "plan-metrica-detalle",
      seleccion?.factor,
      seleccion?.indicador,
      seleccion?.subindicador,
      seleccion?.grupo,
    ],
    queryFn: () =>
      fetchPlanMetricaDetalle({
        factor: seleccion!.factor,
        indicador: seleccion!.indicador,
        subindicador: seleccion?.subindicador ?? undefined,
        grupo: seleccion?.grupo ?? undefined,
      }),
    enabled: !!seleccion,
  });

  if (!seleccion) return null;
  const d = query.data;
  const color = getFactorColor(parseFactorNum(d?.factor ?? seleccion.factor));
  const fmtNum = (v: number | null | undefined) => fmtValor(v, d?.signo ?? null, d?.decimales ?? null);
  const variables = d?.variables ?? [];
  const TENDENCIA_COLORES = ["#7C3AED", "#DB2777", "#059669"];
  const PALETA = [color, "#0EA5E9", "#F59E0B"];
  const lineas = variables.length
    ? variables.map((v, i) => ({ clave: v.nombre, serie: v.serie, color: PALETA[i % PALETA.length] }))
    : [{ clave: "Resultado", serie: d?.serie ?? [], color }];
  const aniosSerie = Array.from(new Set(lineas.flatMap((l) => l.serie.map((p) => p.anio)))).sort((x, y) => x - y);
  const ajustes = lineas.map((l) =>
    lineaTendencia(aniosSerie.map((a) => l.serie.find((p) => p.anio === a)?.ejecucion ?? null)),
  );
  const chartData: Array<{ anio: number } & Record<string, number | null>> = aniosSerie.map((a, i) => {
    const fila: { anio: number } & Record<string, number | null> = { anio: a };
    lineas.forEach((l, k) => {
      const p = l.serie.find((x) => x.anio === a);
      fila[l.clave] = p?.ejecucion ?? null;
      fila[`Variación ${l.clave}`] = p?.variacion_pct ?? null;
      const ajuste = ajustes[k][i];
      fila[`Tendencia ${l.clave}`] = ajuste == null ? null : Math.round(ajuste * 100) / 100;
    });
    fila.Meta = lineas.length === 1 ? (lineas[0].serie.find((x) => x.anio === a)?.meta ?? null) : null;
    return fila;
  });
  const hayTendencia = ajustes.some((aj) => aj.some((v) => v != null));
  const hayMeta = chartData.some((p) => p.Meta != null);
  const desglose = d?.desglose ?? [];
  const filasDesglose: Array<{
    grupo: boolean;
    nombre: string;
    serie: Array<{ anio: number; ejecucion: number | null }>;
    tendencia: string;
  }> = d?.grupos
    ? d.grupos.flatMap((g) => [
        { grupo: true, nombre: g.nombre, serie: g.serie, tendencia: g.tendencia },
        ...desglose
          .filter((c) => c.grupo === g.nombre)
          .map((c) => ({ grupo: false, nombre: c.nombre ?? c.subindicador ?? "—", serie: c.serie, tendencia: c.tendencia })),
      ])
    : desglose.map((c) => ({
        grupo: false,
        nombre: c.nombre ?? c.subindicador ?? "—",
        serie: c.serie,
        tendencia: c.tendencia,
      }));
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
            {seleccion.grupo ? (
              <p className="text-xs text-slate-500">Subtotal · {seleccion.grupo}</p>
            ) : seleccion.subindicador && seleccion.subindicador !== seleccion.indicador ? (
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

              {variables.length ? (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <Ficha label="Periodo">
                    <span className="text-base">{periodoFicha}</span>
                  </Ficha>
                  {variables.map((v) => (
                    <Ficha key={v.nombre} label={`${v.nombre}${v.ultimo_anio ? ` ${v.ultimo_anio}` : ""}`}>
                      {v.valor_fmt}
                      <div className="mt-1 flex flex-wrap items-center gap-2 text-xs font-semibold">
                        <span className={variacionClass(v.variacion_ultima_pct)}>
                          {fmtVariacion(v.variacion_ultima_pct)}
                        </span>
                        <span
                          className={`rounded-full px-2 py-0.5 ${TENDENCIA_BADGE[v.tendencia] ?? TENDENCIA_BADGE["—"]}`}
                        >
                          {v.tendencia}
                        </span>
                      </div>
                    </Ficha>
                  ))}
                </div>
              ) : (
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
              )}

              {chartData.length ? (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 22, right: 24, left: 4, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="anio" tick={{ fontSize: 11 }} />
                      <YAxis
                        tick={{ fontSize: 11 }}
                        domain={[0, "auto"]}
                        allowDataOverflow
                        tickFormatter={(v: number) => fmtNum(v)}
                      />
                      <Tooltip formatter={(v: unknown) => (typeof v === "number" ? fmtNum(v) : String(v ?? "—"))} />
                      <Legend verticalAlign="bottom" height={24} iconType="plainline" wrapperStyle={{ fontSize: 11 }} />
                      {lineas.map((l) => (
                        <Line
                          key={l.clave}
                          type="monotone"
                          dataKey={l.clave}
                          stroke={l.color}
                          strokeWidth={2.5}
                          dot={{ r: 3 }}
                          connectNulls
                        >
                          <LabelList
                            dataKey={l.clave}
                            position="top"
                            fontSize={11}
                            fontWeight={600}
                            fill="#334155"
                            formatter={(v: unknown) => (typeof v === "number" ? fmtNum(v) : "")}
                          />
                        </Line>
                      ))}
                      {hayTendencia
                        ? lineas.map((l, k) => (
                            <Line
                              key={`t-${l.clave}`}
                              type="linear"
                              dataKey={`Tendencia ${l.clave}`}
                              name={lineas.length > 1 ? `Tendencia ${l.clave}` : "Tendencia (lineal)"}
                              stroke={TENDENCIA_COLORES[k % TENDENCIA_COLORES.length]}
                              strokeWidth={2}
                              strokeDasharray="6 4"
                              dot={false}
                              activeDot={false}
                              connectNulls
                            />
                          ))
                        : null}
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
                      {lineas.flatMap((l) => [
                        <tr key={`v-${l.clave}`} className="border-t border-slate-100">
                          <td className="px-3 py-2 text-left font-semibold">
                            {lineas.length > 1 ? l.clave : etiquetaResultado}
                          </td>
                          {chartData.map((p) => (
                            <td key={p.anio} className="px-3 py-2 font-semibold">
                              {fmtNum(p[l.clave])}
                            </td>
                          ))}
                        </tr>,
                        <tr key={`d-${l.clave}`} className="border-t border-slate-100">
                          <td className="px-3 py-2 text-left font-semibold">
                            {lineas.length > 1 ? `Variación ${l.clave}` : "Variación"}
                          </td>
                          {chartData.map((p) => (
                            <td
                              key={p.anio}
                              className={`px-3 py-2 font-medium ${variacionClass(p[`Variación ${l.clave}`])}`}
                            >
                              {fmtVariacion(p[`Variación ${l.clave}`])}
                            </td>
                          ))}
                        </tr>,
                      ])}
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
                        {filasDesglose.map((c, i) => (
                          <tr key={`${c.nombre}|${i}`} className={c.grupo ? "bg-slate-50 font-semibold" : ""}>
                            <td
                              className={`whitespace-normal px-3 py-2 text-left ${
                                c.grupo ? "font-semibold" : d?.grupos ? "pl-7 font-medium" : "font-medium"
                              }`}
                            >
                              {c.nombre}
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
