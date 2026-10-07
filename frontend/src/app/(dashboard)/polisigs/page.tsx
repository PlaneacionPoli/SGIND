"use client";

import { useMemo, useState } from "react";
import Image from "next/image";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown } from "lucide-react";
import { DataFreshnessFooter } from "@/components/layout/DataFreshnessFooter";
import { fmtPct } from "@/components/cmi/nivelUtils";
import { fetchPolisigs } from "@/lib/api";
import { fmtEjecucion, fmtMeta } from "@/lib/formatValor";
import type { PolisigsConsolidado, PolisigsIndicador, PolisigsObjetivo } from "@/lib/types";
import { useAuthReady } from "@/stores/auth-store";

// Paleta tomada de la pieza gráfica de la política POLISIGS V6.
const NAVY = "#0B2A5B";
const NAVY_DEEP = "#06214B";
const CYAN = "#1A9BD7";
const SKY = "#A9CBEC";

const NIVEL_COLOR: Record<string, { bar: string; text: string; bg: string }> = {
  Sobrecumplimiento: { bar: "#2563EB", text: "#1D4ED8", bg: "#DBEAFE" },
  Cumplimiento: { bar: "#16A34A", text: "#166534", bg: "#DCFCE7" },
  Alerta: { bar: "#F59E0B", text: "#B45309", bg: "#FEF3C7" },
  Peligro: { bar: "#DC2626", text: "#B71C1C", bg: "#FEE2E2" },
  "Pendiente de reporte": { bar: "#94A3B8", text: "#475569", bg: "#F1F5F9" },
};
const NIVEL_NEUTRO = NIVEL_COLOR["Pendiente de reporte"];

/** "Pendiente de reporte" del CMI se muestra como "Sin información" (no hay medición en el corte). */
const etiquetaNivel = (n: string) => (n === "Pendiente de reporte" ? "Sin información" : n);

interface ObjetivoMeta {
  img: string;
  /** Fila clara (azul cielo) u oscura (navy), alternadas como en la política. */
  oscuro: boolean;
}

const OBJETIVO_META: Record<number, ObjetivoMeta> = {
  1: { img: "/img/polisigs/obj-ods.png", oscuro: false },
  2: { img: "/img/polisigs/obj1.png", oscuro: true },
  3: { img: "/img/polisigs/obj2.png", oscuro: false },
  4: { img: "/img/polisigs/obj3.png", oscuro: true },
  5: { img: "/img/polisigs/obj4.png", oscuro: false },
  6: { img: "/img/polisigs/obj-legal.png", oscuro: true },
};

