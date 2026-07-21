import { ReactNode } from "react";
import {
  TrendingUp,
  GraduationCap,
  Zap,
  Leaf,
  Target,
  Shield,
  BarChart3,
} from "lucide-react";
import { Line, LineChart, ResponsiveContainer, Tooltip } from "recharts";

const ICON_MAP: Record<string, ({ size, style, className, strokeWidth }: { size: number; style?: React.CSSProperties; className?: string; strokeWidth?: number }) => ReactNode> = {
  rocket: TrendingUp,
  chart: BarChart3,
  medal: Target,
  bulb: Zap,
  leaf: Leaf,
  graduation: GraduationCap,
  shield: Shield,
};

export interface StrategyCardData {
  linea: string;
  icon: string;
  color: string;
  count: number;
  cumplimiento: number;
  unit_label: string;
  historico: { anio: number; cumplimiento: number }[];
  n_indicadores?: number;
  n_proyectos?: number;
  n_retos?: number;
}

interface StrategyCardProps {
  card: StrategyCardData;
}

function buildDetailParts(card: StrategyCardData): string[] {
  const parts: string[] = [];
  if (card.n_indicadores) parts.push(`Indicadores: ${card.n_indicadores}`);
  if (card.n_proyectos) parts.push(`Proyectos: ${card.n_proyectos}`);
  if (card.n_retos && card.n_retos !== card.count) parts.push(`Retos: ${card.n_retos}`);
  return parts;
}

export function StrategyCard({ card }: StrategyCardProps) {
  const IconComponent = ICON_MAP[card.icon];
  const detailParts = buildDetailParts(card);

  return (
    <div
      className="group relative flex flex-col overflow-hidden rounded-lg p-3 transition-shadow duration-200 hover:shadow-md"
      style={{
        borderLeft: `4px solid ${card.color}`,
        background: `linear-gradient(140deg, #fff, ${card.color}1E)`,
      }}
    >
      <div className="mb-2 flex items-center gap-2.5">
        <div className="shrink-0" style={{ color: card.color }}>
          {IconComponent && <IconComponent size={28} strokeWidth={1.75} />}
        </div>
        <div className="flex-1 text-right">
          <div className="text-[22px] font-bold leading-none" style={{ color: card.color }}>
            {card.cumplimiento.toFixed(1)}%
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            {card.count} {card.unit_label}
          </div>
          {detailParts.length > 0 && (
            <div className="mt-1 text-[11px] text-slate-600">{detailParts.join(" · ")}</div>
          )}
        </div>
      </div>

      <h3 className="mb-2 text-[13px] font-bold leading-tight text-slate-700">{card.linea}</h3>

      {card.historico.length > 0 && (
        <div className="h-10 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={card.historico}>
              <Tooltip
                formatter={((value: number) => [`${Number(value ?? 0).toFixed(1)}%`, "Cumplimiento"]) as never}
                labelFormatter={(anio) => `Año ${anio}`}
                contentStyle={{ fontSize: 12 }}
              />
              <Line
                type="monotone"
                dataKey="cumplimiento"
                stroke={card.color}
                strokeWidth={2}
                dot={{ r: 3, fill: card.color, strokeWidth: 0 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export function StrategyCardGrid({ cards }: { cards: StrategyCardData[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 animate-in fade-in-50 duration-500">
      {cards.map((card, idx) => (
        <div
          key={card.linea}
          style={{
            animation: `fadeInUp 0.5s ease-out ${idx * 0.08}s both`,
          }}
        >
          <StrategyCard card={card} />
        </div>
      ))}
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(15px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
