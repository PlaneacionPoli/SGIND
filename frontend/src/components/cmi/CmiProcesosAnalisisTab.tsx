"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Brain,
  AlertTriangle,
  ListChecks,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { CMIProcesosDashboardResponse, NarrativaIaProceso } from "@/lib/types";
import { fetchNarrativaIaBorrador, publicarNarrativaIaProceso } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

interface CmiProcesosAnalisisTabProps {
  data: CMIProcesosDashboardResponse;
  narrativaIaProceso?: NarrativaIaProceso | null;
  narrativaIaPendiente?: boolean;
}

const ESTADO_LABEL: Record<string, string> = {
  "#16A34A": "Favorable",
  "#2563EB": "Estable",
  "#DC2626": "Crítico",
};

type NarrativaDisplay = {
  titulo: string;
  estado_color: string;
  foco_urgente: string;
  directrices: string[];
  texto_html: string;
  fuenteLabel: string;
  esIA: boolean;
};

export function CmiProcesosAnalisisTab({
  data,
  narrativaIaProceso,
  narrativaIaPendiente,
}: CmiProcesosAnalisisTabProps) {
  const { analisis_avanzado, anio, mes, mes_nombre, filtros_aplicados } = data;
  const av = analisis_avanzado ?? {};
  const narrativaHeuristica = av.narrativa_proceso;
  const proceso = filtros_aplicados?.proceso || "Todos";

  const narrativa: NarrativaDisplay | null = narrativaIaProceso
    ? {
        titulo: narrativaIaProceso.titulo,
        estado_color: narrativaIaProceso.estado_color,
        foco_urgente: narrativaIaProceso.foco_urgente,
        directrices: narrativaIaProceso.directrices,
        texto_html: narrativaIaProceso.texto_html,
        fuenteLabel: narrativaIaProceso.revisado_por
          ? `Generado por IA (${narrativaIaProceso.modelo}) · Publicado por ${narrativaIaProceso.revisado_por}`
          : `Generado por IA (${narrativaIaProceso.modelo})`,
        esIA: true,
      }
    : narrativaHeuristica
      ? {
          titulo: narrativaHeuristica.titulo,
          estado_color: narrativaHeuristica.estado_color,
          foco_urgente: narrativaHeuristica.foco_urgente,
          directrices: narrativaHeuristica.directrices,
          texto_html: narrativaHeuristica.texto_html,
          fuenteLabel: "Motor de reglas heurístico SIGP — narrativa IA pendiente de auditoría/publicación",
          esIA: false,
        }
      : null;

  const estadoLabel = narrativa ? (ESTADO_LABEL[narrativa.estado_color] ?? "Diagnóstico") : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2.5 rounded-xl border border-blue-100 bg-blue-50/40 px-4 py-3">
        <Brain className="h-5 w-5 shrink-0 text-poli-navy" />
        <p className="text-sm text-slate-700">
          Diagnóstico generado a partir del catálogo filtrado — {anio}, último reporte de cada indicador (más
          reciente:{" "}
          <span className="font-semibold text-poli-navy">{mes_nombre}</span>)
          .
        </p>
      </div>

      {narrativa && (
        <section
          className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
          style={{ borderLeftWidth: 6, borderLeftColor: narrativa.estado_color }}
        >
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-5 py-4">
            <div className="flex items-center gap-2.5">
              {narrativa.esIA ? (
                <Sparkles className="h-5 w-5" style={{ color: narrativa.estado_color }} />
              ) : (
                <Brain className="h-5 w-5" style={{ color: narrativa.estado_color }} />
              )}
              <h3 className="text-base font-bold text-slate-900">{narrativa.titulo}</h3>
            </div>
            {estadoLabel && (
              <span
                className="rounded-full px-3 py-1 text-xs font-bold text-white"
                style={{ backgroundColor: narrativa.estado_color }}
              >
                {estadoLabel}
              </span>
            )}
          </div>

          <div className="space-y-4 p-5">
            {narrativa.foco_urgente && (
              <div className="flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50 p-3.5">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-amber-800">Foco urgente</p>
                  <p className="text-sm text-amber-900">{narrativa.foco_urgente}</p>
                </div>
              </div>
            )}

            <p
              className="text-sm leading-relaxed text-slate-700"
              dangerouslySetInnerHTML={{ __html: narrativa.texto_html }}
            />

            {narrativa.directrices.length > 0 && (
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <ListChecks className="h-3.5 w-3.5" />
                  Directrices recomendadas
                </p>
                <ul className="space-y-1.5">
                  {narrativa.directrices.map((d, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                      <span
                        className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white"
                        style={{ backgroundColor: narrativa.estado_color }}
                      >
                        {i + 1}
                      </span>
                      {d}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <p className="pt-1 text-[11px] text-slate-400">Fuente: {narrativa.fuenteLabel}</p>
          </div>
        </section>
      )}

      <NarrativaIaAuditPanel
        proceso={proceso}
        anio={anio}
        mes={mes}
        pendiente={!!narrativaIaPendiente}
      />

    </div>
  );
}

const AUDITOR_ROLES = new Set(["auditor_ia", "administrador"]);

function NarrativaIaAuditPanel({
  proceso,
  anio,
  mes,
  pendiente,
}: {
  proceso: string;
  anio: number;
  mes: number;
  pendiente: boolean;
}) {
  const role = useAuthStore((s) => s.role);
  const queryClient = useQueryClient();
  const [revisando, setRevisando] = useState(false);

  const puedeAuditar = !!role && AUDITOR_ROLES.has(role);

  const borradorQuery = useQuery({
    queryKey: ["narrativa-ia-borrador", proceso, anio, mes],
    queryFn: () => fetchNarrativaIaBorrador({ proceso, anio, mes }),
    enabled: puedeAuditar && revisando,
  });

  const publicarMutation = useMutation({
    mutationFn: () => publicarNarrativaIaProceso({ proceso, anio, mes }),
    onSuccess: () => {
      setRevisando(false);
      queryClient.invalidateQueries({ queryKey: ["informe-dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["narrativa-ia-borrador", proceso, anio, mes] });
    },
  });

  if (!puedeAuditar || !pendiente) return null;

  const borrador = borradorQuery.data?.borrador;

  return (
    <section className="rounded-xl border-2 border-dashed border-poli-navy/30 bg-blue-50/30 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="h-5 w-5 text-poli-navy" />
          <div>
            <p className="text-sm font-bold text-poli-navy">Auditoría de narrativa IA</p>
            <p className="text-xs text-slate-600">
              Hay un borrador generado por IA pendiente de revisión para este proceso y corte.
            </p>
          </div>
        </div>
        {!revisando && (
          <button
            type="button"
            onClick={() => setRevisando(true)}
            className="rounded-lg border border-poli-navy px-3 py-1.5 text-xs font-semibold text-poli-navy hover:bg-white"
          >
            Revisar borrador
          </button>
        )}
      </div>

      {revisando && (
        <div className="mt-4 space-y-3 border-t border-poli-navy/20 pt-4">
          {borradorQuery.isLoading && <p className="text-sm text-slate-500">Cargando borrador…</p>}
          {borradorQuery.isError && (
            <p className="text-sm text-red-600">No se pudo cargar el borrador.</p>
          )}
          {borrador && (
            <>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="mb-1 text-sm font-bold text-slate-900">{borrador.titulo}</p>
                <p
                  className="text-sm leading-relaxed text-slate-700"
                  dangerouslySetInnerHTML={{ __html: borrador.texto_html }}
                />
                {borrador.foco_urgente && (
                  <p className="mt-2 text-xs font-semibold text-amber-700">
                    Foco urgente: {borrador.foco_urgente}
                  </p>
                )}
                {borrador.directrices.length > 0 && (
                  <ul className="mt-2 list-inside list-disc text-xs text-slate-600">
                    {borrador.directrices.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                )}
                <p className="mt-2 text-[11px] text-slate-400">Modelo: {borrador.modelo}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => publicarMutation.mutate()}
                  disabled={publicarMutation.isPending}
                  className="rounded-lg bg-poli-navy px-4 py-2 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
                >
                  {publicarMutation.isPending ? "Publicando…" : "Publicar narrativa"}
                </button>
                {publicarMutation.isError && (
                  <span className="text-xs text-red-600">No se pudo publicar.</span>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}
