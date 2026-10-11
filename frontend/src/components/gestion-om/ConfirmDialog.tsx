"use client";

import { useEffect, useRef } from "react";

interface Props {
  titulo: string;
  mensaje: string;
  confirmar: string;
  /** `peligro` para acciones irreversibles (botón rojo). */
  tono?: "normal" | "peligro";
  cargando?: boolean;
  error?: string | null;
  onConfirmar: () => void;
  onCancelar: () => void;
}

/** Diálogo de confirmación accesible: foco inicial en «Cancelar», Escape cierra. */
export function ConfirmDialog({ titulo, mensaje, confirmar, tono = "normal", cargando = false, error, onConfirmar, onCancelar }: Props) {
  const cancelar = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    cancelar.current?.focus();
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && !cargando && onCancelar();
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [cargando, onCancelar]);

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/50 p-4" onClick={() => !cargando && onCancelar()}>
      <div role="alertdialog" aria-modal="true" aria-labelledby="confirm-titulo" aria-describedby="confirm-mensaje" className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h4 id="confirm-titulo" className="text-base font-bold text-slate-900">
          {titulo}
        </h4>
        <p id="confirm-mensaje" className="mt-2 text-sm leading-relaxed text-slate-600">
          {mensaje}
        </p>
        {error && (
          <p role="alert" className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </p>
        )}
        <div className="mt-5 flex justify-end gap-2">
          <button ref={cancelar} type="button" onClick={onCancelar} disabled={cargando} className="h-9 rounded-lg border border-slate-300 px-4 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50">
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            disabled={cargando}
            className={`h-9 rounded-lg px-4 text-sm font-semibold text-white disabled:opacity-50 ${tono === "peligro" ? "bg-rose-600 hover:bg-rose-700" : "bg-poli-navy hover:bg-poli-navy/90"}`}
          >
            {cargando ? "Procesando…" : confirmar}
          </button>
        </div>
      </div>
    </div>
  );
}
