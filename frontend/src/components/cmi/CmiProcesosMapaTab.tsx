"use client";

import { Fragment, useMemo, useState } from "react";
import type {
  CMIMapaIndicador,
  CMIMapaProceso,
  CMIMapaSubproceso,
  CMIProcesosMapaResponse,
} from "@/lib/types";
import { colorCumplimiento } from "@/components/cmi/cmiChartColors";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";

type Serie = Record<string, number | null>;

interface MapaProps {
  mapa: CMIProcesosMapaResponse;
  onOpenFicha: (indicadorId: string) => void;
}

/** Subproceso que repite el nombre del proceso: se muestra como un solo nivel. */
function esNivelUnico(p: CMIMapaProceso): boolean {
  return p.subprocesos.length <= 1 && (p.subprocesos[0]?.subproceso ?? p.proceso) === p.proceso;
}

function etiquetaAnio(anio: number, mapa: CMIProcesosMapaResponse): string {
  return mapa.anio_parcial === anio ? `${anio} parcial` : String(anio);
}

function Variacion({ valor }: { valor: number | null | undefined }) {
  if (valor == null) return <span className="text-slate-400">—</span>;
  const sube = valor > 0;
  return (
    <span className={`font-semibold ${valor === 0 ? "text-slate-500" : sube ? "text-emerald-700" : "text-red-700"}`}>
      {valor === 0 ? "→" : sube ? "▲" : "▼"} {sube ? "+" : ""}
      {valor.toFixed(1)} pp
    </span>
  );
}

function Celda({ valor, parcial }: { valor: number | null | undefined; parcial?: boolean }) {
  if (valor == null) return <span className="text-slate-300">—</span>;
  return (
    <span
      className={`font-semibold ${parcial ? "italic" : ""}`}
      style={{ color: colorCumplimiento(valor) }}
      title={parcial ? "Año en curso: dato parcial" : undefined}
    >
      {fmtPct(valor)}
    </span>
  );
}

export function Sparkline({
  serie,
  anios,
  parcial,
  width = 96,
  height = 26,
}: {
  serie: Serie;
  anios: number[];
  parcial: number | null;
  width?: number;
  height?: number;
}) {
  const pts = anios
    .map((a, i) => ({ a, i, v: serie[String(a)] }))
    .filter((p): p is { a: number; i: number; v: number } => p.v != null);
  if (pts.length < 2) return <span className="text-slate-300">—</span>;
  const vals = pts.map((p) => p.v);
  const lo = Math.min(...vals);
  const hi = Math.max(...vals);
  const span = hi - lo || 1;
  const x = (i: number) => 3 + (i * (width - 6)) / Math.max(anios.length - 1, 1);
  const y = (v: number) => height - 3 - ((v - lo) / span) * (height - 6);
  const color = colorCumplimiento(pts[pts.length - 1].v);
  const tramos = pts.slice(1).map((p, k) => ({ from: pts[k], to: p }));
  return (
    <svg width={width} height={height} role="img" aria-label="Tendencia anual">
      {tramos.map(({ from, to }) => (
        <line
          key={to.a}
          x1={x(from.i)}
          y1={y(from.v)}
          x2={x(to.i)}
          y2={y(to.v)}
          stroke={color}
          strokeWidth={2}
          strokeDasharray={to.a === parcial ? "3 3" : undefined}
        />
      ))}
      {pts.map((p) => (
        <circle
          key={p.a}
          cx={x(p.i)}
          cy={y(p.v)}
          r={2.6}
          fill={p.a === parcial ? "#fff" : color}
          stroke={color}
          strokeWidth={1.5}
        />
      ))}
    </svg>
  );
}

