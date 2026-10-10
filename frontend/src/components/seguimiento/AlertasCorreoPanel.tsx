"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  descargarBorradorProceso,
  descargarBorradores,
  descargarListadoOutlook,
  fetchAlertasConfig,
  fetchAlertasHistorial,
  fetchAlertasVistaPrevia,
  updateAlertasConfig,
  updateAlertasDestinatarios,
  updateAlertasPlazo,
} from "@/lib/api";
import type { AlertaConfig, BorradoresDescarga, TipoAlerta } from "@/lib/types";
import { MESES, corteNombre, errorMessage } from "./constants";

type Form = Omit<AlertaConfig, "updated_by" | "updated_at">;

const TIPO_LABEL: Record<TipoAlerta, string> = {
  recordatorio: "Recordatorio (antes de la fecha límite)",
  apertura: "Apertura (días 1 a 3 del mes)",
};

function Card({ titulo, ayuda, children }: { titulo: string; ayuda?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-base font-bold text-slate-900">{titulo}</h3>
      {ayuda && <p className="mt-0.5 text-xs text-slate-500">{ayuda}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Aviso({ tipo, children }: { tipo: "ok" | "error" | "info"; children: React.ReactNode }) {
  const c = {
    ok: "border-emerald-200 bg-emerald-50 text-emerald-800",
    error: "border-red-200 bg-red-50 text-red-800",
    info: "border-amber-200 bg-amber-50 text-amber-900",
  }[tipo];
  return (
    <div role={tipo === "error" ? "alert" : "status"} className={`rounded-lg border px-3 py-2 text-sm ${c}`}>
      {children}
    </div>
  );
}

function fechaCorta(iso: string | null) {
  return iso ? new Date(iso).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) : "—";
}

const fmtFecha = (d: Date) => d.toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });

