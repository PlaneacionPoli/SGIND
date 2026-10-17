"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CmiProcesosFichaModal } from "@/components/cmi/CmiProcesosFichaModal";
import { DataFreshnessFooter } from "@/components/layout/DataFreshnessFooter";
import { CmiProcesosAlertasTab } from "@/components/cmi/CmiProcesosAlertasTab";
import { CmiProcesosAnalisisTab } from "@/components/cmi/CmiProcesosAnalisisTab";
import { CmiProcesosFilters } from "@/components/cmi/CmiProcesosFilters";
import { CmiProcesosMapaTab } from "@/components/cmi/CmiProcesosMapaTab";
import { CmiProcesosListadoTab } from "@/components/cmi/CmiProcesosListadoTab";
import { CmiProcesosResumenTab } from "@/components/cmi/CmiProcesosResumenTab";
import {
  downloadCMIProcesosExport,
  downloadFichaIndicadorPdf,
  fetchCMIProcesosDashboard,
  fetchCMIProcesosFicha,
  fetchCMIProcesosFiltros,
  fetchCMIProcesosMapa,
} from "@/lib/api";
import { PdiChip } from "@/components/ui/PdiChip";
import { usePdiSeleccionado } from "@/lib/pdi";
import { useAuthReady } from "@/stores/auth-store";

/**
 * Orden del recorrido: ¿cómo vamos? (Resumen) → ¿dónde y cómo ha evolucionado? (Mapa) →
 * ¿qué indicadores hay? (Indicadores) → ¿qué atender? (Alertas) → ¿qué hacer? (Análisis).
 */