export default function PolisigsPage() {
  const { isAuthenticated } = useAuthReady();
  const [abierto, setAbierto] = useState<number | null>(null);

  // Corte vigente de la data: junio 2026 (cierres semestrales: junio y diciembre).
  const [anio, setAnio] = useState(2026);
  const [mes, setMes] = useState(6);

  const query = useQuery({
    queryKey: ["polisigs", anio, mes],
    queryFn: () => fetchPolisigs({ anio, mes }),
    enabled: isAuthenticated,
    placeholderData: (prev) => prev,
  });
  const data = query.data;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-1">
        <span className="w-fit rounded-full bg-poli-navy px-2.5 py-0.5 text-[11px] font-bold text-white shadow-sm">
          Sistema Integrado POLISIGS
        </span>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">Indicadores POLISIGS</h2>
        <p className="text-sm text-slate-600">
          Cumplimiento consolidado de la política y de cada uno de sus objetivos (corte {data?.corte ?? "junio 2026"}).
        </p>
      </header>

      {isAuthenticated && data && (
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
          <FiltroGrupo label="Año">
            {data.filtros.anios.map((a) => (
              <Pill key={a} activo={anio === a} onClick={() => setAnio(a)}>
                {a}
              </Pill>
            ))}
          </FiltroGrupo>
          <FiltroGrupo label="Fecha de corte">
            {data.filtros.cortes.map((c) => (
              <Pill key={c.mes} activo={mes === c.mes} onClick={() => setMes(c.mes)}>
                {c.nombre}
              </Pill>
            ))}
          </FiltroGrupo>
          <span className="ml-auto inline-flex items-center gap-1.5 rounded-full border border-emerald-300 bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
            Corte de la data: {data.corte}
          </span>
        </div>
      )}

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver los indicadores.</p>
      ) : query.isLoading ? (
        <div className="h-72 animate-pulse rounded-2xl bg-slate-200" />
      ) : query.isError || !data ? (
        <p className="text-sm text-red-700">No fue posible cargar los indicadores POLISIGS.</p>
      ) : (
        <>
          <Hero corte={data.corte} politica={data.politica} objetivos={data.objetivos} />

          <section className="space-y-3" aria-label="Objetivos de la política">
            <h3 className="text-lg font-bold text-poli-navy">Cumplimiento por objetivo (versión 6)</h3>
            <p className="-mt-2 text-xs text-slate-500">
              Haga clic en un objetivo para ver los indicadores asociados. Un indicador puede aparecer en más de un objetivo; el consolidado de la política cuenta cada indicador una sola vez.
            </p>
            {data.objetivos.map((o) => (
              <ObjetivoRow
                key={o.numero}
                objetivo={o}
                indicadores={data.indicadores.filter((i) => i.objetivos.includes(o.numero))}
                abierto={abierto === o.numero}
                onToggle={() => setAbierto(abierto === o.numero ? null : o.numero)}
              />
            ))}
          </section>
        </>
      )}

      <DataFreshnessFooter />
    </div>
  );
}