function TipoSelector({ value, onChange }: { value: TipoAlerta; onChange: (t: TipoAlerta) => void }) {
  return (
    <div className="inline-flex rounded-lg bg-slate-100 p-1" role="tablist">
      {(Object.keys(TIPO_LABEL) as TipoAlerta[]).map((t) => (
        <button
          key={t}
          type="button"
          role="tab"
          aria-selected={value === t}
          onClick={() => onChange(t)}
          className={`rounded-md px-3 py-1.5 text-sm font-semibold transition ${
            value === t ? "bg-white text-poli-navy shadow-sm" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          {TIPO_LABEL[t]}
        </button>
      ))}
    </div>
  );
}

export function AlertasCorreoPanel() {
  const qc = useQueryClient();
  const config = useQuery({ queryKey: ["alertas-config"], queryFn: fetchAlertasConfig });
  const historial = useQuery({ queryKey: ["alertas-historial"], queryFn: fetchAlertasHistorial });

  const [form, setForm] = useState<Form | null>(null);
  const [guardado, setGuardado] = useState(false);
  const [tipoMensaje, setTipoMensaje] = useState<TipoAlerta>("recordatorio");
  const cuerpoRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (config.data && form === null) {
      const { updated_by, updated_at, ...resto } = config.data.config;
      void updated_by;
      void updated_at;
      setForm(resto);
    }
  }, [config.data, form]);

  const guardar = useMutation({
    mutationFn: updateAlertasConfig,
    onSuccess: () => {
      setGuardado(true);
      qc.invalidateQueries({ queryKey: ["alertas-config"] });
      qc.invalidateQueries({ queryKey: ["alertas-vista-previa"] });
    },
  });

  if (config.isLoading || !form) return <div className="h-40 animate-pulse rounded-lg bg-slate-200" />;
  if (config.isError || !config.data) {
    return (
      <Aviso tipo="error">
        No se pudo cargar la configuración: {errorMessage(config.error)}. ¿Se aplicó la migración 005?
      </Aviso>
    );
  }

  const cfg = config.data;
  const { anio: anioProx, mes: mesProx } = cfg.proximo_corte;
  const limite = new Date(`${cfg.proximo_corte.fecha_limite}T00:00:00`);
  const aviso = new Date(limite);
  aviso.setDate(aviso.getDate() - form.dias_antes);

  const set = <K extends keyof Form>(k: K, v: Form[K]) => {
    setGuardado(false);
    setForm((f) => (f ? { ...f, [k]: v } : f));
  };

  const campoAsunto = tipoMensaje === "apertura" ? "apertura_asunto" : "asunto";
  const campoCuerpo = tipoMensaje === "apertura" ? "apertura_cuerpo" : "cuerpo";

  const insertarMarca = (marca: string) => {
    const el = cuerpoRef.current;
    const actual = form[campoCuerpo];
    const pos = el?.selectionStart ?? actual.length;
    const fin = el?.selectionEnd ?? pos;
    set(campoCuerpo, `${actual.slice(0, pos)}{${marca}}${actual.slice(fin)}`);
    requestAnimationFrame(() => {
      el?.focus();
      el?.setSelectionRange(pos + marca.length + 2, pos + marca.length + 2);
    });
  };

  return (
    <div className="space-y-6">
      <Aviso tipo="info">
        <strong>Esta sección no envía correos.</strong> Prepara borradores (.eml) con la tabla de indicadores de cada
        proceso. Al abrirlos con Outlook quedan como mensajes sin enviar: revíselos y envíelos usted.
        {!cfg.scheduler_activo && (
          <>
            {" "}
            La preparación automática está apagada en el servidor (ALERTAS_SCHEDULER_ENABLED); mientras tanto use
            «Generar borradores».
          </>
        )}
      </Aviso>

      <Card
        titulo="1. Cuándo se preparan los borradores"
        ayuda="El programador deja los borradores listos y la app le avisa; cada proceso aparece una sola vez por corte y tipo."
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 sm:col-span-2">
            <input type="checkbox" checked={form.activo} onChange={(e) => set("activo", e.target.checked)} className="h-4 w-4" />
            <span className="text-sm font-semibold text-slate-800">Preparación automática</span>
            <span className="text-xs text-slate-500">{form.activo ? "Activa" : "Pausada"}</span>
          </label>
          <label className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 sm:col-span-2">
            <input
              type="checkbox"
              checked={form.apertura_activo}
              onChange={(e) => set("apertura_activo", e.target.checked)}
              className="h-4 w-4"
            />
            <span className="text-sm font-semibold text-slate-800">Aviso de apertura a todos los procesos</span>
          </label>
          <NumberField label="Recordatorio: días antes de la fecha límite" value={form.dias_antes} min={0} max={60} onChange={(v) => set("dias_antes", v)} />
          <NumberField label="Plazo general: día del mes siguiente (15; 13 si aplica)" value={form.plazo_dias} min={0} max={120} onChange={(v) => set("plazo_dias", v)} />
          <NumberField label="Apertura: hasta el día … del mes" value={form.apertura_dias} min={1} max={10} onChange={(v) => set("apertura_dias", v)} />
          <NumberField label="Hora de preparación (Bogotá, 0-23)" value={form.hora_envio} min={0} max={23} onChange={(v) => set("hora_envio", v)} />
          <label className="block sm:col-span-2 lg:col-span-4">
            <span className="mb-1 block text-xs text-slate-600">Con copia a (opcional, separe por coma)</span>
            <input
              value={form.copia_a}
              onChange={(e) => set("copia_a", e.target.value)}
              placeholder="desempeno@poligran.edu.co"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>
        </div>
        <p className="mt-4 rounded-lg bg-poli-blue-50 px-3 py-2 text-sm text-slate-700">
          <strong>Ejemplo con el plazo general guardado ({cfg.config.plazo_dias} días):</strong> el corte{" "}
          {corteNombre(anioProx, mesProx)} se reporta hasta el {fmtFecha(limite)} (si cae en fin de semana o festivo, se corre al día hábil anterior); el recordatorio queda listo desde el {fmtFecha(aviso)}. La apertura queda lista los días 1 a{" "}
          {form.apertura_dias} de cada mes con el corte recién cerrado. Los procesos con plazo propio (tabla 4) usan el suyo.
        </p>
      </Card>

      <Card
        titulo="2. Mensaje"
        ayuda="Cuerpo en HTML. Toque una variable para insertarla donde está el cursor; {tabla_html} inserta la tabla con ID, nombre del indicador, subproceso y frecuencia."
      >
        <div className="space-y-3">
          <TipoSelector value={tipoMensaje} onChange={setTipoMensaje} />
          <label className="block">
            <span className="mb-1 block text-xs text-slate-600">Asunto</span>
            <input
              value={form[campoAsunto]}
              onChange={(e) => set(campoAsunto, e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs text-slate-600">Cuerpo (HTML)</span>
            <textarea
              ref={cuerpoRef}
              value={form[campoCuerpo]}
              onChange={(e) => set(campoCuerpo, e.target.value)}
              rows={14}
              spellCheck={false}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            {Object.entries(cfg.placeholders).map(([k, desc]) => (
              <button
                key={k}
                type="button"
                title={desc}
                onClick={() => insertarMarca(k)}
                className="rounded-full bg-slate-100 px-3 py-1 font-mono text-xs text-slate-700 hover:bg-slate-200"
              >
                {`{${k}}`}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            disabled={guardar.isPending}
            onClick={() => guardar.mutate(form)}
            className="rounded-lg bg-poli-navy px-4 py-2 text-sm font-semibold text-white hover:bg-poli-navy-700 disabled:opacity-50"
          >
            {guardar.isPending ? "Guardando…" : "Guardar parámetros y mensajes"}
          </button>
          {guardado && <span className="text-sm text-emerald-700">✔ Guardado</span>}
          {guardar.isError && <span className="text-sm text-red-700">{errorMessage(guardar.error)}</span>}
        </div>
      </Card>

      <VistaPrevia procesos={cfg.procesos} proximoCorte={cfg.proximo_corte} destinatarios={cfg.destinatarios} />

      <DestinatariosYPlazos
        procesos={cfg.procesos}
        destinatarios={cfg.destinatarios}
        origen={cfg.origen_destinatarios}
        plazos={cfg.plazos}
        plazoGeneral={form.plazo_dias}
      />

      <GenerarBorradores proximoCorte={cfg.proximo_corte} />

      <Card titulo="6. Historial" ayuda="Últimos 50 registros: borradores preparados por el programador o descargados.">
        {historial.data && historial.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-2 py-1">Fecha</th>
                  <th className="px-2 py-1">Proceso</th>
                  <th className="px-2 py-1">Tipo</th>
                  <th className="px-2 py-1">Corte</th>
                  <th className="px-2 py-1">Estado</th>
                  <th className="px-2 py-1">Origen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {historial.data.map((e) => (
                  <tr key={e.id}>
                    <td className="whitespace-nowrap px-2 py-1.5">{fechaCorta(e.enviado_at)}</td>
                    <td className="px-2 py-1.5">{e.proceso}</td>
                    <td className="px-2 py-1.5 capitalize">{e.tipo}</td>
                    <td className="whitespace-nowrap px-2 py-1.5">{corteNombre(e.anio, e.mes)}</td>
                    <td className="px-2 py-1.5">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${
                          e.estado === "listo"
                            ? "bg-amber-50 text-amber-800 ring-amber-200"
                            : "bg-emerald-50 text-emerald-800 ring-emerald-200"
                        }`}
                      >
                        {e.estado === "listo" ? "listo para descargar" : "descargado"}
                      </span>
                    </td>
                    <td className="px-2 py-1.5 text-xs text-slate-500">{e.origen}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Aún no hay borradores registrados.</p>
        )}
      </Card>
    </div>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-slate-600">{label}</span>
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Math.min(max, Math.max(min, Number(e.target.value) || 0)))}
        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
      />
    </label>
  );
}

