import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn() } }));

import {
  destinoValido,
  MODULOS_SIN_SELECCION,
  moduloHref,
  pdiPorDefecto,
  seleccionPdiHref,
  type Marco,
} from "./pdi";

describe("selector de PDI", () => {
  it("solo acepta como destino los módulos que exigen PDI", () => {
    expect(destinoValido("/resumen-general")).toBe("/resumen-general");
    expect(destinoValido("/cmi-estrategico")).toBe("/cmi-estrategico");
    expect(destinoValido("/cmi-procesos")).toBe("/cmi-procesos");
    expect(destinoValido("/gestion-om")).toBeNull();
    expect(destinoValido("https://evil.example")).toBeNull();
    expect(destinoValido(null)).toBeNull();
  });

  it("arma la URL del módulo con el PDI elegido", () => {
    expect(moduloHref("/cmi-estrategico", "PDI-2026-2030")).toBe("/cmi-estrategico?pdi=PDI-2026-2030");
  });

  it("arma la URL del selector con el destino codificado", () => {
    expect(seleccionPdiHref("/cmi-procesos")).toBe("/seleccion-pdi?destino=%2Fcmi-procesos");
  });
});

describe("pdiPorDefecto / MODULOS_SIN_SELECCION", () => {
  const marco = (version_id: string, estado: "activo" | "cerrado", orden: number) =>
    ({ version_id, estado, orden }) as Marco;

  it("elige el ciclo vigente y, sin vigente, el más reciente", () => {
    expect(pdiPorDefecto([marco("A", "cerrado", 1), marco("B", "activo", 2)])).toBe("B");
    expect(pdiPorDefecto([marco("A", "cerrado", 1), marco("C", "cerrado", 3)])).toBe("C");
    expect(pdiPorDefecto([])).toBeNull();
  });

  it("CMI por Procesos entra directo, sin pantalla de selección", () => {
    expect(MODULOS_SIN_SELECCION.has("/cmi-procesos")).toBe(true);
    expect(MODULOS_SIN_SELECCION.has("/cmi-estrategico")).toBe(false);
  });
});
