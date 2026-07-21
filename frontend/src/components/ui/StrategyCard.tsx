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
      className="group relative flex min-h-[13rem] flex-col overflow-hidden rounded-2xl p-5 shadow-md transition-all duration-300 hover:shadow-2xl hover:scale-[1.02]"
      style={{ background: card.color }}
    >
      <div className="absolute inset-0 bg-black opacity-0 group-hover:opacity-10 transition-opacity duration-300" />

      <div className="relative z-10 flex flex-1 flex-col text-white">
        <div className="flex items-start justify-between gap-2">
          <div className="transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6">
            {IconComponent && <IconComponent size={32} strokeWidth={1.5} />}
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold leading-none">
              {card.cumplimiento.toFixed(1)}%
            </div>
            <div className="mt-1 text-xs text-white/80">
              {card.count} {card.unit_label}
            </div>
          </div>
        </div>

        {detailParts.length > 0 && (
          <p className="mt-2 text-xs text-white/70">{detailParts.join(" · ")}</p>
        )}

        <h3 className="mt-3 text-base font-bold leading-tight">{card.linea}</h3>

        {card.historico.length > 0 && (
          <div className="mt-auto h-12 w-full pt-2">
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
                  stroke="#ffffff"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "#ffffff", strokeWidth: 0 }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-1 bg-white opacity-0 group-hover:opacity-30 transition-opacity duration-300" />
    </div>
  );
}

export function StrategyCardGrid({ cards }: { cards: StrategyCardData[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 animate-in fade-in-50 duration-500">
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
