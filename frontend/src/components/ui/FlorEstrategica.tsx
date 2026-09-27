"use client";

import { useRouter } from "next/navigation";
import { STRATEGIC_LINES } from "@/lib/strategic-lines";

// Réplica fiel de la landing "flor" del proyecto de referencia
// Informe_Interactivo_Poli_2025 (index.html, slide-home): imagen
// lineas-estrategicas.jpg en un contenedor aspect-ratio 721/735, círculo
// blanco + esfera giratoria en el centro medido (cx=374,cy=352,r=105 sobre
// el viewBox 721x735), y 6 elipses clicables por pétalo (coordenadas
// tomadas 1:1 del original). El centro navega de vuelta a Resumen General
// en vez de a una hoja de línea.
const PETALOS: { slug: string; cx: number; cy: number; rx: number; ry: number }[] = [
  { slug: "calidad", cx: 72, cy: 303, rx: 59, ry: 180 },
  { slug: "expansion", cx: 611, cy: 236, rx: 100, ry: 117 },
  { slug: "educacion-para-toda-la-vida", cx: 193, cy: 605, rx: 103, ry: 69 },
  { slug: "experiencia", cx: 594, cy: 487, rx: 95, ry: 105 },
  { slug: "transformacion-organizacional", cx: 462, cy: 656, rx: 86, ry: 200 },
  { slug: "sostenibilidad", cx: 489, cy: 12, rx: 75, ry: 200 },
];

interface FlorEstrategicaProps {
  onSelectLinea: (slug: string) => void;
  onSelectCentro: () => void;
  cumplimientoPorLinea?: Record<string, number>;
}