function CortePicker({ anio, mes, onChange }: { anio: number; mes: number; onChange: (anio: number, mes: number) => void }) {
  return (
    <div className="flex gap-2">
      <select
        value={mes}
        onChange={(e) => onChange(anio, Number(e.target.value))}
        className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
        aria-label="Mes del corte"
      >
        {MESES.map((m, i) => (
          <option key={m} value={i + 1}>
            {m}
          </option>
        ))}
      </select>
      <select
        value={anio}
        onChange={(e) => onChange(Number(e.target.value), mes)}
        className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
        aria-label="Año del corte"
      >
        {[anio - 1, anio, anio + 1].map((a) => (
          <option key={a} value={a}>
            {a}
          </option>
        ))}
      </select>
    </div>
  );
}

function VistaPrevia({
  procesos,
  proximoCorte,
  destinatarios,
}: {
  procesos: string[];
  proximoCorte: { anio: number; mes: number };
  destinatarios: Record<string, string[]>;
}) {
  const [proceso, setProceso] = useState(procesos[0] ?? "");
  const [tipo, setTipo] = useState<TipoAlerta>("recordatorio");
  const [corte, setCorte] = useState(proximoCorte);

  const preview = useQuery({
    queryKey: ["alertas-vista-previa", proceso, tipo, corte.anio, corte.mes],
    queryFn: () => fetchAlertasVistaPrevia({ proceso, tipo, anio: corte.anio, mes: corte.mes }),
    enabled: Boolean(proceso),
  });

  const descarga = useMutation({
    mutationFn: () => descargarBorradorProceso({ proceso, tipo, anio: corte.anio, mes: corte.mes }),
  });

  return (
    <Card titulo="3. Vista previa" ayuda="Revise cómo quedará el borrador de un proceso y descárguelo para abrirlo en Outlook.">
      <div className="mb-3">
        <TipoSelector value={tipo} onChange={setTipo} />
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <label className="block min-w-[16rem] flex-1">
          <span className="mb-1 block text-xs text-slate-600">Proceso</span>
          <select
            value={proceso}
            onChange={(e) => setProceso(e.target.value)}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
          >
            {procesos.map((p) => (
              <option key={p} value={p}>
                {p}
                {destinatarios[p]?.length ? "" : " (sin destinatarios)"}
              </option>
            ))}
          </select>
        </label>
        <div>
          <span className="mb-1 block text-xs text-slate-600">Corte</span>
          <CortePicker anio={corte.anio} mes={corte.mes} onChange={(anio, mes) => setCorte({ anio, mes })} />
        </div>
        <button
          type="button"
          disabled={!preview.data || preview.data.total_indicadores === 0 || descarga.isPending}
          onClick={() => descarga.mutate()}
          className="rounded-lg border border-poli-navy px-4 py-2 text-sm font-semibold text-poli-navy hover:bg-poli-navy-50 disabled:opacity-50"
        >
          {descarga.isPending ? "Descargando…" : "Descargar borrador (.eml)"}
        </button>
      </div>
      {descarga.isError && (
        <div className="mt-3">
          <Aviso tipo="error">{errorMessage(descarga.error)}</Aviso>
        </div>
      )}

      <div className="mt-4 rounded-lg border border-slate-200">
        {preview.isLoading ? (
          <div className="h-32 animate-pulse bg-slate-100" />
        ) : preview.data ? (
          <>
            <div className="border-b border-slate-200 bg-slate-50 px-4 py-2 text-sm">
              <span className="text-slate-500">Asunto: </span>
              <strong>{preview.data.asunto}</strong>
              <span className="ml-3 text-xs text-slate-500">
                {preview.data.total_indicadores} indicadores · plazo {preview.data.plazo_dias} días · límite{" "}
                {fmtFecha(new Date(`${preview.data.fecha_limite}T00:00:00`))}
              </span>
            </div>
            {preview.data.total_indicadores === 0 && (
              <p className="p-4 text-sm text-slate-500">
                Este proceso no tiene indicadores por reportar en {corteNombre(corte.anio, corte.mes)}.
              </p>
            )}
            <iframe title="Vista previa del correo" sandbox="" srcDoc={preview.data.html} className="h-96 w-full bg-white" />
          </>
        ) : (
          <p className="p-4 text-sm text-red-700">{errorMessage(preview.error)}</p>
        )}
      </div>
    </Card>
  );
}

