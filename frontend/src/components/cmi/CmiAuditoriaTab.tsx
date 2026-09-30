"use client";

import { useMemo, useState } from "react";
import type { LucideIcon } from "lucide-react";
import { LayoutGrid, CheckCircle2, Lightbulb, ShieldAlert, ClipboardCheck, CalendarClock, Target } from "lucide-react";
import type { InformeDashboardResponse } from "@/lib/types";

type AuditoriaSeccion = InformeDashboardResponse["auditoria"][number];
type AuditoriaCategoria = AuditoriaSeccion["fichas"][number]["categorias"][number];
type AuditoriaItem = AuditoriaCategoria["items"][number];

interface CmiAuditoriaTabProps {
  secciones: AuditoriaSeccion[];
  error: string | null;
}

const RIESGO_CAMPOS = new Set(["no_conformidad", "nuevo_riesgo"]);

type SubtabId = "all" | "fortaleza" | "oportunidad_de_mejora" | "riesgo" | "planes";

const SUBTAB_META: Record<SubtabId, { label: string; icon: LucideIcon; iconColor: string }> = {
  all: { label: "Vista General", icon: LayoutGrid, iconColor: "text-white" },
  fortaleza: { label: "Fortalezas", icon: CheckCircle2, iconColor: "text-emerald-600" },
  oportunidad_de_mejora: { label: "Oportunidades de Mejora", icon: Lightbulb, iconColor: "text-amber-600" },
  riesgo: { label: "Riesgos & Alertas", icon: ShieldAlert, iconColor: "text-red-600" },
  planes: { label: "Planes de Acción", icon: ClipboardCheck, iconColor: "text-poli-navy" },
};

interface FlatCategoria {
  proceso: string;
  categoria: AuditoriaCategoria;
}

