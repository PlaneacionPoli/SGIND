"use client";

import { useRouter } from "next/navigation";
import { STRATEGIC_LINES } from "@/lib/strategic-lines";

// Réplica EXACTA del diagrama "Avance Líneas Estratégicas" del proyecto de
// referencia Informe_Interactivo_Poli_2025 (index.html, var avPiezas +
// slide-avances): 6 imágenes PNG independientes por línea (PDI/*.png)
// ensambladas con posicionamiento absoluto sobre un contenedor
// aspect-ratio 945/944, cada una con el mismo efecto hover del original
// (filter: brightness/saturate/drop-shadow con el color de la línea) y
// cursor pointer + onClick. Comunidad.png va decorativa en el centro.
// Única diferencia funcional: el centro navega de vuelta a Resumen
// General (en el original es solo decorativo, sin acción).
interface PiezaDef {
  slug: string;
  img: string;
  css: React.CSSProperties;
}

const PIEZAS: PiezaDef[] = [
  {
    slug: "sostenibilidad",
    img: "/img/pdi/SOSTENIBILIDAD.png",
    css: { top: "5.3%", left: 0, width: "100%", height: "50%", zIndex: 1 },
  },
  {
    slug: "transformacion-organizacional",
    img: "/img/pdi/Tranformacion.png",
    css: { bottom: "5.84%", left: 0, width: "100%", height: "50%", zIndex: 1 },
  },
  {
    slug: "expansion",
    img: "/img/pdi/Expansion.png",
    css: { top: "13%", right: "9%", width: "50%", height: "50%", zIndex: 3 },
  },
  {
    slug: "educacion-para-toda-la-vida",
    img: "/img/pdi/Eduvida.png",
    css: { bottom: "9%", right: "13.3%", width: "50%", height: "50%", zIndex: 3 },
  },
  {
    slug: "experiencia",
    img: "/img/pdi/Experiencia.png",
    css: { bottom: "13.4%", left: "9%", width: "50%", height: "50%", zIndex: 3 },
  },
  {
    slug: "calidad",
    img: "/img/pdi/Calidad.png",
    css: { top: "17%", left: "18%", width: "41%", height: "31.5%", zIndex: 3 },
  },
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
    <div className="flor-estrategica mx-auto" style={{ aspectRatio: "945/944", maxWidth: 560 }}>
      {PIEZAS.map((p) => {
        const line = STRATEGIC_LINES.find((l) => l.slug === p.slug);
        return (
          <div
            key={p.slug}
            className="pieza"
            style={{ ...p.css, ["--glow" as string]: `${line?.color ?? "#0F385A"}CC` }}
            onClick={() => onSelectLinea(p.slug)}
            role="button"
            tabIndex={0}
            aria-label={`Ir a la línea estratégica ${line?.label ?? p.slug}`}
            title={line?.label ?? p.slug}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectLinea(p.slug);
              }
            }}
          >
            <img src={p.img} alt={line?.label ?? p.slug} draggable={false} />
          </div>
        );
      })}

      {/* Comunidad Universitaria — centro; clic = volver a Resumen General */}
      <div
        className="pieza pieza-centro"
        onClick={onSelectCentro}
        role="button"
        tabIndex={0}
        aria-label="Volver a Resumen General"
        title="Volver a Resumen General"
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onSelectCentro();
          }
        }}
      >
        <img src="/img/pdi/Comunidad.png" alt="Comunidad Universitaria" draggable={false} />
      </div>

      {/* Alternativa accesible sin depender del hover/hit-area (lectores de pantalla / teclado) */}
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
        .pieza {
          position: absolute; cursor: pointer; transition: filter 0.18s ease;
        }
        .pieza img { width: 100%; height: 100%; display: block; pointer-events: none; }
        .pieza:hover, .pieza:focus-visible {
          filter: brightness(1.2) saturate(1.3) drop-shadow(0 0 18px var(--glow));
          outline: none;
        }
        .pieza-centro {
          position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
          width: 70%; height: auto; z-index: 5; border-radius: 50%;
        }
        .pieza-centro:hover, .pieza-centro:focus-visible {
          filter: brightness(1.08) drop-shadow(0 0 14px rgba(11,95,255,0.55));
        }
        .sr-only {
          position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
          overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0;
        }
      `}</style>
    </div>
  );
}
