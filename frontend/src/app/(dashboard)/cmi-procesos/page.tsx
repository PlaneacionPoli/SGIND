"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CmiProcesosFichaModal } from "@/components/cmi/CmiProcesosFichaModal";
import { CmiProcesosAlertasTab } from "@/components/cmi/CmiProcesosAlertasTab";
import { CmiProcesosAnalisisTab } from "@/components/cmi/CmiProcesosAnalisisTab";
import { CmiProcesosFilters } from "@/components/cmi/CmiProcesosFilters";
import { CmiProcesosListadoTab } from "@/components/cmi/CmiProcesosListadoTab";
import { CmiProcesosResumenTab } from "@/components/cmi/CmiProcesosResumenTab";
import { CmiProcesosUnidadesTab } from "@/components/cmi/CmiProcesosUnidadesTab";
import {
  downloadCMIProcesosExport,
  downloadFichaIndicadorPdf,
  fetchCMIProcesosDashboard,
  fetchCMIProcesosFicha,
  fetchCMIProcesosFiltros,
} from "@/lib/api";
import { useAuthReady } from "@/stores/auth-store";

const TABS = [
  { id: "resumen", label: "Resumen", icon: "📋" },
  { id: "procesos", label: "Procesos y Unidades", icon: "🏢" },
  { id: "listado", label: "Indicadores", icon: "📊" },
  { id: "alertas", label: "Alertas", icon: "🚨" },
  { id: "analisis", label: "Análisis Avanzado", icon: "📈" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function CMIProcesosPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Cargando CMI por procesos...</p>}>
      <CMIProcesosContent />
    </Suspense>
  );
}