function TendenciaGrande({ serie, mapa }: { serie: Serie; mapa: CMIProcesosMapaResponse }) {
  const W = 560;
  const H = 180;
  const padX = 36;
  const padY = 22;
  const pts = mapa.anios
    .map((a, i) => ({ a, i, v: serie[String(a)] }))
    .filter((p): p is { a: number; i: number; v: number } => p.v != null);
  if (pts.length === 0) return <p className="text-sm text-slate-500">Sin datos históricos.</p>;
  const vals = [...pts.map((p) => p.v), 100];
  const lo = Math.floor(Math.min(...vals) / 10) * 10 - 10;
  const hi = Math.ceil(Math.max(...vals) / 10) * 10 + 10;
  const x = (i: number) => padX + (i * (W - padX * 2)) / Math.max(mapa.anios.length - 1, 1);
  const y = (v: number) => H - padY - ((v - lo) / (hi - lo)) * (H - padY * 2);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Tendencia anual de cumplimiento">
      <line x1={padX} x2={W - padX} y1={y(100)} y2={y(100)} stroke="#94A3B8" strokeDasharray="4 4" />
      <text x={W - padX + 4} y={y(100) + 3} fontSize={10} fill="#64748B">
        100%
      </text>
      {pts.slice(1).map((p, k) => (
        <line
          key={p.a}
          x1={x(pts[k].i)}
          y1={y(pts[k].v)}
          x2={x(p.i)}
          y2={y(p.v)}
          stroke="#1A3A5C"
          strokeWidth={2.5}
          strokeDasharray={p.a === mapa.anio_parcial ? "5 4" : undefined}
        />
      ))}
      {pts.map((p) => (
        <g key={p.a}>
          <circle
            cx={x(p.i)}
            cy={y(p.v)}
            r={5}
            fill={p.a === mapa.anio_parcial ? "#fff" : colorCumplimiento(p.v)}
            stroke={colorCumplimiento(p.v)}
            strokeWidth={2}
          />
          <text x={x(p.i)} y={y(p.v) - 10} textAnchor="middle" fontSize={11} fontWeight={700} fill="#0F172A">
            {p.v.toFixed(1)}
          </text>
        </g>
      ))}
      {mapa.anios.map((a, i) => (
        <text key={a} x={x(i)} y={H - 4} textAnchor="middle" fontSize={11} fill="#475569">
          {etiquetaAnio(a, mapa)}
        </text>
      ))}
    </svg>
  );
}

function ChipTipoCalculo({ tipo }: { tipo: string | null }) {
  if (!tipo)
    return (
      <span
        title="El indicador no tiene TipoCalculo en el catálogo; el ETL lo trata como Cierre"
        className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-700"
      >
        Sin tipo
      </span>
    );
  return (
    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700">{tipo}</span>
  );
}

