"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { CmiAlertasTab } from "@/components/cmi/CmiAlertasTab";
import { CmiFichaModal } from "@/components/cmi/CmiFichaModal";
import { CmiFilters } from "@/components/cmi/CmiFilters";
import { CmiLineasTab } from "@/components/cmi/CmiLineasTab";
import { CmiListadoTab } from "@/components/cmi/CmiListadoTab";
import { CmiResumenTab } from "@/components/cmi/CmiResumenTab";
import { downloadFichaIndicadorPdf, fetchCMIDashboard, fetchCMIFicha, fetchCMIFiltros } from "@/lib/api";
import { useAuthReady } from "@/stores/auth-store";

const TABS = [
  { id: "resumen", label: "Resumen Desglosado" },
  { id: "lineas", label: "Líneas Estratégicas" },
  { id: "listado", label: "Listado de Indicadores" },
  { id: "alertas", label: "Alertas" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function CMIEstrategicoPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Cargando CMI estratégico...</p>}>
      <CMIEstrategicoContent />
    </Suspense>
  );
}

function CMIEstrategicoContent() {
  const { isAuthenticated } = useAuthReady();
  const searchParams = useSearchParams();
  const [anio, setAnio] = useState<number | null>(null);
  const [corte, setCorte] = useState<string>("Diciembre");
  const [tab, setTab] = useState<TabId>("resumen");
  const [expandLineaKey, setExpandLineaKey] = useState<string | null>(null);
  const [fichaId, setFichaId] = useState<string | null>(null);
  const [downloadingFichaPdf, setDownloadingFichaPdf] = useState(false);

  const filtrosQuery = useQuery({
    queryKey: ["cmi-filtros"],
    queryFn: fetchCMIFiltros,
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (anio == null && filtrosQuery.data?.anio_default) {
      setAnio(filtrosQuery.data.anio_default);
      setCorte(filtrosQuery.data.corte_default);
    }
  }, [anio, filtrosQuery.data]);

  useEffect(() => {
    const lineaParam = searchParams.get("cmi_linea");
    if (lineaParam) {
      setTab("lineas");
      setExpandLineaKey(lineaParam);
    }
  }, [searchParams]);

  const anioEfectivo = anio ?? filtrosQuery.data?.anio_default ?? new Date().getFullYear();

  const dashboardQuery = useQuery({
    queryKey: ["cmi-dashboard", anioEfectivo, corte],
    queryFn: () => fetchCMIDashboard({ anio: anioEfectivo, corte }),
    enabled: isAuthenticated && anio != null,
  });

  const fichaQuery = useQuery({
    queryKey: ["cmi-ficha", fichaId, anioEfectivo, corte],
    queryFn: () => fetchCMIFicha(fichaId!, { anio: anioEfectivo, corte }),
    enabled: isAuthenticated && !!fichaId,
  });

  const handleVerLinea = useCallback((lineaKey: string) => {
    setTab("lineas");
    setExpandLineaKey(lineaKey);
  }, []);

  const handleDownloadFichaPdf = useCallback(async () => {
    if (!fichaId) return;
    setDownloadingFichaPdf(true);
    try {
      await downloadFichaIndicadorPdf(fichaId, { anio: anioEfectivo, corte, origen: "estrategico" });
    } finally {
      setDownloadingFichaPdf(false);
    }
  }, [fichaId, anioEfectivo, corte]);

  const handleReset = () => {
    if (filtrosQuery.data) {
      setAnio(filtrosQuery.data.anio_default);
      setCorte(filtrosQuery.data.corte_default);
    }
  };

  const data = dashboardQuery.data;
  const anios = data?.anios_disponibles ?? filtrosQuery.data?.anios ?? [];
  const cortes = data?.cortes ?? filtrosQuery.data?.cortes ?? ["Junio", "Diciembre"];

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 px-1">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">CMI Estratégico</h2>
        <p className="mt-1 text-slate-600">
          Indicadores del Plan Estratégico (PDI) interactivo y detallado.
        </p>
      </div>

      {isAuthenticated && (
        <CmiFilters
          anio={anioEfectivo}
          corte={corte}
          anios={anios}
          cortes={cortes}
          onAnioChange={setAnio}
          onCorteChange={setCorte}
          onReset={handleReset}
        />
      )}

      <div className="inline-flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-4 py-2.5 text-sm font-semibold transition ${
              tab === t.id
                ? "bg-poli-navy text-white shadow-md"
                : "text-slate-600 hover:bg-white hover:text-slate-900"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver el CMI estratégico.</p>
      ) : dashboardQuery.isLoading ? (
        <p className="text-sm text-slate-500">Cargando datos del CMI estratégico...</p>
      ) : dashboardQuery.isError ? (
        <p className="text-sm text-red-600">No se pudieron cargar los datos del CMI.</p>
      ) : !data || data.total_indicadores === 0 ? (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          No hay indicadores para los filtros seleccionados (año {anioEfectivo}, corte {corte}).
        </p>
      ) : tab === "resumen" ? (
        <CmiResumenTab data={data} onVerLinea={handleVerLinea} />
      ) : tab === "lineas" ? (
        <CmiLineasTab lineas={data.lineas_detalle} expandLineaKey={expandLineaKey} />
      ) : tab === "listado" ? (
        <CmiListadoTab indicadores={data.indicadores} onOpenFicha={setFichaId} />
      ) : (
        <CmiAlertasTab
          peligro={data.alertas.peligro}
          alerta={data.alertas.alerta}
          items={data.alertas.items}
          onOpenFicha={setFichaId}
        />
      )}

      <CmiFichaModal
        ficha={fichaQuery.data ?? null}
        loading={fichaQuery.isLoading}
        onClose={() => setFichaId(null)}
        onDownloadPdf={handleDownloadFichaPdf}
        downloadingPdf={downloadingFichaPdf}
      />
    </div>
  );
}
