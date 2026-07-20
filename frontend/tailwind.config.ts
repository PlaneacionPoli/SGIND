import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // ─── Colores ───────────────────────────────────────────────────────────
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",

        // Marca Poli
        poli: {
          navy:       "#1a2b4a",   // sidebar, headings
          "navy-700": "#243554",   // hover sobre navy
          "navy-50":  "#f0f3f8",   // fondos muy claros con tono navy
          blue:       "#2563eb",   // CTAs, estados activos
          "blue-dark":"#1d4ed8",   // hover sobre blue
          "blue-50":  "#eff6ff",   // fondos informativos
          gold:       "#c9a227",   // acento logo/marca
          "gold-50":  "#fef9e7",   // fondos dorados suaves
        },

        // Semáforo de indicadores (fuente única — §3.3 PROJECT_RULES)
        semaforo: {
          peligro:          "#ef4444",  // rojo
          "peligro-bg":     "#fef2f2",
          alerta:           "#f59e0b",  // ámbar
          "alerta-bg":      "#fffbeb",
          cumplimiento:     "#22c55e",  // verde
          "cumplimiento-bg":"#f0fdf4",
          sobre:            "#3b82f6",  // azul (sobrecumplimiento)
          "sobre-bg":       "#eff6ff",
        },

        // Neutros de UI (complementan slate de Tailwind)
        border:   "var(--border)",
        surface:  "var(--surface)",
        muted:    "var(--muted)",
        "muted-fg": "var(--muted-fg)",
      },

      // ─── Tipografía ────────────────────────────────────────────────────────
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.875rem" }],
      },

      // ─── Sombras ───────────────────────────────────────────────────────────
      boxShadow: {
        card:     "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        elevated: "0 4px 12px 0 rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.06)",
        overlay:  "0 20px 40px -8px rgb(0 0 0 / 0.18)",
        "inner-sm":"inset 0 1px 2px 0 rgb(0 0 0 / 0.06)",
      },

      // ─── Radios ────────────────────────────────────────────────────────────
      borderRadius: {
        "4xl": "2rem",
      },

      // ─── Animaciones ───────────────────────────────────────────────────────
      keyframes: {
        shimmer: {
          "0%":   { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
        "fade-in": {
          "0%":   { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in": {
          "0%":   { opacity: "0", transform: "translateX(-8px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
      },
      animation: {
        shimmer:  "shimmer 1.6s ease-in-out infinite",
        "fade-in":"fade-in 0.2s ease-out",
        "slide-in":"slide-in 0.18s ease-out",
      },

      // ─── Transiciones ──────────────────────────────────────────────────────
      transitionDuration: {
        "250": "250ms",
      },
    },
  },
  plugins: [],
};
export default config;