function CMIProcesosContent() {
  const { isAuthenticated } = useAuthReady();
  const [anio, setAnio] = useState<number | null>(null);
  const [mes, setMes] = useState<number | null>(null);
  const [unidad, setUnidad] = useState("Todos");
  const [proceso, setProceso] = useState("Todos");
  const [subproceso, setSubproceso] = useState("Todos");
  const [clasificacion, setClasificacion] = useState("Todos");
  const [frecuencia, setFrecuencia] = useState("Todos");
  const [tab, setTab] = useState<TabId>("resumen");
  const [fichaId, setFichaId] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [downloadingFichaPdf, setDownloadingFichaPdf] = useState(false);

  const filtrosQuery = useQuery({
    queryKey: ["cmi-procesos-filtros", anio],
    queryFn: () => fetchCMIProcesosFiltros(anio ?? undefined),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (anio == null && filtrosQuery.data?.anio_default) {
      setAnio(filtrosQuery.data.anio_default);
      setMes(filtrosQuery.data.mes_default);
    }
  }, [anio, filtrosQuery.data]);

  useEffect(() => {
    if (filtrosQuery.data?.mes_default != null && mes == null) {
      setMes(filtrosQuery.data.mes_default);
    }
  }, [filtrosQuery.data, mes]);

  const anioEfectivo = anio ?? filtrosQuery.data?.anio_default ?? new Date().getFullYear();
  const mesEfectivo = mes ?? filtrosQuery.data?.mes_default ?? 12;

  const subprocesosFiltrados: string[] =
    proceso !== "Todos" && filtrosQuery.data?.subprocesos_por_proceso
      ? (filtrosQuery.data.subprocesos_por_proceso[proceso] ?? [])
      : (filtrosQuery.data?.subprocesos ?? []);

  const dashboardQuery = useQuery({
    queryKey: [
      "cmi-procesos-dashboard",
      anioEfectivo,
      mesEfectivo,
      unidad,
      proceso,
      subproceso,
      clasificacion,
      frecuencia,
    ],
    queryFn: () =>
      fetchCMIProcesosDashboard({
        anio: anioEfectivo,
        mes: mesEfectivo,
        unidad: unidad !== "Todos" ? unidad : undefined,
        proceso: proceso !== "Todos" ? proceso : undefined,
        subproceso: subproceso !== "Todos" ? subproceso : undefined,
        clasificacion: clasificacion !== "Todos" ? clasificacion : undefined,
        frecuencia: frecuencia !== "Todos" ? frecuencia : undefined,
      }),
    enabled: isAuthenticated && anio != null && mes != null,
  });

  const fichaQuery = useQuery({
    queryKey: ["cmi-procesos-ficha", fichaId, anioEfectivo, mesEfectivo, unidad, proceso, subproceso],
    queryFn: () =>
      fetchCMIProcesosFicha(fichaId!, {
        anio: anioEfectivo,
        mes: mesEfectivo,
        unidad: unidad !== "Todos" ? unidad : undefined,
        proceso: proceso !== "Todos" ? proceso : undefined,
        subproceso: subproceso !== "Todos" ? subproceso : undefined,
      }),
    enabled: isAuthenticated && !!fichaId,
  });

  const exportParams = {
    anio: anioEfectivo,
    mes: mesEfectivo,
    unidad: unidad !== "Todos" ? unidad : undefined,
    proceso: proceso !== "Todos" ? proceso : undefined,
    subproceso: subproceso !== "Todos" ? subproceso : undefined,
    clasificacion: clasificacion !== "Todos" ? clasificacion : undefined,
    frecuencia: frecuencia !== "Todos" ? frecuencia : undefined,
  };

  const handleExport = async (formato: "csv" | "xlsx") => {
    setExporting(true);
    try {
      await downloadCMIProcesosExport({ ...exportParams, formato });
    } finally {
      setExporting(false);
    }
  };

  const handleDownloadFichaPdf = async () => {
    if (!fichaId) return;
    setDownloadingFichaPdf(true);
    try {
      await downloadFichaIndicadorPdf(fichaId, {
        anio: anioEfectivo,
        mes: mesEfectivo,
        origen: "procesos",
        unidad: unidad !== "Todos" ? unidad : undefined,
        proceso: proceso !== "Todos" ? proceso : undefined,
        subproceso: subproceso !== "Todos" ? subproceso : undefined,
      });
    } finally {
      setDownloadingFichaPdf(false);
    }
  };

  const handleReset = useCallback(() => {
    if (filtrosQuery.data) {
      setAnio(filtrosQuery.data.anio_default);
      setMes(filtrosQuery.data.mes_default);
    }
    setUnidad("Todos");
    setProceso("Todos");
    setSubproceso("Todos");
    setClasificacion("Todos");
    setFrecuencia("Todos");
  }, [filtrosQuery.data]);

  const data = dashboardQuery.data;

  return (
    <div className="mx-auto max-w-[1400px] space-y-5 px-1">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">CMI por Procesos</h2>
        <p className="mt-1 text-slate-600">
          Balanced Scorecard por procesos — Subprocesos=1, validados contra Kawak
        </p>
      </div>

      {isAuthenticated && filtrosQuery.data && anio != null && mes != null && (
        <CmiProcesosFilters
          anio={anioEfectivo}
          mes={mesEfectivo}
          anios={filtrosQuery.data.anios}
          meses={filtrosQuery.data.meses}
          mesesNombres={filtrosQuery.data.meses_nombres}
          unidades={filtrosQuery.data.unidades}
          procesos={filtrosQuery.data.procesos}
          subprocesos={subprocesosFiltrados}
          clasificaciones={filtrosQuery.data.clasificaciones}
          frecuencias={filtrosQuery.data.frecuencias}
          unidad={unidad}
          proceso={proceso}
          subproceso={subproceso}
          clasificacion={clasificacion}
          frecuencia={frecuencia}
          onAnioChange={(y) => {
            setAnio(y);
            setMes(null);
          }}
          onMesChange={setMes}
          onUnidadChange={setUnidad}
          onProcesoChange={(v) => { setProceso(v); setSubproceso("Todos"); }}
          onSubprocesoChange={setSubproceso}
          onClasificacionChange={setClasificacion}
          onFrecuenciaChange={setFrecuencia}
          onReset={handleReset}
        />
      )}

      {data && tab !== "resumen" && (
        <p className="text-xs text-slate-500">
          Corte filtrado: {data.mes_nombre} {data.anio}
          {tab === "listado" || tab === "alertas"
            ? ` · ${data.filtros_aplicados.unidad} · ${data.filtros_aplicados.proceso}`
            : data.vista_global?.mes_nombre
              ? ` · Global: ${data.vista_global.mes_nombre}`
              : ""}
        </p>
      )}

      <div className="inline-flex max-w-full flex-wrap gap-1 rounded-xl bg-slate-100 p-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-3 py-2.5 text-sm font-semibold transition sm:px-4 ${
              tab === t.id
                ? "bg-poli-navy text-white shadow-md"
                : "text-slate-600 hover:bg-white hover:text-slate-900"
            }`}
          >
            <span className="mr-1.5">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver CMI por procesos.</p>
      ) : dashboardQuery.isLoading ? (
        <div className="space-y-4">
          <div className="h-32 animate-pulse rounded-2xl bg-slate-200" />
          <div className="grid gap-4 sm:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 animate-pulse rounded-2xl bg-slate-200" />
            ))}
          </div>
        </div>
      ) : dashboardQuery.isError ? (
        <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          No se pudieron cargar los datos. Verifique que el backend esté activo y reconstruya el contenedor
          frontend si acaba de actualizar.
        </p>
      ) : !data ? (
        <p className="text-sm text-slate-500">No hay datos disponibles.</p>
      ) : (
        <>
          {data.total_indicadores === 0 && (
            <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              No hay datos para la combinación de filtros seleccionada.
            </p>
          )}
          {tab === "resumen" && (
            data.vista_global?.kpis ? (
              <CmiProcesosResumenTab vista={data.vista_global} baseAnio={data.meta.base_anio} />
            ) : (
              <p className="text-sm text-slate-500">Sin datos globales para el resumen.</p>
            )
          )}
          {tab === "procesos" && (
            data.vista_global?.kpis ? (
              <CmiProcesosUnidadesTab
                unidades={data.vista_global.unidades_detalle}
                procesoBars={data.vista_global.proceso_bars}
                tipoCards={data.vista_global.tipo_proceso_cards}
                procesos={data.vista_global.procesos_detalle}
                comparativa={data.vista_global.comparativa_procesos ?? []}
                baseAnio={data.meta.base_anio}
              />
            ) : (
              <p className="text-sm text-slate-500">Sin datos globales de procesos.</p>
            )
          )}
          {tab === "listado" && (
            <CmiProcesosListadoTab
              indicadores={data.indicadores}
              summary={data.indicadores_summary}
              ejecucionVariacion={data.ejecucion_variacion}
              onOpenFicha={setFichaId}
              onExportCsv={() => handleExport("csv")}
              onExportExcel={() => handleExport("xlsx")}
              exporting={exporting}
            />
          )}
          {tab === "alertas" && (
            <CmiProcesosAlertasTab
              peligro={data.alertas.peligro}
              alerta={data.alertas.alerta}
              items={data.alertas.items}
              alertasCriticas={data.vista_global?.alertas_criticas ?? []}
              onOpenFicha={setFichaId}
            />
          )}
          {tab === "analisis" && (
            <CmiProcesosAnalisisTab
              data={data}
              comparativa={data.vista_global?.comparativa_procesos ?? []}
            />
          )}
        </>
      )}

      <CmiProcesosFichaModal
        ficha={fichaQuery.data ?? null}
        loading={fichaQuery.isLoading}
        onClose={() => setFichaId(null)}
        onDownloadPdf={handleDownloadFichaPdf}
        downloadingPdf={downloadingFichaPdf}
      />
    </div>
  );
}
