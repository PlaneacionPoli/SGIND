"use client";

import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { COLOR, tonoCumplimiento } from "@/components/seguimiento/constants";
import type { OMFila, OMHistorialPunto } from "@/lib/types";
import { CATEGORIA_STYLE, PLACEHOLDERS_TIPO_ACCION, TIPOS_ACCION, estadoOM, formatNumero, validarRegistro } from "./utils";

export interface DatosRegistro {
  tipo_accion: string;
  numero_om: string;
  comentario: string;
}

interface Props {
  fila: OMFila;
  periodo: string;
  historial: OMHistorialPunto[];
  pendiente: boolean;
  error: string | null;
  onGuardar: (datos: DatosRegistro) => void;
  onCerrar: () => void;
}

const MAX_OBS = 500;

/** Panel lateral de registro: contexto del indicador a la vista mientras se completa el formulario. */
export function PanelRegistro({ fila, periodo, historial, pendiente, error, onGuardar, onCerrar }: Props) {
  const edicion = fila.om_id != null;
  const [tipo, setTipo] = useState(fila.tipo_accion !== "Sin acción" ? fila.tipo_accion : "OM Kawak");
  const [numero, setNumero] = useState(fila.numero_om ?? "");
  const [obs, setObs] = useState(fila.comentario ?? "");
  const [intento, setIntento] = useState(false);
  const primero = useRef<HTMLInputElement>(null);

  useEffect(() => {
    primero.current?.focus();
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && !pendiente && onCerrar();
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [pendiente, onCerrar]);

  const errorValidacion = validarRegistro(tipo, numero);
  const cat = CATEGORIA_STYLE[fila.categoria] ?? { chip: "bg-slate-100 text-slate-700 ring-slate-200", dot: "bg-slate-400" };
  const tono = tonoCumplimiento(fila.cumplimiento_pct);
  const serie = historial.filter((h) => h.cumplimiento_pct != null);

  const enviar = (e: React.FormEvent) => {
    e.preventDefault();
    setIntento(true);
    if (errorValidacion) return;
    onGuardar({ tipo_accion: tipo, numero_om: numero.trim(), comentario: obs.trim() });
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40" onClick={() => !pendiente && onCerrar()}>
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="registro-titulo"
        className="flex h-full w-full max-w-md flex-col overflow-y-auto bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              {edicion ? (estadoOM(fila) === "cerrada" ? "Reabrir / editar OM" : "Editar OM") : "Registrar OM"} · {periodo}
            </p>
            <h4 id="registro-titulo" className="mt-1 text-base font-bold leading-snug text-slate-900">
              <span className="font-mono text-sm text-slate-500">{fila.id}</span> {fila.indicador}
            </h4>
            <p className="mt-1 text-xs text-slate-500">{[fila.proceso, fila.subproceso !== fila.proceso ? fila.subproceso : null].filter(Boolean).join(" · ")}</p>
          </div>
          <button type="button" aria-label="Cerrar panel" onClick={onCerrar} disabled={pendiente} className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100">
            <X className="h-4 w-4" aria-hidden />
          </button>
        </header>

        <section className="space-y-3 border-b border-slate-100 bg-slate-50/60 px-5 py-4" aria-label="Contexto del indicador">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="rounded-xl bg-white p-2.5 ring-1 ring-slate-200">
              <p className="text-[11px] uppercase tracking-wide text-slate-400">Ejecución</p>
              <p className="text-base font-bold text-slate-900">{formatNumero(fila.ejecucion)}</p>
            </div>
            <div className="rounded-xl bg-white p-2.5 ring-1 ring-slate-200">
              <p className="text-[11px] uppercase tracking-wide text-slate-400">Meta</p>
              <p className="text-base font-bold text-slate-900">{formatNumero(fila.meta)}</p>
            </div>
            <div className="rounded-xl bg-white p-2.5 ring-1 ring-slate-200">
              <p className="text-[11px] uppercase tracking-wide text-slate-400">Cumplimiento</p>
              <p className={`text-base font-bold ${tono.text}`}>{fila.cumplimiento_pct != null ? `${fila.cumplimiento_pct}%` : "—"}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span className={`inline-flex rounded-md px-1.5 py-0.5 font-semibold ring-1 ${cat.chip}`}>{fila.categoria}</span>
            {fila.periodicidad && <span>Periodicidad {fila.periodicidad.toLowerCase()}</span>}
          </div>
          {serie.length >= 2 ? (
            <div className="h-28" role="img" aria-label="Cumplimiento de los últimos periodos">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={serie} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
                  <CartesianGrid stroke={COLOR.rejilla} vertical={false} />
                  <XAxis dataKey="periodo" tick={{ fontSize: 10, fill: COLOR.texto }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: COLOR.texto }} axisLine={false} tickLine={false} width={44} />
                  <ReferenceLine y={100} stroke="#10b981" strokeDasharray="4 3" />
                  <Tooltip formatter={(v) => [`${v}%`, "Cumplimiento"]} />
                  <Line type="monotone" dataKey="cumplimiento_pct" stroke={COLOR.acento} strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-xs text-slate-400">Sin historial suficiente para graficar.</p>
          )}
        </section>

        <form onSubmit={enviar} className="flex flex-1 flex-col gap-4 px-5 py-4" noValidate>
          <fieldset>
            <legend className="mb-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">Tipo de acción</legend>
            <div className="grid grid-cols-2 gap-2">
              {TIPOS_ACCION.map((t) => (
                <label key={t} className={`flex cursor-pointer items-center justify-center rounded-lg border px-2 py-2 text-center text-xs font-semibold transition ${tipo === t ? "border-poli-navy bg-poli-navy text-white" : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}>
                  <input type="radio" name="tipo_accion" value={t} checked={tipo === t} onChange={() => setTipo(t)} className="sr-only" />
                  {t}
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <label htmlFor="om-numero" className="mb-1.5 block text-[11px] font-bold uppercase tracking-wider text-slate-400">
              {PLACEHOLDERS_TIPO_ACCION[tipo] ?? "Identificador"} {tipo === "OM Kawak" && <span className="text-rose-500">*</span>}
            </label>
            <input
              id="om-numero"
              ref={primero}
              value={numero}
              onChange={(e) => setNumero(e.target.value)}
              aria-invalid={intento && !!errorValidacion}
              aria-describedby={intento && errorValidacion ? "om-numero-error" : undefined}
              placeholder={PLACEHOLDERS_TIPO_ACCION[tipo] ?? "Identificador OM"}
              className={`h-10 w-full rounded-lg border px-3 text-sm ${intento && errorValidacion ? "border-rose-400" : "border-slate-200"}`}
            />
            {intento && errorValidacion && (
              <p id="om-numero-error" role="alert" className="mt-1 text-xs text-rose-600">
                {errorValidacion}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="om-obs" className="mb-1.5 block text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Observación
            </label>
            <textarea
              id="om-obs"
              rows={4}
              maxLength={MAX_OBS}
              value={obs}
              onChange={(e) => setObs(e.target.value)}
              placeholder="Describe la situación o la justificación…"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
            <p className="mt-1 text-right text-[11px] text-slate-400">
              {obs.length}/{MAX_OBS}
            </p>
          </div>

          {error && (
            <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {error}
            </p>
          )}

          <div className="mt-auto flex gap-2 border-t border-slate-100 pt-4">
            <button type="submit" disabled={pendiente} className="h-10 flex-1 rounded-lg bg-poli-navy px-4 text-sm font-semibold text-white hover:bg-poli-navy/90 disabled:opacity-50">
              {pendiente ? "Guardando…" : edicion ? "Guardar cambios" : "Asociar OM"}
            </button>
            <button type="button" onClick={onCerrar} disabled={pendiente} className="h-10 rounded-lg border border-slate-300 px-4 text-sm font-medium text-slate-600 hover:bg-slate-50">
              Cancelar
            </button>
          </div>
        </form>
      </aside>
    </div>
  );
}