function ChipCierre({ estado }: { estado: string | null }) {
  if (!estado) return <span className="text-slate-300">—</span>;
  const parcial = estado === "Parcial";
  return (
    <span
      title={parcial ? "Cierre parcial: último corte del año en curso" : "Cierre final del año"}
      className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
        parcial ? "bg-amber-50 text-amber-700" : "bg-emerald-50 text-emerald-700"
      }`}
    >
      {estado}
    </span>
  );
}

function TablaIndicadores({
  indicadores,
  mapa,
  onOpenFicha,
}: {
  indicadores: CMIMapaIndicador[];
  mapa: CMIProcesosMapaResponse;
  onOpenFicha: (id: string) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-xs">
        <thead className="text-[10px] uppercase text-slate-500">
          <tr>
            <th className="py-1.5 pr-3">Id</th>
            <th className="py-1.5 pr-3">Indicador</th>
            <th className="py-1.5 pr-3">Cálculo</th>
            <th className="py-1.5 pr-3">Periodicidad</th>
            {mapa.anios.map((a) => (
              <th key={a} className="py-1.5 pr-3 text-right">
                {etiquetaAnio(a, mapa)}
              </th>
            ))}
            <th className="py-1.5 pr-3">Último reporte</th>
            <th className="py-1.5 pr-3">Cierre</th>
            <th className="py-1.5">Estado</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {indicadores.map((ind) => (
            <tr key={ind.id} className="hover:bg-slate-50">
              <td className="py-1.5 pr-3 font-mono text-slate-500">{ind.id}</td>
              <td className="py-1.5 pr-3">
                <button
                  type="button"
                  onClick={() => onOpenFicha(ind.id)}
                  className="text-left font-medium text-blue-700 hover:underline"
                >
                  {ind.indicador}
                </button>
              </td>
              <td className="py-1.5 pr-3">
                <ChipTipoCalculo tipo={ind.tipo_calculo} />
              </td>
              <td className="py-1.5 pr-3 text-slate-600">{ind.periodicidad ?? "—"}</td>
              {mapa.anios.map((a) => (
                <td key={a} className="py-1.5 pr-3 text-right">
                  <Celda valor={ind.anios[String(a)]} parcial={a === mapa.anio_parcial} />
                </td>
              ))}
              <td className="py-1.5 pr-3 whitespace-nowrap text-slate-600">{ind.ultimo_reporte ?? "—"}</td>
              <td className="py-1.5 pr-3">
                <ChipCierre estado={ind.estado_cierre} />
              </td>
              <td className="py-1.5">
                <NivelBadge nivel={ind.nivel ?? undefined} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Subficha({
  sub,
  mapa,
  onOpenFicha,
}: {
  sub: CMIMapaSubproceso;
  mapa: CMIProcesosMapaResponse;
  onOpenFicha: (id: string) => void;
}) {
  const [a, b, c] = mapa.anios.slice(-3);
  return (
    <details className="rounded-xl border border-slate-200 bg-white" open={sub.n_indicadores <= 6}>
      <summary className="flex cursor-pointer flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div>
          <p className="text-sm font-bold text-slate-900">{sub.subproceso}</p>
          <p className="text-xs text-slate-500">
            {sub.n_indicadores} indicadores · {sub.en_riesgo} en riesgo
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <Sparkline serie={sub.anios} anios={mapa.anios} parcial={mapa.anio_parcial} />
          <span className="text-right">
            <span className="block text-[10px] text-slate-500">
              Δ {a}→{b}
            </span>
            <Variacion valor={sub.variaciones[`${a}-${b}`]} />
          </span>
          <span className="text-right">
            <span className="block text-[10px] text-slate-500">
              Δ {b}→{c}
              {mapa.anio_parcial === c ? "p" : ""}
            </span>
            <Variacion valor={sub.variaciones[`${b}-${c}`]} />
          </span>
        </div>
      </summary>
      <div className="border-t border-slate-100 px-4 py-3">
        <TablaIndicadores indicadores={sub.indicadores} mapa={mapa} onOpenFicha={onOpenFicha} />
      </div>
    </details>
  );
}

function FichaProceso({
  proceso,
  mapa,
  onClose,
  onOpenFicha,
}: {
  proceso: CMIMapaProceso;
  mapa: CMIProcesosMapaResponse;
  onClose: () => void;
  onOpenFicha: (id: string) => void;
}) {
  const [a, b, c] = mapa.anios.slice(-3);
  const actual = proceso.anios[String(mapa.anios[mapa.anios.length - 1])];
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <aside
        className="h-full w-full max-w-4xl overflow-y-auto bg-slate-50 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        aria-label={`Ficha del proceso ${proceso.proceso}`}
      >
        <div className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-slate-200 bg-white px-6 py-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
              Ficha de proceso · {proceso.tipo_proceso || "Sin tipo"}
            </p>
            <h3 className="text-lg font-bold text-poli-navy">{proceso.proceso}</h3>
            {proceso.unidad && <p className="text-xs text-slate-500">{proceso.unidad}</p>}
          </div>
          <button type="button" onClick={onClose} className="text-slate-500 hover:text-slate-800" aria-label="Cerrar">
            ✕
          </button>
        </div>

        <div className="space-y-5 p-6">
          <div className="grid gap-3 sm:grid-cols-4">
            {[
              {
                label: `Cumplimiento ${etiquetaAnio(mapa.anios[mapa.anios.length - 1], mapa)}`,
                node: <Celda valor={actual} parcial={mapa.anio_parcial === mapa.anios[mapa.anios.length - 1]} />,
              },
              { label: `Δ ${a}→${b}`, node: <Variacion valor={proceso.variaciones[`${a}-${b}`]} /> },
              {
                label: `Δ ${b}→${c}${mapa.anio_parcial === c ? " (parcial)" : ""}`,
                node: <Variacion valor={proceso.variaciones[`${b}-${c}`]} />,
              },
              { label: "Indicadores · en riesgo", node: `${proceso.n_indicadores} · ${proceso.en_riesgo}` },
            ].map((k) => (
              <div key={k.label} className="rounded-xl border border-slate-200 bg-white p-3">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{k.label}</p>
                <p className="mt-1 text-lg font-bold text-slate-900">{k.node}</p>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="mb-2 text-sm font-semibold text-slate-700">
              Tendencia de cumplimiento {mapa.anios[0]}–{mapa.anios[mapa.anios.length - 1]}
            </p>
            <TendenciaGrande serie={proceso.anios} mapa={mapa} />
            {mapa.anio_parcial && (
              <p className="mt-1 text-[11px] text-slate-500">
                {mapa.anio_parcial} es parcial: cada indicador aporta su último reporte disponible; el trazo
                punteado y el punto vacío lo indican.
              </p>
            )}
          </div>

          <div>
            <p className="mb-2 text-sm font-semibold text-slate-700">
              {esNivelUnico(proceso) ? "Indicadores asociados" : `Subprocesos (${proceso.subprocesos.length})`}
            </p>
            <div className="space-y-3">
              {proceso.subprocesos.map((s) => (
                <Subficha key={s.subproceso} sub={s} mapa={mapa} onOpenFicha={onOpenFicha} />
              ))}
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}

export function CmiProcesosMapaTab({ mapa, onOpenFicha }: MapaProps) {
  const [busqueda, setBusqueda] = useState("");
  const [tipo, setTipo] = useState("Todos");
  const [abiertos, setAbiertos] = useState<Set<string>>(new Set());
  const [seleccion, setSeleccion] = useState<string | null>(null);

  const tipos = useMemo(
    () => ["Todos", ...Array.from(new Set(mapa.procesos.map((p) => p.tipo_proceso).filter(Boolean))).sort()],
    [mapa.procesos],
  );
  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return mapa.procesos.filter(
      (p) =>
        (tipo === "Todos" || p.tipo_proceso === tipo) &&
        (!q ||
          p.proceso.toLowerCase().includes(q) ||
          p.subprocesos.some((s) => s.subproceso.toLowerCase().includes(q))),
    );
  }, [mapa.procesos, busqueda, tipo]);

  const [a, b, c] = mapa.anios.slice(-3);
  const procesoSel = mapa.procesos.find((p) => p.proceso === seleccion) ?? null;
  const alternar = (nombre: string) =>
    setAbiertos((prev) => {
      const next = new Set(prev);
      if (next.has(nombre)) next.delete(nombre);
      else next.add(nombre);
      return next;
    });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="search"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar proceso o subproceso…"
            className="w-64 rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <div className="inline-flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1">
            {tipos.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTipo(t)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
                  tipo === t ? "bg-poli-navy text-white shadow-md" : "text-slate-600 hover:bg-white"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
        <p className="text-xs text-slate-500">
          {filtrados.length} procesos
          {mapa.sin_tipo_calculo > 0 && (
            <span className="ml-2 rounded-full bg-amber-50 px-2 py-0.5 font-semibold text-amber-700">
              {mapa.sin_tipo_calculo} indicadores sin tipo de cálculo
            </span>
          )}
        </p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Proceso / Subproceso</th>
              <th className="px-3 py-3">Tipo</th>
              {mapa.anios.map((anio) => (
                <th key={anio} className="px-3 py-3 text-right">
                  {etiquetaAnio(anio, mapa)}
                </th>
              ))}
              <th className="px-3 py-3">Tendencia</th>
              <th className="px-3 py-3 text-right">
                Δ {a}→{b}
              </th>
              <th className="px-3 py-3 text-right">
                Δ {b}→{c}
                {mapa.anio_parcial === c ? "p" : ""}
              </th>
              <th className="px-3 py-3 text-right">Ind.</th>
              <th className="px-3 py-3 text-right">Riesgo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtrados.map((p) => {
              const unico = esNivelUnico(p);
              const abierto = abiertos.has(p.proceso) || (!!busqueda && !unico);
              return (
                <Fragment key={p.proceso}>
                  <tr className="hover:bg-slate-50">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        {unico ? (
                          <span className="w-4" />
                        ) : (
                          <button
                            type="button"
                            onClick={() => alternar(p.proceso)}
                            aria-expanded={abierto}
                            aria-label={`${abierto ? "Contraer" : "Expandir"} ${p.proceso}`}
                            className="w-4 text-slate-500 hover:text-slate-900"
                          >
                            {abierto ? "▾" : "▸"}
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => setSeleccion(p.proceso)}
                          className="text-left font-semibold text-slate-900 hover:text-blue-700 hover:underline"
                        >
                          {p.proceso}
                        </button>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-600">{p.tipo_proceso}</td>
                    {mapa.anios.map((anio) => (
                      <td key={anio} className="px-3 py-2.5 text-right">
                        <Celda valor={p.anios[String(anio)]} parcial={anio === mapa.anio_parcial} />
                      </td>
                    ))}
                    <td className="px-3 py-2.5">
                      <Sparkline serie={p.anios} anios={mapa.anios} parcial={mapa.anio_parcial} />
                    </td>
                    <td className="px-3 py-2.5 text-right text-xs">
                      <Variacion valor={p.variaciones[`${a}-${b}`]} />
                    </td>
                    <td className="px-3 py-2.5 text-right text-xs">
                      <Variacion valor={p.variaciones[`${b}-${c}`]} />
                    </td>
                    <td className="px-3 py-2.5 text-right">{p.n_indicadores}</td>
                    <td className="px-3 py-2.5 text-right text-amber-700">{p.en_riesgo}</td>
                  </tr>
                  {abierto &&
                    !unico &&
                    p.subprocesos.map((s) => (
                      <tr key={`${p.proceso}|${s.subproceso}`} className="bg-slate-50/60">
                        <td className="py-2 pl-12 pr-4 text-slate-700">{s.subproceso}</td>
                        <td />
                        {mapa.anios.map((anio) => (
                          <td key={anio} className="px-3 py-2 text-right">
                            <Celda valor={s.anios[String(anio)]} parcial={anio === mapa.anio_parcial} />
                          </td>
                        ))}
                        <td className="px-3 py-2">
                          <Sparkline serie={s.anios} anios={mapa.anios} parcial={mapa.anio_parcial} />
                        </td>
                        <td className="px-3 py-2 text-right text-xs">
                          <Variacion valor={s.variaciones[`${a}-${b}`]} />
                        </td>
                        <td className="px-3 py-2 text-right text-xs">
                          <Variacion valor={s.variaciones[`${b}-${c}`]} />
                        </td>
                        <td className="px-3 py-2 text-right">{s.n_indicadores}</td>
                        <td className="px-3 py-2 text-right text-amber-700">{s.en_riesgo}</td>
                      </tr>
                    ))}
                </Fragment>
              );
            })}
            {filtrados.length === 0 && (
              <tr>
                <td colSpan={mapa.anios.length + 7} className="px-4 py-8 text-center text-sm text-slate-500">
                  No hay procesos para la búsqueda.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-slate-500">
        El cumplimiento anual de cada indicador sigue su tipo de cálculo del catálogo (Cierre, Promedio o
        Acumulado) y es un cierre final por año; subprocesos y procesos promedian sus indicadores. Δ en puntos porcentuales.
        {mapa.anio_parcial
          ? ` ${mapa.anio_parcial} es parcial: cada indicador usa su último reporte disponible (mensual, bimestral, trimestral o semestral), calculado con los registros del año; su corte aparece en la ficha.`
          : ""}
      </p>

      {procesoSel && (
        <FichaProceso
          proceso={procesoSel}
          mapa={mapa}
          onClose={() => setSeleccion(null)}
          onOpenFicha={onOpenFicha}
        />
      )}
    </div>
  );
}
