interface NarrativaProps {
  titulo: string;
  parrafos: string[];
}

export function NarrativaBlock({ titulo, parrafos }: NarrativaProps) {
  if (!parrafos.length) return null;
  return (
    <div className="rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-poli-navy">{titulo}</h3>
      <div className="mt-3 space-y-2 text-sm leading-relaxed text-slate-700">
        {parrafos.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </div>
    </div>
  );
}
