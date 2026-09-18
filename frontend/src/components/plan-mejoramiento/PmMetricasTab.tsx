"use client";

import { Fragment, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { KPICard } from "@/components/ui/KPICard";
import { Pagination } from "@/components/ui/Pagination";
import { useDebounce } from "@/hooks/use-debounce";
import { usePagination } from "@/hooks/use-pagination";
import { fetchPlanMetricasDashboard } from "@/lib/api";
import { useAuthReady } from "@/stores/auth-store";
import { PmFactorBadge } from "./PmFactorBadge";
import { PmFactorRings } from "./PmFactorRings";
import { PmMetricaModal } from "./PmMetricaModal";
import { PmSparkline } from "./PmSparkline";
import { getFactorColor } from "./pmFactorTheme";

const TENDENCIA_BADGE: Record<string, string> = {
  Creciente: "bg-emerald-50 text-emerald-700",
  Decreciente: "bg-rose-50 text-rose-700",
  Estable: "bg-slate-100 text-slate-600",
  "—": "bg-slate-50 text-slate-400",
};

interface PmMetricasTabProps {
  /** Factor y Característica son filtros globales del módulo — el estado
   * vive en PlanMejoramientoPage y se comparte con PmIndicadoresTab. */
  factor: string;
  onFactorChange: (value: string) => void;
  caracteristica: string;
  onCaracteristicaChange: (value: string) => void;
}

/** Pestaña "Métricas" del Plan de Mejoramiento — paridad con
 * pages/plan_mejoramiento.py::_render_tab_metricas (ver
 * docs/migration/PLAN_MIGRACION_PRIORIZADO.md ítem 0). */
export function PmMetricasTab({
  factor,
  onFactorChange,
  caracteristica,
  onCaracteristicaChange,
}: PmMetricasTabProps) {
  const { isAuthenticated } = useAuthReady();
  const [tendencia, setTendencia] = useState("Toda tendencia");
  const [nombre, setNombre] = useState("");
  const nombreDebounced = useDebounce(nombre);
  const [expandidos, setExpandidos] = useState<Set<string>>(new Set());
  const [seleccion, setSeleccion] = useState<{
    factor: string;
    indicador: string;
    subindicador: string | null;
  } | null>(null);

  const toggleExpandido = (key: string) => {
    setExpandidos((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const query = useQuery({
    queryKey: ["plan-metricas", factor, caracteristica, tendencia, nombreDebounced],
    queryFn: () =>
      fetchPlanMetricasDashboard({
        ...(factor !== "Todos" ? { factor } : {}),
        ...(caracteristica !== "Todas" ? { caracteristica } : {}),
        ...(tendencia !== "Toda tendencia" ? { tendencia } : {}),
        ...(nombreDebounced.trim() ? { nombre: nombreDebounced.trim() } : {}),
      }),
    enabled: isAuthenticated,
  });

  const data = query.data;
  const tabla = data?.tabla ?? [];
  const { page, setPage, pageSize, setPageSize, pageItems, totalPages } = usePagination(tabla);

  return (
    <div className="space-y-6">
      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver el plan de mejoramiento.</p>
      ) : query.isLoading ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-200" />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard label="Métricas con histórico" value={data?.kpis.total ?? 0} unit="series 2019–2026" />
            <KPICard
              label="Factores cubiertos"
              value={data?.kpis.factores_cubiertos ?? 0}
              unit="de 12 del modelo CNA"
            />
            <KPICard
              label="En tendencia creciente"
              value={data?.kpis.n_creciente ?? 0}
              unit={`${data?.kpis.pct_creciente ?? 0}% del total`}
            />
            <KPICard
              label="En tendencia decreciente"
              value={data?.kpis.n_decreciente ?? 0}
              unit={`${data?.kpis.pct_decreciente ?? 0}% del total`}
            />
          </div>

          <div>
            <h3 className="mb-1 text-sm font-bold text-slate-800">Resultados por factor</h3>
            <p className="mb-2 text-xs text-slate-500">
              Número de métricas con serie histórica registrada, por factor del modelo CNA. Clic en una
              barra para filtrar.
            </p>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <PmFactorRings
                data={(data?.grafico_por_factor ?? []).map((f) => ({
                  factor: f.factor,
                  factorNum: f.factor_num,
                  value: f.cantidad,
                }))}
                onFactorClick={onFactorChange}
              />
            </div>
          </div>

          <div>
            <h3 className="mb-1 text-sm font-bold text-slate-800">Resultados, tendencia y variaciones</h3>
            <p className="mb-2 text-xs text-slate-500">
              Selecciona un factor para filtrar. Haz clic en una métrica para ver su gráfica completa.
            </p>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={factor}
                  onChange={(e) => onFactorChange(e.target.value)}
                >
                  <option value="Todos">Todos los factores</option>
                  {(data?.filtros.factores ?? []).map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={caracteristica}
                  onChange={(e) => onCaracteristicaChange(e.target.value)}
                >
                  <option value="Todas">Todas las características</option>
                  {(data?.filtros.caracteristicas ?? []).map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={tendencia}
                  onChange={(e) => setTendencia(e.target.value)}
                >
                  {(data?.filtros.tendencias ?? ["Toda tendencia"]).map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
                <input
                  type="search"
                  placeholder="Buscar métrica…"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                />
              </div>
              {factor !== "Todos" || caracteristica !== "Todas" ? (
                <p className="mt-2 text-xs text-slate-500">
                  Filtrando por:{" "}
                  {[factor !== "Todos" ? factor : null, caracteristica !== "Todas" ? caracteristica : null]
                    .filter(Boolean)
                    .map((f) => <strong key={f}>{f}</strong>)
                    .reduce((acc, el, i) => (i === 0 ? [el] : [...acc, " · ", el]), [] as React.ReactNode[])}
                </p>
              ) : null}
            </div>
          </div>

          {!tabla.length ? (
            <p className="text-sm text-slate-500">No hay métricas que coincidan con el filtro.</p>
          ) : (
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-slate-50/80 text-[11px] font-bold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Factor</th>
                      <th className="px-4 py-3">Métrica</th>
                      <th className="px-4 py-3">Proceso</th>
                      <th className="px-4 py-3 text-right">Último año</th>
                      <th className="px-4 py-3 text-right">Resultado</th>
                      <th className="px-4 py-3 text-right">Variación</th>
                      <th className="px-4 py-3">Tendencia</th>
                      <th className="px-4 py-3">Serie</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {pageItems.map((row, i) => {
                      const key = `${row.factor}|${row.indicador}`;
                      const expandible = row.n_desglose > 1;
                      const abierto = expandidos.has(key);
                      return (
                        <Fragment key={key}>
                          <tr
                            className={`group border-l-2 border-l-transparent transition-colors hover:border-l-4 hover:!bg-slate-50 ${
                              expandible ? "cursor-pointer" : "cursor-default"
                            } ${i % 2 === 1 ? "bg-slate-50/40" : ""}`}
                            onMouseEnter={(e) =>
                              (e.currentTarget.style.borderLeftColor = getFactorColor(row.factor_num))
                            }
                            onMouseLeave={(e) => (e.currentTarget.style.borderLeftColor = "transparent")}
                            onClick={() =>
                              expandible
                                ? toggleExpandido(key)
                                : setSeleccion({ factor: row.factor, indicador: row.indicador, subindicador: null })
                            }
                          >
                            <td className="px-4 py-2.5">
                              <PmFactorBadge factorNum={row.factor_num} />
                            </td>
                            <td className="px-4 py-2.5 font-medium text-slate-800">
                              <span className="flex items-start gap-1.5">
                                {expandible ? (
                                  <span
                                    className={`inline-block shrink-0 text-slate-400 transition-transform ${abierto ? "rotate-90" : ""}`}
                                    aria-hidden
                                  >
                                    ▸
                                  </span>
                                ) : null}
                                <span className="whitespace-normal break-words">{row.indicador}</span>
                                {expandible ? (
                                  <span className="shrink-0 rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500">
                                    {row.n_desglose}
                                  </span>
                                ) : null}
                              </span>
                            </td>
                            <td className="px-4 py-2.5 text-slate-600">{row.proceso ?? "—"}</td>
                            <td className="px-4 py-2.5 text-right tabular-nums text-slate-700">
                              {row.ultimo_anio ?? "—"}
                            </td>
                            <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-slate-800">
                              {row.valor_fmt}
                            </td>
                            <td className="px-4 py-2.5 text-right tabular-nums text-slate-700">
                              {row.variacion_ultima_pct != null
                                ? `${row.variacion_ultima_pct > 0 ? "+" : ""}${row.variacion_ultima_pct.toFixed(1)}%`
                                : "—"}
                            </td>
                            <td className="px-4 py-2.5">
                              <span
                                className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                                  TENDENCIA_BADGE[row.tendencia] ?? TENDENCIA_BADGE["—"]
                                }`}
                              >
                                {row.tendencia}
                              </span>
                            </td>
                            <td className="px-4 py-2.5">
                              <PmSparkline
                                values={row.serie}
                                color={getFactorColor(row.factor_num)}
                                trend={row.tendencia}
                              />
                            </td>
                          </tr>
                          {expandible && abierto
                            ? row.desglose.map((d, j) => (
                                <tr
                                  key={`${key}|${j}`}
                                  className="cursor-pointer bg-slate-50/70 hover:bg-slate-100"
                                  onClick={() =>
                                    setSeleccion({
                                      factor: row.factor,
                                      indicador: row.indicador,
                                      subindicador: d.subindicador,
                                    })
                                  }
                                >
                                  <td className="px-4 py-2" />
                                  <td className="whitespace-normal break-words px-4 py-2 pl-9 text-slate-600">
                                    {d.subindicador ?? "—"}
                                  </td>
                                  <td className="px-4 py-2 text-slate-500">{d.proceso ?? "—"}</td>
                                  <td className="px-4 py-2 text-right tabular-nums text-slate-600">
                                    {d.ultimo_anio ?? "—"}
                                  </td>
                                  <td className="px-4 py-2 text-right tabular-nums text-slate-700">{d.valor_fmt}</td>
                                  <td className="px-4 py-2 text-right tabular-nums text-slate-600">
                                    {d.variacion_ultima_pct != null
                                      ? `${d.variacion_ultima_pct > 0 ? "+" : ""}${d.variacion_ultima_pct.toFixed(1)}%`
                                      : "—"}
                                  </td>
                                  <td className="px-4 py-2">
                                    <span
                                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                                        TENDENCIA_BADGE[d.tendencia] ?? TENDENCIA_BADGE["—"]
                                      }`}
                                    >
                                      {d.tendencia}
                                    </span>
                                  </td>
                                  <td className="px-4 py-2">
                                    <PmSparkline
                                      values={d.serie}
                                      color={getFactorColor(row.factor_num)}
                                      trend={d.tendencia}
                                    />
                                  </td>
                                </tr>
                              ))
                            : null}
                        </Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="border-t border-slate-100 px-4 py-3">
                <Pagination
                  page={page}
                  totalPages={totalPages}
                  pageSize={pageSize}
                  onPageChange={setPage}
                  onPageSizeChange={setPageSize}
                />
              </div>
            </div>
          )}
        </>
      )}

      <PmMetricaModal seleccion={seleccion} onClose={() => setSeleccion(null)} />
    </div>
  );
}
