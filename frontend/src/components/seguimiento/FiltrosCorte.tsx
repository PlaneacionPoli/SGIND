"use client";

import { Calendar, Download, Search, X } from "lucide-react";
import type { SeguimientoFiltros } from "@/lib/types";
import { COLOR, ESTADO_STYLE, MESES_CORTO } from "./constants";

export interface FiltrosState {
  anio: number | null;
  anioTodos: boolean;
  mes: number | null;
  proceso: string;
  estado: string;
  busqueda: string;
}

interface Props {
  filtros: SeguimientoFiltros;
  valor: FiltrosState;
  onChange: (cambio: Partial<FiltrosState>) => void;
  onLimpiar: () => void;
  onExportar: () => void;
  exportando: boolean;
}

const ESTADOS = ["Todos", "Reportado", "Pendiente", "No aplica"];

function Chip({ activo, disabled, onClick, children, title }: { activo: boolean; disabled?: boolean; onClick: () => void; children: React.ReactNode; title?: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      aria-pressed={activo}
      className={`h-8 rounded-lg px-3 text-xs font-semibold transition ${
        activo
          ? "bg-poli-navy text-white shadow-sm"
          : disabled
            ? "cursor-not-allowed bg-slate-50 text-slate-300"
            : "bg-slate-100 text-slate-600 hover:bg-slate-200"
      }`}
    >
      {children}
    </button>
  );
}

function Etiqueta({ children }: { children: React.ReactNode }) {
  return <p className="mb-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">{children}</p>;
}

export function FiltrosCorte({ filtros, valor, onChange, onLimpiar, onExportar, exportando }: Props) {
  const mesesConDatos = new Set(
    valor.anioTodos || valor.anio == null ? filtros.meses : (filtros.meses_por_anio[String(valor.anio)] ?? []),
  );

  const activos: Array<{ clave: string; texto: string; quitar: () => void }> = [];
  if (valor.proceso !== "Todos") activos.push({ clave: "proceso", texto: valor.proceso, quitar: () => onChange({ proceso: "Todos" }) });
  if (valor.estado !== "Todos") activos.push({ clave: "estado", texto: valor.estado, quitar: () => onChange({ estado: "Todos" }) });
  if (valor.busqueda) activos.push({ clave: "q", texto: `«${valor.busqueda}»`, quitar: () => onChange({ busqueda: "" }) });

  return (
    <section aria-label="Filtros" className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card">
      <div className="grid gap-5 lg:grid-cols-[auto_1fr]">
        <div>
          <Etiqueta>Año</Etiqueta>
          <div className="flex flex-wrap gap-1.5">
            <Chip activo={valor.anioTodos} onClick={() => onChange({ anioTodos: true, mes: null })}>
              Todos
            </Chip>
            {filtros.anios.map((y) => (
              <Chip
                key={y}
                activo={!valor.anioTodos && valor.anio === y}
                onClick={() => {
                  const disponibles = filtros.meses_por_anio[String(y)] ?? [];
                  onChange({
                    anioTodos: false,
                    anio: y,
                    mes: valor.mes != null && !disponibles.includes(valor.mes) ? (disponibles[disponibles.length - 1] ?? null) : valor.mes,
                  });
                }}
              >
                {y}
              </Chip>
            ))}
          </div>
        </div>
        <div className="min-w-0">
          <Etiqueta>Mes del corte</Etiqueta>
          <div className="flex flex-wrap gap-1.5">
            <Chip activo={valor.mes == null} onClick={() => onChange({ mes: null })}>
              Todos
            </Chip>
            {MESES_CORTO.map((nombre, i) => {
              const m = i + 1;
              const hay = mesesConDatos.has(m);
              return (
                <Chip key={m} activo={valor.mes === m} disabled={!hay} title={hay ? undefined : "Sin datos en este año"} onClick={() => onChange({ mes: m })}>
                  {nombre}
                </Chip>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-4 border-t border-slate-100 pt-5 md:grid-cols-2 xl:grid-cols-[minmax(0,1.2fr)_auto_minmax(0,1fr)_auto]">
        <div>
          <Etiqueta>Proceso</Etiqueta>
          <select
            value={valor.proceso}
            onChange={(e) => onChange({ proceso: e.target.value })}
            className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-800"
          >
            <option value="Todos">Todos los procesos</option>
            {filtros.procesos.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Etiqueta>Estado</Etiqueta>
          <div className="flex flex-wrap gap-1.5">
            {ESTADOS.filter((e) => e === "Todos" || filtros.estados.includes(e)).map((e) => (
              <button
                key={e}
                type="button"
                aria-pressed={valor.estado === e}
                onClick={() => onChange({ estado: e })}
                className={`inline-flex h-8 items-center gap-1.5 rounded-lg px-3 text-xs font-semibold transition ${
                  valor.estado === e ? "bg-poli-navy text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {e !== "Todos" && <span className="h-2 w-2 rounded-full" style={{ background: ESTADO_STYLE[e]?.color ?? COLOR.noAplica }} />}
                {e}
              </button>
            ))}
          </div>
        </div>
        <div>
          <Etiqueta>Buscar</Etiqueta>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
            <input
              type="search"
              value={valor.busqueda}
              onChange={(e) => onChange({ busqueda: e.target.value })}
              placeholder="Indicador, proceso o ID…"
              className="h-9 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm"
            />
          </div>
        </div>
        <div className="flex items-end">
          <button
            type="button"
            onClick={onExportar}
            disabled={exportando}
            className="inline-flex h-9 items-center gap-2 rounded-lg bg-poli-navy px-4 text-sm font-semibold text-white shadow-sm hover:bg-poli-navy-700 disabled:opacity-50"
          >
            <Download className="h-4 w-4" aria-hidden />
            {exportando ? "Exportando…" : "Excel"}
          </button>
        </div>
      </div>

      {activos.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4">
          <span className="inline-flex items-center gap-1.5 text-xs text-slate-500">
            <Calendar className="h-3.5 w-3.5" aria-hidden /> Filtros activos:
          </span>
          {activos.map((a) => (
            <span key={a.clave} className="inline-flex items-center gap-1 rounded-full bg-poli-blue-50 py-1 pl-3 pr-1.5 text-xs font-semibold text-poli-blue-dark">
              <span className="max-w-[16rem] truncate">{a.texto}</span>
              <button type="button" onClick={a.quitar} aria-label={`Quitar filtro ${a.texto}`} className="rounded-full p-0.5 hover:bg-poli-blue/10">
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
          <button type="button" onClick={onLimpiar} className="text-xs font-semibold text-slate-500 hover:text-slate-800 hover:underline">
            Limpiar todo
          </button>
        </div>
      )}
    </section>
  );
}
