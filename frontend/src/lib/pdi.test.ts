import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn() } }));

import { destinoValido, moduloHref, seleccionPdiHref } from "./pdi";

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
