"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, PieChart as PieIcon } from "lucide-react";
import { ConfirmDialog } from "@/components/gestion-om/ConfirmDialog";
import { FiltrosOM, type FiltrosOMState } from "@/components/gestion-om/FiltrosOM";
import { ProcesoChart, TipoAccionDona } from "@/components/gestion-om/GraficosOM";
import { KpisOM } from "@/components/gestion-om/KpisOM";
import { PanelRegistro, type DatosRegistro } from "@/components/gestion-om/PanelRegistro";
import { PlanAccionModal } from "@/components/gestion-om/PlanAccionModal";
import { TablaOM } from "@/components/gestion-om/TablaOM";
import { contarPorEstado, type Pestana } from "@/components/gestion-om/utils";
import { Panel } from "@/components/seguimiento/Panel";
import { errorMessage } from "@/components/seguimiento/constants";
import { cerrarOM, createOM, deleteOM, fetchOMMatriz, fetchOMPlanAccion, updateOM } from "@/lib/api";
import type { OMFila } from "@/lib/types";
import { useAuthReady, useAuthStore } from "@/stores/auth-store";

const PESTANAS: Pestana[] = ["pendientes", "en_gestion", "cerradas", "todos"];
const FILTROS_INICIALES: FiltrosOMState = { anio: null, mes: null, proceso: "Todos", subproceso: "Todos", mostrarAlerta: false, busqueda: "" };

/** Lee los filtros de la URL (compartibles y sobreviven al recargar). */
function leerUrl(): { filtros: FiltrosOMState; pestana: Pestana } {
  const q = new URLSearchParams(window.location.search);
  const anio = Number(q.get("anio"));
  const tab = q.get("vista") as Pestana | null;
  return {
    filtros: {
      anio: Number.isInteger(anio) && anio > 2000 ? anio : null,
      mes: q.get("mes"),
      proceso: q.get("proceso") ?? "Todos",
      subproceso: q.get("subproceso") ?? "Todos",
      mostrarAlerta: q.get("alerta") === "1",
      busqueda: q.get("q") ?? "",
    },
    pestana: tab && PESTANAS.includes(tab) ? tab : "pendientes",
  };
}

type Confirmacion = { tipo: "cerrar" | "eliminar"; fila: OMFila } | null;