const TABS = [
  { id: "resumen", label: "Resumen", icon: "📋", usaFiltros: true },
  { id: "mapa", label: "Mapa de procesos", icon: "🗺️", usaFiltros: false },
  { id: "listado", label: "Indicadores", icon: "📊", usaFiltros: true },
  { id: "alertas", label: "Alertas", icon: "🚨", usaFiltros: true },
  { id: "analisis", label: "Análisis", icon: "📈", usaFiltros: true },
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
  // El PDI es solo informativo (alineación en la ficha del indicador): no se exige, no filtra
  // y no recorta los años. Sin ?pdi= el backend usa el vigente.
  const pdi = usePdiSeleccionado(false) ?? undefined;
  const { isAuthenticated } = useAuthReady();
  const [anio, setAnio] = useState<number | null>(null);
  const [unidad, setUnidad] = useState("Todos");
  const [proceso, setProceso] = useState("Todos");
  const [subproceso, setSubproceso] = useState("Todos");
  const [clasificacion, setClasificacion] = useState("Todos");
  const [frecuencia, setFrecuencia] = useState("Todos");
  const [tab, setTab] = useState<TabId>("resumen");
  const [fichaId, setFichaId] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [downloadingFichaPdf, setDownloadingFichaPdf] = useState(false);

  const mapaQuery = useQuery({
    queryKey: ["cmi-procesos-mapa"],
    queryFn: fetchCMIProcesosMapa,
    enabled: isAuthenticated,
  });

  const filtrosQuery = useQuery({
    queryKey: ["cmi-procesos-filtros", pdi, anio],
    queryFn: () => fetchCMIProcesosFiltros(anio ?? undefined, undefined, pdi),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (anio == null && filtrosQuery.data?.anio_default) setAnio(filtrosQuery.data.anio_default);
  }, [anio, filtrosQuery.data]);

  const anioEfectivo = anio ?? filtrosQuery.data?.anio_default ?? new Date().getFullYear();

  const subprocesosFiltrados: string[] =
    proceso !== "Todos" && filtrosQuery.data?.subprocesos_por_proceso
      ? (filtrosQuery.data.subprocesos_por_proceso[proceso] ?? [])
      : (filtrosQuery.data?.subprocesos ?? []);

  // Un solo corte por año: el cierre anual o, en el año en curso, el último reporte de cada indicador.
  const filtrosApi = {
    anio: anioEfectivo,
    unidad: unidad !== "Todos" ? unidad : undefined,
    proceso: proceso !== "Todos" ? proceso : undefined,
    subproceso: subproceso !== "Todos" ? subproceso : undefined,
    clasificacion: clasificacion !== "Todos" ? clasificacion : undefined,
    frecuencia: frecuencia !== "Todos" ? frecuencia : undefined,
    pdi,
  };

  const dashboardQuery = useQuery({
    queryKey: ["cmi-procesos-dashboard", filtrosApi],
    queryFn: () => fetchCMIProcesosDashboard(filtrosApi),
    enabled: isAuthenticated && anio != null,
  });

  const fichaQuery = useQuery({
    queryKey: ["cmi-procesos-ficha", pdi, fichaId, anioEfectivo],
    queryFn: () => fetchCMIProcesosFicha(fichaId!, { anio: anioEfectivo, pdi }),
    enabled: isAuthenticated && !!fichaId,
  });

  const handleExport = async (formato: "csv" | "xlsx") => {
    setExporting(true);
    try {
      await downloadCMIProcesosExport({ ...filtrosApi, formato });
    } finally {
      setExporting(false);
    }
  };

  const handleDownloadFichaPdf = async () => {
    if (!fichaId) return;
    setDownloadingFichaPdf(true);
    try {
      await downloadFichaIndicadorPdf(fichaId, { anio: anioEfectivo, origen: "procesos" });
    } finally {
      setDownloadingFichaPdf(false);
    }
  };

  const handleReset = useCallback(() => {
    if (filtrosQuery.data) setAnio(filtrosQuery.data.anio_default);
    setUnidad("Todos");
    setProceso("Todos");
    setSubproceso("Todos");
    setClasificacion("Todos");
    setFrecuencia("Todos");
  }, [filtrosQuery.data]);

  const data = dashboardQuery.data;
  const vista = data?.vista_filtrada ?? data?.vista_global;
  const tabActual = TABS.find((t) => t.id === tab);
  const mostrarFiltros = !!tabActual?.usaFiltros;
  const esParcial = mapaQuery.data?.anio_parcial === anioEfectivo;

  return (
    <div className="mx-auto max-w-[1400px] space-y-5 px-1">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-2xl font-bold text-slate-900">CMI por Procesos</h2>
          {pdi && <PdiChip pdi={pdi} className="text-slate-700" />}
        </div>
        <p className="mt-1 text-slate-600">
          Cumplimiento por proceso y subproceso. Años anteriores: cierre anual; año en curso: último reporte de cada
          indicador.
        </p>
      </div>

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

      {mostrarFiltros && isAuthenticated && filtrosQuery.data && anio != null && (
        <CmiProcesosFilters
          anio={anioEfectivo}
          mes={0}
          anios={filtrosQuery.data.anios}
          meses={[]}
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
          onAnioChange={setAnio}
          onMesChange={() => undefined}
          onUnidadChange={setUnidad}
          onProcesoChange={(v) => {
            setProceso(v);
            setSubproceso("Todos");
          }}
          onSubprocesoChange={setSubproceso}
          onClasificacionChange={setClasificacion}
          onFrecuenciaChange={setFrecuencia}
          onReset={handleReset}
        />
      )}

      {mostrarFiltros && data && (
        <p className="text-xs text-slate-500">
          Base: {esParcial ? `${anioEfectivo} parcial · último reporte de cada indicador (más reciente: ${data.mes_nombre})` : `cierre ${anioEfectivo}`}
          . Cada indicador muestra su propio mes de reporte.
        </p>
      )}

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver CMI por procesos.</p>
      ) : tab === "mapa" ? (
        mapaQuery.isLoading ? (
          <div className="h-64 animate-pulse rounded-2xl bg-slate-200" />
        ) : mapaQuery.isError || !mapaQuery.data ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            No se pudo cargar el mapa de procesos.
          </p>
        ) : (
          <CmiProcesosMapaTab mapa={mapaQuery.data} onOpenFicha={setFichaId} />
        )
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
          {tab === "resumen" &&
            (vista?.kpis ? (
              <CmiProcesosResumenTab
                vista={vista}
                mixNiveles={mapaQuery.data?.mix_niveles}
                anioParcial={mapaQuery.data?.anio_parcial ?? null}
              />
            ) : (
              <p className="text-sm text-slate-500">Sin datos para el resumen.</p>
            ))}
          {tab === "listado" && (
            <CmiProcesosListadoTab
              indicadores={data.indicadores}
              summary={data.indicadores_summary}
              ejecucionVariacion={data.ejecucion_variacion}
              catalogCharts={data.catalog_charts}
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
              alertasCriticas={vista?.alertas_criticas ?? []}
              onOpenFicha={setFichaId}
            />
          )}
          {tab === "analisis" && <CmiProcesosAnalisisTab data={data} />}
        </>
      )}

      <CmiProcesosFichaModal
        ficha={fichaQuery.data ?? null}
        loading={fichaQuery.isLoading}
        onClose={() => setFichaId(null)}
        onDownloadPdf={handleDownloadFichaPdf}
        downloadingPdf={downloadingFichaPdf}
      />

      <DataFreshnessFooter />
    </div>
  );
}