function FiltroGrupo({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function Pill({
  activo,
  onClick,
  children,
}: {
  activo: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={activo}
      className={`rounded-lg px-3.5 py-1.5 text-sm font-semibold transition ${
        activo ? "bg-poli-navy text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
      }`}
    >
      {children}
    </button>
  );
}

function Hero({
  corte,
  politica,
  objetivos,
}: {
  corte: string;
  politica: PolisigsConsolidado;
  objetivos: PolisigsObjetivo[];
}) {
  const estilo = NIVEL_COLOR[politica.nivel] ?? NIVEL_NEUTRO;
  return (
    <section
      className="overflow-hidden rounded-2xl p-6 text-white shadow-md md:p-8"
      style={{ background: `linear-gradient(135deg, ${NAVY_DEEP} 0%, ${NAVY} 60%, #0F3F7D 100%)` }}
    >
      <div className="grid items-center gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]">
        <div className="flex flex-col items-center gap-5 lg:items-start">
          <Image
            src="/img/polisigs/logo-bg.png"
            alt="POLISIGS"
            width={345}
            height={200}
            priority
            className="h-auto w-56"
          />
          <div className="text-center lg:text-left">
            <p className="text-xs font-bold uppercase tracking-widest text-sky-200">
              Cumplimiento consolidado de la política · {corte}
            </p>
            <p className="mt-1 text-6xl font-extrabold leading-none">{fmtPct(politica.cumplimiento)}</p>
            <span
              className="mt-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold"
              style={{ color: estilo.text, backgroundColor: estilo.bg }}
            >
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: estilo.bar }} />
              {etiquetaNivel(politica.nivel)}
            </span>
            <p className="mt-3 text-xs text-sky-100/80">
              {politica.con_dato} de {politica.total} indicadores con información · {politica.sobrecumple + politica.cumple} cumplen ·{" "}
              {politica.alerta} en alerta · {politica.peligro} en peligro
            </p>
          </div>
        </div>

        <ul className="grid gap-3 sm:grid-cols-2">
          {objetivos.map((o) => {
            const meta = OBJETIVO_META[o.numero];
            const c = NIVEL_COLOR[o.nivel] ?? NIVEL_NEUTRO;
            return (
              <li
                key={o.numero}
                className="flex items-center gap-3 rounded-xl bg-white/10 p-3 ring-1 ring-white/15 backdrop-blur-sm"
              >
                {meta && (
                  <Image
                    src={meta.img}
                    alt=""
                    width={56}
                    height={56}
                    className="h-14 w-14 shrink-0 rounded-full bg-white/10 object-cover ring-2 ring-white/40"
                  />
                )}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-semibold uppercase tracking-wide text-sky-100">
                    {o.numero}. {o.corto}
                  </p>
                  <p className="text-2xl font-extrabold leading-tight">{fmtPct(o.cumplimiento)}</p>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/20">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${Math.min(100, o.cumplimiento ?? 0)}%`, backgroundColor: c.bar }}
                    />
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}

function ObjetivoRow({
  objetivo,
  indicadores,
  abierto,
  onToggle,
}: {
  objetivo: PolisigsObjetivo;
  indicadores: PolisigsIndicador[];
  abierto: boolean;
  onToggle: () => void;
}) {
  const meta = OBJETIVO_META[objetivo.numero];
  const oscuro = meta?.oscuro ?? false;
  const c = NIVEL_COLOR[objetivo.nivel] ?? NIVEL_NEUTRO;
  const panelId = `polisigs-obj-${objetivo.numero}`;

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={abierto}
        aria-controls={panelId}
        className="flex w-full items-center gap-4 p-4 text-left transition hover:brightness-105 md:p-5"
        style={{ backgroundColor: oscuro ? NAVY : SKY, color: oscuro ? "#fff" : NAVY_DEEP }}
      >
        {meta && (
          <Image
            src={meta.img}
            alt=""
            width={72}
            height={72}
            className="h-[72px] w-[72px] shrink-0 rounded-full object-cover ring-4"
            style={{ ["--tw-ring-color" as string]: oscuro ? "rgba(255,255,255,0.35)" : "#fff" }}
          />
        )}
        <div className="min-w-0 flex-1">
          <p className="text-base font-extrabold md:text-lg">
            {objetivo.numero}. {objetivo.corto}
          </p>
          <p className={`mt-0.5 line-clamp-2 text-xs md:text-sm ${oscuro ? "text-sky-100" : "text-slate-700"}`}>
            {objetivo.nombre}
          </p>
          <p className={`mt-1 text-[11px] font-semibold ${oscuro ? "text-sky-200" : "text-slate-600"}`}>
            {objetivo.con_dato} de {objetivo.total} indicadores con información · {objetivo.sobrecumple + objetivo.cumple} cumplen ·{" "}
            {objetivo.alerta} alerta · {objetivo.peligro} peligro
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1.5">
          <span className="text-3xl font-extrabold leading-none md:text-4xl">{fmtPct(objetivo.cumplimiento)}</span>
          <span
            className="rounded-full px-2.5 py-0.5 text-[11px] font-bold"
            style={{ color: c.text, backgroundColor: c.bg }}
          >
            {etiquetaNivel(objetivo.nivel)}
          </span>
        </div>
        <ChevronDown className={`h-6 w-6 shrink-0 transition-transform ${abierto ? "rotate-180" : ""}`} aria-hidden />
      </button>

      {abierto && (
        <div id={panelId} className="space-y-5 border-t border-slate-200 p-4 md:p-6">
          <ObjetivoDetalle objetivo={objetivo} indicadores={indicadores} />
        </div>
      )}
    </div>
  );
}

function ObjetivoDetalle({
  objetivo,
  indicadores,
}: {
  objetivo: PolisigsObjetivo;
  indicadores: PolisigsIndicador[];
}) {
  const [soloConDato, setSoloConDato] = useState(false);
  const filas = useMemo(
    () => (soloConDato ? indicadores.filter((i) => i.cumplimiento_pct != null) : indicadores),
    [indicadores, soloConDato]
  );

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-sm font-bold text-poli-navy">
          Indicadores asociados <span className="font-normal text-slate-500">({filas.length})</span>
        </h4>
        <label className="flex cursor-pointer items-center gap-2 text-xs font-medium text-slate-600">
          <input
            type="checkbox"
            checked={soloConDato}
            onChange={(e) => setSoloConDato(e.target.checked)}
            className="h-3.5 w-3.5 accent-[#0B2A5B]"
          />
          Ocultar indicadores sin información
        </label>
      </div>
      {filas.length === 0 ? (
        <p className="rounded-xl border border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">
          Sin indicadores para mostrar en este corte.
        </p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {filas.map((i) => (
            <FichaIndicador key={i.Id} ind={i} mostrarOds={objetivo.numero === 1} />
          ))}
        </div>
      )}
      <p className="mt-3 text-[11px]" style={{ color: CYAN }}>
        Meta, ejecución y cumplimiento de Resultados Consolidados en el corte seleccionado; sin medición en el corte = sin
        información. Cumplimiento de cada indicador topado en 100 %; consolidado = promedio de los indicadores con
        cumplimiento.
      </p>
    </div>
  );
}

function FichaIndicador({ ind, mostrarOds }: { ind: PolisigsIndicador; mostrarOds: boolean }) {
  const nivel = ind["Nivel de cumplimiento"];
  const c = NIVEL_COLOR[nivel] ?? NIVEL_NEUTRO;
  const rec = ind as unknown as Record<string, unknown>;
  const sinInfo = ind.Meta == null && ind.Ejecucion == null && ind.cumplimiento_pct == null;
  return (
    <article className="flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex-1 space-y-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <h5 className="text-sm font-bold leading-snug text-slate-900">{ind.Indicador}</h5>
          <span className="shrink-0 rounded-md bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] font-semibold text-slate-600">
            {ind.Id}
          </span>
        </div>

        {mostrarOds && ind.ods.length > 0 && (
          <ul className="flex flex-wrap gap-1.5" aria-label="ODS asociados">
            {ind.ods.map((o) => (
              <li
                key={o.numero}
                title={`ODS ${o.numero} – ${o.nombre}`}
                className="inline-flex items-center gap-1 rounded-full border border-sky-200 bg-sky-50 px-2 py-0.5 text-[11px] font-semibold text-sky-900"
              >
                <span className="rounded-full bg-poli-navy px-1.5 text-[10px] font-bold text-white">
                  ODS {o.numero}
                </span>
                {o.nombre}
              </li>
            ))}
          </ul>
        )}

        {sinInfo ? (
          <p className="rounded-lg bg-slate-50 py-4 text-center text-sm font-semibold text-slate-500">
            Sin información en este corte
          </p>
        ) : (
          <>
            <dl className="grid grid-cols-3 gap-2 text-center">
              <Medida k="Meta" v={fmtMeta(rec)} />
              <Medida k="Ejecución" v={fmtEjecucion(rec)} />
              <Medida k="Cumplimiento" v={fmtPct(ind.cumplimiento_pct)} fuerte color={c.text} />
            </dl>
            <div className="flex items-center gap-2">
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${Math.min(100, ind.cumplimiento_pct ?? 0)}%`, backgroundColor: c.bar }}
                />
              </div>
              <span
                className="rounded-full px-2 py-0.5 text-[11px] font-bold"
                style={{ color: c.text, backgroundColor: c.bg }}
                title={ind.cumplimiento_real != null ? `Cumplimiento real: ${fmtPct(ind.cumplimiento_real)}` : undefined}
              >
                {etiquetaNivel(nivel)}
              </span>
            </div>
          </>
        )}
      </div>
      <footer className="border-t border-slate-100 bg-slate-50 px-4 py-2 text-[11px] text-slate-600">
        <span className="font-semibold text-slate-500">Proceso: </span>
        {ind.proceso ?? "—"}
        {ind.frecuencia ? <span className="text-slate-400"> · {ind.frecuencia}</span> : null}
      </footer>
    </article>
  );
}

function Medida({ k, v, fuerte, color }: { k: string; v: string; fuerte?: boolean; color?: string }) {
  return (
    <div className="rounded-lg bg-slate-50 px-1 py-2">
      <dt className="text-[10px] font-bold uppercase tracking-wide text-slate-500">{k}</dt>
      <dd className={`mt-0.5 tabular-nums ${fuerte ? "text-base font-extrabold" : "text-sm font-semibold text-slate-800"}`} style={fuerte ? { color } : undefined}>
        {v}
      </dd>
    </div>
  );
}
