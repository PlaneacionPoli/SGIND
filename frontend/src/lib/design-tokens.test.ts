import { describe, expect, it } from "vitest";
import {
  getSemaforoBg,
  getSemaforoColor,
  NEUTRAL,
  SEMAFORO,
  SEMAFORO_BG,
  SEMAFORO_COLOR,
} from "./design-tokens";

describe("getSemaforoColor", () => {
  it.each([
    ["Peligro", SEMAFORO.peligro],
    ["peligro", SEMAFORO.peligro],
    ["Alerta", SEMAFORO.alerta],
    ["Cumplimiento", SEMAFORO.cumplimiento],
    ["Sobrecumplimiento", SEMAFORO.sobre],
  ])("resuelve %s -> %s (case-insensitive)", (nivel, expected) => {
    expect(getSemaforoColor(nivel)).toBe(expected);
  });

  it("cae a NEUTRAL.mutedFg para un nivel desconocido", () => {
    expect(getSemaforoColor("no-existe")).toBe(NEUTRAL.mutedFg);
  });
});

describe("getSemaforoBg", () => {
  it.each([
    ["Peligro", SEMAFORO.peligroBg],
    ["Alerta", SEMAFORO.alertaBg],
    ["Cumplimiento", SEMAFORO.cumplimientoBg],
    ["Sobrecumplimiento", SEMAFORO.sobreBg],
  ])("resuelve %s -> %s", (nivel, expected) => {
    expect(getSemaforoBg(nivel)).toBe(expected);
  });

  it("cae a NEUTRAL.muted para un nivel desconocido", () => {
    expect(getSemaforoBg("no-existe")).toBe(NEUTRAL.muted);
  });
});

describe("consistencia SEMAFORO_COLOR / SEMAFORO_BG", () => {
  it("tiene una entrada de color y de fondo para cada NivelSemaforo declarado", () => {
    const niveles = Object.keys(SEMAFORO_COLOR);
    expect(Object.keys(SEMAFORO_BG).sort()).toEqual(niveles.sort());
  });
});
