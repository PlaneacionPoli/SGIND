import { describe, expect, it } from "vitest";
import { TRAMOS_CALOR, tonoCumplimiento, tramoCalor } from "./constants";
import { ventanaPaginas } from "./Paginador";

describe("ventanaPaginas", () => {
  it("muestra todas las páginas si son pocas", () => {
    expect(ventanaPaginas(0, 5)).toEqual([0, 1, 2, 3, 4]);
  });

  it("agrega puntos suspensivos entre la ventana y los extremos", () => {
    expect(ventanaPaginas(10, 20)).toEqual([0, "…", 9, 10, 11, "…", 19]);
  });

  it("al inicio y al final mantiene un bloque contiguo", () => {
    expect(ventanaPaginas(0, 20)).toEqual([0, 1, 2, 3, "…", 19]);
    expect(ventanaPaginas(19, 20)).toEqual([0, "…", 16, 17, 18, 19]);
  });

  it("nunca repite ni sale del rango", () => {
    for (let total = 1; total <= 30; total++) {
      for (let actual = 0; actual < total; actual++) {
        const nums = ventanaPaginas(actual, total).filter((n): n is number => n !== "…");
        expect(new Set(nums).size).toBe(nums.length);
        expect(nums.every((n) => n >= 0 && n < total)).toBe(true);
        expect(nums).toContain(actual);
      }
    }
  });
});

describe("escala del mapa de calor", () => {
  it("asigna cada porcentaje a un tramo, incluidos los bordes", () => {
    expect(tramoCalor(0).label).toBe("< 50 %");
    expect(tramoCalor(49.9).label).toBe("< 50 %");
    expect(tramoCalor(50).label).toBe("50–79 %");
    expect(tramoCalor(80).label).toBe("80–99 %");
    expect(tramoCalor(99.9).label).toBe("80–99 %");
    expect(tramoCalor(100).label).toBe("100 %");
  });

  it("los tramos cubren 0–100 sin huecos", () => {
    for (let i = 1; i < TRAMOS_CALOR.length; i++) {
      expect(TRAMOS_CALOR[i].min).toBe(TRAMOS_CALOR[i - 1].max);
    }
  });

  it("etiqueta el cumplimiento de un proceso", () => {
    expect(tonoCumplimiento(null).label).toBe("Sin exigibles");
    expect(tonoCumplimiento(100).label).toBe("Al día");
    expect(tonoCumplimiento(85).label).toBe("En curso");
    expect(tonoCumplimiento(40).label).toBe("Atrasado");
  });
});
