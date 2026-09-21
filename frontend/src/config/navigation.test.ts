import { describe, expect, it } from "vitest";
import { canAccessPath, navItemsForRole, splitIntoRows } from "./navigation";

const PROCESOS_HREFS = [
  "/resumen-general",
  "/cmi-estrategico",
  "/cmi-procesos",
  "/informe-procesos",
  "/plan-mejoramiento",
];

describe("navItemsForRole", () => {
  it("procesos ve solo las 5 pantallas permitidas, en orden", () => {
    expect(navItemsForRole("procesos").map((i) => i.href)).toEqual(PROCESOS_HREFS);
  });

  it.each(["administrador", "calidad", "desempeno"])("%s ve las 7 pantallas", (role) => {
    expect(navItemsForRole(role)).toHaveLength(7);
  });

  it("un rol ausente o desconocido se trata como procesos", () => {
    expect(navItemsForRole(null)).toHaveLength(5);
    expect(navItemsForRole(undefined)).toHaveLength(5);
    expect(navItemsForRole("otro")).toHaveLength(5);
  });
});

describe("canAccessPath", () => {
  it("procesos no accede a seguimiento operativo ni a gestión OM (ni subrutas)", () => {
    expect(canAccessPath("procesos", "/seguimiento-operativo")).toBe(false);
    expect(canAccessPath("procesos", "/gestion-om")).toBe(false);
    expect(canAccessPath("procesos", "/gestion-om/nuevo")).toBe(false);
  });

  it("procesos accede a sus 5 pantallas", () => {
    for (const href of PROCESOS_HREFS) expect(canAccessPath("procesos", href)).toBe(true);
  });

  it("administrador accede a todo", () => {
    expect(canAccessPath("administrador", "/gestion-om")).toBe(true);
    expect(canAccessPath("administrador", "/seguimiento-operativo")).toBe(true);
  });

  it("rutas fuera del menú (p. ej. /menu) no se restringen aquí", () => {
    expect(canAccessPath("procesos", "/menu")).toBe(true);
  });
});

describe("splitIntoRows", () => {
  const sizes = (n: number) =>
    splitIntoRows(Array.from({ length: n }, (_, i) => i)).map((r) => r.length);

  it("reparte parejo: 7 → 4+3, 5 → 3+2, 6 → 3+3, 4 → 4", () => {
    expect(sizes(7)).toEqual([4, 3]);
    expect(sizes(5)).toEqual([3, 2]);
    expect(sizes(6)).toEqual([3, 3]);
    expect(sizes(4)).toEqual([4]);
  });

  it("no pierde ni duplica elementos y conserva el orden", () => {
    expect(splitIntoRows([1, 2, 3, 4, 5]).flat()).toEqual([1, 2, 3, 4, 5]);
  });

  it("lista vacía → sin filas", () => {
    expect(splitIntoRows([])).toEqual([]);
  });
});
