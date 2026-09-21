"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { KPICard } from "@/components/ui/KPICard";
import { Pagination } from "@/components/ui/Pagination";
import { useDebounce } from "@/hooks/use-debounce";
import { usePagination } from "@/hooks/use-pagination";
import { downloadPlanIndicadoresExport, fetchPlanIndicadoresDashboard } from "@/lib/api";
import { useAuthReady } from "@/stores/auth-store";
import { PmBulletProgress } from "./PmBulletProgress";
import { PmFactorBadge } from "./PmFactorBadge";
import { PmFactorRings } from "./PmFactorRings";
import { PmIndicadorModal } from "./PmIndicadorModal";
import { getFactorColor } from "./pmFactorTheme";

type SubVista = "metas" | "historico";

const METAS_YEARS = ["2026", "2027", "2028", "2029", "2030"] as const;

const TIPO_STYLES: Record<string, string> = {
  Indicador: "bg-sky-50 text-sky-700",
  Metrica: "bg-lime-50 text-lime-700",
};
const TIPO_DEFAULT = "bg-rose-50 text-rose-700";

function TipoTag({ tipo }: { tipo: string | null }) {
  const cls = (tipo && TIPO_STYLES[tipo]) || TIPO_DEFAULT;
  return (
    <span className={`inline-block rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${cls}`}>
      {tipo || "Sin clasificar"}
    </span>
  );
}

function CaracteristicaTag({ num, nombre }: { num: number | null; nombre: string | null }) {
  return (
    <span
      title={nombre ?? undefined}
      className="inline-block rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] font-bold text-slate-600"
    >
      {num != null ? `C${num}` : "—"}
    </span>
  );
}

interface PmIndicadoresTabProps {
  /** Factor y Característica son filtros globales del módulo — el estado
   * vive en PlanMejoramientoPage y se comparte con PmMetricasTab. */
  factor: string;
  onFactorChange: (value: string) => void;
  caracteristica: string;
  onCaracteristicaChange: (value: string) => void;
}

/** Pestaña "Indicadores" del Plan de Mejoramiento — paridad con
 * pages/plan_mejoramiento.py::_render_tab_indicadores (ver
 * docs/migration/PLAN_MIGRACION_PRIORIZADO.md ítem 0). */
