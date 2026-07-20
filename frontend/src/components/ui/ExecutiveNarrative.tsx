export interface ExecutiveNarrativeData {
  texto: string;
  estado_color: string;
  estado_icon: string;
  health_rate?: number;
}

export function ExecutiveNarrative({ data }: { data: ExecutiveNarrativeData }) {
  const texto = data?.texto ?? "";
  const estadoColor = data?.estado_color ?? "#0B5FFF";

  return (
    <div
      className="rounded-xl border bg-gradient-to-br from-white to-blue-50 p-5 shadow-sm"
      style={{ borderLeftWidth: 6, borderLeftColor: estadoColor }}
    >
      <p
        className="text-sm leading-relaxed text-slate-700"
        dangerouslySetInnerHTML={{ __html: texto }}
      />
    </div>
  );
}