function DestinatariosYPlazos({
  procesos,
  destinatarios,
  origen,
  plazos,
  plazoGeneral,
}: {
  procesos: string[];
  destinatarios: Record<string, string[]>;
  origen: Record<string, "directorio" | "manual">;
  plazos: Record<string, number>;
  plazoGeneral: number;
}) {
  const qc = useQueryClient();
  const [correos, setCorreos] = useState<Record<string, string>>({});
  const [plazosBorrador, setPlazosBorrador] = useState<Record<string, string>>({});
  const [busqueda, setBusqueda] = useState("");
  const [soloSin, setSoloSin] = useState(false);
  const [errores, setErrores] = useState<Record<string, string>>({});

  const guardar = useMutation({
    mutationFn: async (v: { proceso: string; emails?: string[]; plazo?: number | null }) => {
      if (v.emails) await updateAlertasDestinatarios({ proceso: v.proceso, emails: v.emails });
      if (v.plazo !== undefined) await updateAlertasPlazo({ proceso: v.proceso, plazo_dias: v.plazo });
    },
    onSuccess: (_d, v) => {
      const sinClave = (o: Record<string, string>) =>
        Object.fromEntries(Object.entries(o).filter(([k]) => k !== v.proceso));
      setCorreos(sinClave);
      setPlazosBorrador(sinClave);
      setErrores(sinClave);
      qc.invalidateQueries({ queryKey: ["alertas-config"] });
      qc.invalidateQueries({ queryKey: ["alertas-vista-previa"] });
    },
    onError: (e, v) => setErrores((prev) => ({ ...prev, [v.proceso]: errorMessage(e) })),
  });

  const sinDestinatarios = procesos.filter((p) => !destinatarios[p]?.length).length;
  const visibles = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return procesos.filter((p) => (!q || p.toLowerCase().includes(q)) && (!soloSin || !destinatarios[p]?.length));
  }, [procesos, destinatarios, busqueda, soloSin]);

  return (
    <Card
      titulo="4. Destinatarios y plazo por proceso"
      ayuda={`Los correos salen del directorio institucional (Correos.xlsx) y van en «Para» del borrador. Si los edita aquí, lo editado reemplaza al directorio; vacíe el campo y guarde para volver al directorio. El plazo propio reemplaza al general (${plazoGeneral} días); déjelo vacío para usar el general.`}
    >
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <input
          type="search"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar proceso…"
          className="w-60 rounded-lg border border-slate-200 px-3 py-1.5 text-sm"
        />
        <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" checked={soloSin} onChange={(e) => setSoloSin(e.target.checked)} className="h-4 w-4" />
          Solo sin destinatarios ({sinDestinatarios})
        </label>
      </div>
      <ul className="divide-y divide-slate-100">
        {visibles.map((p) => {
          const correosActual = (destinatarios[p] ?? []).join(", ");
          const correosValor = correos[p] ?? correosActual;
          const plazoActual = plazos[p] !== undefined ? String(plazos[p]) : "";
          const plazoValor = plazosBorrador[p] ?? plazoActual;
          const sucioCorreos = correosValor !== correosActual;
          const sucioPlazo = plazoValor !== plazoActual;
          return (
            <li key={p} className="grid gap-2 py-2.5 md:grid-cols-[minmax(0,1fr)_6rem_minmax(0,1.4fr)_auto] md:items-center">
              <span className="text-sm font-medium text-slate-800">
                {p}
                {!correosActual ? (
                  <span className="ml-2 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-800 ring-1 ring-inset ring-amber-200">
                    sin destinatarios
                  </span>
                ) : (
                  <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600 ring-1 ring-inset ring-slate-200">
                    {origen[p] === "manual" ? "editado" : "directorio"}
                  </span>
                )}
              </span>
              <input
                type="number"
                min={0}
                max={120}
                value={plazoValor}
                onChange={(e) => setPlazosBorrador((b) => ({ ...b, [p]: e.target.value }))}
                placeholder={`${plazoGeneral} (general)`}
                aria-label={`Plazo en días de ${p}`}
                className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm"
              />
              <div>
                <input
                  value={correosValor}
                  onChange={(e) => setCorreos((b) => ({ ...b, [p]: e.target.value }))}
                  placeholder="responsable@poligran.edu.co, otro@poligran.edu.co"
                  aria-label={`Destinatarios de ${p}`}
                  className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm"
                />
                {errores[p] && <p className="mt-1 text-xs text-red-700">{errores[p]}</p>}
              </div>
              <button
                type="button"
                disabled={(!sucioCorreos && !sucioPlazo) || guardar.isPending}
                onClick={() =>
                  guardar.mutate({
                    proceso: p,
                    ...(sucioCorreos ? { emails: correosValor.split(/[,;\s]+/).filter(Boolean) } : {}),
                    ...(sucioPlazo ? { plazo: plazoValor === "" ? null : Number(plazoValor) } : {}),
                  })
                }
                className="rounded-lg bg-poli-navy px-3 py-1.5 text-xs font-semibold text-white hover:bg-poli-navy-700 disabled:opacity-30"
              >
                Guardar
              </button>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

function GenerarBorradores({ proximoCorte }: { proximoCorte: { anio: number; mes: number } }) {
  const qc = useQueryClient();
  const [tipo, setTipo] = useState<TipoAlerta>("recordatorio");
  const [corte, setCorte] = useState(proximoCorte);
  const [resultado, setResultado] = useState<BorradoresDescarga | null>(null);

  const listado = useMutation({
    mutationFn: () => descargarListadoOutlook({ tipo, anio: corte.anio, mes: corte.mes }),
  });

  const generar = useMutation({
    mutationFn: () => descargarBorradores({ tipo, anio: corte.anio, mes: corte.mes }),
    onSuccess: (r) => {
      setResultado(r);
      qc.invalidateQueries({ queryKey: ["alertas-historial"] });
      qc.invalidateQueries({ queryKey: ["alertas-notificaciones"] });
    },
  });

  return (
    <Card
      titulo="5. Generar borradores ahora"
      ayuda="Descarga un ZIP con un borrador por proceso que tenga indicadores por reportar en el corte. No espera la fecha programada."
    >
      <div className="mb-3">
        <TipoSelector
          value={tipo}
          onChange={(t) => {
            setTipo(t);
            setResultado(null);
          }}
        />
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <span className="mb-1 block text-xs text-slate-600">Corte</span>
          <CortePicker anio={corte.anio} mes={corte.mes} onChange={(anio, mes) => setCorte({ anio, mes })} />
        </div>
        <button
          type="button"
          disabled={generar.isPending}
          onClick={() => {
            setResultado(null);
            generar.mutate();
          }}
          className="rounded-lg bg-poli-blue px-4 py-2 text-sm font-semibold text-white hover:bg-poli-blue-dark disabled:opacity-50"
        >
          {generar.isPending ? "Generando…" : "Generar y descargar ZIP"}
        </button>
        <button
          type="button"
          disabled={listado.isPending}
          onClick={() => listado.mutate()}
          title="Excel con las hojas Indicadores y Destinatarios que lee Auto_Correo para crear los borradores directamente en Outlook"
          className="rounded-lg border border-poli-navy px-4 py-2 text-sm font-semibold text-poli-navy hover:bg-poli-navy-50 disabled:opacity-50"
        >
          {listado.isPending ? "Preparando…" : "Listado para Auto_Correo (Outlook)"}
        </button>
      </div>
      {listado.isError && (
        <div className="mt-3">
          <Aviso tipo="error">{errorMessage(listado.error)}</Aviso>
        </div>
      )}
      {generar.isError && (
        <div className="mt-3">
          <Aviso tipo="error">{errorMessage(generar.error)}</Aviso>
        </div>
      )}
      {resultado && (
        <div className="mt-3">
          <Aviso tipo="ok">
            {resultado.total} borradores listos para revisar y enviar ({corteNombre(corte.anio, corte.mes)}). Ábralos con
            Outlook: quedan como mensajes sin enviar.
            {resultado.sinDestinatarios > 0 && <> {resultado.sinDestinatarios} no tienen destinatarios (ver LEEME.txt).</>}
          </Aviso>
        </div>
      )}
    </Card>
  );
}