export function FlorEstrategica({
  onSelectLinea,
  onSelectCentro,
  cumplimientoPorLinea,
}: FlorEstrategicaProps) {
  const router = useRouter();

  return (
    <div className="flor-estrategica mx-auto" style={{ aspectRatio: "721/735", maxWidth: 560 }}>
      <img
        src="/img/brand/lineas-estrategicas.jpg"
        alt="Líneas estratégicas del PDI"
        className="flor-img"
        draggable={false}
      />

      {/* Círculo blanco que cubre el ícono original del centro, igual que la referencia */}
      <svg viewBox="0 0 721 735" className="flor-overlay" aria-hidden="true">
        <circle cx="374" cy="352" r="105" fill="white" />
      </svg>

      {/* Esfera giratoria: Comunidad -> Logo Poli -> Comunidad (loop), clic = volver */}
      <button
        type="button"
        className="esfera"
        onClick={onSelectCentro}
        aria-label="Volver a Resumen General"
        title="Volver a Resumen General"
      >
        <span className="esfera-banda">
          <span className="esfera-cara">
            <img src="/img/pdi/Comunidad.png" alt="" />
          </span>
          <span className="esfera-cara esfera-cara-logo">
            <img src="/img/brand/logo-poli.jpg" alt="" />
          </span>
          <span className="esfera-cara">
            <img src="/img/pdi/Comunidad.png" alt="" />
          </span>
        </span>
        <span className="esfera-curva" />
        <span className="esfera-luz" />
      </button>

      {/* Pétalos clicables por línea estratégica */}
      <svg viewBox="0 0 721 735" className="flor-petalos" aria-hidden="false">
        {PETALOS.map((p) => (
          <ellipse
            key={p.slug}
            cx={p.cx}
            cy={p.cy}
            rx={p.rx}
            ry={p.ry}
            className="petalo-hit"
            role="button"
            tabIndex={0}
            aria-label={`Ir a la línea estratégica ${p.slug.replace(/-/g, " ")}`}
            onClick={() => onSelectLinea(p.slug)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectLinea(p.slug);
              }
            }}
          />
        ))}
      </svg>

      {/* Alternativa accesible sin depender del hit-area SVG */}
      <nav aria-label="Líneas estratégicas" className="sr-only">
        <ul>
          {STRATEGIC_LINES.map((l) => (
            <li key={l.slug}>
              <a
                href={`/resumen-general/consolidado-por-linea/linea/${l.slug}`}
                onClick={(e) => {
                  e.preventDefault();
                  router.push(`/resumen-general/consolidado-por-linea/linea/${l.slug}`);
                }}
              >
                {l.label}
                {cumplimientoPorLinea?.[l.slug] != null
                  ? ` — ${cumplimientoPorLinea[l.slug]?.toFixed(1)}%`
                  : ""}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      <style>{`
        .flor-estrategica { position: relative; width: 100%; }
        .flor-img { width: 100%; height: 100%; display: block; object-fit: contain; }
        .flor-overlay { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 1; pointer-events: none; }
        .flor-petalos { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 4; pointer-events: none; }
        .petalo-hit { fill: rgba(0,0,0,0.001); cursor: pointer; pointer-events: all; transition: fill 0.2s ease; }
        .petalo-hit:hover, .petalo-hit:focus-visible { fill: rgba(11,95,255,0.12); outline: none; }

        .esfera {
          position: absolute; left: 51.9%; top: 47.9%; transform: translate(-50%, -50%);
          width: 28%; aspect-ratio: 1/1; border-radius: 50%; overflow: hidden;
          background: radial-gradient(circle at 38% 32%, #ffffff 0%, #f2eff2 38%, #d0cdd0 75%, #b8b5b8 100%);
          box-shadow: inset 0 -8px 18px rgba(0,30,80,0.1), inset 3px 3px 10px rgba(255,255,255,0.9),
            0 5px 18px rgba(0,0,0,0.18), 0 0 0 2px rgba(255,255,255,0.95);
          z-index: 3; padding: 0; border: none; cursor: pointer;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .esfera:hover, .esfera:focus-visible {
          transform: translate(-50%, -50%) scale(1.06);
          box-shadow: inset 0 -8px 18px rgba(0,30,80,0.1), inset 3px 3px 10px rgba(255,255,255,0.9),
            0 8px 24px rgba(11,95,255,0.35), 0 0 0 3px rgba(11,95,255,0.55);
          outline: none;
        }
        .esfera-banda {
          position: absolute; top: 0; left: 0; height: 100%; width: 300%;
          display: flex; animation: girar-esfera 8s linear infinite;
        }
        .esfera-cara { flex: 1; height: 100%; background: #f5f1f4; overflow: hidden; position: relative; }
        .esfera-cara img {
          position: absolute; width: 160%; height: auto; top: 50%; left: 50%; transform: translate(-50%, -50%);
        }
        .esfera-cara-logo img { width: 88%; mix-blend-mode: multiply; }
        .esfera-curva {
          position: absolute; inset: 0;
          background:
            radial-gradient(circle at 50% 50%, transparent 36%, rgba(0,20,60,0.14) 58%, rgba(0,20,60,0.50) 82%, rgba(0,20,60,0.68) 100%),
            radial-gradient(ellipse 28% 100% at 0% 50%, rgba(0,20,60,0.18) 0%, transparent 100%),
            radial-gradient(ellipse 28% 100% at 100% 50%, rgba(0,20,60,0.10) 0%, transparent 100%),
            radial-gradient(ellipse 100% 22% at 50% 100%, rgba(0,20,60,0.18) 0%, transparent 100%);
          z-index: 2; pointer-events: none;
        }
        .esfera-luz {
          position: absolute; width: 32%; height: 26%; top: 7%; left: 9%; border-radius: 50%;
          background: radial-gradient(ellipse, rgba(255,255,255,0.96) 0%, rgba(255,255,255,0.65) 35%, transparent 68%);
          pointer-events: none; z-index: 4;
        }
        @keyframes girar-esfera {
          from { transform: translateX(0%); }
          to   { transform: translateX(-66.66%); }
        }
        .sr-only {
          position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
          overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0;
        }
      `}</style>
    </div>
  );
}
