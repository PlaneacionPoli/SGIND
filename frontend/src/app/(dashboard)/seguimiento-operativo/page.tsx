"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Grid3x3, Layers, Mail, ClipboardList } from "lucide-react";
import { DataFreshnessFooter } from "@/components/layout/DataFreshnessFooter";
import { AlertasCorreoPanel } from "@/components/seguimiento/AlertasCorreoPanel";
import { AlertasFrecuencia } from "@/components/seguimiento/AlertasFrecuencia";
import { BorradoresListos } from "@/components/seguimiento/BorradoresListos";
import { CumplimientoProcesos } from "@/components/seguimiento/CumplimientoProcesos";
import { DetalleTabla } from "@/components/seguimiento/DetalleTabla";
import { FiltrosCorte, type FiltrosState } from "@/components/seguimiento/FiltrosCorte";
import { EstadoDonut, FrecuenciaChart, TendenciaChart, TopPendientesChart } from "@/components/seguimiento/Graficos";
import { KpiCards } from "@/components/seguimiento/KpiCards";
import { MatrizCalor } from "@/components/seguimiento/MatrizCalor";
import { corteNombre } from "@/components/seguimiento/constants";
import {
  downloadSeguimientoExport,
  fetchSeguimientoDashboard,
  fetchSeguimientoFiltros,
  type SeguimientoColumna,
} from "@/lib/api";
import { useAuthReady } from "@/stores/auth-store";

type Vista = "seguimiento" | "correo";
type VistaProcesos = "mapa" | "lista";
type Orden = { por: SeguimientoColumna | null; dir: "asc" | "desc" };

const COLUMNAS: SeguimientoColumna[] = ["Id", "Indicador", "Proceso", "Periodicidad", "Corte", "Estado"];
const PAGE_SIZES = [25, 50, 100];

const FILTROS_VACIOS: FiltrosState = { anio: null, anioTodos: false, mes: null, proceso: "Todos", estado: "Todos", busqueda: "" };

/** Lee los filtros de la URL (compartibles y sobreviven al recargar). */
function leerUrl() {
  const q = new URLSearchParams(window.location.search);
  const num = (k: string) => (q.get(k) && !Number.isNaN(Number(q.get(k))) ? Number(q.get(k)) : null);
  const orden = q.get("orden") as SeguimientoColumna | null;
  return {
    tieneCorte: q.has("anio") || q.has("mes"),
    filtros: {
      anio: q.get("anio") === "todos" ? null : num("anio"),
      anioTodos: q.get("anio") === "todos",
      mes: num("mes"),
      proceso: q.get("proceso") ?? "Todos",
      estado: q.get("estado") ?? "Todos",
      busqueda: q.get("q") ?? "",
    } satisfies FiltrosState,
    page: Math.max(0, (num("pagina") ?? 1) - 1),
    pageSize: PAGE_SIZES.includes(num("tam") ?? 0) ? (num("tam") as number) : 25,
    orden: { por: orden && COLUMNAS.includes(orden) ? orden : null, dir: q.get("dir") === "desc" ? "desc" : "asc" } as Orden,
    vista: q.get("vista") === "correo" ? ("correo" as Vista) : ("seguimiento" as Vista),
  };
}