export default function GestionOMPage() {
  const { isAuthenticated } = useAuthReady();
  const role = useAuthStore((s) => s.role);
  const canEdit = role === "administrador" || role === "calidad" || role === "desempeno";
  // Eliminar es irreversible: solo administrador (el backend lo refuerza con 403).
  const canDelete = role === "administrador";
  const queryClient = useQueryClient();

  const [f, setF] = useState<FiltrosOMState>(FILTROS_INICIALES);
  const [busquedaAplicada, setBusquedaAplicada] = useState("");
  const [pestana, setPestana] = useState<Pestana>("pendientes");
  const [urlLista, setUrlLista] = useState(false);
  const [registro, setRegistro] = useState<OMFila | null>(null);
  const [confirmacion, setConfirmacion] = useState<Confirmacion>(null);
  const [verPlanOm, setVerPlanOm] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  // Estado inicial desde la URL (una sola vez, en el cliente).
  useEffect(() => {
    const u = leerUrl();
    setF(u.filtros);
    setBusquedaAplicada(u.filtros.busqueda);
    setPestana(u.pestana);
    setUrlLista(true);
  }, []);

  // Búsqueda con retardo para no refiltrar en cada tecla.
  useEffect(() => {
    const t = setTimeout(() => setBusquedaAplicada(f.busqueda.trim()), 250);
    return () => clearTimeout(t);
  }, [f.busqueda]);

  // Escribe el estado en la URL.
  useEffect(() => {
    if (!urlLista) return;
    const q = new URLSearchParams();
    if (f.anio != null) q.set("anio", String(f.anio));
    if (f.mes != null) q.set("mes", f.mes);
    if (f.proceso !== "Todos") q.set("proceso", f.proceso);
    if (f.subproceso !== "Todos") q.set("subproceso", f.subproceso);
    if (f.mostrarAlerta) q.set("alerta", "1");
    if (busquedaAplicada) q.set("q", busquedaAplicada);
    if (pestana !== "pendientes") q.set("vista", pestana);
    window.history.replaceState(null, "", `${window.location.pathname}?${q.toString()}`);
  }, [urlLista, f, busquedaAplicada, pestana]);

  const query = useQuery({
    queryKey: ["om-matriz", f.anio, f.mes, f.proceso, f.subproceso, f.mostrarAlerta],
    queryFn: () =>
      fetchOMMatriz({
        ...(f.anio != null ? { anio: f.anio } : {}),
        ...(f.mes != null ? { mes: f.mes } : {}),
        ...(f.proceso !== "Todos" ? { proceso: f.proceso } : {}),
        ...(f.subproceso !== "Todos" ? { subproceso: f.subproceso } : {}),
        mostrar_alerta: f.mostrarAlerta,
      }),
    enabled: isAuthenticated && urlLista,
    placeholderData: keepPreviousData,
  });
  const data = query.data;

  // Sin corte en la URL, se adopta el que resolvió el servidor (el más reciente con datos, hoy 2026).
  useEffect(() => {
    if (data && !data.error && (f.anio == null || f.mes == null)) {
      setF((p) => ({ ...p, anio: p.anio ?? data.anio, mes: p.mes ?? data.mes }));
    }
  }, [data, f.anio, f.mes]);

  // Si el año de la URL ya no existe en el servidor, se usa el que este propone. Solo si es inválido:
  // un cambio manual de año o mes nunca se revierte.
  useEffect(() => {
    const anios = data?.filtros?.anios;
    if (f.anio != null && anios?.length && !anios.includes(String(f.anio))) {
      setF((p) => ({ ...p, anio: Number(data?.filtros.anio_default) || Number(anios[anios.length - 1]) }));
    }
  }, [data?.filtros, f.anio]);

  const planQuery = useQuery({
    queryKey: ["om-plan-accion", verPlanOm],
    queryFn: () => fetchOMPlanAccion(verPlanOm as string),
    enabled: isAuthenticated && !!verPlanOm,
  });

  const filas = useMemo(() => data?.filas ?? [], [data?.filas]);
  const conteo = useMemo(() => contarPorEstado(filas), [filas]);
  const anioCorte = f.anio ?? data?.anio ?? 0;
  const mesCorte = f.mes ?? data?.mes ?? "";
  const periodo = `${mesCorte} ${anioCorte}`;

  const cambiar = useCallback((c: Partial<FiltrosOMState>) => setF((p) => ({ ...p, ...c })), []);
  const limpiar = useCallback(() => setF((p) => ({ ...p, proceso: "Todos", subproceso: "Todos", busqueda: "" })), []);

  const refrescar = () => queryClient.invalidateQueries({ queryKey: ["om-matriz"] });
  const exito = (texto: string) => {
    setAviso(texto);
    setTimeout(() => setAviso(null), 4000);
  };

  const guardarMutation = useMutation({
    mutationFn: ({ fila, datos }: { fila: OMFila; datos: DatosRegistro }) => {
      const comun = {
        tipo_accion: datos.tipo_accion,
        numero_om: datos.numero_om || undefined,
        comentario: datos.comentario || undefined,
      };
      if (fila.om_id != null) return updateOM(fila.om_id, { ...comun, tiene_om: 1 });
      return createOM({
        id_indicador: fila.id,
        nombre_indicador: fila.indicador,
        proceso: fila.proceso,
        periodo: mesCorte,
        anio: anioCorte,
        tiene_om: 1,
        ...comun,
      });
    },
    onSuccess: (_r, { fila }) => {
      refrescar();
      setRegistro(null);
      exito(`OM del indicador ${fila.id} guardada.`);
    },
  });

  const confirmarMutation = useMutation({
    mutationFn: async ({ tipo, fila }: NonNullable<Confirmacion>): Promise<void> => {
      if (tipo === "cerrar") await cerrarOM(fila.om_id as number);
      else await deleteOM(fila.om_id as number);
    },
    onSuccess: (_r, { tipo, fila }) => {
      refrescar();
      setConfirmacion(null);
      exito(tipo === "cerrar" ? `OM del indicador ${fila.id} cerrada.` : `Registro OM del indicador ${fila.id} eliminado.`);
    },
  });

  const historial = registro ? (data?.historial?.[registro.id] ?? []) : [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Gestión OM</h2>
        <p className="mt-1 text-slate-600">
          Indicadores en Peligro{f.mostrarAlerta ? " y Alerta" : ""} y su oportunidad de mejora registrada. Fuente: Consolidado Histórico.
        </p>
      </div>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver la matriz OM.</p>
      ) : query.isError ? (
        <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          No se pudo cargar la matriz OM: {errorMessage(query.error)}
        </div>
      ) : !data ? (
        <div className="space-y-4" aria-busy="true">
          <div className="h-40 animate-pulse rounded-2xl bg-slate-200" />
          <div className="h-64 animate-pulse rounded-2xl bg-slate-200" />
        </div>
      ) : data.error ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{data.error}</div>
      ) : (
        <>
          <FiltrosOM anios={data.filtros.anios ?? []} mesesPorAnio={data.filtros.meses_por_anio} procesos={data.filtros.procesos ?? []} subprocesos={data.filtros.subprocesos ?? []} valor={f} onChange={cambiar} onLimpiar={limpiar} />

          <div className="flex items-center justify-between gap-3">
            <h3 className="text-lg font-semibold text-slate-800">Indicadores en riesgo — {periodo}</h3>
            {query.isFetching && <span className="text-xs text-slate-400">Actualizando…</span>}
          </div>

          <div role="status" aria-live="polite" className={aviso ? "rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800" : "sr-only"}>
            {aviso}
          </div>

          <KpisOM kpis={data.kpis} conteo={conteo} />

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
            <Panel titulo="Indicadores en riesgo por proceso" subtitulo="Rojo: sin OM · Azul: con OM. Clic en una barra para filtrar la tabla." icono={BarChart3}>
              <ProcesoChart datos={data.por_proceso ?? []} seleccionado={f.proceso} onSeleccionar={(p) => cambiar({ proceso: p })} />
            </Panel>
            <Panel titulo="OM por tipo de acción" subtitulo="Solo indicadores con registro en este corte." icono={PieIcon}>
              <TipoAccionDona filas={filas} colores={data.tipo_accion_colores ?? {}} textoVacio={canEdit ? "Aún no hay OM registradas. Usa «Registrar OM» en la tabla." : "Aún no hay OM registradas en este corte."} />
            </Panel>
          </div>

          <TablaOM
            filas={filas}
            busqueda={busquedaAplicada}
            pestana={pestana}
            onPestana={setPestana}
            canEdit={canEdit}
            canDelete={canDelete}
            onRegistrar={(fila) => {
              guardarMutation.reset();
              setRegistro(fila);
            }}
            onVerPlan={setVerPlanOm}
            onCerrar={(fila) => {
              confirmarMutation.reset();
              setConfirmacion({ tipo: "cerrar", fila });
            }}
            onEliminar={(fila) => {
              confirmarMutation.reset();
              setConfirmacion({ tipo: "eliminar", fila });
            }}
          />
        </>
      )}

      {registro && (
        <PanelRegistro
          key={registro.id}
          fila={registro}
          periodo={periodo}
          historial={historial}
          pendiente={guardarMutation.isPending}
          error={guardarMutation.isError ? errorMessage(guardarMutation.error) : null}
          onGuardar={(datos) => guardarMutation.mutate({ fila: registro, datos })}
          onCerrar={() => setRegistro(null)}
        />
      )}

      {confirmacion && (
        <ConfirmDialog
          titulo={confirmacion.tipo === "cerrar" ? `¿Cerrar la OM del indicador ${confirmacion.fila.id}?` : `¿Eliminar el registro OM del indicador ${confirmacion.fila.id}?`}
          mensaje={
            confirmacion.tipo === "cerrar"
              ? "La OM dejará de contar como activa. Podrás reabrirla editando el registro."
              : `${confirmacion.fila.numero_om ? `Se eliminará la OM ${confirmacion.fila.numero_om}. ` : ""}Esta acción no se puede deshacer.`
          }
          confirmar={confirmacion.tipo === "cerrar" ? "Cerrar OM" : "Eliminar"}
          tono={confirmacion.tipo === "eliminar" ? "peligro" : "normal"}
          cargando={confirmarMutation.isPending}
          error={confirmarMutation.isError ? errorMessage(confirmarMutation.error) : null}
          onConfirmar={() => confirmarMutation.mutate(confirmacion)}
          onCancelar={() => setConfirmacion(null)}
        />
      )}

      {verPlanOm && <PlanAccionModal numeroOm={verPlanOm} cargando={planQuery.isLoading} actividades={planQuery.data} onCerrar={() => setVerPlanOm(null)} />}
    </div>
  );
}
