"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { descargarBorradoresPendientes, fetchAlertasNotificaciones } from "@/lib/api";
import type { BorradoresDescarga } from "@/lib/types";
import { corteNombre, errorMessage } from "./constants";

/** Aviso de que el programador dejó borradores listos para revisar y enviar desde Outlook. */
export function BorradoresListos({ enabled }: { enabled: boolean }) {
  const qc = useQueryClient();
  const [descargado, setDescargado] = useState<BorradoresDescarga | null>(null);

  const noti = useQuery({
    queryKey: ["alertas-notificaciones"],
    queryFn: fetchAlertasNotificaciones,
    enabled,
    refetchInterval: 5 * 60 * 1000,
  });

  const descargar = useMutation({
    mutationFn: descargarBorradoresPendientes,
    onSuccess: (r) => {
      setDescargado(r);
      qc.invalidateQueries({ queryKey: ["alertas-notificaciones"] });
      qc.invalidateQueries({ queryKey: ["alertas-historial"] });
    },
  });

  if (descargado) {
    return (
      <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
        Se descargaron {descargado.total} borradores. Ábralos con Outlook: quedan como mensajes sin enviar para que los
        revise y envíe.
        {descargado.sinDestinatarios > 0 && (
          <> {descargado.sinDestinatarios} no tienen destinatarios; agréguelos en Outlook (detalle en LEEME.txt del ZIP).</>
        )}
      </div>
    );
  }

  const listos = noti.data?.listos ?? 0;
  if (listos === 0) return null;

  return (
    <div
      role="status"
      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-poli-blue/30 bg-poli-blue-50 px-4 py-3"
    >
      <div className="text-sm text-slate-800">
        <p className="font-semibold text-poli-navy">
          ✉️ Hay {listos} {listos === 1 ? "borrador listo" : "borradores listos"} para revisar y enviar
        </p>
        <p className="text-xs text-slate-600">
          {noti.data?.items
            .map((i) => `${i.tipo === "apertura" ? "Apertura" : "Recordatorio"} ${corteNombre(i.anio, i.mes)} (${i.borradores})`)
            .join(" · ")}
        </p>
        {descargar.isError && <p className="mt-1 text-xs text-red-700">{errorMessage(descargar.error)}</p>}
      </div>
      <button
        type="button"
        disabled={descargar.isPending}
        onClick={() => descargar.mutate()}
        className="rounded-lg bg-poli-blue px-4 py-2 text-sm font-semibold text-white hover:bg-poli-blue-dark disabled:opacity-50"
      >
        {descargar.isPending ? "Preparando…" : "Descargar borradores (.eml)"}
      </button>
    </div>
  );
}
