"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KPICard } from "@/components/ui/KPICard";
import { cerrarOM, createOM, fetchOMMatriz, fetchOMPlanAccion, updateOM } from "@/lib/api";
import { useAuthReady, useAuthStore } from "@/stores/auth-store";

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

const TIPOS_ACCION = ["OM Kawak", "Reto Plan Anual", "Proyecto Institucional", "Otro"];

// Placeholder contextual por tipo de acción — paridad con streamlit_app/pages/gestion_om.py
const PLACEHOLDERS_TIPO_ACCION: Record<string, string> = {
  "OM Kawak": "N° OM Kawak",
  "Reto Plan Anual": "Nombre del reto",
  "Proyecto Institucional": "Nombre del proyecto",
  Otro: "Descripción de la acción",
};

export default function GestionOMPage() {
  const { isAuthenticated } = useAuthReady();
  const role = useAuthStore((s) => s.role);
  const canEdit = role === "calidad" || role === "desempeno";
  const queryClient = useQueryClient();

  const [anio, setAnio] = useState(2025);
  const [mes, setMes] = useState("Diciembre");
  const [proceso, setProceso] = useState("Todos");
  const [subproceso, setSubproceso] = useState("Todos");
  const [mostrarAlerta, setMostrarAlerta] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editingOmId, setEditingOmId] = useState<number | null>(null);
  const [tipoAccion, setTipoAccion] = useState("OM Kawak");
  const [numeroOm, setNumeroOm] = useState("");
  const [observacion, setObservacion] = useState("");
  const [verMasOmId, setVerMasOmId] = useState<string | null>(null);

  const planAccionQuery = useQuery({
    queryKey: ["om-plan-accion", verMasOmId],
    queryFn: () => fetchOMPlanAccion(verMasOmId as string),
    enabled: isAuthenticated && !!verMasOmId,
  });

  const query = useQuery({
    queryKey: ["om-matriz", anio, mes, proceso, subproceso, mostrarAlerta],
    queryFn: () =>
      fetchOMMatriz({
        anio,
        mes,
        ...(proceso !== "Todos" ? { proceso } : {}),
        ...(subproceso !== "Todos" ? { subproceso } : {}),
        mostrar_alerta: mostrarAlerta,
      }),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (query.data?.filtros) {
      const defAnio = Number(query.data.filtros.anio_default) || 2025;
      if (!Number.isNaN(defAnio)) setAnio(defAnio);
      setMes(query.data.filtros.mes_default ?? "Diciembre");
    }
  }, [query.data?.filtros]);

  const resetForm = () => {
    setFormOpen(false);
    setSelectedId(null);
    setEditingOmId(null);
    setTipoAccion("OM Kawak");
    setNumeroOm("");
    setObservacion("");
  };

  const createMutation = useMutation({
    mutationFn: createOM,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["om-matriz"] });
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      tipo_accion,
      numero_om,
      comentario,
    }: { id: number; tipo_accion: string; numero_om?: string; comentario?: string }) =>
      updateOM(id, { tipo_accion, numero_om, comentario }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["om-matriz"] });
      resetForm();
    },
  });

  const cerrarMutation = useMutation({
    mutationFn: (id: number) => cerrarOM(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["om-matriz"] });
    },
  });

  const data = query.data;
  const selectedRow = data?.filas.find((f) => f.id === selectedId);

  const handleEditar = (row: NonNullable<typeof data>["filas"][number]) => {
    setSelectedId(row.id);
    setEditingOmId(row.om_id);
    setTipoAccion(row.tipo_accion !== "Sin acción" ? row.tipo_accion : "OM Kawak");
    setNumeroOm(row.numero_om);
    setObservacion(row.comentario ?? "");
    setFormOpen(true);
  };

  const handleSubmit = () => {
    if (!selectedRow) return;
    if (editingOmId != null) {
      updateMutation.mutate({
        id: editingOmId,
        tipo_accion: tipoAccion,
        numero_om: numeroOm || undefined,
        comentario: observacion || undefined,
      });
      return;
    }
    createMutation.mutate({
      id_indicador: selectedRow.id,
      nombre_indicador: selectedRow.indicador,
      proceso: selectedRow.proceso,
      periodo: mes,
      anio,
      tiene_om: 1,
      tipo_accion: tipoAccion,
      numero_om: numeroOm || undefined,
      comentario: observacion || undefined,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Gestión OM</h2>
        <p className="mt-1 text-slate-600">
          Indicadores en Peligro/Alerta con registro de oportunidades de mejora. Fuente: Consolidado Histórico.
        </p>
      </div>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver la matriz OM.</p>
      ) : query.isLoading ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-200" />
      ) : data?.error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{data.error}</div>
      ) : (
        <>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="mb-1 text-xs text-slate-500">Año</p>
                <div className="flex flex-wrap gap-1">
                  {(data?.filtros.anios ?? ["2025"]).map((y) => (
                    <button
                      key={y}
                      type="button"
                      onClick={() => setAnio(Number(y))}
                      className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
                        String(anio) === String(y) ? "bg-poli-navy text-white" : "bg-slate-100"
                      }`}
                    >
                      {y}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <p className="mb-1 text-xs text-slate-500">Mes</p>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={mes}
                  onChange={(e) => setMes(e.target.value)}
                >
                  {MESES.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <p className="mb-1 text-xs text-slate-500">Proceso</p>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={proceso}
                  onChange={(e) => setProceso(e.target.value)}
                >
                  <option value="Todos">Todos</option>
                  {(data?.filtros.procesos ?? []).map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <p className="mb-1 text-xs text-slate-500">Subproceso</p>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={subproceso}
                  onChange={(e) => setSubproceso(e.target.value)}
                >
                  <option value="Todos">Todos</option>
                  {(data?.filtros.subprocesos ?? []).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <label className="mt-3 flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={mostrarAlerta}
                onChange={(e) => setMostrarAlerta(e.target.checked)}
              />
              Mostrar también indicadores en Alerta
            </label>
          </div>

          <h3 className="text-lg font-semibold text-slate-800">
            📊 Indicadores en Riesgo — {mes} {anio}
          </h3>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard label="🔴 Peligro" value={data?.kpis.peligro ?? 0} />
            <KPICard label="🟡 Alerta" value={data?.kpis.alerta ?? 0} />
            <KPICard label="📋 Con OM" value={`${data?.kpis.con_om ?? 0} / ${data?.kpis.total ?? 0}`} />
            <KPICard
              label="📊 Avance OM"
              value={
                data?.kpis.avance_om_promedio != null ? `${data.kpis.avance_om_promedio}%` : "—"
              }
            />
          </div>

          {canEdit && (
            <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="min-w-[200px] flex-1">
                <p className="mb-1 text-xs text-slate-500">Indicador</p>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={selectedId ?? ""}
                  onChange={(e) => {
                    setSelectedId(e.target.value || null);
                    setEditingOmId(null);
                    setTipoAccion("OM Kawak");
                    setNumeroOm("");
                    setFormOpen(!!e.target.value);
                  }}
                >
                  <option value="">Seleccionar indicador…</option>
                  {(data?.filas ?? []).map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.id} — {f.indicador.slice(0, 60)}
                    </option>
                  ))}
                </select>
              </div>
              {formOpen && selectedRow ? (
                <>
                  <div>
                    <p className="mb-1 text-xs text-slate-500">Tipo de acción</p>
                    <select
                      className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      value={tipoAccion}
                      onChange={(e) => setTipoAccion(e.target.value)}
                    >
                      {TIPOS_ACCION.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <p className="mb-1 text-xs text-slate-500">Nº OM / Identificador</p>
                    <input
                      className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      value={numeroOm}
                      onChange={(e) => setNumeroOm(e.target.value)}
                      placeholder={PLACEHOLDERS_TIPO_ACCION[tipoAccion] ?? "Identificador OM"}
                    />
                  </div>
                  <div className="min-w-[240px] flex-1">
                    <p className="mb-1 text-xs text-slate-500">Observación</p>
                    <textarea
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      rows={2}
                      value={observacion}
                      onChange={(e) => setObservacion(e.target.value)}
                      placeholder="Describe la situación o justificación…"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={createMutation.isPending || updateMutation.isPending}
                    className="rounded-lg bg-poli-navy px-4 py-2 text-sm font-semibold text-white hover:bg-poli-navy/90 disabled:opacity-50"
                  >
                    {createMutation.isPending || updateMutation.isPending
                      ? "Guardando…"
                      : editingOmId != null
                        ? "Guardar cambios"
                        : "Asociar nueva OM"}
                  </button>
                  <button
                    type="button"
                    onClick={resetForm}
                    className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-white"
                  >
                    Cancelar
                  </button>
                </>
              ) : null}
            </div>
          )}

          {!data?.filas.length ? (
            <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
              No hay indicadores en Peligro con los filtros seleccionados.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
              <table className="min-w-full text-left text-base">
                <thead className="bg-slate-800 text-sm uppercase text-white">
                  <tr>
                    {[
                      "Id",
                      "Indicador",
                      "Subproceso",
                      "Periodicidad",
                      "Meta",
                      "Ejecución",
                      "Cumplimiento",
                      "Categoría",
                      "Tipo de Acción",
                      "OM",
                      "Avance OM",
                      "Plan de Acción",
                      ...(canEdit ? ["Acciones"] : []),
                    ].map((h) => (
                      <th key={h} className="whitespace-nowrap px-3 py-2">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.filas.map((row) => (
                    <tr key={row.id} style={{ backgroundColor: row.row_bg }}>
                      <td className="px-3 py-2 font-mono text-sm">{row.id}</td>
                      <td className="max-w-[200px] truncate px-3 py-2" title={row.indicador}>
                        {row.indicador}
                      </td>
                      <td className="px-3 py-2">{row.subproceso}</td>
                      <td className="px-3 py-2">{row.periodicidad}</td>
                      <td className="px-3 py-2 text-right">{row.meta != null ? String(row.meta) : "—"}</td>
                      <td className="px-3 py-2 text-right">{row.ejecucion != null ? String(row.ejecucion) : "—"}</td>
                      <td className="px-3 py-2 text-right">
                        {row.cumplimiento_pct != null ? `${row.cumplimiento_pct}%` : "—"}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className="rounded px-1.5 py-0.5 text-xs font-medium text-white"
                          style={{ backgroundColor: row.categoria_color }}
                        >
                          {row.categoria}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className="rounded-full px-2 py-0.5 text-xs font-medium text-white"
                          style={{ backgroundColor: row.tipo_accion_color }}
                        >
                          {row.tipo_accion}
                        </span>
                      </td>
                      <td className="px-3 py-2">{row.numero_om || "—"}</td>
                      <td className="px-3 py-2">
                        {row.avance_om != null ? (
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-16 overflow-hidden rounded-full bg-slate-200">
                              <div
                                className="h-full rounded-full bg-emerald-500"
                                style={{ width: `${Math.min(100, row.avance_om)}%` }}
                              />
                            </div>
                            <span className="text-xs">{row.avance_om}%</span>
                          </div>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="whitespace-nowrap px-3 py-2">
                        {row.tiene_om === 1 && row.numero_om ? (
                          <button
                            type="button"
                            onClick={() => setVerMasOmId(row.numero_om)}
                            className="rounded border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                          >
                            Ver más
                          </button>
                        ) : (
                          "—"
                        )}
                      </td>
                      {canEdit && (
                        <td className="whitespace-nowrap px-3 py-2">
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => handleEditar(row)}
                              className="rounded border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                            >
                              {row.tiene_om ? "Editar" : "Registrar"}
                            </button>
                            {row.tiene_om === 1 && row.om_id != null && (
                              <button
                                type="button"
                                onClick={() => {
                                  if (window.confirm(`¿Cerrar la OM del indicador ${row.id}?`)) {
                                    cerrarMutation.mutate(row.om_id as number);
                                  }
                                }}
                                disabled={cerrarMutation.isPending}
                                className="rounded border border-amber-300 px-2 py-1 text-xs font-medium text-amber-700 hover:bg-amber-50 disabled:opacity-50"
                              >
                                Cerrar
                              </button>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {verMasOmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[80vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white p-5 shadow-xl">
            <div className="mb-3 flex items-center justify-between">
              <h4 className="text-lg font-semibold text-slate-900">
                Plan de Acción — OM {verMasOmId}
              </h4>
              <button
                type="button"
                onClick={() => setVerMasOmId(null)}
                className="rounded border border-slate-300 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
              >
                Cerrar
              </button>
            </div>
            {planAccionQuery.isLoading ? (
              <div className="h-24 animate-pulse rounded-lg bg-slate-200" />
            ) : !planAccionQuery.data?.length ? (
              <p className="text-sm text-slate-500">OM {verMasOmId} sin actividades asociadas.</p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-slate-100 text-xs uppercase text-slate-600">
                    <tr>
                      <th className="px-3 py-2">Acción</th>
                      <th className="px-3 py-2">Responsable</th>
                      <th className="px-3 py-2">Avance</th>
                      <th className="px-3 py-2">Estado (Plan)</th>
                      <th className="px-3 py-2">Estado (OM)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {planAccionQuery.data.map((act, idx) => (
                      <tr key={act.id_accion || idx} className="border-t border-slate-200">
                        <td className="px-3 py-2">{act.accion || "—"}</td>
                        <td className="px-3 py-2">{act.responsable || "—"}</td>
                        <td className="px-3 py-2">{act.avance || "—"}</td>
                        <td className="px-3 py-2">{act.estado_plan || "—"}</td>
                        <td className="px-3 py-2">{act.estado_om || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
