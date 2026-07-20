"use client";

export interface CmiDonutNivelItem {
  nivel: string;
  cantidad: number;
  porcentaje: number;
  color: string;
}

interface CmiDonutNivelPlotlyProps {
  data: CmiDonutNivelItem[];
  total: number;
}

const MIN_PCT_LABEL = 8;

export function CmiDonutNivelPlotly({ data, total }: CmiDonutNivelPlotlyProps) {
  if (!data.length) {
    return (
      <div className="flex h-72 items-center justify-center text-sm text-slate-500">
        Sin distribución por nivel
      </div>
    );
  }

  const sum = data.reduce((a, d) => a + d.cantidad, 0) || 1;

  // Construir segmentos SVG (donut)
  const cx = 110;
  const cy = 110;
  const R = 90;
  const r = 52;

  function polarToXY(angleDeg: number, radius: number) {
    const rad = ((angleDeg - 90) * Math.PI) / 180;
    return { x: cx + radius * Math.cos(rad), y: cy + radius * Math.sin(rad) };
  }

  function arcPath(startDeg: number, endDeg: number) {
    const large = endDeg - startDeg > 180 ? 1 : 0;
    const o = polarToXY(startDeg, R);
    const i1 = polarToXY(endDeg, R);
    const o2 = polarToXY(endDeg, r);
    const i2 = polarToXY(startDeg, r);
    return [
      `M ${o.x} ${o.y}`,
      `A ${R} ${R} 0 ${large} 1 ${i1.x} ${i1.y}`,
      `L ${o2.x} ${o2.y}`,
      `A ${r} ${r} 0 ${large} 0 ${i2.x} ${i2.y}`,
      "Z",
    ].join(" ");
  }

  let angle = 0;
  const segments = data.map((d) => {
    const pct = (d.cantidad / sum) * 100;
    const sweep = (pct / 100) * 360;
    const start = angle;
    const end = angle + sweep;
    const mid = start + sweep / 2;
    const labelPos = polarToXY(mid, (R + r) / 2);
    angle = end;
    return { ...d, pct, start, end, mid, labelPos };
  });

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative">
        <svg viewBox="0 0 220 220" className="w-52 h-52">
          {segments.map((seg) => (
            <path
              key={seg.nivel}
              d={arcPath(seg.start, seg.end)}
              fill={seg.color}
              stroke="#fff"
              strokeWidth="2"
            >
              <title>{seg.nivel}: {seg.cantidad} ({seg.pct.toFixed(1)}%)</title>
            </path>
          ))}
          {segments.map((seg) =>
            seg.pct >= MIN_PCT_LABEL ? (
              <text
                key={seg.nivel}
                x={seg.labelPos.x}
                y={seg.labelPos.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="10"
                fontWeight="600"
                fill="#fff"
              >
                {seg.pct.toFixed(1)}%
              </text>
            ) : null,
          )}
          {/* Centro */}
          <circle cx={cx} cy={cy} r={r - 2} fill="#fff" />
          <text x={cx} y={cy - 8} textAnchor="middle" fontSize="22" fontWeight="800" fill="#1A3A5C">
            {total}
          </text>
          <text x={cx} y={cy + 12} textAnchor="middle" fontSize="10" fill="#64748b">
            indicadores
          </text>
        </svg>
      </div>

      {/* Leyenda */}
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5">
        {data.map((d) => (
          <span key={d.nivel} className="flex items-center gap-1.5 text-xs text-slate-700">
            <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: d.color }} />
            {d.nivel}
            <span className="font-semibold text-slate-500">({d.cantidad})</span>
          </span>
        ))}
      </div>
    </div>
  );
}
