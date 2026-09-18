"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { KPICard } from "@/components/ui/KPICard";
import { downloadPlanIndicadoresExport, fetchPlanIndicadoresDashboard } from "@/lib/api";
import { useAuthReady } from "@/stores/auth-store";
import { PmFactorBarChart } from "./PmFactorBarChart";
import { PmIndicadorModal } from "./PmIndicadorModal";

type SubVista = "metas" | "historico";

const METAS_YEARS = ["2026", "2027", "2028", "2029", "2030"] as const;

/** Pestaña "Indicadores" del Plan de Mejoramiento — paridad con
 * pages/plan_mejoramiento.py::_render_tab_indicadores (ver
 * docs/migration/PLAN_MIGRACION_PRIORIZADO.md ítem 0). */
export function PmIndicadoresTab() {
  const { isAuthenticated } = useAuthReady();
  const [subvista, setSubvista] = useState<SubVista>("metas");
  const [factor, setFactor] = useState("Todos");
  const [tipo, setTipo] = useState("Todos");
  const [nombre, setNombre] = useState("");
  const [seleccion, setSeleccion] = useState<{ factor: string; indicador: string } | null>(null);

  const query = useQuery({
    queryKey: ["plan-indicadores", subvista, factor, tipo, nombre],
    queryFn: () =>
      fetchPlanIndicadoresDashboard({
        subvista,
        ...(factor !== "Todos" ? { factor } : {}),
        ...(tipo !== "Todos" ? { tipo } : {}),
        ...(nombre.trim() ? { nombre: nombre.trim() } : {}),
      }),
    enabled: isAuthenticated,
  });

  const data = query.data;
  const tabla = data?.tabla ?? [];

  const chartData = useMemo(() => {
    const porFactor = new Map<string, { suma: number; n: number }>();
    for (const row of tabla) {
      const acc = porFactor.get(row.factor) ?? { suma: 0, n: 0 };
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
    return Array.from(porFactor.entries()).map(([f, { suma, n }]) => ({
      factor: f,
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
                className={`rounded-lg px-4 py-2 text-sm font-semibold ${
                  subvista === v ? "bg-poli-navy text-white" : "bg-slate-100 text-slate-600"
                }`}
              >
                {v === "metas" ? "Metas 2026–2030" : "Cumplimiento histórico"}
              </button>
            ))}
          </div>
          <p className="text-xs text-slate-500">
            {subvista === "metas"
              ? "Trayectoria de metas definidas por indicador, agrupadas por factor CNA."
              : "Meta, ejecución y % de cumplimiento 2025–2026, solo para indicadores con información registrada."}
          </p>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="grid gap-3 sm:grid-cols-4">
              <select
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                value={factor}
                onChange={(e) => setFactor(e.target.value)}
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
                value={tipo}
                onChange={(e) => setTipo(e.target.value)}
              >
                <option value="Todos">Indicador y métrica</option>
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
              <span className="text-xs font-semibold text-slate-500">
                {data?.total ?? 0} {subvista === "metas" ? "con meta definida" : "con dato histórico"}
              </span>
              <button
                type="button"
                disabled={!tabla.length}
                onClick={() =>
                  downloadPlanIndicadoresExport({
                    subvista,
                    ...(factor !== "Todos" ? { factor } : {}),
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

          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <PmFactorBarChart
              data={chartData}
              valueSuffix={subvista === "metas" ? "" : "%"}
              emptyMessage="No hay indicadores con este filtro."
            />
          </div>

          {!tabla.length ? (
            <p className="text-sm text-slate-500">
              {subvista === "metas"
                ? "No hay indicadores con metas 2026–2030 definidas para este filtro."
                : "Ningún indicador de este filtro tiene cumplimiento histórico registrado todavía."}
            </p>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    {subvista === "metas" ? (
                      <>
                        <th className="px-3 py-2">Factor</th>
                        <th className="px-3 py-2">Indicador</th>
                        <th className="px-3 py-2">Tipo</th>
                        {METAS_YEARS.map((y) => (
                          <th key={y} className="px-3 py-2">
                            Meta {y}
                          </th>
                        ))}
                      </>
                    ) : (
                      <>
                        <th className="px-3 py-2">Factor</th>
                        <th className="px-3 py-2">Indicador</th>
                        <th className="px-3 py-2">Meta 2025</th>
                        <th className="px-3 py-2">Ejec. 2025</th>
                        <th className="px-3 py-2">% Cump 2025</th>
                        <th className="px-3 py-2">Meta 2026</th>
                        <th className="px-3 py-2">Ejec. 2026</th>
                        <th className="px-3 py-2">% Cump 2026</th>
                      </>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {tabla.map((row, i) => (
                    <tr
                      key={i}
                      className="cursor-pointer hover:bg-slate-50"
                      onClick={() => setSeleccion({ factor: row.factor, indicador: row.indicador })}
                    >
                      {"metas" in row ? (
                        <>
                          <td className="px-3 py-2">{row.factor_num != null ? `F${row.factor_num}` : "—"}</td>
                          <td className="max-w-xs truncate px-3 py-2">{row.indicador}</td>
                          <td className="px-3 py-2">{row.tipo}</td>
                          {METAS_YEARS.map((y) => (
                            <td key={y} className="px-3 py-2">
                              {row.metas[y].valor_fmt}
                            </td>
                          ))}
                        </>
                      ) : (
                        <>
                          <td className="px-3 py-2">{row.factor_num != null ? `F${row.factor_num}` : "—"}</td>
                          <td className="max-w-xs truncate px-3 py-2">{row.indicador}</td>
                          <td className="px-3 py-2">{row.meta_2025.valor_fmt}</td>
                          <td className="px-3 py-2">{row.ejecucion_2025.valor_fmt}</td>
                          <td className="px-3 py-2">{row.cump_2025.valor_fmt}</td>
                          <td className="px-3 py-2">{row.meta_2026.valor_fmt}</td>
                          <td className="px-3 py-2">{row.ejecucion_2026.valor_fmt}</td>
                          <td className="px-3 py-2">{row.cump_2026.valor_fmt}</td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      <PmIndicadorModal seleccion={seleccion} onClose={() => setSeleccion(null)} />
    </div>
  );
}