export function CmiAuditoriaTab({ secciones, error }: CmiAuditoriaTabProps) {
  const [subtab, setSubtab] = useState<SubtabId>("all");

  const flat: FlatCategoria[] = useMemo(
    () =>
      secciones.flatMap((sec) =>
        sec.fichas.flatMap((ficha) => ficha.categorias.map((categoria) => ({ proceso: ficha.proceso, categoria })))
      ),
    [secciones]
  );

  const counts = useMemo(() => {
    let fortaleza = 0;
    let oportunidad = 0;
    let riesgo = 0;
    let planes = 0;
    for (const { categoria } of flat) {
      const n = categoria.items.length;
      if (categoria.campo === "fortaleza") fortaleza += n;
      else if (categoria.campo === "oportunidad_de_mejora") oportunidad += n;
      else if (RIESGO_CAMPOS.has(categoria.campo)) riesgo += n;
      planes += categoria.items.filter((it) => it.recomendaciones).length;
    }
    return { fortaleza, oportunidad, riesgo, planes, total: fortaleza + oportunidad + riesgo };
  }, [flat]);

  const dictamenFavorable = counts.riesgo === 0;

  const visible = useMemo(() => {
    if (subtab === "all") return flat;
    if (subtab === "riesgo") return flat.filter((f) => RIESGO_CAMPOS.has(f.categoria.campo));
    if (subtab === "planes") return [];
    return flat.filter((f) => f.categoria.campo === subtab);
  }, [flat, subtab]);

  if (error) {
    return <p className="text-sm text-amber-700">{error}</p>;
  }

  if (flat.length === 0) {
    return <p className="text-sm text-slate-500">Sin hallazgos de auditoría para este filtro.</p>;
  }

  const tituloConsolidado = secciones[0]?.titulo ?? "Consolidado Auditoría";

  return (
    <div className="space-y-6">
      <p className="inline-flex w-fit items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
        <CalendarClock className="h-3.5 w-3.5" />
        Resultados de auditoría 2026 — no varían con el filtro de año
      </p>

      <section className="space-y-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-bold text-slate-900">{tituloConsolidado}</h2>
          <div className="flex items-center gap-2">
            {dictamenFavorable ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                <span className="h-2 w-2 rounded-full bg-emerald-600" />
                Dictamen Favorable
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700">
                <span className="h-2 w-2 rounded-full bg-red-600" />
                Requiere Atención
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <SummaryCard
            label="Fortalezas Clave"
            value={counts.fortaleza}
            hint="Detectadas"
            icon={<CheckCircle2 className="h-[18px] w-[18px]" />}
            accent="#16a34a"
            bg="bg-emerald-50/40"
          />
          <SummaryCard
            label="Oportunidades de Mejora"
            value={counts.oportunidad}
            hint="Requerimientos"
            icon={<Lightbulb className="h-[18px] w-[18px]" />}
            accent="#d97706"
            bg="bg-amber-50/40"
          />
          <SummaryCard
            label="Planes de Acción Articulados"
            value={counts.planes}
            hint="Con recomendación de auditoría"
            icon={<Target className="h-[18px] w-[18px]" />}
            accent="#00288e"
            bg="bg-blue-50/40"
          />
        </div>
      </section>

      <nav className="flex items-center gap-1.5 overflow-x-auto rounded-xl border border-slate-200 bg-white p-1.5 shadow-sm">
        {(Object.keys(SUBTAB_META) as SubtabId[]).map((id) => {
          const meta = SUBTAB_META[id];
          const Icon = meta.icon;
          const active = subtab === id;
          const count =
            id === "all"
              ? counts.total
              : id === "riesgo"
                ? counts.riesgo
                : id === "planes"
                  ? counts.planes
                  : id === "fortaleza"
                    ? counts.fortaleza
                    : counts.oportunidad;
          return (
            <button
              key={id}
              type="button"
              onClick={() => setSubtab(id)}
              className={`inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-lg px-3.5 py-2 text-sm font-semibold transition-all ${
                active ? "bg-poli-navy text-white shadow-xs" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <Icon className={`h-[18px] w-[18px] ${active ? "text-white" : meta.iconColor}`} />
              <span>{meta.label}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
                  active ? "bg-white/20 text-white" : "bg-slate-100 text-slate-600"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </nav>

      <div className="space-y-6">
        {subtab === "planes" ? (
          <PlanesSection flat={flat} />
        ) : visible.length === 0 ? (
          <p className="text-sm text-slate-500">Sin hallazgos para esta categoría.</p>
        ) : (
          groupByProceso(visible).map(([proceso, categorias]) => (
            <div key={proceso} className="space-y-4">
              {categorias.map(({ categoria }, i) => (
                <CategoriaSection key={`${proceso}-${categoria.campo}-${i}`} proceso={proceso} categoria={categoria} />
              ))}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function groupByProceso(items: FlatCategoria[]): [string, FlatCategoria[]][] {
  const map = new Map<string, FlatCategoria[]>();
  for (const item of items) {
    const list = map.get(item.proceso) ?? [];
    list.push(item);
    map.set(item.proceso, list);
  }
  return Array.from(map.entries());
}

function CategoriaSection({ proceso, categoria }: { proceso: string; categoria: AuditoriaCategoria }) {
  return (
    <section
      className="overflow-hidden rounded-xl border-2 shadow-sm"
      style={{ borderColor: `${categoria.dot_color}66` }}
    >
      <div
        className="flex flex-col gap-3 border-b px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
        style={{ backgroundColor: categoria.pill_bg, borderColor: `${categoria.dot_color}44` }}
      >
        <div className="flex items-center gap-3">
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-xl shadow-xs"
            style={{ backgroundColor: "#ffffff", color: categoria.pill_text }}
          >
            {categoria.emoji}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold" style={{ color: categoria.pill_text }}>
                {categoria.label}
              </h3>
              <span
                className="rounded-full border px-2.5 py-0.5 text-[11px] font-bold"
                style={{ color: categoria.pill_text, borderColor: categoria.dot_color, backgroundColor: "#ffffff" }}
              >
                {categoria.items.length} {categoria.items.length === 1 ? "hallazgo" : "hallazgos"}
              </span>
            </div>
            <p className="text-xs font-medium text-slate-600">{proceso}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 bg-white p-5 lg:grid-cols-2">
        {categoria.items.map((item, i) => (
          <ItemCard key={i} index={i + 1} item={item} categoria={categoria} />
        ))}
      </div>
    </section>
  );
}

function ItemCard({ index, item, categoria }: { index: number; item: AuditoriaItem; categoria: AuditoriaCategoria }) {
  return (
    <article className="flex flex-col justify-between rounded-lg border border-slate-200 p-4 transition-all hover:shadow-md">
      <div>
        <div className="mb-2 flex items-start gap-2.5">
          <span
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold"
            style={{ backgroundColor: categoria.pill_bg, color: categoria.pill_text }}
          >
            {index}
          </span>
          {item.nombre && <h4 className="text-sm font-bold leading-tight text-slate-900">{item.nombre}</h4>}
        </div>
        {item.descripcion && (
          <p className="pl-8 text-sm leading-relaxed text-slate-600">{item.descripcion}</p>
        )}
      </div>
      {item.recomendaciones && (
        <div
          className="ml-8 mt-3 rounded-lg border border-slate-200 border-l-4 bg-slate-50 p-3 text-sm shadow-xs"
          style={{ borderLeftColor: categoria.dot_color }}
        >
          <p
            className="mb-1 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider"
            style={{ color: categoria.pill_text }}
          >
            Recomendación de auditoría
          </p>
          <p className="leading-relaxed text-slate-700">{item.recomendaciones}</p>
        </div>
      )}
    </article>
  );
}

function PlanesSection({ flat }: { flat: FlatCategoria[] }) {
  const planes = flat.flatMap(({ proceso, categoria }) =>
    categoria.items
      .filter((it) => it.recomendaciones)
      .map((it) => ({ proceso, categoria, item: it }))
  );

  if (planes.length === 0) {
    return <p className="text-sm text-slate-500">No hay recomendaciones de auditoría registradas.</p>;
  }

  return (
    <section className="overflow-hidden rounded-xl border-2 border-blue-200 shadow-sm">
      <div className="flex items-center gap-3 border-b border-blue-100 bg-blue-50/60 px-5 py-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-poli-navy shadow-xs">
          <ClipboardCheck className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-poli-navy">Planes de Acción Articulados</h3>
          <p className="text-xs font-medium text-blue-800">
            {planes.length} recomendación{planes.length === 1 ? "" : "es"} de auditoría con seguimiento
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 bg-white p-5 lg:grid-cols-2">
        {planes.map(({ proceso, categoria, item }, i) => (
          <article key={i} className="flex flex-col gap-2 rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between gap-2">
              <span
                className="rounded-full px-2 py-0.5 text-[11px] font-bold"
                style={{ backgroundColor: categoria.pill_bg, color: categoria.pill_text }}
              >
                {categoria.emoji} {categoria.label}
              </span>
              <span className="text-[11px] text-slate-400">{proceso}</span>
            </div>
            {item.nombre && <h4 className="text-sm font-bold text-slate-900">{item.nombre}</h4>}
            <div className="rounded-lg border border-l-4 border-slate-200 border-l-poli-navy bg-slate-50 p-3 text-sm">
              <p className="mb-1 text-[11px] font-bold uppercase tracking-wider text-poli-navy">Recomendación</p>
              <p className="leading-relaxed text-slate-700">{item.recomendaciones}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function SummaryCard({
  label,
  value,
  hint,
  icon,
  accent,
  bg,
}: {
  label: string;
  value: number;
  hint: string;
  icon: React.ReactNode;
  accent: string;
  bg: string;
}) {
  return (
    <div className={`flex flex-col justify-between rounded-xl border border-slate-200 border-t-2 p-4 shadow-sm ${bg}`} style={{ borderTopColor: accent }}>
      <div className="flex items-start justify-between">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
        <div
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg"
          style={{ backgroundColor: `${accent}1f`, color: accent }}
        >
          {icon}
        </div>
      </div>
      <div className="my-2 flex items-baseline gap-2">
        <span className="text-3xl font-extrabold" style={{ color: accent }}>
          {value}
        </span>
      </div>
      <p className="text-xs font-medium text-slate-500">{hint}</p>
    </div>
  );
}