export default function SeguimientoOperativoPage() {
  const { isAuthenticated } = useAuthReady();
  const [vista, setVista] = useState<Vista>("seguimiento");
  const [vistaProcesos, setVistaProcesos] = useState<VistaProcesos>("mapa");
  const [f, setF] = useState<FiltrosState>(FILTROS_VACIOS);
  const [busquedaAplicada, setBusquedaAplicada] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [orden, setOrden] = useState<Orden>({ por: null, dir: "asc" });
  const [exportando, setExportando] = useState(false);
  const [urlLista, setUrlLista] = useState(false);
  const urlTieneCorte = useRef(false);

  // Estado inicial desde la URL (una sola vez, en el cliente).
  useEffect(() => {
    const u = leerUrl();
    urlTieneCorte.current = u.tieneCorte;
    setF(u.filtros);
    setBusquedaAplicada(u.filtros.busqueda);
    setPage(u.page);
    setPageSize(u.pageSize);
    setOrden(u.orden);
    setVista(u.vista);
    setUrlLista(true);
  }, []);

  // Búsqueda con retardo para no consultar en cada tecla.
  useEffect(() => {
    const t = setTimeout(() => setBusquedaAplicada(f.busqueda.trim()), 300);
    return () => clearTimeout(t);
  }, [f.busqueda]);

  const filtrosQ = useQuery({ queryKey: ["seguimiento-filtros"], queryFn: fetchSeguimientoFiltros, enabled: isAuthenticated });
  const filtros = filtrosQ.data;

  // Corte por defecto (el más reciente con datos) si la URL no trae uno.
  useEffect(() => {
    if (urlLista && filtros && f.anio == null && !f.anioTodos && !urlTieneCorte.current) {
      setF((p) => ({ ...p, anio: filtros.anio_default ?? new Date().getFullYear(), mes: filtros.mes_default ?? null }));
    }
  }, [urlLista, filtros, f.anio, f.anioTodos]);

  // Escribe el estado en la URL.
  useEffect(() => {
    if (!urlLista) return;
    const q = new URLSearchParams();
    if (f.anioTodos) q.set("anio", "todos");
    else if (f.anio != null) q.set("anio", String(f.anio));
    if (f.mes != null) q.set("mes", String(f.mes));
    if (f.proceso !== "Todos") q.set("proceso", f.proceso);
    if (f.estado !== "Todos") q.set("estado", f.estado);
    if (busquedaAplicada) q.set("q", busquedaAplicada);
    if (page > 0) q.set("pagina", String(page + 1));
    if (pageSize !== 25) q.set("tam", String(pageSize));
    if (orden.por) {
      q.set("orden", orden.por);
      if (orden.dir === "desc") q.set("dir", "desc");
    }
    if (vista === "correo") q.set("vista", "correo");
    const qs = q.toString();
    window.history.replaceState(null, "", qs ? `?${qs}` : window.location.pathname);
  }, [urlLista, f.anio, f.anioTodos, f.mes, f.proceso, f.estado, busquedaAplicada, page, pageSize, orden, vista]);

  const listo = urlLista && (f.anio != null || f.anioTodos);
  const params = useMemo(
    () => ({
      ...(f.anio != null && !f.anioTodos ? { anio: f.anio } : {}),
      ...(f.mes != null ? { mes: f.mes } : {}),
      ...(f.proceso !== "Todos" ? { proceso: f.proceso } : {}),
      ...(f.estado !== "Todos" ? { estado: f.estado } : {}),
      ...(busquedaAplicada ? { busqueda: busquedaAplicada } : {}),
    }),
    [f.anio, f.anioTodos, f.mes, f.proceso, f.estado, busquedaAplicada],
  );

  const query = useQuery({
    queryKey: ["seguimiento", params, page, pageSize, orden],
    queryFn: () =>
      fetchSeguimientoDashboard({
        ...params,
        ...(orden.por ? { orden_por: orden.por, orden_dir: orden.dir } : {}),
        limit: pageSize,
        offset: page * pageSize,
      }),
    enabled: isAuthenticated && listo && vista === "seguimiento",
    placeholderData: keepPreviousData,
  });
  const data = query.data;

  const cambiar = useCallback((cambio: Partial<FiltrosState>) => {
    setPage(0);
    setF((p) => ({ ...p, ...cambio }));
  }, []);

  const irACorte = useCallback(
    (anio: number, mes: number, proceso?: string) => cambiar({ anio, anioTodos: false, mes, ...(proceso ? { proceso } : {}) }),
    [cambiar],
  );

  const exportar = async () => {
    setExportando(true);
    try {
      await downloadSeguimientoExport(params);
    } finally {
      setExportando(false);
    }
  };

  const corteSel = f.anio != null && !f.anioTodos && f.mes != null ? { anio: f.anio, mes: f.mes } : null;
  const corteTexto = f.anioTodos || f.anio == null ? "Todos los años" : f.mes != null ? corteNombre(f.anio, f.mes) : `Año ${f.anio}, todos los meses`;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Seguimiento Operativo</h2>
          <p className="mt-1 max-w-2xl text-sm text-slate-600">
            {vista === "seguimiento" ? (
              <>
                ¿Quién ha reportado sus indicadores y a quién le falta? Corte actual: <strong className="text-slate-900">{corteTexto}</strong>
                {f.proceso !== "Todos" && <> · {f.proceso}</>}.
              </>
            ) : (
              "Borradores de correo para Outlook, con plazos y destinatarios por proceso."
            )}
          </p>
        </div>
        <div className="inline-flex rounded-xl bg-slate-100 p-1" role="tablist">
          {(
            [
              ["seguimiento", "Seguimiento", ClipboardList],
              ["correo", "Alertas por correo", Mail],
            ] as const
          ).map(([key, label, Icono]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={vista === key}
              onClick={() => setVista(key)}
              className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${vista === key ? "bg-white text-poli-navy shadow-sm" : "text-slate-500 hover:text-slate-800"}`}
            >
              <Icono className="h-4 w-4" aria-hidden />
              {label}
            </button>
          ))}
        </div>
      </div>

      <BorradoresListos enabled={isAuthenticated} />

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver el seguimiento.</p>
      ) : vista === "correo" ? (
        <AlertasCorreoPanel />
      ) : !listo || query.isLoading || !filtros ? (
        <div className="space-y-4" aria-busy>
          <div className="h-40 animate-pulse rounded-2xl bg-slate-200/70" />
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="h-32 animate-pulse rounded-2xl bg-slate-200/70" />
            ))}
          </div>
        </div>
      ) : data?.error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{data.error}</div>
      ) : data ? (
        <>
          <FiltrosCorte
            filtros={filtros}
            valor={f}
            onChange={cambiar}
            onLimpiar={() => cambiar({ proceso: "Todos", estado: "Todos", busqueda: "" })}
            onExportar={exportar}
            exportando={exportando}
          />

          <div className={`space-y-6 transition-opacity ${query.isFetching ? "opacity-70" : ""}`}>
            <KpiCards kpis={data.kpis} tendencia={data.tendencia} />

            <div className="grid gap-6 xl:grid-cols-3">
              <div className="xl:col-span-2">
                <TendenciaChart datos={data.tendencia} seleccionado={corteSel} proceso={f.proceso} onSeleccionar={(a, m) => irACorte(a, m)} />
              </div>
              <EstadoDonut kpis={data.kpis} />
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <FrecuenciaChart datos={data.por_periodicidad} />
              <TopPendientesChart procesos={data.cumplimiento_procesos} seleccionado={f.proceso} onSeleccionar={(p) => cambiar({ proceso: f.proceso === p ? "Todos" : p })} />
            </div>

            <div className="space-y-3">
              <div className="inline-flex rounded-xl bg-slate-100 p-1" role="tablist" aria-label="Vista de procesos">
                {(
                  [
                    ["mapa", "Mapa de calor", Grid3x3],
                    ["lista", "Lista por proceso", Layers],
                  ] as const
                ).map(([key, label, Icono]) => (
                  <button
                    key={key}
                    type="button"
                    role="tab"
                    aria-selected={vistaProcesos === key}
                    onClick={() => setVistaProcesos(key)}
                    className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-sm font-semibold transition ${vistaProcesos === key ? "bg-white text-poli-navy shadow-sm" : "text-slate-500 hover:text-slate-800"}`}
                  >
                    <Icono className="h-4 w-4" aria-hidden />
                    {label}
                  </button>
                ))}
              </div>
              {vistaProcesos === "mapa" ? (
                <MatrizCalor matriz={data.matriz_calor} corte={corteSel} proceso={f.proceso} onSeleccionar={(p, a, m) => irACorte(a, m, p)} />
              ) : (
                <CumplimientoProcesos procesos={data.cumplimiento_procesos} seleccionado={f.proceso} onSeleccionar={(p) => cambiar({ proceso: p })} />
              )}
            </div>

            <AlertasFrecuencia referencia={data.alertas.referencia} vencidos={data.alertas.vencidos} porVencer={data.alertas.por_vencer} />

            <DetalleTabla
              filas={data.detalle}
              total={data.detalle_total}
              page={page}
              pageSize={pageSize}
              orden={orden}
              cargando={query.isFetching}
              onPage={setPage}
              onPageSize={(s) => {
                setPageSize(s);
                setPage(0);
              }}
              onOrden={(col) => {
                setPage(0);
                setOrden((o) => (o.por === col ? (o.dir === "asc" ? { por: col, dir: "desc" } : { por: null, dir: "asc" }) : { por: col, dir: "asc" }));
              }}
            />
          </div>
        </>
      ) : null}

      <DataFreshnessFooter />
    </div>
  );
}