export function PmIndicadoresTab({
  factor,
  onFactorChange,
  caracteristica,
  onCaracteristicaChange,
}: PmIndicadoresTabProps) {
  const { isAuthenticated } = useAuthReady();
  const [subvista, setSubvista] = useState<SubVista>("metas");
  const [tipo, setTipo] = useState("Todos");
  const [nombre, setNombre] = useState("");
  const nombreDebounced = useDebounce(nombre);
  const [seleccion, setSeleccion] = useState<{ factor: string; indicador: string } | null>(null);

  const query = useQuery({
    queryKey: ["plan-indicadores", subvista, factor, caracteristica, tipo, nombreDebounced],
    queryFn: () =>
      fetchPlanIndicadoresDashboard({
        subvista,
        ...(factor !== "Todos" ? { factor } : {}),
        ...(caracteristica !== "Todas" ? { caracteristica } : {}),
        ...(tipo !== "Todos" ? { tipo } : {}),
        ...(nombreDebounced.trim() ? { nombre: nombreDebounced.trim() } : {}),
      }),
    enabled: isAuthenticated,
  });

  const data = query.data;
  const tabla = useMemo(() => data?.tabla ?? [], [data]);
  const { page, setPage, pageSize, setPageSize, pageItems, totalPages } = usePagination(tabla);

  const chartData = useMemo(() => {
    const porFactor = new Map<string, { suma: number; n: number; factorNum: number | null }>();
    for (const row of tabla) {
      const acc = porFactor.get(row.factor) ?? { suma: 0, n: 0, factorNum: row.factor_num };
      if ("metas" in row) {
        const tieneMeta = METAS_YEARS.some((y) => row.metas[y].valor != null);
        acc.n += tieneMeta ? 1 : 0;
        acc.suma = acc.n;
      } else {
        const vals = [row.cump_2025.valor, row.cump_2026.valor].filter(
          (v): v is number => v != null
        );
        if (vals.length) {
          acc.suma += vals.reduce((s, v) => s + v, 0) / vals.length;
          acc.n += 1;
        }
      }
      porFactor.set(row.factor, acc);
    }
    return Array.from(porFactor.entries()).map(([f, { suma, n, factorNum }]) => ({
      factor: f,
      factorNum,
      value: subvista === "metas" ? n : n ? Math.round((suma / n) * 10) / 10 : 0,
    }));
  }, [tabla, subvista]);

  return (
    <div className="space-y-6">
      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver el plan de mejoramiento.</p>
      ) : query.isLoading ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-200" />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard label="Indicadores del plan" value={data?.kpis.total ?? 0} unit="asociados a 12 factores CNA" />
            <KPICard label="Con meta 2026–2030" value={data?.kpis.con_meta_futura ?? 0} />
            <KPICard label="Con cumplimiento histórico" value={data?.kpis.con_cumplimiento_historico ?? 0} />
            <KPICard
              label="Aprobados"
              value={data?.kpis.aprobados ?? 0}
              unit={`${data?.kpis.pct_aprobados ?? 0}% del total`}
            />
          </div>

          <div className="flex gap-2">
            {(["metas", "historico"] as const).map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setSubvista(v)}
                className={`rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
                  subvista === v ? "bg-poli-navy text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {v === "metas" ? "Metas 2026–2030" : "Cumplimiento histórico"}
              </button>
            ))}
          </div>
          <p className="text-xs text-slate-500">
            {subvista === "metas"
              ? "Trayectoria de metas definidas por indicador, agrupadas por factor CNA."
              : "Meta, ejecución y % de cumplimiento 2025–2026 por indicador."}
          </p>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
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
                value={tipo}
                onChange={(e) => setTipo(e.target.value)}
              >
                <option value="Todos">Todos los tipos</option>
                {(data?.filtros.tipos ?? []).map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <input
                type="search"
                placeholder="Buscar indicador, característica…"
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm sm:col-span-2"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
              />
            </div>
            <div className="mt-3 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">{data?.total ?? 0} indicadores</span>
              <button
                type="button"
                disabled={!tabla.length}
                onClick={() =>
                  downloadPlanIndicadoresExport({
                    subvista,
                    ...(factor !== "Todos" ? { factor } : {}),
                    ...(caracteristica !== "Todas" ? { caracteristica } : {}),
                    ...(tipo !== "Todos" ? { tipo } : {}),
                    ...(nombre.trim() ? { nombre: nombre.trim() } : {}),
                  })
                }
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40"
              >
                Exportar a Excel
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <PmFactorRings
              data={chartData}
              valueSuffix={subvista === "metas" ? "" : "%"}
              emptyMessage="No hay indicadores con este filtro."
            />
          </div>

          {!tabla.length ? (
            <p className="text-sm text-slate-500">No hay indicadores para este filtro.</p>
          ) : (
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-slate-50/80 text-[11px] font-bold uppercase tracking-wide text-slate-500">
                    <tr>
                      {subvista === "metas" ? (
                        <>
                          <th className="px-4 py-3">Factor</th>
                          <th className="px-4 py-3">Caract.</th>
                          <th className="px-4 py-3">Indicador</th>
                          <th className="px-4 py-3">Tipo</th>
                          {METAS_YEARS.map((y) => (
                            <th key={y} className="px-4 py-3 text-right">
                              Meta {y}
                            </th>
                          ))}
                        </>
                      ) : (
                        <>
                          <th className="px-4 py-3">Factor</th>
                          <th className="px-4 py-3">Caract.</th>
                          <th className="px-4 py-3">Indicador</th>
                          <th className="px-4 py-3">Meta vs Ejec. 2025</th>
                          <th className="px-4 py-3 text-right">% Cump 2025</th>
                          <th className="px-4 py-3">Meta vs Ejec. 2026</th>
                          <th className="px-4 py-3 text-right">% Cump 2026</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {pageItems.map((row, i) => (
                      <tr
                        key={i}
                        className={`group cursor-pointer border-l-2 border-l-transparent transition-colors hover:border-l-4 hover:!bg-slate-50 ${
                          i % 2 === 1 ? "bg-slate-50/40" : ""
                        }`}
                        onMouseEnter={(e) => (e.currentTarget.style.borderLeftColor = getFactorColor(row.factor_num))}
                        onMouseLeave={(e) => (e.currentTarget.style.borderLeftColor = "transparent")}
                        onClick={() => setSeleccion({ factor: row.factor, indicador: row.indicador })}
                      >
                        {"metas" in row ? (
                          <>
                            <td className="px-4 py-2.5">
                              <PmFactorBadge factorNum={row.factor_num} />
                            </td>
                            <td className="px-4 py-2.5">
                              <CaracteristicaTag num={row.caracteristica_num} nombre={row.caracteristica} />
                            </td>
                            <td className="whitespace-normal break-words px-4 py-2.5 font-medium text-slate-800">
                              {row.indicador}
                            </td>
                            <td className="px-4 py-2.5">
                              <TipoTag tipo={row.tipo} />
                            </td>
                            {METAS_YEARS.map((y) => (
                              <td key={y} className="px-4 py-2.5 text-right tabular-nums text-slate-700">
                                {row.metas[y].valor_fmt}
                              </td>
                            ))}
                          </>
                        ) : (
                          <>
                            <td className="px-4 py-2.5">
                              <PmFactorBadge factorNum={row.factor_num} />
                            </td>
                            <td className="px-4 py-2.5">
                              <CaracteristicaTag num={row.caracteristica_num} nombre={row.caracteristica} />
                            </td>
                            <td className="whitespace-normal break-words px-4 py-2.5 font-medium text-slate-800">
                              {row.indicador}
                            </td>
                            <td className="px-4 py-2.5">
                              <PmBulletProgress
                                meta={row.meta_2025.valor}
                                ejecucion={row.ejecucion_2025.valor}
                                metaFmt={row.meta_2025.valor_fmt}
                                ejecucionFmt={row.ejecucion_2025.valor_fmt}
                                color={getFactorColor(row.factor_num)}
                              />
                            </td>
                            <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-slate-800">
                              {row.cump_2025.valor_fmt}
                            </td>
                            <td className="px-4 py-2.5">
                              <PmBulletProgress
                                meta={row.meta_2026.valor}
                                ejecucion={row.ejecucion_2026.valor}
                                metaFmt={row.meta_2026.valor_fmt}
                                ejecucionFmt={row.ejecucion_2026.valor_fmt}
                                color={getFactorColor(row.factor_num)}
                              />
                            </td>
                            <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-slate-800">
                              {row.cump_2026.valor_fmt}
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
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

      <PmIndicadorModal seleccion={seleccion} onClose={() => setSeleccion(null)} />
    </div>
  );
}
