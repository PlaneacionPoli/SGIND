"use client";

import { Fragment, useMemo, useState } from "react";
import Image from "next/image";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown } from "lucide-react";
import { DataFreshnessFooter } from "@/components/layout/DataFreshnessFooter";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";
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

interface ObjetivoMeta {
  img: string;
  /** Fila clara (azul cielo) u oscura (navy), alternadas como en la política. */
  oscuro: boolean;
}

const LOGO_ICON = "/icons/nav/polisigs.png";
const OBJETIVO_META: Record<number, ObjetivoMeta> = {
  1: { img: LOGO_ICON, oscuro: false },
  2: { img: "/img/polisigs/obj1.png", oscuro: true },
  3: { img: "/img/polisigs/obj2.png", oscuro: false },
  4: { img: "/img/polisigs/obj3.png", oscuro: true },
  5: { img: "/img/polisigs/obj4.png", oscuro: false },
  6: { img: LOGO_ICON, oscuro: true },
};

export default function PolisigsPage() {
  const { isAuthenticated } = useAuthReady();
  const [abierto, setAbierto] = useState<number | null>(null);

  const query = useQuery({
    queryKey: ["polisigs"],
    queryFn: fetchPolisigs,
    enabled: isAuthenticated,
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
          Cumplimiento consolidado de la política y de cada uno de sus objetivos (vigencia {data?.anio ?? 2026}).
        </p>
      </header>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver los indicadores.</p>
      ) : query.isLoading ? (
        <div className="h-72 animate-pulse rounded-2xl bg-slate-200" />
      ) : query.isError || !data ? (
        <p className="text-sm text-red-700">No fue posible cargar los indicadores POLISIGS.</p>
      ) : (
        <>
          <Hero anio={data.anio} politica={data.politica} objetivos={data.objetivos} />

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

function Hero({
  anio,
  politica,
  objetivos,
}: {
  anio: number;
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
              Cumplimiento consolidado de la política · {anio}
            </p>
            <p className="mt-1 text-6xl font-extrabold leading-none">{fmtPct(politica.cumplimiento)}</p>
            <span
              className="mt-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold"
              style={{ color: estilo.text, backgroundColor: estilo.bg }}
            >
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: estilo.bar }} />
              {politica.nivel}
            </span>
            <p className="mt-3 text-xs text-sky-100/80">
              {politica.con_dato} de {politica.total} indicadores con dato · {politica.sobrecumple + politica.cumple} cumplen ·{" "}
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
            {objetivo.con_dato} de {objetivo.total} indicadores con dato · {objetivo.sobrecumple + objetivo.cumple} cumplen ·{" "}
            {objetivo.alerta} alerta · {objetivo.peligro} peligro
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1.5">
          <span className="text-3xl font-extrabold leading-none md:text-4xl">{fmtPct(objetivo.cumplimiento)}</span>
          <span
            className="rounded-full px-2.5 py-0.5 text-[11px] font-bold"
            style={{ color: c.text, backgroundColor: c.bg }}
          >
            {objetivo.nivel}
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
  const [proceso, setProceso] = useState<string | null>(null);
  const [soloConDato, setSoloConDato] = useState(false);
  const [detalle, setDetalle] = useState<string | null>(null);

  const filas = useMemo(
    () =>
      indicadores.filter(
        (i) =>
          (proceso == null || (i.proceso ?? "Sin proceso") === proceso) &&
          (!soloConDato || i.cumplimiento_pct != null)
      ),
    [indicadores, proceso, soloConDato]
  );

  return (
    <>
      <div>
        <div className="mb-2 flex items-center justify-between">
          <h4 className="text-sm font-bold text-poli-navy">Procesos con indicadores en el objetivo</h4>
          {proceso && (
            <button
              type="button"
              onClick={() => setProceso(null)}
              className="text-xs font-semibold text-blue-700 underline"
            >
              Ver todos
            </button>
          )}
        </div>
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {objetivo.procesos.map((comp) => {
            const c = NIVEL_COLOR[comp.nivel] ?? NIVEL_NEUTRO;
            const activo = proceso === comp.nombre;
            return (
              <button
                key={comp.nombre}
                type="button"
                onClick={() => setProceso(activo ? null : comp.nombre)}
                aria-pressed={activo}
                className={`rounded-xl border p-3 text-left transition ${
                  activo ? "border-poli-navy bg-blue-50 shadow-sm" : "border-slate-200 bg-white hover:border-slate-300"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-semibold text-slate-800">{comp.nombre}</span>
                  <span className="shrink-0 text-sm font-extrabold" style={{ color: c.text }}>
                    {fmtPct(comp.cumplimiento)}
                  </span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${Math.min(100, comp.cumplimiento ?? 0)}%`, backgroundColor: c.bar }}
                  />
                </div>
                <p className="mt-1.5 text-[10px] text-slate-500">
                  {comp.con_dato}/{comp.total} con dato
                </p>
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
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
            Ocultar indicadores sin dato
          </label>
        </div>
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full min-w-[980px] border-collapse text-left text-sm">
            <thead>
              <tr
                className="text-[11px] font-bold uppercase tracking-wider text-white"
                style={{ backgroundColor: NAVY }}
              >
                <th className="px-3 py-2.5">ID</th>
                <th className="px-3 py-2.5">Indicador</th>
                <th className="px-3 py-2.5">Proceso</th>
                <th className="px-3 py-2.5">Tipo</th>
                <th className="px-3 py-2.5 text-right">Meta</th>
                <th className="px-3 py-2.5 text-right">Ejecución</th>
                <th className="px-3 py-2.5">Cumplimiento</th>
                <th className="px-3 py-2.5 text-center">Nivel</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filas.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-3 py-6 text-center text-sm text-slate-500">
                    Sin indicadores para el filtro seleccionado.
                  </td>
                </tr>
              )}
              {filas.map((i) => {
                const c = NIVEL_COLOR[i["Nivel de cumplimiento"]] ?? NIVEL_NEUTRO;
                const expandido = detalle === i.Id;
                const rec = i as unknown as Record<string, unknown>;
                return (
                  <Fragment key={i.Id}>
                    <tr
                      onClick={() => setDetalle(expandido ? null : i.Id)}
                      className="cursor-pointer align-top transition-colors hover:bg-slate-50"
                    >
                      <td className="px-3 py-2.5 font-mono text-xs font-semibold text-slate-600">{i.Id}</td>
                      <td className="px-3 py-2.5 font-medium text-slate-900">{i.Indicador}</td>
                      <td className="px-3 py-2.5 text-xs text-slate-600">{i.proceso ?? "—"}</td>
                      <td className="px-3 py-2.5">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                            i.tipo === "Efectividad"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {i.tipo ?? "—"}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-right font-medium tabular-nums">{fmtMeta(rec)}</td>
                      <td className="px-3 py-2.5 text-right font-medium tabular-nums">{fmtEjecucion(rec)}</td>
                      <td className="px-3 py-2.5">
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-16 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className="h-full rounded-full"
                              style={{ width: `${Math.min(100, i.cumplimiento_pct ?? 0)}%`, backgroundColor: c.bar }}
                            />
                          </div>
                          <span className="text-xs font-bold tabular-nums text-slate-800">
                            {fmtPct(i.cumplimiento_pct)}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <NivelBadge nivel={i["Nivel de cumplimiento"]} />
                      </td>
                    </tr>
                    {expandido && (
                      <tr className="bg-slate-50">
                        <td colSpan={8} className="px-4 py-3 text-xs text-slate-700">
                          <dl className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
                            <Dato k="Objetivos asociados" v={i.objetivos.map((n) => `O${n}`).join(", ")} />
                            <Dato k="Responsable" v={i.responsable} />
                            <Dato k="Frecuencia" v={i.frecuencia} />
                            <Dato k="Último periodo reportado" v={i.periodo} />
                            <Dato k="Sentido" v={i.sentido} />
                            <Dato k="ODS relacionados" v={i.ods} />
                            <Dato k="Relevancia ODS" v={i.relevancia_ods} />
                          </dl>
                          {i.observaciones && (
                            <p className="mt-2 border-t border-slate-200 pt-2 italic text-slate-600">
                              {i.observaciones}
                            </p>
                          )}
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-[11px]" style={{ color: CYAN }}>
          Meta, ejecución y cumplimiento de Resultados Consolidados (último periodo reportado de 2026); consolidado = promedio de los indicadores con cumplimiento.
        </p>
      </div>
    </>
  );
}

function Dato({ k, v }: { k: string; v: string | null }) {
  return (
    <div className="flex gap-1.5">
      <dt className="font-semibold text-slate-500">{k}:</dt>
      <dd>{v ?? "—"}</dd>
    </div>
  );
}
