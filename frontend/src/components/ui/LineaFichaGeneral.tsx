"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { FileText, X } from "lucide-react";
import { STRATEGIC_ICON_MAP } from "@/lib/strategic-icons";
import { fetchResumenLinea } from "@/lib/api";
import { PDI_VISTAS_POR_LINEA } from "@/lib/pdi";
import type { ResumenLineaProyectoItem } from "@/lib/types";

interface LineaFichaGeneralProps {
  slug: string;
  color: string;
  icon: string;
  onClose: () => void;
}

// Mismo umbral de "en riesgo" que ya usa el mindmap (PdiMindmap.tsx) — una
// línea consolidada por debajo de 100% no alcanzó su meta del ciclo.
const CUMPLE_UMBRAL = 100;

export function LineaFichaGeneral({ slug, color, icon, onClose }: LineaFichaGeneralProps) {
  const query = useQuery({
    queryKey: ["resumen-linea", slug, "rango"],
    queryFn: () => fetchResumenLinea(slug, undefined, PDI_VISTAS_POR_LINEA),
  });

  const IconComponent = STRATEGIC_ICON_MAP[icon];
  const data = query.data;
  const totalIndicadores = data?.objetivos.reduce((acc, o) => acc + o.indicadores.length, 0) ?? 0;
  const proyectosClave = data ? [...data.proyectos].sort((a, b) => a.cumplimiento - b.cumplimiento).slice(0, 3) : [];
  const cumplimiento = data?.cumplimiento_consolidado ?? 0;
  const cumpliendo = cumplimiento >= CUMPLE_UMBRAL;
  const descripcion = data?.narrativa?.parrafo_logros?.consolidado;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <span
          className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wide"
          style={{ backgroundColor: `${color}1A`, color }}
        >
          Línea seleccionada
        </span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar ficha de línea"
          className="rounded p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
        >
          <X size={16} />
        </button>
      </div>

      {query.isLoading || !data ? (
        <div className="h-72 animate-pulse rounded-lg bg-slate-100" />
      ) : (
        <>
          <div className="mb-1 flex items-start justify-between gap-3">
            <div className="flex items-center gap-2" style={{ color }}>
              {IconComponent && <IconComponent size={22} strokeWidth={2} />}
              <h3 className="text-base font-bold leading-tight text-slate-800">{data.linea}</h3>
            </div>
            <span className="shrink-0 text-2xl font-black leading-none" style={{ color }}>
              {cumplimiento.toFixed(1)}%
            </span>
          </div>
          <p className={`mb-3 text-xs font-semibold ${cumpliendo ? "text-emerald-600" : "text-amber-600"}`}>
            {cumpliendo ? "↗ Cumpliendo" : "⚠ En riesgo"}
          </p>

          {descripcion && <p className="mb-4 text-sm leading-relaxed text-slate-600">{descripcion}</p>}

          <div className="mb-4 grid grid-cols-2 gap-2 rounded-lg bg-slate-50 p-3">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                Iniciativas en línea
              </p>
              <p className="text-sm font-bold text-slate-800">{data.proyectos.length} Proyectos</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Indicadores CMI</p>
              <p className="text-sm font-bold text-slate-800">{totalIndicadores} Indicadores</p>
            </div>
          </div>

          {proyectosClave.length > 0 && (
            <>
              <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-500">
                Proyectos tributarios clave · {proyectosClave.length} de {data.proyectos.length}
              </p>
              <div className="mb-4 space-y-2">
                {proyectosClave.map((proyecto) => (
                  <ProyectoClaveCard key={proyecto.id} proyecto={proyecto} color={color} />
                ))}
              </div>
            </>
          )}

          <Link
            href={`/resumen-general/consolidado-por-linea/linea/${slug}`}
            className="flex items-center justify-center gap-2 rounded-lg bg-poli-navy px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
          >
            <FileText size={16} />
            Ver Ficha Técnica Completa de la Línea
          </Link>
        </>
      )}
    </div>
  );
}

function ProyectoClaveCard({ proyecto, color }: { proyecto: ResumenLineaProyectoItem; color: string }) {
  const pct = Math.max(0, Math.min(100, proyecto.cumplimiento));
  const estadoColor = proyecto.estado_color ?? "#64748B";
  return (
    <div className="rounded-lg border border-slate-200 p-2.5">
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-bold leading-tight text-slate-700">
          {proyecto.id} · {proyecto.nombre}
        </p>
        <span
          className="shrink-0 rounded-md px-2 py-1 text-center leading-tight"
          style={{ backgroundColor: `${estadoColor}22`, color: estadoColor }}
        >
          <span className="block text-xs font-black">{proyecto.cumplimiento.toFixed(0)}%</span>
          <span className="block text-[9px] font-semibold">{proyecto.estado}</span>
        </span>
      </div>
      <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <p className="mt-1 text-[10px] text-slate-400">
        Vigencia {proyecto.anio_inicio}–{proyecto.anio_fin}
      </p>
    </div>
  );
}
