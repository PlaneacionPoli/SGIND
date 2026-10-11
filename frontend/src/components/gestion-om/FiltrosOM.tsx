"use client";

import { Search, X } from "lucide-react";
import { MESES, MESES_CORTO } from "@/components/seguimiento/constants";

export interface FiltrosOMState {
  /** `null` mientras el servidor resuelve el corte más reciente. */
  anio: number | null;
  mes: string | null;
  proceso: string;
  subproceso: string;
  mostrarAlerta: boolean;
  busqueda: string;
}

interface Props {
  anios: string[];
  mesesPorAnio?: Record<string, string[]>;
  procesos: string[];
  subprocesos: string[];
  valor: FiltrosOMState;
  onChange: (cambio: Partial<FiltrosOMState>) => void;
  onLimpiar: () => void;
}

function Chip({ activo, onClick, children, disabled, title }: { activo: boolean; onClick: () => void; children: React.ReactNode; disabled?: boolean; title?: string }) {
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

const SELECT = "h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-800";

export function FiltrosOM({ anios, mesesPorAnio, procesos, subprocesos, valor, onChange, onLimpiar }: Props) {
  const activos: Array<{ clave: string; texto: string; quitar: () => void }> = [];
  if (valor.proceso !== "Todos") activos.push({ clave: "proceso", texto: valor.proceso, quitar: () => onChange({ proceso: "Todos" }) });
  if (valor.subproceso !== "Todos") activos.push({ clave: "sub", texto: valor.subproceso, quitar: () => onChange({ subproceso: "Todos" }) });
  if (valor.busqueda) activos.push({ clave: "q", texto: `«${valor.busqueda}»`, quitar: () => onChange({ busqueda: "" }) });

  return (
    <section aria-label="Filtros" className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card">
      <div className="grid gap-5 lg:grid-cols-[auto_1fr]">
        <div>
          <Etiqueta>Año</Etiqueta>
          <div className="flex flex-wrap gap-1.5">
            {anios.map((y) => (
              <Chip
                key={y}
                activo={String(valor.anio) === String(y)}
                onClick={() => {
                  const disponibles = mesesPorAnio?.[String(y)];
                  // Si el mes elegido no tiene datos en ese año, se pasa al último que sí.
                  const mes = disponibles?.length && valor.mes && !disponibles.includes(valor.mes) ? disponibles[disponibles.length - 1] : valor.mes;
                  onChange({ anio: Number(y), mes });
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
            {MESES_CORTO.map((nombre, i) => {
              const disponibles = valor.anio != null ? mesesPorAnio?.[String(valor.anio)] : undefined;
              const hay = !disponibles || disponibles.includes(MESES[i]);
              return (
                <Chip key={nombre} activo={valor.mes === MESES[i]} disabled={!hay} title={hay ? undefined : "Sin indicadores evaluados en este mes"} onClick={() => onChange({ mes: MESES[i] })}>
                  {nombre}
                </Chip>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-4 border-t border-slate-100 pt-5 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1.2fr_auto]">
        <div>
          <Etiqueta>Proceso</Etiqueta>
          <select aria-label="Proceso" value={valor.proceso} onChange={(e) => onChange({ proceso: e.target.value })} className={SELECT}>
            <option value="Todos">Todos los procesos</option>
            {procesos.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Etiqueta>Subproceso</Etiqueta>
          <select aria-label="Subproceso" value={valor.subproceso} onChange={(e) => onChange({ subproceso: e.target.value })} className={SELECT}>
            <option value="Todos">Todos los subprocesos</option>
            {subprocesos.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Etiqueta>Buscar</Etiqueta>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
            <input
              type="search"
              aria-label="Buscar indicador"
              value={valor.busqueda}
              onChange={(e) => onChange({ busqueda: e.target.value })}
              placeholder="Id, indicador, proceso u OM…"
              className="h-9 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-800 placeholder:text-slate-400"
            />
          </div>
        </div>
        <div>
          <Etiqueta>Incluir</Etiqueta>
          <button
            type="button"
            role="switch"
            aria-checked={valor.mostrarAlerta}
            onClick={() => onChange({ mostrarAlerta: !valor.mostrarAlerta })}
            className="flex h-9 items-center gap-2 rounded-lg px-1 text-sm font-medium text-slate-700"
          >
            <span className={`relative h-5 w-9 rounded-full transition ${valor.mostrarAlerta ? "bg-amber-500" : "bg-slate-300"}`}>
              <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${valor.mostrarAlerta ? "left-[18px]" : "left-0.5"}`} />
            </span>
            También en Alerta
          </button>
        </div>
      </div>

      {activos.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4">
          <span className="text-xs text-slate-500">Filtros activos:</span>
          {activos.map((a) => (
            <button
              key={a.clave}
              type="button"
              onClick={a.quitar}
              aria-label={`Quitar filtro ${a.texto}`}
              className="inline-flex items-center gap-1 rounded-full bg-poli-navy-50 px-2.5 py-1 text-xs font-medium text-poli-navy hover:bg-slate-200"
            >
              {a.texto}
              <X className="h-3 w-3" aria-hidden />
            </button>
          ))}
          <button type="button" onClick={onLimpiar} className="text-xs font-semibold text-slate-500 underline-offset-2 hover:underline">
            Limpiar todo
          </button>
        </div>
      )}
    </section>
  );
}
