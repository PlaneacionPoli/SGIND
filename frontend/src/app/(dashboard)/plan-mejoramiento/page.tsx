"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CmiCumplimientoHorizBarPlotly } from "@/components/cmi/CmiCumplimientoHorizBarPlotly";
import { CmiDonutNivelPlotly } from "@/components/cmi/CmiDonutNivelPlotly";
import { KPICard } from "@/components/ui/KPICard";
import { YearSegmentedControl } from "@/components/ui/YearSegmentedControl";
import { fetchPlanMejoramientoDashboard } from "@/lib/api";
import { fmtValorSigno } from "@/lib/formatValor";
import { useAuthReady } from "@/stores/auth-store";

const CORTES = ["Junio", "Diciembre"] as const;

export default function PlanMejoramientoPage() {
  const { isAuthenticated } = useAuthReady();
  const [anio, setAnio] = useState<number | null>(null);
  const [corte, setCorte] = useState<string>("Diciembre");
  const [factor, setFactor] = useState("Todos");
  const [caracteristica, setCaracteristica] = useState("Todas");
  const [nombre, setNombre] = useState("");

  const query = useQuery({
    queryKey: ["plan-mejoramiento", anio, corte, factor, caracteristica, nombre],
    queryFn: () =>
      fetchPlanMejoramientoDashboard({
        ...(anio != null ? { anio } : {}),
        corte,
        ...(factor !== "Todos" ? { factor } : {}),
        ...(caracteristica !== "Todas" ? { caracteristica } : {}),
        ...(nombre.trim() ? { nombre: nombre.trim() } : {}),
      }),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (query.data?.filtros_corte && anio == null) {
      setAnio(query.data.filtros_corte.anio_default ?? new Date().getFullYear());
      setCorte(query.data.filtros_corte.corte_default ?? "Diciembre");
    }
  }, [query.data, anio]);

  const data = query.data;
  const anioEff = anio ?? data?.filtros_corte.anio_default ?? new Date().getFullYear();
  const donutData = (data?.graficos.nivel_donut ?? []).map((d) => ({
    nivel: d.nivel,
    cantidad: d.cantidad,
    porcentaje: 0,
    color: d.color,
  }));
  const donutTotal = donutData.reduce((s, d) => s + d.cantidad, 0);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Plan de Mejoramiento</h2>
        <p className="mt-1 text-slate-600">
          Indicadores CNA con filtros por Factor y Característica + cumplimiento de cierre.
        </p>
      </div>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver el plan de mejoramiento.</p>
      ) : query.isLoading ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-200" />
      ) : data?.error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{data.error}</div>
      ) : (
        <>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Filtros de corte</p>
            <div className="flex flex-wrap gap-4">
              {data?.filtros_corte.anios?.length ? (
                <YearSegmentedControl years={data.filtros_corte.anios} anio={anioEff} onChange={setAnio} />
              ) : null}
              <div className="flex gap-2">
                {CORTES.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setCorte(c)}
                    className={`rounded-lg px-4 py-2 text-sm font-semibold ${
                      corte === c ? "bg-poli-navy text-white" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Filtros CNA</p>
            <div className="grid gap-3 sm:grid-cols-3">
              <select
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
                value={factor}
                onChange={(e) => {
                  setFactor(e.target.value);
                  setCaracteristica("Todas");
                }}
              >
                <option value="Todos">Todos los factores</option>
                {(data?.filtros_cna.factores ?? []).map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
              <select
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
                value={caracteristica}
                onChange={(e) => setCaracteristica(e.target.value)}
              >
                <option value="Todas">Todas las características</option>
                {(data?.filtros_cna.caracteristicas ?? []).map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <input
                type="search"
                placeholder="Buscar indicador…"
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
              />
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Corte seleccionado: {corte} {anioEff}
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <KPICard label="Indicadores CNA" value={data?.kpis.indicadores_cna ?? 0} />
            <KPICard label="Factores visibles" value={data?.kpis.factores_visibles ?? 0} />
            <KPICard label="Características visibles" value={data?.kpis.caracteristicas_visibles ?? 0} />
            <KPICard label="Con cumplimiento" value={data?.kpis.con_cumplimiento ?? 0} />
            <KPICard label="Promedio cumplimiento" value={`${data?.kpis.promedio_cumplimiento ?? 0}%`} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="mb-2 text-sm font-bold text-slate-800">Cumplimiento promedio por factor</h3>
              <CmiCumplimientoHorizBarPlotly
                data={(data?.graficos.factor_bars ?? []).map((b) => ({
                  label: b.factor,
                  value: b.cumplimiento,
                  color: b.color,
                }))}
              />
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="mb-2 text-sm font-bold text-slate-800">Distribución de niveles</h3>
              <CmiDonutNivelPlotly data={donutData} total={donutTotal} />
            </div>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <h3 className="border-b border-slate-100 px-4 py-3 text-sm font-bold text-slate-800">Indicadores CNA</h3>
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  {["Id", "Indicador", "Factor", "Característica", "Cumplimiento", "Nivel", "Meta", "Ejecución"].map(
                    (h) => (
                      <th key={h} className="px-3 py-2">
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(data?.tabla_cna ?? []).map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-mono text-xs">{String(row.Id ?? "")}</td>
                    <td className="max-w-xs truncate px-3 py-2">{String(row.Indicador ?? "")}</td>
                    <td className="px-3 py-2">{String(row.Factor ?? "")}</td>
                    <td className="px-3 py-2">{String(row.Caracteristica ?? "")}</td>
                    <td className="px-3 py-2">
                      {row.cumplimiento_pct != null ? `${row.cumplimiento_pct}%` : "—"}
                    </td>
                    <td className="px-3 py-2">
                      <span title={String(row.nivel ?? "")}>
                        {String(row.nivel_emoji ?? "")} {String(row.nivel ?? "")}
                      </span>
                    </td>
                    <td className="px-3 py-2">{fmtValorSigno(row.Meta as number | null, String(row.Meta_Signo ?? "%"), row.Decimales_Meta as number | null)}</td>
                    <td className="px-3 py-2">{fmtValorSigno(row.Ejecucion as number | null, String(row.Ejecucion_s ?? row.EjecS ?? "%"), row.Decimales_Ejecucion as number | null)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <section className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800">Acciones de Mejora asociadas</h3>
            <div className="grid gap-4 sm:grid-cols-4">
              <KPICard label="Total" value={data?.acciones.kpis.total ?? 0} />
              <KPICard label="Cerradas" value={data?.acciones.kpis.cerradas ?? 0} />
              <KPICard label="Abiertas" value={data?.acciones.kpis.abiertas ?? 0} />
              <KPICard
                label="Avance promedio"
                value={data?.acciones.kpis.avance_promedio != null ? `${data.acciones.kpis.avance_promedio}%` : "—"}
              />
            </div>
            {data?.acciones.kpis.vencidas ? (
              <p className="text-xs text-amber-700">{data.acciones.kpis.vencidas} acciones vencidas</p>
            ) : null}
            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    {["Id indicador", "Acción", "Estado", "Estado tiempo", "Avance", "Fecha compromiso", "Responsable"].map(
                      (h) => (
                        <th key={h} className="px-3 py-2">
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(data?.acciones.tabla ?? []).map((row, i) => (
                    <tr key={i}>
                      <td className="px-3 py-2 font-mono text-xs">{String(row.id_indicador ?? "")}</td>
                      <td className="max-w-xs truncate px-3 py-2">{String(row.accion ?? "")}</td>
                      <td className="px-3 py-2">{String(row.estado ?? "")}</td>
                      <td className="px-3 py-2">{String(row.estado_tiempo ?? "")}</td>
                      <td className="px-3 py-2">{row.avance != null ? `${row.avance}%` : "—"}</td>
                      <td className="px-3 py-2">{String(row.fecha_compromiso ?? "")}</td>
                      <td className="px-3 py-2">{String(row.responsable ?? "")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
